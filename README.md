## Release

Latest clean distribution release:

- [Revit QC Toolkit v2.7.1](https://github.com/bimmaster-Yoon/Revit-QC-Toolkit/releases/tag/v2.7.1-clean-distribution)

# Revit QC Toolkit

Revit QC Toolkit is a pyRevit extension for Revit 2026 that helps review BIM model,
drawing, and documentation quality from inside Revit. It started as a Sheet/View/
Parameter QC tool and is now being expanded with a Scan QC workflow for point-cloud-
based wall deviation review.

The toolkit is designed as a practical BIM/DX portfolio project: it focuses on
repeatable model checks, readable review summaries, and report outputs that can be
used during interior design documentation and coordination.

> Current safety note: the existing Sheet QC, View QC, Parameter QC, summary, and
> report export tools are read-only inspection workflows. Scan QC is in active
> development and currently creates dedicated QC working views and 2D review
> annotations only in generated `SCAN_QC_*` views.

## Project Overview

This repository contains a pyRevit extension named `YJH_RevitTools.extension`.
The main ribbon location is:

```text
Revit QC > QC Toolkit
```

The toolkit supports two review tracks:

1. **Model / drawing metadata QC**
   - Sheet QC
   - View QC
   - Parameter QC
   - Compact Summary
   - Review Group Summary
   - Review Item Samples
   - Full/Summary CSV export
   - Styled Excel report export

2. **Scan QC, in progress**
   - Source Plan View selection
   - Point Cloud instance selection
   - Selected Walls / Active Plan Level analysis scope
   - QC Plan and QC 3D working view creation
   - Standards validation and installation
   - 2D Revision Cloud callouts with centered A/B/C IDs
   - Early PointCloudInstance sampling and wall deviation debug

## Features

### Sheet QC

- Checks sheet number and sheet name state.
- Reviews whether sheets contain placed views.
- Reports sheet-related issues as individual review items and grouped summaries.

### View QC

- Checks view naming issues such as temporary keywords.
- Reviews view scale, template assignment, and sheet placement state.
- Helps identify unplaced or coordination-risk views before documentation delivery.

### Parameter QC

- Uses JSON rule sets to define required parameters by category.
- Checks missing or empty required parameter values.
- Supports default, interior, company-template, and custom rule presets.

### Compact Summary

- Shows a short pyRevit Output summary for quick review.
- Highlights checked sheet/view/parameter counts, total review items, grouped issues,
  and QC status.

### Review Group Summary

- Groups repeated issues by category, item type, QC item, and issue message.
- Keeps the output readable when many elements share the same issue.
- Shows sample items without hiding the full detail export.

### Review Item Samples

- Displays key examples from the detected review items.
- Keeps the on-screen report compact while preserving complete raw data in exports.

### Full / Summary Report Export

- **Full CSV**: all individual review items.
- **Summary CSV**: grouped issue summary for review meetings and tracking.
- **Styled Excel Report**: formatted workbook with summary, review groups, key
  samples, and full detail sheets.
- Export can be disabled when the user only wants to inspect pyRevit Output.

### Scan QC - In Progress

Scan QC is being developed as a separate feature module under `lib/scan_qc`.

Current direction:

- 2D plan-view-based review workflow.
- Scan QC setup dialog for source plan view, point cloud, analysis scope, tolerance,
  and output options.
- QC Plan View and QC 3D View generation from project standards.
- Revision Cloud callouts in generated `SCAN_QC_PLAN_*` views.
- Each Revision Cloud displays a centered uppercase ID such as `A`, `B`, or `C`.
- Detailed callout information is shown in pyRevit Output and is planned to be
  reused later in PDF/image reports or a sheet-side/bottom summary table.
- Point cloud sampling is currently limited to a Selected Walls MVP path.
- Wall deviation debug includes coordinate transform checks and wall-face correction.

Current Scan QC limitations:

- Active Plan Level full-wall deviation is still a fallback/preview path.
- PDF and CSV outputs for Scan QC are not implemented yet.
- Point cloud points are not recolored.
- 3D preview markers are disabled for now.
- Deviation results should be treated as an MVP validation workflow until tested
  against more project datasets.

## Current Status

| Area | Status |
| --- | --- |
| Sheet QC | Working |
| View QC | Working |
| Parameter QC | Working |
| Compact Summary | Working |
| Review Group Summary | Working |
| Review Item Samples | Working |
| Full CSV Export | Working |
| Summary CSV Export | Working |
| Styled Excel Report | Working with external CPython + `openpyxl` |
| QC Settings / Rule Presets | Working |
| Open Last Report | Working |
| Scan QC UI | In progress |
| Scan QC Standards Check / Install | In progress |
| Scan QC Working Views | In progress |
| Scan QC Revision Cloud ID Callouts | In progress |
| Scan QC Point Cloud Deviation | MVP / debugging |
| Scan QC PDF / Image Report | Planned |
| Scan QC CSV Export | Planned |

## Folder Structure

```text
Revit_Codex_Automation/
├─ README.md
├─ CHANGELOG.md
├─ requirements.txt
├─ docs/
│  ├─ INSTALL.md
│  ├─ USAGE.md
│  ├─ CONFIG.md
│  ├─ workflow.md
│  └─ changelog.md
└─ YJH_RevitTools.extension/
   ├─ Revit QC.tab/
   │  └─ QC Toolkit.panel/
   │     ├─ Run Full QC.pushbutton/
   │     ├─ Quick QC.pushbutton/
   │     ├─ QC Settings.pushbutton/
   │     ├─ Open Last Report.pushbutton/
   │     ├─ Help.pushbutton/
   │     └─ Scan QC.pushbutton/
   ├─ config/
   │  ├─ qc_config_default.json
   │  ├─ qc_config_interior.json
   │  ├─ qc_config_company_template.json
   │  └─ scan_qc_defaults.json
   ├─ lib/
   │  ├─ checks_sheet.py
   │  ├─ checks_view.py
   │  ├─ checks_parameter.py
   │  ├─ exporters.py
   │  ├─ grouping.py
   │  ├─ report_ui.py
   │  └─ scan_qc/
   │     ├─ dialog.py
   │     ├─ settings.py
   │     ├─ standards.py
   │     ├─ source_views.py
   │     ├─ views.py
   │     ├─ deviation.py
   │     ├─ markers.py
   │     └─ reporting.py
   ├─ resources/
   │  ├─ standards/
   │  ├─ families/
   │  └─ report_templates/
   ├─ reports/
   └─ tools/
      └─ make_styled_xlsx.py
```

## Installation / Setup

Requirements:

- Windows
- Autodesk Revit 2026
- pyRevit connected to Revit 2026
- Git or GitHub Desktop
- Optional: external CPython with `openpyxl` for Styled Excel Report export

Basic setup:

1. Clone the repository.
2. Add the repository root folder to pyRevit custom extension directories.
3. Reload pyRevit.
4. Confirm the `Revit QC > QC Toolkit` panel appears in Revit.
5. Optional: install Excel report dependencies.

```powershell
py -3 -m pip install -r requirements.txt
```

Then open `QC Settings` in Revit and select the Python executable that has
`openpyxl` installed.

More setup details are available in [docs/INSTALL.md](docs/INSTALL.md).

## Usage

### Run Full QC

Use this for a full Sheet + View + Parameter review.

1. Open a Revit 2026 model.
2. Click `Run Full QC`.
3. Choose export options.
4. Review pyRevit Output and exported files.

### Quick QC

Use this for a faster Sheet + View review when Parameter QC is not needed.

### QC Settings

Use this to:

- Set the external Python path for Styled Excel Report export.
- Test `openpyxl` availability.
- Select the active JSON rule preset.
- Copy a preset into a custom rule set.

### Scan QC

Use this only as an in-progress validation workflow.

Current Scan QC flow:

1. Open a model with walls and Point Cloud instances.
2. Click `Scan QC`.
3. Select a Source Plan View.
4. Select a Point Cloud instance.
5. Choose `Active Plan Level` or `Selected Walls`.
6. Confirm tolerance and output options.
7. Run Scan QC.
8. Review generated QC working views and pyRevit Output.

For Selected Walls, the current MVP samples nearby point cloud points, compares
coordinate modes, applies wall-face correction using wall thickness, and creates
Revision Cloud ID callouts for Review/Critical results.

## Roadmap

Planned improvements:

- Harden Scan QC point cloud sampling across more Revit/point-cloud datasets.
- Improve wall-face deviation logic for non-linear walls and complex wall geometry.
- Add Scan QC PDF or image report output.
- Add Scan QC CSV export.
- Add a sheet/report table that maps A/B/C Revision Cloud IDs to detailed findings.
- Expand Scan QC standards automation with view templates and report assets.
- Add more validation around point cloud coordinate systems and transforms.
- Continue keeping Sheet/View/Parameter QC behavior stable while Scan QC evolves.

## Portfolio Notes

This repository is intended to demonstrate practical Revit/BIM/DX implementation
ability, not only UI mockups.

It highlights:

- pyRevit extension structure and deployment awareness.
- Revit model and drawing QC logic.
- Rule-set-driven parameter checking.
- Report design for both compact review and full traceability.
- Local settings management without committing user-specific paths.
- Early point-cloud-based Scan QC exploration using Revit API constraints.
- A workflow that connects BIM model checking to coordination-ready deliverables.

No confidential company data, real project names, client names, pricing data, or
internal project documents are required to use this repository.

## Documentation

- [Installation Guide](docs/INSTALL.md)
- [Usage Guide](docs/USAGE.md)
- [Configuration Guide](docs/CONFIG.md)
- [Workflow Notes](docs/workflow.md)
- [Detailed Historical Changelog](docs/changelog.md)
- [Repository Changelog](CHANGELOG.md)
