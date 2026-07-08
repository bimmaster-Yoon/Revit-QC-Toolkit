# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible.
# Scan QC setup, standards installation, working views, and marker preview entry point.

import os
import sys

from pyrevit import forms, revit, script


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
from scan_qc.collectors import (
    collect_point_cloud_instances,
    collect_selected_walls,
    get_element_id_value
)
from scan_qc.dialog import request_scan_qc_options
from scan_qc.deviation import calculate_wall_deviations
from scan_qc.markers import (
    build_marker_preview_result,
    create_3d_marker_preview,
    create_plan_marker_preview
)
from scan_qc.reporting import render_scan_qc_summary
from scan_qc.settings import get_view_creation_options, load_scan_qc_settings
from scan_qc.source_views import (
    collect_source_plan_views,
    get_default_source_plan_view,
    get_source_plan_view_by_id
)
from scan_qc.standards import install_missing_standards
from scan_qc.views import create_requested_scan_qc_views


doc = revit.doc
uidoc = revit.uidoc
original_active_view = doc.ActiveView

selected_walls = collect_selected_walls(uidoc)
point_clouds = collect_point_cloud_instances(doc)
source_plan_views = collect_source_plan_views(doc)
if not source_plan_views:
    forms.alert(
        "Scan QC requires at least one duplicable Plan View "
        "(Floor Plan, Ceiling Plan, Engineering Plan, or Area Plan).",
        title="Scan QC - Source Plan View Required",
        warn_icon=True
    )
    script.exit()

default_source_plan_view = get_default_source_plan_view(
    source_plan_views,
    original_active_view
)
default_source_plan_view_id = (
    get_element_id_value(default_source_plan_view.Id)
    if default_source_plan_view is not None
    else None
)
scan_qc_settings = load_scan_qc_settings()
selected_options = request_scan_qc_options(
    len(selected_walls),
    point_clouds,
    source_plan_views,
    default_source_plan_view_id,
    scan_qc_settings
)

if selected_options is None:
    script.exit()

selected_walls, wall_selection_warning = resolve_selected_walls(
    uidoc,
    selected_options["analysis_scope"],
    selected_walls
)
source_plan_view = get_source_plan_view_by_id(
    source_plan_views,
    selected_options.get("source_plan_view_id")
)
if source_plan_view is None:
    forms.alert(
        "The selected Source Plan View is no longer available. "
        "Please run Scan QC again and select a valid Plan View.",
        title="Scan QC - Source Plan View Missing",
        warn_icon=True
    )
    script.exit()

view_creation_options = get_view_creation_options(scan_qc_settings)
analysis_scope_result = build_analysis_scope_result(
    doc,
    source_plan_view,
    selected_walls,
    selected_options["analysis_scope"],
    view_creation_options["section_box_margin_mm"]
)
if wall_selection_warning:
    analysis_scope_result["warnings"].append(wall_selection_warning)

standards_result = install_missing_standards(doc, scan_qc_settings)
view_creation_result = create_requested_scan_qc_views(
    doc,
    source_plan_view,
    analysis_scope_result,
    selected_options,
    scan_qc_settings
)

deviation_result = calculate_wall_deviations(
    doc,
    source_plan_view,
    selected_walls,
    point_clouds,
    selected_options,
    scan_qc_settings
)
view_creation_result["deviation"] = deviation_result

plan_view = None
plan_view_id = view_creation_result["plan"].get("view_id")
if view_creation_result["plan"]["created"] and plan_view_id is not None:
    try:
        plan_view = doc.GetElement(plan_view_id)
    except Exception:
        plan_view = None

view3d = None
view3d_id = view_creation_result["view3d"].get("view_id")
if view_creation_result["view3d"]["created"] and view3d_id is not None:
    try:
        view3d = doc.GetElement(view3d_id)
    except Exception:
        view3d = None

plan_marker_preview = create_plan_marker_preview(
    doc,
    plan_view,
    selected_walls,
    analysis_scope_result,
    deviation_result,
    selected_options.get(
        "create_preview_callouts_when_no_deviation_data",
        True
    ),
    requested=selected_options.get("create_plan_view", False)
)
view3d_marker_preview = create_3d_marker_preview(
    view3d,
    requested=selected_options.get("create_3d_view", False)
)
view_creation_result["marker_preview"] = build_marker_preview_result(
    plan_marker_preview,
    view3d_marker_preview
)

render_scan_qc_summary(
    script.get_output(),
    len(selected_walls),
    selected_options,
    standards_result,
    view_creation_result
)
