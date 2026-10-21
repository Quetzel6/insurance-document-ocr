"""Validate OCR evidence, load typed SQLite tables and report SQL results."""

import argparse
import csv
import hashlib
import html
import json
import math
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .catalog import FIELDS, ROOT, catalog, read_json

SCHEMA_VERSION = "ocr-analytics-v1"
TABLES = ("runs", "images", "predictions", "field_results", "review_decisions", "review_fields")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_frozen(root=ROOT):
    inventory = read_json(root / "docs/evidence/frozen_files.json")
    for path, digest in inventory.items():
        if sha(root / path) != digest:
            raise ValueError("frozen evidence changed: " + path)
    return len(inventory)


def required_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing or invalid " + label)
    return value


def prepare(spec):
    manifest = read_json(spec["manifest"])
    source = read_json(spec["report"])
    records = source["records"] if isinstance(source, dict) else source
    if not isinstance(records, list) or not records:
        raise ValueError("empty prediction report")
    images = [r for r in manifest["records"] if r.get("split", "challenge") == spec["split"]]
    by_id = {}
    for r in images:
        image_id = required_string(r.get("id"), "image id")
        if image_id in by_id:
            raise ValueError("duplicate manifest image")
        for field in ("original_id", "condition", "image"):
            required_string(r.get(field), field)
        if set(r["fields"]) != set(FIELDS):
            raise ValueError("invalid label fields")
        for field in FIELDS:
            required_string(r["fields"][field], "expected " + field)
        folder = Path(spec["manifest"]).parent.resolve()
        path = (folder / r["image"]).resolve()
        if (
            not path.is_relative_to(folder)
            or (path.exists() and sha(path) != r.get("sha", r.get("sha256")))
            or (not path.exists() and spec.get("require_images", True))
        ):
            raise ValueError("image path/hash mismatch")
        r = dict(r, image_bytes_verified=int(path.is_file()))
        by_id[image_id] = r
    if not by_id:
        raise ValueError("empty manifest split")
    expected_keys = {(image_id, method) for image_id in by_id for method in spec["methods"]}
    seen = set()
    prepared = []
    for row in records:
        key = (row["id"], row["method"])
        if key not in expected_keys or key in seen:
            raise ValueError("unknown or duplicate prediction")
        seen.add(key)
        source_image = by_id[row["id"]]
        if (
            row.get("original_id") != source_image["original_id"]
            or row.get("condition") != source_image["condition"]
        ):
            raise ValueError("prediction lineage mismatch")
        if set(row["prediction"]) != set(FIELDS) or set(row["matches"]) != set(FIELDS):
            raise ValueError("prediction field schema mismatch")
        if not isinstance(row.get("text"), str):
            raise ValueError("OCR text must be a string")
        confidence = row.get("mean_word_confidence")
        if confidence is not None and (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 100
        ):
            raise ValueError("invalid confidence")
        values = []
        for field in FIELDS:
            predicted = row["prediction"][field]
            if predicted is not None and not isinstance(predicted, str):
                raise ValueError("predicted value must be text or null")
            predicted = predicted if predicted else None
            expected = source_image["fields"][field]
            exact = predicted == expected
            if not isinstance(row["matches"][field], bool) or row["matches"][field] != exact:
                raise ValueError("recorded score differs from source labels")
            values.append(
                (
                    field,
                    expected,
                    predicted,
                    "missing" if predicted is None else "correct" if exact else "wrong",
                )
            )
        prepared.append((row, confidence, values))
    if seen != expected_keys:
        raise ValueError("prediction coverage differs from manifest")
    manifest_sha, report_sha = sha(spec["manifest"]), sha(spec["report"])
    identity = json.dumps([spec["cohort"], spec["split"], manifest_sha, report_sha], separators=(",", ":"))
    return dict(
        spec=spec,
        images=by_id,
        predictions=prepared,
        manifest_sha=manifest_sha,
        report_sha=report_sha,
        run_id=hashlib.sha256(identity.encode()).hexdigest(),
    )


def connect_owned(path):
    path = Path(path)
    if path.exists():
        conn = sqlite3.connect(path)
        try:
            owner = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if owner != (SCHEMA_VERSION,):
                raise ValueError("unowned analytical database")
        except Exception:
            conn.close()
            raise ValueError("unowned analytical database") from None
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.executescript((ROOT / "sql/analytics/schema.sql").read_text())
        conn.execute("INSERT INTO metadata VALUES ('schema_version',?)", (SCHEMA_VERSION,))
        conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def reconcile_bundle(conn, bundle):
    run_id = bundle["run_id"]
    expected = sorted(
        (run_id, row["id"], row["method"], *value)
        for row, _, values in bundle["predictions"]
        for value in values
    )
    actual = conn.execute(
        "SELECT * FROM field_results WHERE run_id=? ORDER BY run_id,image_id,method,field", (run_id,)
    ).fetchall()
    if actual != expected:
        raise ValueError("stored field results differ from source")
    expected_predictions = sorted(
        (run_id, bundle["spec"]["cohort"], row["id"], row["method"], row["text"], confidence)
        for row, confidence, _ in bundle["predictions"]
    )
    actual_predictions = conn.execute(
        "SELECT * FROM predictions WHERE run_id=? ORDER BY run_id,cohort_id,image_id,method", (run_id,)
    ).fetchall()
    if actual_predictions != expected_predictions:
        raise ValueError("stored predictions differ from source")


