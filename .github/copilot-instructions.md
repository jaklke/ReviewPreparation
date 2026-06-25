# Copilot Instructions

## Purpose

This repository supports **sprint review preparation**. When asked to prepare a sprint review, fetch tasks from the Skyline API and write a formatted HTML page (`index.html`) ready for copy-paste into PowerPoint.

## Sprint Review Workflow

1. The user provides a list of task IDs.
2. Use `skylineAPI-get_tasks_by_id_raw` to fetch all tasks in one call and save the output to a temp file.
3. Pipe the saved JSON through `scripts/generate_sprint_review.py` to produce `index.html` (git-ignored — never committed):
   ```
   Get-Content <temp-file> | python scripts/generate_sprint_review.py
   ```
4. The script handles `$id`/`$ref` resolution, field extraction, product derivation, sorting, and HTML generation.

## Fields to Extract

| Column header | API field | Notes |
|---|---|---|
| Task | `ID` | Render as hyperlink: `https://collaboration.dataminer.services/task/[ID]` |
| RN | `ReleaseNote` | Render as hyperlink: `https://collaboration.dataminer.services/releasenotes/[ReleaseNote]` — leave cell empty if value is blank/null |
| Title | `Title` | Plain text |
| Customer | `Customer.Name` | Plain text |
| Main Release | `MainReleaseVersion` | Plain text |
| Feature Release | `FeatureReleaseVersion` | Plain text |
| SLA | `SlaLevel` | Plain text |
| State | `Status` | Plain text |
| Developer | `Developer.Name` | First name only (split on space, take first word) |
| Project | `Project.Title` | Plain text |
| Product | derived | See **Product derivation** below |

## Product Derivation

Derive the **Product** column value using this priority order:

1. **IDP exception**: if `Project.Title` is exactly `SLC-SE-DataMiner Solutions-IDP` → `IDP`
2. **Project starts with "R&D"**: strip the `R&D ` prefix from `Project.Title` and use the remainder (e.g. `R&D Data Engine` → `Data Engine`)
3. **Label starts with "R&D"**: find the first entry in `Labels` whose title starts with `R&D`, strip the `R&D ` prefix (e.g. label `R&D Communication & Synchronisation` → `Communication & Synchronisation`)
4. **Fallback**: Put `Other` if none of the above rules match
Also include `Labels` in the API call (they are returned automatically with `get_tasks_by_id_raw`) — no extra fetch is needed.

## Sorting

Sort rows by **Product** (alphabetically), then within each product by **State** in this fixed order:

1. Completed
2. Ready To Deploy
3. Quality Assurance
4. Code Review
5. In Progress

Rows with a state not in the list above sort last. Rows with an empty Product sort last.

## HTML Output Requirements

- Write a complete HTML page to `index.html` in the repo root — no markdown, no explanation in the output
- Structure: `<!DOCTYPE html>` + `<html lang="en">` + `<head>` (UTF-8 charset, title "Sprint Review") + `<body style="font-family:sans-serif;padding:24px">`
- **One table per product**, each preceded by an `<h2>` with the product name. Tasks with no product go in a final section titled "(No product)"
- The **Product** column is omitted from the table (it's conveyed by the heading)
- Apply inline styles for PowerPoint compatibility:
  - `border-collapse:collapse;margin-bottom:32px` on each `<table>`
  - `border: 1px solid #999; padding: 6px` on every `<td>` and `<th>`
  - `background: #f2f2f2` on header `<th>` cells
- Render Task and RN values as `<a href="...">` links
- Use empty `<td></td>` for any missing or null field
