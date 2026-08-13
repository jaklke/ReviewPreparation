"""
Generates sprint-review.html from Skyline API JSON piped to stdin.

Usage:
    <skyline API output> | python scripts/generate_sprint_review.py
"""

import json
import sys
from html import escape
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
    if not text:
        return ""
    return (
        f'<a href="{escape(url)}" target="_blank" '
        'style="color:#0063b1;text-decoration:none">'
        f"{escape(str(text))}</a>"
    )


def cell(v, style):
    return f'<td style="{style}">{v}</td>'


def make_table(group_rows, std, sth):
    headers = ["Task", "RN", "Title", "Customer", "MR", "FR", "SLA", "State", "Developer", "Project"]
    th = "".join(f'<th style="{sth}">{h}</th>' for h in headers)
    thead = f"<thead><tr>{th}</tr></thead>"
    body_rows = []
    for r in group_rows:
        _, _, tid, rn, title, customer, main_rel, feat_rel, sla, state, dev, proj, _ = r
        task_link = link(f"https://collaboration.dataminer.services/task/{tid}", tid)
        rn_link = link(f"https://collaboration.dataminer.services/releasenotes/{rn}", rn) if rn else ""
        cols = [
            task_link,
            rn_link,
            escape(str(title)),
            escape(str(customer)),
            escape(str(main_rel)),
            escape(str(feat_rel)),
            escape(str(sla)),
            escape(str(state)),
            escape(str(dev)),
            escape(str(proj)),
        ]
        body_rows.append("<tr>" + "".join(cell(c, std) for c in cols) + "</tr>")
    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"
    return (
        "<table style=\"width:100%;border-collapse:collapse;margin-bottom:0;"
        "background:#ffffff;border-radius:8px;overflow:hidden\">"
        f"{thead}{tbody}</table>"
    )


def main():
    sth = (
        "border:1px solid #999;padding:8px;background:#e8f0fb;color:#003366;"
        "font-size:13px;text-align:left"
    )
    std = "border:1px solid #999;padding:7px;font-size:12px;color:#1f2937;vertical-align:top"

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
    for slide_index, (product, group) in enumerate(groupby(rows, key=lambda r: r[0])):
        heading = product if product else "(No product)"
        table = make_table(list(group), std, sth)
        sections.append(
            f"<section id=\"slide-{slide_index}\" data-slide-index=\"{slide_index}\" "
            "style=\"width:1280px;min-height:720px;box-sizing:border-box;"
            "padding:36px;background:#f5f8fc;border:1px solid #d7e3f5;"
            "border-radius:14px;margin:0 auto 28px auto;position:relative;"
            "box-shadow:0 8px 24px rgba(17, 24, 39, 0.08);page-break-after:always\">"
            "<div style=\"position:absolute;top:0;left:0;right:0;height:10px;"
            "background:linear-gradient(90deg,#005bbb 0%,#00a3ff 100%);"
            "border-top-left-radius:14px;border-top-right-radius:14px\"></div>"
            "<div style=\"display:flex;justify-content:space-between;align-items:flex-end;"
            "margin:10px 0 24px 0;gap:20px\">"
            f"<h1 style=\"margin:0;font-size:34px;line-height:1.2;color:#003366\">{escape(heading)}</h1>"
            "<div style=\"font-size:14px;color:#4b5563\">Skyline Sprint Review</div>"
            "</div>"
            f"{table}</section>"
        )

    body = "\n".join(sections)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Sprint Review</title></head>
<body style="font-family:Segoe UI,Arial,sans-serif;padding:24px;background:#eaf1fb">
{body}
<script>
(function () {{
  const slides = Array.from(document.querySelectorAll("section[data-slide-index]"));
  if (!slides.length) {{
    return;
  }}

  function nearestSlideIndex() {{
    const viewportCenter = window.scrollY + (window.innerHeight / 2);
    let bestIndex = 0;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (let i = 0; i < slides.length; i += 1) {{
      const rect = slides[i].getBoundingClientRect();
      const slideCenter = window.scrollY + rect.top + (rect.height / 2);
      const distance = Math.abs(viewportCenter - slideCenter);
      if (distance < bestDistance) {{
        bestDistance = distance;
        bestIndex = i;
      }}
    }}
    return bestIndex;
  }}

  function goToSlide(index) {{
    const bounded = Math.max(0, Math.min(index, slides.length - 1));
    slides[bounded].scrollIntoView({{ behavior: "smooth", block: "start" }});
  }}

  document.addEventListener("keydown", function (event) {{
    const target = event.target;
    if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {{
      return;
    }}

    const currentIndex = nearestSlideIndex();
    if (event.key === "ArrowRight" || event.key === "ArrowDown" || event.key === "PageDown" || event.key === " ") {{
      event.preventDefault();
      goToSlide(currentIndex + 1);
    }} else if (event.key === "ArrowLeft" || event.key === "ArrowUp" || event.key === "PageUp") {{
      event.preventDefault();
      goToSlide(currentIndex - 1);
    }} else if (event.key === "Home") {{
      event.preventDefault();
      goToSlide(0);
    }} else if (event.key === "End") {{
      event.preventDefault();
      goToSlide(slides.length - 1);
    }}
  }});
}})();
</script>
</body>
</html>"""

    output_path = "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
