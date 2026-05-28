"""
Generates sprint-review.html from Skyline API JSON piped to stdin.

Usage:
    <skyline API output> | python scripts/generate_sprint_review.py
"""

import json
import sys
from itertools import groupby


def resolve_refs(obj, registry=None):
    if registry is None:
        registry = {}
    if isinstance(obj, dict):
        if "$id" in obj:
            registry[obj["$id"]] = obj
        if "$ref" in obj:
            return registry.get(obj["$ref"], {})
        return {k: resolve_refs(v, registry) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_refs(i, registry) for i in obj]
    return obj


STATE_ORDER = ["Completed", "Ready To Deploy", "Quality Assurance", "Code Review", "In Progress"]


def get_product(task):
    proj = (task.get("Project") or {}).get("Title") or ""
    labels = [l.get("Title", "") for l in (task.get("Labels") or []) if isinstance(l, dict) and "Title" in l]
    if proj == "SLC-SE-DataMiner Solutions-IDP":
        return "IDP"
    if proj.startswith("R&D "):
        return proj[4:]
    for lbl in labels:
        if lbl.startswith("R&D "):
            return lbl[4:]
    return ""


def state_key(s):
    try:
        return STATE_ORDER.index(s)
    except ValueError:
        return len(STATE_ORDER)


def link(url, text):
    return f'<a href="{url}" target="_blank">{text}</a>' if text else ""


def cell(v, style):
    return f'<td style="{style}">{v}</td>'


def make_table(group_rows, std, sth):
    headers = ["Task", "RN", "Title", "Customer", "Main Release", "Feature Release", "SLA", "State", "Developer", "Project"]
    th = "".join(f'<th style="{sth}">{h}</th>' for h in headers)
    thead = f"<thead><tr>{th}</tr></thead>"
    body_rows = []
    for r in group_rows:
        _, _, tid, rn, title, customer, main_rel, feat_rel, sla, state, dev, proj, _ = r
        task_link = link(f"https://collaboration.dataminer.services/task/{tid}", tid)
        rn_link = link(f"https://collaboration.dataminer.services/releasenotes/{rn}", rn) if rn else ""
        cols = [task_link, rn_link, title, customer, main_rel, feat_rel, sla, state, dev, proj]
        body_rows.append("<tr>" + "".join(cell(c, std) for c in cols) + "</tr>")
    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"
    return f'<table style="border-collapse:collapse;margin-bottom:32px">{thead}{tbody}</table>'


def main():
    sth = "border:1px solid #999;padding:6px;background:#f2f2f2"
    std = "border:1px solid #999;padding:6px"

    data = resolve_refs(json.loads(sys.stdin.buffer.read().decode("utf-8")))

    rows = []
    for t in data:
        tid = t.get("ID", "")
        rn = t.get("ReleaseNote", "") or ""
        title = t.get("Title", "")
        customer = (t.get("Customer") or {}).get("Name", "") or ""
        main_rel = t.get("MainReleaseVersion", "") or ""
        feat_rel = t.get("FeatureReleaseVersion", "") or ""
        sla = t.get("SlaLevel", "") or ""
        state = t.get("Status", "") or ""
        dev_full = (t.get("Developer") or {}).get("Name", "") or ""
        dev = dev_full.split()[0] if dev_full else ""
        proj = (t.get("Project") or {}).get("Title", "") or ""
        product = get_product(t)
        rows.append((product, state_key(state), tid, rn, title, customer, main_rel, feat_rel, sla, state, dev, proj, product))

    rows.sort(key=lambda r: (r[0] == "", r[0].lower(), r[1]))

    sections = []
    for product, group in groupby(rows, key=lambda r: r[0]):
        heading = product if product else "(No product)"
        table = make_table(list(group), std, sth)
        sections.append(f"<h2>{heading}</h2>{table}")

    body = "\n".join(sections)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Sprint Review</title></head>
<body style="font-family:sans-serif;padding:24px">
{body}
</body>
</html>"""

    output_path = "sprint-review.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
