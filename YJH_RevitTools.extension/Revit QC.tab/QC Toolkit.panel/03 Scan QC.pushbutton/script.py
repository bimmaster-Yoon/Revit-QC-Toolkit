# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible.
# Scan QC setup, standards installation, working views, and marker preview entry point.

__persistentengine__ = True

import io
import os
import sys

from pyrevit import forms, revit, script
from System import DateTime
from System.Diagnostics import Stopwatch


STARTUP_WATCH = Stopwatch.StartNew()


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from scan_qc.collectors import (
    collect_point_cloud_instances,
    collect_selected_walls,
    get_element_id_value
)
from scan_qc.dialog import request_scan_qc_options
from scan_qc.settings import load_scan_qc_settings
from scan_qc.source_views import (
    collect_source_plan_views,
    get_default_source_plan_view,
    get_source_plan_view_by_id
)
from scan_qc.startup_cache import (
    get_or_collect,
    register_document_invalidation,
    set_cached_value
)
from scan_qc.target_parameter import (
    collect_target_walls,
    inspect_target_parameter,
    install_target_parameter,
    pick_walls,
    select_target_walls,
    set_selected_wall_targets
)
from ui_close_profiler import is_ui_perf_debug_enabled


STARTUP_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Revit_QC_Toolkit",
    "logs",
    "scan_qc_startup.log"
)


