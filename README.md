# ReviewPreparation

## Copilot CLI prompt: Skyline API to HTML table

Use this prompt with GitHub Copilot CLI:

```text
Fetch data from the Skyline API and extract only these fields for each record:
- id
- name
- status
- owner
- priority
- createdAt
- updatedAt

Return the result as a complete HTML table with:
1) A header row using the exact field names above
2) One row per record
3) Empty cells if a field is missing
4) Basic inline styling suitable for copy/paste into PowerPoint:
   - collapsed borders
   - 1px solid #999 borders
   - 6px cell padding
   - header background #f2f2f2

Output only the final HTML table (no markdown, no explanation).
```