def load(specs, database):
    bundles = [prepare(s) for s in specs]  # Fail before creating a database on invalid input.
    conn = connect_owned(database)
    loaded, duplicates = 0, 0
    try:
        with conn:
            for b in bundles:
                s, run_id = b["spec"], b["run_id"]
                if conn.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
                    reconcile_bundle(conn, b)
                    duplicates += 1
                    continue
                conn.execute(
                    "INSERT INTO runs VALUES (?,?,?,?,?,?)",
                    (run_id, s["cohort"], b["report_sha"], b["manifest_sha"], s["split"], s["scope"]),
                )
                for image_id, r in b["images"].items():
                    image = (
                        s["cohort"],
                        image_id,
                        r["original_id"],
                        s["split"],
                        r["condition"],
                        r.get("font"),
                        r.get("sha", r.get("sha256")),
                        r["image_bytes_verified"],
                    )
                    old = conn.execute(
                        "SELECT * FROM images WHERE cohort_id=? AND image_id=?", image[:2]
                    ).fetchone()
                    if old is not None and old != image:
                        raise ValueError("image dimension conflict")
                    if old is None:
                        conn.execute("INSERT INTO images VALUES (?,?,?,?,?,?,?,?)", image)
                for row, confidence, values in b["predictions"]:
                    conn.execute(
                        "INSERT INTO predictions VALUES (?,?,?,?,?,?)",
                        (run_id, s["cohort"], row["id"], row["method"], row["text"], confidence),
                    )
                    conn.executemany(
                        "INSERT INTO field_results VALUES (?,?,?,?,?,?,?)",
                        [(run_id, row["id"], row["method"], *v) for v in values],
                    )
                reconcile_bundle(conn, b)
                loaded += 1
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("foreign key violations")
            counts = dict(
                conn.execute(
                    "SELECT 'predictions',COUNT(*) FROM predictions UNION ALL SELECT 'field_results',COUNT(*) FROM field_results"
                )
            )
            if counts["field_results"] != 3 * counts["predictions"]:
                raise ValueError("field count mismatch")
    finally:
        conn.close()
    return dict(loaded_runs=loaded, duplicate_runs=duplicates)


def import_reviews(database, export_path):
    data = read_json(export_path)
    if data.get("queue_kind") != "benchmark":
        raise ValueError("only synthetic benchmark review exports are supported")
    round_id = required_string(data.get("run_id"), "review round")
    conn = connect_owned(database)
    try:
        run = conn.execute(
            "SELECT run_id FROM runs WHERE report_sha=? AND cohort_id='legacy' AND split='test'",
            (data.get("report_sha"),),
        ).fetchone()
        if run is None:
            raise ValueError("review source report not loaded")
        seen = set()
        with conn:
            for d in data["decisions"]:
                image_id = required_string(d.get("id"), "review image")
                if image_id in seen:
                    raise ValueError("duplicate decision")
                seen.add(image_id)
                if d.get("review_mode", "structured") != "structured" or d["status"] not in (
                    "approved",
                    "rejected",
                ):
                    raise ValueError("invalid review mode/status")
                if (
                    not isinstance(d.get("version"), int)
                    or isinstance(d["version"], bool)
                    or d["version"] < 1
                ):
                    raise ValueError("invalid decision version")
                timestamp = datetime.fromisoformat(d["saved_at"])
                if timestamp.tzinfo is None:
                    raise ValueError("review timestamp requires timezone")
                for group in ("values", "original"):
                    if set(d[group]) != set(FIELDS) or any(not isinstance(v, str) for v in d[group].values()):
                        raise ValueError("invalid review field schema")
                originals = dict(
                    conn.execute(
                        "SELECT field,COALESCE(predicted_value,'') FROM field_results WHERE run_id=? AND image_id=? AND method='enhanced'",
                        (run[0], image_id),
                    )
                )
                if originals != d["original"]:
                    raise ValueError("review original differs from recorded prediction")
                key = (round_id, run[0], image_id, "enhanced")
                record = (*key, d["version"], d["status"], d["saved_at"])
                old = conn.execute(
                    "SELECT * FROM review_decisions WHERE review_round=? AND run_id=? AND image_id=? AND method=?",
                    key,
                ).fetchone()
                values = [(*key, f, d["values"][f], int(d["values"][f] != d["original"][f])) for f in FIELDS]
                if old:
                    existing = conn.execute(
                        "SELECT * FROM review_fields WHERE review_round=? AND run_id=? AND image_id=? AND method=? ORDER BY field",
                        key,
                    ).fetchall()
                    if old != record or existing != sorted(values, key=lambda r: r[4]):
                        raise ValueError(
                            "review snapshot conflict; use a new analytical output for changed decisions"
                        )
                    continue
                conn.execute("INSERT INTO review_decisions VALUES (?,?,?,?,?,?,?)", record)
                conn.executemany("INSERT INTO review_fields VALUES (?,?,?,?,?,?,?)", values)
    finally:
        conn.close()


