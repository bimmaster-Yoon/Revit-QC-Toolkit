# Project Instructions

## Repository Scope

Work in `R:\Revit_Codex_Automation`. This repository is a Revit 2026 pyRevit extension named `YJH_RevitTools.extension`. The existing production toolkit is the Revit QC Toolkit, with DOC QC, QC Lite, Scan QC, QC Settings, Report, and Help.

The planned Material Area Takeoff Toolkit must be added inside the same pyRevit extension, but kept separate from existing QC features. Do not mix takeoff logic, config, buttons, reports, or UI state into the QC modules unless explicitly requested.

## Change Rules

- Do not modify existing QC behavior unless the task explicitly asks for it.
- Prefer additive changes over broad rewrites.
- Keep changes small, scoped, and high-confidence.
- Keep Revit tools read-only by default.
- Do not add Revit model-modifying `Transaction` code unless explicitly requested.
- Keep pyRevit runtime compatibility. Avoid f-strings unless the active runtime is confirmed to support them.
- Do not add heavy dependencies. Reuse the standard library and existing lightweight dependencies where practical.
- Keep MCP/tool usage limited to what is necessary for the task.

## Project Structure

- `YJH_RevitTools.extension/Revit QC.tab/`: pyRevit ribbon tabs, panels, and button entry scripts.
- `YJH_RevitTools.extension/lib/`: shared Python logic for QC and future toolkits.
- `YJH_RevitTools.extension/lib/scan_qc/`: Scan QC-specific logic.
- `YJH_RevitTools.extension/config/`: JSON presets and local configuration.
- `YJH_RevitTools.extension/reports/`: generated report outputs and runtime report pointers.
- `docs/`: user-facing setup, configuration, usage, workflow, and changelog documentation.

For new Material Area Takeoff work, create clearly named modules and button folders instead of extending QC files by convenience.

## Coding Style

Use 4-space indentation and `snake_case` names. Keep pyRevit button `script.py` files thin: collect Revit context, call pure Python functions, and display results. Move business logic into testable modules under `lib/`. Prefer `.format()` over f-strings unless compatibility is verified.

## TDD Guidance

Use TDD where practical. Write tests first for pure Python business logic before wiring it to pyRevit or the Revit API.

Good test targets include unit conversion, severity classification, JSON config validation, material grouping, area aggregation, room/level mapping using fake data, and report row generation.

Revit API integration, pyRevit UI, Revision Cloud creation, and model graphics may require manual verification inside Revit. Keep those integration layers thin so most decisions remain testable without Revit.

## Verification Requirements

Every completed coding task should report:

- Files changed
- Behavior changed
- Behavior intentionally not changed
- Tests added or updated
- Tests run and results
- Manual Revit verification required, if any

For Revit-facing changes, state whether Revit 2026 and pyRevit manual validation was performed or still needs to be performed.

## Local Configuration & Outputs

Do not commit local machine state, generated reports, debug logs, raw project files, or private Revit assets. Treat `qc_config_local.json`, report path pointers, CSV/XLSX/PDF outputs, and local Python paths as user-specific runtime data.
