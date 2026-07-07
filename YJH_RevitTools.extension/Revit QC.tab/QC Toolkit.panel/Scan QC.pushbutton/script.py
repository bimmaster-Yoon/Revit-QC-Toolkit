# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible.
# Scan QC setup, standards installation, and working view creation entry point.

import os
import sys

from pyrevit import revit, script


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from scan_qc.analysis_scope import (
    build_analysis_scope_result,
    resolve_selected_walls
)
from scan_qc.collectors import collect_point_cloud_instances, collect_selected_walls
from scan_qc.dialog import request_scan_qc_options
from scan_qc.reporting import render_scan_qc_summary
from scan_qc.settings import get_view_creation_options, load_scan_qc_settings
from scan_qc.standards import install_missing_standards
from scan_qc.views import create_requested_scan_qc_views


doc = revit.doc
uidoc = revit.uidoc
original_active_view = doc.ActiveView

selected_walls = collect_selected_walls(uidoc)
point_clouds = collect_point_cloud_instances(doc)
scan_qc_settings = load_scan_qc_settings()
selected_options = request_scan_qc_options(
    len(selected_walls),
    point_clouds,
    scan_qc_settings
)

if selected_options is None:
    script.exit()

selected_walls, wall_selection_warning = resolve_selected_walls(
    uidoc,
    selected_options["analysis_scope"],
    selected_walls
)
view_creation_options = get_view_creation_options(scan_qc_settings)
analysis_scope_result = build_analysis_scope_result(
    doc,
    original_active_view,
    selected_walls,
    selected_options["analysis_scope"],
    view_creation_options["section_box_margin_mm"]
)
if wall_selection_warning:
    analysis_scope_result["warnings"].append(wall_selection_warning)

standards_result = install_missing_standards(doc, scan_qc_settings)
view_creation_result = create_requested_scan_qc_views(
    doc,
    original_active_view,
    analysis_scope_result,
    selected_options,
    scan_qc_settings
)

render_scan_qc_summary(
    script.get_output(),
    len(selected_walls),
    selected_options,
    standards_result,
    view_creation_result
)
