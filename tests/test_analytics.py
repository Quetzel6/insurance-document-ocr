"""Data-contract and transactional tests for analytical OCR tables."""

import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ocr_analytics.catalog import catalog, read_json
from ocr_analytics.pipeline import import_reviews, load, prepare, report, sha


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = self.folder / "analytics.sqlite3"
        self.spec = catalog()[-1]

    def changed(self, mutate):
        spec = dict(self.spec)
        rows = copy.deepcopy(read_json(spec["report"]))
        mutate(rows)
        spec["report"] = self.folder / "predictions.json"
        spec["report"].write_text(json.dumps(rows))
        return spec

    def count(self, table):
        with sqlite3.connect(self.db) as c:
            return c.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]

    def test_manifest_counts_exact_scores_and_replay(self):
        self.assertEqual(load([self.spec], self.db)["loaded_runs"], 1)
        self.assertEqual(
            (self.count("images"), self.count("predictions"), self.count("field_results")), (36, 72, 216)
        )
        self.assertEqual(load([self.spec], self.db), dict(loaded_runs=0, duplicate_runs=1))
        with sqlite3.connect(self.db) as c:
            actual = c.execute(
                "SELECT method,SUM(outcome='wrong') FROM field_results GROUP BY method"
            ).fetchall()
        self.assertEqual(actual, [("raw", 7), ("upscale_sharpen", 6)])

    def test_missing_prediction_fails_before_database_creation(self):
        spec = self.changed(lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "coverage"):
            load([spec], self.db)
        self.assertFalse(self.db.exists())

    def test_duplicate_prediction_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            prepare(self.changed(lambda rows: rows.append(rows[0])))

    def test_incorrect_recorded_match_rejected(self):
        with self.assertRaisesRegex(ValueError, "recorded score"):
            prepare(self.changed(lambda rows: rows[0]["matches"].update(date=False)))

    def test_unknown_field_rejected(self):
        with self.assertRaisesRegex(ValueError, "schema"):
            prepare(self.changed(lambda rows: rows[0]["prediction"].update(extra="x")))

    def test_invalid_confidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "confidence"):
            prepare(self.changed(lambda rows: rows[0].update(mean_word_confidence=float("nan"))))

    def test_missing_original_lineage_rejected(self):
        with self.assertRaisesRegex(ValueError, "lineage"):
            prepare(self.changed(lambda rows: rows[0].update(original_id=None)))

    def test_unowned_database_preserved(self):
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TABLE private_data(value TEXT)")
        before = self.db.read_bytes()
        with self.assertRaisesRegex(ValueError, "unowned"):
            load([self.spec], self.db)
        self.assertEqual(self.db.read_bytes(), before)

    def test_dimension_conflict_rolls_back_new_run(self):
        load([self.spec], self.db)
        with sqlite3.connect(self.db) as c:
            c.execute("UPDATE images SET font='changed'")
        spec = self.changed(lambda rows: rows[0].update(text=rows[0]["text"] + "\n"))
        with self.assertRaisesRegex(ValueError, "dimension conflict"):
            load([spec], self.db)
        self.assertEqual(self.count("runs"), 1)
        self.assertEqual(self.count("predictions"), 72)

    def test_sql_constraints_reject_false_outcome(self):
        load([self.spec], self.db)
        with sqlite3.connect(self.db) as c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("UPDATE field_results SET outcome='missing' WHERE predicted_value IS NOT NULL")

    def test_all_recorded_cohorts_have_complete_coverage(self):
        specs = catalog()
        load(specs, self.db)
        self.assertEqual(self.count("runs"), len(specs))
        self.assertEqual(self.count("field_results"), self.count("predictions") * 3)
        self.assertEqual(self.count("review_decisions"), 0)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                c.execute("SELECT COUNT(*) FROM images WHERE image_bytes_verified=0").fetchone()[0], 96
            )

    def review_fixture(self):
        spec = next(s for s in catalog() if s["cohort"] == "legacy" and s["split"] == "test")
        load([spec], self.db)
        row = next(r for r in read_json(spec["report"])["records"] if r["method"] == "enhanced")
        original = {k: v or "" for k, v in row["prediction"].items()}
        decision = dict(
            id=row["id"],
            version=1,
            status="rejected",
            review_mode="structured",
            original=original,
            values=dict(original, amount="1.00"),
            saved_at="2026-10-21T01:00:00+00:00",
        )
        data = dict(
            queue_kind="benchmark",
            run_id="test-only-round",
            report_sha=sha(spec["report"]),
            decisions=[decision],
        )
        path = self.folder / "reviews.json"
        path.write_text(json.dumps(data))
        return path, data

    def test_actual_export_mapping_and_duplicate_import(self):
        path, data = self.review_fixture()
        import_reviews(self.db, path)
        import_reviews(self.db, path)
        self.assertEqual(self.count("review_decisions"), 1)
        self.assertEqual(self.count("review_fields"), 3)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute("SELECT SUM(changed) FROM review_fields").fetchone()[0], 1)
        data["decisions"][0]["original"]["amount"] = "not-source"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "original differs"):
            import_reviews(self.db, path)
        self.assertEqual(self.count("review_decisions"), 1)

    def test_review_snapshot_conflict_rejected(self):
        path, data = self.review_fixture()
        import_reviews(self.db, path)
        data["decisions"][0]["values"]["date"] = "2020-01-01"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "snapshot conflict"):
            import_reviews(self.db, path)

    def test_report_escapes_observed_text_and_no_fake_reviews(self):
        spec = dict(self.spec, cohort="<script>alert(1)</script>")
        load([spec], self.db)
        result = report(self.db, self.folder)
        self.assertEqual(result["counts"]["review_decisions"], 0)
        self.assertIn("No review decisions supplied", (self.folder / "report.html").read_text())
        self.assertEqual(result["integrity_check"], "ok")
        page = (self.folder / "report.html").read_text()
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_replay_detects_modified_storage(self):
        load([self.spec], self.db)
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE predictions SET ocr_text='changed'")
        with self.assertRaisesRegex(ValueError, "stored predictions"):
            load([self.spec], self.db)


if __name__ == "__main__":
    unittest.main()
