"""Keep public documentation linked to recorded evidence and free of private notes."""

import re

from ocr_analytics.catalog import ROOT, catalog
from ocr_analytics.pipeline import prepare


def check(root=ROOT):
    errors = []
    if (root / "PORTFOLIO_FINISH.md").exists():
        errors.append("private portfolio note is present")
    paths = [root / "README.md"]
    for directory in ("docs", "supplements", "experiments"):
        paths.extend((root / directory).rglob("*.md"))
    for path in paths:
        text = path.read_text()
        if re.search(
            r"Dhipaya application scope|Interview story|the actual user|the assistant.s Linux", text, re.I
        ):
            errors.append(str(path.relative_to(root)) + ": private or ambiguous narration")
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose):
            if target.startswith(("https:", "http:", "mailto:", "#")):
                continue
            target = target.split("#")[0]
            if target and not (path.parent / target).exists():
                errors.append(str(path.relative_to(root)) + ": missing link " + target)
    readme = (root / "README.md").read_text()
    for spec in catalog(root):
        bundle = prepare(spec)
        link = str(spec["report"].relative_to(root))
        matching = [line for line in readme.splitlines() if "](" + link + ")" in line]
        if len(matching) != 1:
            errors.append("missing or duplicate results row: " + link)
            continue
        for method in spec["methods"]:
            values = [v for row, _, v in bundle["predictions"] if row["method"] == method]
            complete = sum(all(field[3] == "correct" for field in v) for v in values)
            wrong = sum(field[3] == "wrong" for v in values for field in v)
            expected = f"{method}: **{complete}/{len(values)}**; {wrong} wrong fields"
            if expected not in matching[0]:
                errors.append("README score differs from evidence: " + link + " " + method)
    if errors:
        raise ValueError("\n".join(errors))
    print(f"Checked {len(paths)} documents and all 11 recorded result rows")


if __name__ == "__main__":
    check()
