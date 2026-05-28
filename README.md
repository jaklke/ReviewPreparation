# ReviewPreparation

A repository for automating sprint review preparation using GitHub Copilot CLI and the Skyline API.

## What it does

Given a list of task IDs, Copilot fetches the tasks from the Skyline API and generates a `sprint-review.html` file containing one table per product, ready for copy-paste into PowerPoint.

Each table includes: Task (linked), RN (linked), Title, Customer, Main Release, Feature Release, SLA, State, Developer, and Project.

Tables are sorted alphabetically by product, then by state: Completed → Ready To Deploy → Quality Assurance → Code Review → In Progress.

## Prerequisites

- [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli) installed and authenticated
- Python 3 available on your PATH
- The `skylineAPI` MCP server configured in Copilot CLI

## Usage

1. Open this repository in GitHub Copilot CLI:
   ```
   copilot
   ```

2. Ask Copilot to prepare the sprint review and provide your task IDs:
   ```
   prepare sprint review

   123456, 123457, 123458, ...
   ```

3. Copilot will fetch the tasks and generate `sprint-review.html` in the repo root.

4. Open `sprint-review.html` in a browser and copy the table(s) into PowerPoint.

> `sprint-review.html` is git-ignored and never committed.

## How the Product column is derived

| Condition | Product value |
|---|---|
| `Project` is `SLC-SE-DataMiner Solutions-IDP` | `IDP` |
| `Project` starts with `R&D ` | remainder after `R&D ` |
| First label starting with `R&D ` | remainder after `R&D ` |
| None of the above | *(empty)* |

## Files

| File | Description |
|---|---|
| `scripts/generate_sprint_review.py` | Reads Skyline API JSON from stdin, writes `sprint-review.html` |
| `.github/copilot-instructions.md` | Instructions that guide Copilot's behaviour in this repo |