class _StartupFileLogger(object):
    def info(self, message):
        if not is_ui_perf_debug_enabled():
            return
        try:
            log_folder = os.path.dirname(STARTUP_LOG_PATH)
            if not os.path.isdir(log_folder):
                os.makedirs(log_folder)
            timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")
            with io.open(STARTUP_LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(u"{0} {1}\r\n".format(timestamp, message))
        except Exception:
            pass


doc = revit.doc
uidoc = revit.uidoc
original_active_view = doc.ActiveView
startup_logger = _StartupFileLogger()


def _log_startup_stage(stage_name, started_ms, detail=u""):
    elapsed_ms = STARTUP_WATCH.ElapsedMilliseconds - started_ms
    detail_text = u" ({0})".format(detail) if detail else u""
    try:
        startup_logger.info(
            u"[Scan QC Startup] {0}: {1} ms{2}".format(
                stage_name,
                elapsed_ms,
                detail_text
            )
        )
    except Exception:
        pass


register_document_invalidation(doc.Application)

stage_started_ms = STARTUP_WATCH.ElapsedMilliseconds
scan_qc_settings = load_scan_qc_settings()
_log_startup_stage(u"settings JSON load", stage_started_ms)

stage_started_ms = STARTUP_WATCH.ElapsedMilliseconds
target_parameter_status, parameter_cache_hit = get_or_collect(
    doc,
    "target_parameter_status",
    lambda: inspect_target_parameter(doc)
)
_log_startup_stage(
    u"SCAN_QC_TARGET parameter existence check",
    stage_started_ms,
    u"cache hit" if parameter_cache_hit else u"collected"
)
if target_parameter_status.get("same_name_different_guid", False):
    forms.alert(
        "A parameter named SCAN_QC_TARGET already exists with a different GUID. "
        "It will not be replaced automatically.",
        title="Scan QC - Parameter GUID Conflict",
        warn_icon=True
    )

if (
    not target_parameter_status.get("available", False)
    and not (
        target_parameter_status.get("same_name_different_guid", False)
        and not target_parameter_status.get("same_guid_found", False)
    )
):
    should_install_target_parameter = forms.alert(
        "SCAN_QC_TARGET is not installed as a Wall instance Shared Parameter.\n\n"
        "Install it now under Identity Data? Existing Wall values will remain No.",
        title="Scan QC - Install Target Parameter",
        yes=True,
        no=True
    )
    if should_install_target_parameter:
        target_parameter_status = install_target_parameter(
            doc,
            doc.Application
        )
        set_cached_value(
            doc,
            "target_parameter_status",
            target_parameter_status
        )
        if not target_parameter_status.get("available", False):
            forms.alert(
                "SCAN_QC_TARGET could not be installed.\n\n{0}".format(
                    target_parameter_status.get("error", "Unknown error")
                ),
                title="Scan QC - Parameter Installation Failed",
                warn_icon=True
            )

stage_started_ms = STARTUP_WATCH.ElapsedMilliseconds
source_plan_views, source_views_cache_hit = get_or_collect(
    doc,
    "source_plan_views",
    lambda: collect_source_plan_views(doc)
)
_log_startup_stage(
    u"source plan view collection",
    stage_started_ms,
    u"cache hit" if source_views_cache_hit else u"collected"
)
if not source_plan_views:
    forms.alert(
        "Scan QC requires at least one duplicable Plan View "
        "(Floor Plan, Ceiling Plan, Engineering Plan, or Area Plan).",
        title="Scan QC - Source Plan View Required",
        warn_icon=True
    )
    script.exit()

stage_started_ms = STARTUP_WATCH.ElapsedMilliseconds
point_clouds, point_clouds_cache_hit = get_or_collect(
    doc,
    "point_clouds",
    lambda: collect_point_cloud_instances(doc)
)
_log_startup_stage(
    u"point cloud collection",
    stage_started_ms,
    u"cache hit" if point_clouds_cache_hit else u"collected"
)

default_source_plan_view = get_default_source_plan_view(
    source_plan_views,
    original_active_view
)
default_source_plan_view_id = (
    get_element_id_value(default_source_plan_view.Id)
    if default_source_plan_view is not None
    else None
)
selected_walls = collect_selected_walls(uidoc)

try:
    startup_logger.info(
        u"[Scan QC Startup] standards check: 0 ms (deferred until Run)"
    )
    startup_logger.info(
        u"[Scan QC Startup] sheet/titleblock collection: 0 ms "
        u"(deferred until requested)"
    )
    startup_logger.info(
        u"[Scan QC Startup] target wall count: 0 ms (deferred)"
    )
except Exception:
    pass


def _handle_target_parameter_action(action_name, source_plan_view):
    if action_name == u"select_targets":
        select_result = select_target_walls(
            doc,
            uidoc,
            source_plan_view
        )
        if select_result.get("error", u""):
            return {
                "error": select_result["error"],
                "target_count": select_result.get("selected_count", 0)
            }
        selected_count = select_result.get("selected_count", 0)
        return {
            "target_count": selected_count,
            "message": (
                u"Showing {0} target Wall(s).".format(selected_count)
                if selected_count
                else u"No target Walls were found in this Source Plan View."
            )
        }

    pick_result = pick_walls(uidoc)
    if pick_result.get("cancelled", False):
        return {"cancelled": True}
    if pick_result.get("error", u""):
        return {"error": pick_result["error"]}

    target_value = action_name == u"mark_selected"
    action_result = set_selected_wall_targets(
        doc,
        pick_result.get("walls", []),
        target_value
    )
    if action_result.get("error", u""):
        return {"error": action_result["error"]}

    target_count = len(collect_target_walls(doc, source_plan_view))
    return {
        "target_count": target_count,
        "message": (
            u"Updated {0} Wall(s); skipped {1}.".format(
                action_result.get("updated_count", 0),
                action_result.get("skipped_count", 0)
            )
        )
    }


def _load_existing_report_sheets():
    from scan_qc.report_export import collect_report_sheets

    lazy_watch = Stopwatch.StartNew()
    sheets = collect_report_sheets(doc)
    lazy_watch.Stop()
    try:
        startup_logger.info(
            u"[Scan QC Startup] sheet collection (lazy): {0} ms".format(
                lazy_watch.ElapsedMilliseconds
            )
        )
    except Exception:
        pass
    return sheets


selected_options = request_scan_qc_options(
    len(selected_walls),
    point_clouds,
    source_plan_views,
    [],
    default_source_plan_view_id,
    scan_qc_settings,
    target_parameter_status,
    {},
    None,
    _handle_target_parameter_action,
    _load_existing_report_sheets,
    {"logger": startup_logger, "total_watch": STARTUP_WATCH}
)

if selected_options is None:
    script.exit()

selected_walls = collect_selected_walls(uidoc)

from scan_qc.analysis_scope import (
    build_analysis_scope_result,
    resolve_selected_walls
)
from scan_qc.deviation import calculate_wall_deviations
from scan_qc.markers import (
    build_marker_preview_result,
    create_3d_marker_preview,
    create_plan_marker_preview
)
from scan_qc.report_export import create_scan_qc_report
from scan_qc.reporting import render_scan_qc_summary
from scan_qc.settings import get_view_creation_options
from scan_qc.standards import install_missing_standards
from scan_qc.views import create_requested_scan_qc_views

if selected_options.get("create_pdf_report", False):
    pdf_plan_dependency = selected_options.get("pdf_required_qc_plan_view", u"")
    if selected_options.get("create_plan_view", False):
        if not pdf_plan_dependency or pdf_plan_dependency == u"N/A":
            selected_options["pdf_required_qc_plan_view"] = u"Existing"
    else:
        selected_options["create_plan_view"] = True
        selected_options["pdf_required_qc_plan_view"] = u"Auto-created"
        selected_output_options = selected_options.get("selected_output_options", [])
        if isinstance(selected_output_options, list):
            selected_output_options.append(u"Create QC Plan View (auto for PDF)")
else:
    selected_options["pdf_required_qc_plan_view"] = u"Not requested"

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
    requested=selected_options.get("create_plan_view", False),
    selected_options=selected_options
)
view3d_marker_preview = create_3d_marker_preview(
    view3d,
    requested=selected_options.get("create_3d_view", False)
)
view_creation_result["marker_preview"] = build_marker_preview_result(
    plan_marker_preview,
    view3d_marker_preview
)
view_creation_result["report"] = create_scan_qc_report(
    doc,
    source_plan_view,
    plan_view,
    selected_options,
    view_creation_result,
    scan_qc_settings
)

render_scan_qc_summary(
    script.get_output(),
    len(selected_walls),
    selected_options,
    standards_result,
    view_creation_result
)