def report(database, output):
    output = Path(output)
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    results = {}
    try:
        for table in TABLES:
            cursor = conn.execute("SELECT * FROM " + table + " ORDER BY 1,2,3")
            with (output / (table + ".csv")).open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([c[0] for c in cursor.description])
                writer.writerows(cursor)
        for query in sorted((ROOT / "sql/analytics").glob("[0-9]*.sql")):
            results[query.stem] = [dict(r) for r in conn.execute(query.read_text())]
        counts = {t: conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in TABLES}
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("database integrity check failed")
    finally:
        conn.close()
    (output / "query_results.json").write_text(json.dumps(results, indent=2))
    body = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>OCR analytical evidence</title>',
        "<style>body{font:15px/1.5 system-ui;margin:32px;color:#173b4a}table{border-collapse:collapse;font-size:13px}td,th{border:1px solid #ccd8dd;padding:7px;max-width:240px;overflow-wrap:anywhere}details{margin:20px 0}h1{margin-bottom:4px}</style>",
        "<h1>OCR analytical evidence</h1><p>Synthetic evaluation, separated by cohort, split and run. All images require human review. Missing values and wrong emitted values are separate. Review edits are observations, not correctness labels.</p>",
        "<p>Six SQL questions; full results in query_results.json and typed CSV exports. Tables preview at most 120 rows each.</p>",
        "<p>Row counts: " + html.escape(json.dumps(counts)) + "</p>",
    ]
    for name, rows in results.items():
        body.append(
            "<details open><summary>" + html.escape(name) + " (" + str(len(rows)) + " rows)</summary>"
        )
        if not rows:
            body.append(
                "<p>No review decisions supplied; no human corrections or productivity benefit can be inferred.</p>"
            )
        else:
            keys = list(rows[0])
            body.append("<table><tr>" + "".join("<th>" + html.escape(k) + "</th>" for k in keys) + "</tr>")
            for row in rows[:120]:
                body.append(
                    "<tr>"
                    + "".join(
                        "<td>" + html.escape(str(row[k]) if row[k] is not None else "not available") + "</td>"
                        for k in keys
                    )
                    + "</tr>"
                )
            body.append("</table>")
        body.append("</details>")
    (output / "report.html").write_text("".join(body) + "</html>")
    return dict(counts=counts, integrity_check=integrity)


def run(output=None, live=False, review_export=None):
    verify_frozen()
    out = (
        Path(output)
        if output
        else ROOT
        / "output/analytics"
        / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out = out.resolve()
    if out.exists():
        raise ValueError("output exists; choose a new run directory")
    # Runs may only be inside the ignored analytical output tree or outside the repository.
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / "output/analytics"):
        raise ValueError("output must be under output/analytics or outside repository")
    out.mkdir(parents=True)
    fresh = None
    stages = []
    try:
        if live:
            child = out / "font_reproduction"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "supplements/review_priority/challenge_eval.py"),
                    "run",
                    "--dataset",
                    str(ROOT / "supplements/review_priority/challenge_font_dataset"),
                    "--out",
                    str(child),
                ],
                check=True,
            )
            fresh = child / "predictions.json"
            stages.append("actual OCR and extraction completed")
        database = out / "analytics.sqlite3"
        first = load(catalog(fresh_font=fresh), database)
        stages.append("validated inputs and committed analytical tables")
        replay = load(catalog(fresh_font=fresh), database)
        if replay["loaded_runs"] != 0:
            raise ValueError("replay inserted new runs")
        if review_export:
            import_reviews(database, review_export)
            stages.append("imported supplied review decisions")
        result = dict(
            status="passed_local",
            api_calls=0,
            live_ocr=live,
            run_dir=str(out),
            first_load=first,
            replay=replay,
            stages=stages,
            **report(database, out),
        )
        verify_frozen()
    except Exception as exc:
        (out / "pipeline_status.json").write_text(
            json.dumps(dict(status="failed", stages=stages, error=type(exc).__name__), indent=2)
        )
        raise
    (out / "pipeline_status.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--review-export", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.live, args.review_export), indent=2))


if __name__ == "__main__":
    main()
