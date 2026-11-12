"""
Generates sprint-planning.html (top 15 backlog table) from Skyline API JSON piped to stdin.

Input is the raw JSON response of get_api_Tasks_ByAssignedTo (same shape as get_tasks_by_id_raw).

Usage:
    <skyline API output> | python scripts/generate_sprint_planning.py
"""

import json
import re
import sys
from html import escape

ASSIGNED_TO_USER_ID = 8859
ALLOWED_LABEL_IDS = {
    "2809", "2816", "2825", "2963", "4595", "4600", "5969", "5993",
    "6260", "6570", "6571", "6572", "2826", "6573", "2836", "2918",
}
KEEP_STATUS = "To Be Scheduled"
TOP_N = 15

ESTIMATE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)")
LABELED_ESTIMATE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:DEV|DEVELOPMENT)\s*\+\s*"
    r"(\d+(?:\.\d+)?)\s*QA",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"<[^>]+>")


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


def has_allowed_label(task):
    labels = task.get("Labels") or []
    return any(str(l.get("ID")) in ALLOWED_LABEL_IDS for l in labels if isinstance(l, dict))


def extract_estimates(description):
    if not description:
        return "", ""
    text = TAG_RE.sub(" ", description)
    match = LABELED_ESTIMATE_RE.search(text) or ESTIMATE_RE.search(text)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def link(url, text):
    if not text:
        return ""
    return (
        f'<a href="{escape(url)}" target="_blank" '
        'style="color:#0063b1;text-decoration:none">'
        f"{escape(str(text))}</a>"
    )


def cell(v, style):
    return f'<td style="{style}">{v}</td>'


def make_row(task, std):
    tid = task.get("ID", "")
    url = f"https://collaboration.dataminer.services/task/{tid}"
    title = task.get("Title", "") or ""
    state = task.get("Status", "") or ""
    dev_estimate, qa_estimate = extract_estimates(task.get("Description", ""))

    # Target release, customer, SLA are only shown when present; internal customer/SLA are not useful.
    target_release = task.get("TargetRelease") or ""
    customer = (task.get("Customer") or {}).get("Name", "") or ""
    if customer == "Skyline Communications":
        customer = ""
    sla = task.get("SlaLevel", "") or ""
    if sla == "n/a":
        sla = ""
    else:
        sla = f"SLA {sla}"
    extra = ", ".join(v for v in (target_release, customer, sla) if v)

    cols = [
        escape(str(tid)),
        link(url, "Click"),
        escape(title),
        "",
        escape(state),
        "",
        escape(dev_estimate),
        "",
        escape(qa_estimate),
        escape(extra),
    ]
    return "<tr>" + "".join(cell(c, std) for c in cols) + "</tr>"


def main():
    sth = "border:1px solid #999;padding:6px;background:#f2f2f2"
    std = "border:1px solid #999;padding:6px"

    data = resolve_refs(json.loads(sys.stdin.buffer.read().decode("utf-8")))

    tasks = [
        t for t in data
        if t.get("Status") == KEEP_STATUS and has_allowed_label(t)
    ]
    tasks.sort(key=lambda t: t.get("BusinessValue") or 0, reverse=True)
    tasks = tasks[:TOP_N]

    headers = ["Task", "Link", "Title", "", "State", "", "Dev estimate", "", "QA estimate", "Release / Customer / SLA"]
    thead = "<thead><tr>" + "".join(f'<th style="{sth}">{escape(h)}</th>' for h in headers) + "</tr></thead>"
    tbody = "<tbody>" + "".join(make_row(t, std) for t in tasks) + "</tbody>"
    table = f'<table style="border-collapse:collapse;margin-bottom:32px">{thead}{tbody}</table>'

    page = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Sprint Planning</title></head>
<body style="font-family:sans-serif;padding:24px">
{table}
</body>
</html>"""

    output_path = "sprint-planning.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
