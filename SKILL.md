---
name: pbi-user-guide-drafter
description: >
  Auto-generate a professional branded DOCX user guide from a Power BI Project
  (PBIP) folder. Parses PBIR/PBIR-Legacy report structure and TMDL/TMSL semantic
  model, then Claude Code generates the content and writes it into a Word template
  with screenshot placeholders for each dashboard page. Optionally captures live
  screenshots via Playwright if a Power BI Service URL is provided.
  Use when user says: generate user guide, create PBI documentation,
  document this dashboard, pbip user guide, user guide for path,
  PBIP文書生成, ユーザーガイド生成, ダッシュボードドキュメント,
  write user guide for this pbip, document this report,
  or provides a .pbip file path with intent to document it.
---

# PBI User Guide Drafter

## Overview

Two-phase skill:

- **Phase 1 (always)** — Parse the PBIP, generate all text sections, write a DOCX with `<<<SCREENSHOT: PageName>>>` placeholders.
- **Phase 2 (optional)** — If a Power BI Service URL and Playwright are available, capture live screenshots and inject them into the DOCX.

---

## Workflow

### 1. Get the .pbip path from the user

### 2. Parse the PBIP

```bash
python pbi-user-guide-drafter/scripts/parse_pbip.py "<pbip_path>"
```

Capture stdout as JSON. If exit code != 0, show the stderr output to the user and stop.

### 3. Ask three optional questions (in one message)

Ask the user all three questions together:

> **Optional — answer any you want, skip the rest:**
> 1. **Document Control**: version, author name(s), reviewer name(s) — or skip for defaults (v0.1, today's date, TBC)
> 2. **Background paragraph**: a 1–3 sentence description of the business context — or skip and I'll infer from the metadata
> 3. **Power BI Service direct link**: the URL to open this report in the browser — or skip for a placeholder

Wait for the response, then proceed.

### 4. Generate user guide content

Using the JSON from Step 2 and the user's answers from Step 3, write ALL sections below as a single markdown string. Use the exact section order shown.

---

#### Document Control

If the user provided version/author/reviewer, use those. Otherwise:

```
## Document Control

| Version | Date | Author | Reviewed By |
|---|---|---|---|
| 0.1 | {today's date} | {auto} | TBC |
```

---

#### Background

If the user provided a background paragraph, use it verbatim. Otherwise, infer a 1–2 sentence background from the dashboard name, page names, and table names.

```
# Background

{background paragraph}
```

---

#### Document Purpose

```
# Document Purpose

## Intended Users of the Dashboard

{Infer from page content — e.g. "Finance teams, Budget holders, Executive leadership"}

## Guide to Using This Document

This guide is intended to assist users in navigating and interpreting the {dashboard name} Power BI Dashboard. Each section provides step-by-step instructions and descriptions to help users extract meaningful insights from the report. For technical queries or access issues, please contact the report owner or the Corporate Analytics team.

## Data Sources

{List sources from JSON `sources[]` array.}
```

Write a markdown table:
```
| Table | Source Type | Description |
|---|---|---|
| {table} | {type} | {infer a plain-English description from the query_snippet and table name} |
```

---

#### Dashboard Functions

```
# Dashboard Functions

<<<BOILERPLATE: boilerplate_dashboard_functions.md>>>
```

---

#### How to Access the Dashboard

```
# How to Access the Dashboard

## Via Direct Link

{If user provided a URL: "Navigate directly to the dashboard using this link: {URL}"}
{If no URL provided: "Navigate directly to the dashboard using the Power BI Service link provided by your report owner. Insert the direct link here: [Dashboard Link]"}

## Via Power BI App

1. Sign in to [Power BI Service](https://app.powerbi.com) with your organisational account.
2. In the left navigation pane, click **Apps**.
3. Locate the **{app name or workspace name}** app and click to open it.
4. Select the **{dashboard name}** report from the app contents list.
```

---

#### Reports Section

Build a Tab Overview Table from `report.pages` (ordered by `order`):

```
# {dashboard name} Reports

The {dashboard name} Dashboard contains the following report pages (tabs):

| Tab | Report Page | Description |
|---|---|---|
| TAB 1 | {page 1 displayName} | {one-line description inferred from visuals and page name} |
| TAB 2 | {page 2 displayName} | {one-line description} |
```

Then for EACH page in `report.pages` (ordered by `order`), write a subsection:

```
## {displayName}

<<<SCREENSHOT: {displayName}>>>

{2–3 sentence description of what this page shows and what business questions it answers}

{For each non-hidden visual: one bullet per visual group. Group KPI cards together, describe slicers as "Use the X slicer to filter by Y", describe charts/tables by what they show}

{If the page has KPI visuals (from `kpi_visuals[displayName]`), add a definition table:}

### KPI Summary

| Dashboard Item | Definition |
|---|---|
| {kpi title or field} | {plain-English definition of what this metric measures} |
```

---

#### Other Useful Tips and Tools

```
# Other Useful Tips and Tools

<<<BOILERPLATE: boilerplate_tips_and_tools.md>>>
```

---

#### Export

```
# Export (Excel / PDF)

<<<BOILERPLATE: boilerplate_export.md>>>
```

---

#### Appendix

```
# APPENDIX

## Acronyms

The following abbreviations appear in this dashboard:

| Acronym | Meaning | Found In |
|---|---|---|
{For each entry in JSON `acronyms[]`: | {acronym} | {infer plain-English expansion} | {found_in} |}
```

```
## User Access Form

<<<BOILERPLATE: boilerplate_access_form.md>>>
```

---

### 5. Save content and metadata to temp files

```
<TEMP_DIR>/pbip_guide_content.md
<TEMP_DIR>/pbip_guide_metadata.json
```

Where `<TEMP_DIR>` is the OS temp directory (`%TEMP%` on Windows, `/tmp` on Linux/Mac).

### 6. Generate the DOCX

Default template: `pbi-user-guide-drafter/template/template.docx`
Custom template: pass `--template <path>` to override.

```bash
python pbi-user-guide-drafter/scripts/write_docx.py \
  --content "<TEMP_DIR>/pbip_guide_content.md" \
  --metadata "<TEMP_DIR>/pbip_guide_metadata.json" \
  --output "pbi-user-guide-drafter/output/User Guide - <Name> Dashboard (Power BI User Guide).docx" \
  [--template "<custom_template.docx>"]
```

### 7. Phase 2 — Screenshots (optional)

If the user provided a Power BI Service URL AND Playwright is available:

```bash
# Check playwright availability
playwright --version 2>/dev/null || echo "playwright not available"
```

If available, capture each page screenshot:
```bash
playwright screenshot "<service_url>#page=<pageName>" \
  pbi-user-guide-drafter/screenshots/<PageName>.png
```

Then re-run `write_docx.py` with the `--screenshots pbi-user-guide-drafter/screenshots/` flag to inject images in place of `<<<SCREENSHOT: ...>>>` placeholders.

### 8. Present the output path to the user

Tell the user the full path to the generated DOCX and that they should open it in Word to review. The Table of Contents and page numbers are updated automatically.

### 9. Clean up temp files

```bash
rm "<TEMP_DIR>/pbip_guide_content.md" "<TEMP_DIR>/pbip_guide_metadata.json"
```

---

## Prerequisites

```bash
pip install python-docx
# For Phase 2 screenshots:
pip install playwright && playwright install chromium
```

The `template/template.docx` file must be present (or pass `--template <custom_path>`). A generic `template/template_sample.docx` is committed; replace with your branded template and rename to `template.docx`.

---

## Section Coverage

| Section | Source | Status |
|---|---|---|
| Document Control | User input / defaults | Auto with placeholders |
| Background | User input / inferred | Auto-inferred |
| Document Purpose | Inferred + static | Auto |
| Data Sources | `sources[]` from parse_pbip | Auto |
| Dashboard Functions | Boilerplate | Auto |
| How to Access | User link / static | Auto with placeholder |
| Tab Overview Table | `pages[]` order | Auto |
| Page-by-Page Guide | `pages[].visuals` | Auto |
| KPI Definition Tables | `kpi_visuals[]` | Auto |
| Other Tips & Tools | Boilerplate | Auto |
| Export | Boilerplate | Auto |
| Acronyms | `acronyms[]` | Auto (may need expansion) |
| User Access Form | Boilerplate | Auto |
| Screenshots | Playwright (Phase 2) | Placeholder until Phase 2 runs |

---

## Error Handling

| Error | Message |
|-------|---------|
| Missing `.pbip` | File not found — check the path |
| Missing `.Report/` or `.SemanticModel/` | Not a valid PBIP project |
| `parse_pbip.py` non-zero exit | Show stderr to user |
| Missing `template/template.docx` | Template not found — check template/ directory or pass `--template` |
| Missing boilerplate file | FileNotFoundError from write_docx.py — check assets/ directory |
| Playwright not installed | Skip Phase 2, inform user screenshots remain as placeholders |

---

## PBIP Folder Structure Reference

```
<Name>.pbip                              # JSON — project entry point
<Name>.Report/
  ├── definition.pbir                    # semantic model reference
  ├── report.json                        # PBIR-Legacy format
  └── definition/                        # PBIR format (granular)
      ├── pages/
      │   ├── pages.json
      │   └── <pageId>/
      │       ├── page.json
      │       └── visuals/<visualId>/visual.json
      └── bookmarks/
<Name>.SemanticModel/
  ├── definition/                        # TMDL format
  │   ├── tables/<TableName>.tmdl
  │   └── relationships.tmdl
  └── model.bim                          # TMSL format
```

Detection: `definition/` subfolder present → granular format; else single-file fallback.
