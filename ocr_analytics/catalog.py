"""Explicit report catalog; development and test runs never share a denominator."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("document_id", "date", "amount")


def catalog(root=ROOT, fresh_font=None):
    rows = []

    def add(cohort, split, manifest, report, methods, scope):
        rows.append(
            dict(
                cohort=cohort,
                split=split,
                manifest=root / manifest,
                report=root / report,
                methods=methods,
                scope=scope,
            )
        )

    add(
        "legacy",
        "dev",
        "challenge_data/manifest.json",
        "challenge_output/dev_report.json",
        ["raw", "grayscale_threshold"],
        "initial challenge development",
    )
    for split in ("dev", "test"):
        add(
            "legacy",
            split,
            "challenge_data/manifest.json",
            f"enhanced_output/{split}_report.json",
            ["raw", "grayscale_threshold", "raw_validated", "enhanced"],
            "enhanced comparison",
        )
    add(
        "legacy",
        "dev",
        "challenge_data/manifest.json",
        "experiments/ocr_variants_20261016/report.json",
        ["current", "prepared_sparse", "grayscale_block", "prepared_otsu"],
        "inspected development variants",
    )
    for family, methods in [
        ("line", ["page_current", "line_upscale"]),
        ("model", ["installed", "tessdata_best"]),
    ]:
        prefix = f"experiments/{family}_cohort_20261016"
        for split in ("dev", "test"):
            add(
                family,
                split,
                f"{prefix}/manifest.json",
                f"{prefix}/{split}_report.json",
                methods,
                family + " comparison; pretrained weights only",
            )
    prefix = "supplements/review_priority"
    for split in ("dev", "test"):
        add(
            "priority",
            split,
            f"{prefix}/dataset/manifest.json",
            f"{prefix}/measured_linux/{split}_predictions.json",
            ["raw", "upscale_sharpen"],
            "development Linux; frozen dev-selected policy",
        )
    add(
        "font_challenge",
        "challenge",
        f"{prefix}/challenge_font_dataset/manifest.json",
        f"{prefix}/measured_font_challenge/predictions.json",
        ["raw", "upscale_sharpen"],
        "development Linux; frozen font/layout challenge",
    )
    if fresh_font:
        rows[-1]["report"] = Path(fresh_font)
        rows[-1]["scope"] = "fresh local reproduction of inspected font/layout cohort"
    for spec in rows:
        spec["require_images"] = spec["cohort"] not in ("line", "model")
    return rows


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
