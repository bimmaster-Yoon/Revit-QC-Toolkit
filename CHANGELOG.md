# Changelog

This file summarizes the main repository-level changes for GitHub visitors.
Detailed historical development notes are kept in [docs/changelog.md](docs/changelog.md).

## Current - Scan QC MVP and Portfolio Documentation

- Updated the root README for GitHub portfolio presentation.
- Documented the current Revit QC Toolkit feature set:
  - Sheet QC
  - View QC
  - Parameter QC
  - Compact Summary
  - Review Group Summary
  - Review Item Samples
  - Full/Summary CSV export
  - Styled Excel Report export
- Documented Scan QC as an in-progress feature module.
- Clarified the current Scan QC direction:
  - 2D plan-view-based review workflow
  - generated QC Plan / QC 3D working views
  - Revision Cloud callouts in generated Scan QC plan views
  - centered A/B/C ID labels
  - future report/table mapping for ID details
- Documented the Selected Walls Scan QC MVP:
  - PointCloudInstance sampling
  - coordinate transform comparison
  - wall-face deviation correction using WallType.Width / 2
  - Review/Critical Revision Cloud ID connection
- Added GitHub-oriented sections:
  - Project Overview
  - Features
  - Current Status
  - Folder Structure
  - Installation / Setup
  - Usage
  - Roadmap
  - Portfolio Notes

## Earlier Milestones

- Added pyRevit QC Toolkit panel with Full QC, Quick QC, QC Settings, Open Last Report, and Help.
- Split Sheet, View, Parameter, grouping, reporting, and export logic into maintainable modules.
- Added JSON rule preset support for default, interior, company-template, and custom configurations.
- Added Compact Summary, Review Group Summary, and Review Item Samples in pyRevit Output.
- Added Full CSV and Summary CSV export.
- Added Styled Excel Report generation using external CPython and `openpyxl`.
- Added local-only settings for external Python path and active rule preset.
- Added Scan QC module structure, settings, standards validation, standards installation, and working view creation.
- Added Scan QC Revision Cloud ID preview and early Point Cloud sampling/deviation debug workflow.
