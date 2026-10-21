"""Validate the supplied Docker-on-Mac artifacts without rerunning or relabeling OCR."""

import importlib.util
import json
import math
from pathlib import Path

from ocr_analytics.catalog import ROOT, catalog, read_json
from ocr_analytics.pipeline import prepare, sha

PREFIX = Path("supplements/review_priority")


def verify(root=ROOT):
    folder = root / PREFIX / "mac_font_challenge_01"
    evidence = read_json(root / PREFIX / "MAC_ARTIFACT_VERIFICATION.json")
    for name, digest in evidence["artifact_sha256"].items():
        if sha(folder / name) != digest:
            raise ValueError("supplied Mac artifact changed: " + name)
    spec = next(s for s in catalog(root) if s["cohort"] == "font_challenge")
    spec = dict(spec, report=folder / "predictions.json")
    bundle = prepare(spec)
    rows = read_json(spec["report"])
    result = read_json(folder / "results.json")
    protocol = read_json(folder / "frozen_protocol.json")
    fingerprint = result["fingerprint"]
    expected_sources = {
        "original_policy_sha256": root / PREFIX / "measured_linux/frozen_policy.json",
        "experiment_sha256": root / PREFIX / "experiment.py",
        "challenge_source_sha256": root / PREFIX / "challenge_eval.py",
        "original_manifest_sha256": root / PREFIX / "dataset/manifest.json",
    }
    for key, path in expected_sources.items():
        if fingerprint["protocol"][key] != sha(path):
            raise ValueError("Mac source fingerprint differs: " + key)
    if fingerprint["manifest_sha256"] != bundle["manifest_sha"] or protocol["fingerprint"] != fingerprint:
        raise ValueError("Mac manifest/protocol fingerprint differs")
    if fingerprint["protocol"]["method"] != "upscale_sharpen" or fingerprint["protocol"]["threshold"] != 0:
        raise ValueError("Mac policy differs")
    module_spec = importlib.util.spec_from_file_location("frozen_priority", root / PREFIX / "experiment.py")
    base = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(base)
    for row in rows:
        expected = bundle["images"][row["id"]]["fields"]
        if row["expected"] != expected or row["complete_correct"] != all(row["matches"].values()):
            raise ValueError("Mac record score/labels differ")
        if not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0:
            raise ValueError("invalid elapsed time")
    comparisons = [base.summary(rows, method, 0) for method in ("raw", "upscale_sharpen")]
    if result["descriptive_comparators"] != comparisons or result["selected_policy"] != comparisons[1]:
        raise ValueError("Mac aggregate differs from per-image predictions")
    for dimension in ("font", "condition"):
        breakdown = {
            value: base.summary([r for r in rows if r[dimension] == value], "upscale_sharpen", 0)
            for value in sorted({r[dimension] for r in rows})
        }
        if result["breakdown"][dimension] != breakdown:
            raise ValueError("Mac breakdown differs")
    linux = read_json(root / PREFIX / "measured_font_challenge/predictions.json")
    by_key = {(r["id"], r["method"]): r for r in linux}
    differences = {
        key: sum(row[key] != by_key[(row["id"], row["method"])][key] for row in rows)
        for key in ("prediction", "text", "mean_word_confidence")
    }
    if differences != evidence["record_differences_vs_development_linux"]:
        raise ValueError("documented cross-run differences changed")
    print(
        json.dumps(dict(status="verified_supplied_artifacts", predictions=len(rows), differences=differences))
    )


if __name__ == "__main__":
    verify()
