# -*- coding: utf-8 -*-

# Quick read-only QC summary: Sheet + View + Parameter. No Transaction.

import io
import os
import sys

from pyrevit import revit, script
from System import DateTime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
CONFIG_PATH = os.path.join(
    EXTENSION_DIR,
    "config",
    "qc_config_default.json"
)
REPORTS_DIR = os.path.join(EXTENSION_DIR, "reports")

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from checks_parameter import run_parameter_checks
from checks_sheet import run_sheet_checks
from checks_view import run_view_checks
from collectors import (
    collect_parameter_elements,
    collect_placed_view_ids,
    collect_sheets,
    collect_views,
    to_text
)
from config_loader import load_config
from export_options import request_export_options
from compact_summary import save_compact_summary_html
from exporters import (
    export_compact_summary_pdf,
    export_styled_xlsx,
    save_full_csv,
    save_summary_csv
)
from grouping import (
    build_issue_group_rows,
    build_key_issue_rows,
    build_representative_issue_rows,
    build_summary_data,
    get_qc_status
)
from report_history import select_latest_report_path, write_latest_report_path
from report_ui import html_escape, render_quick_report
import qc_lite_dashboard
from qc_workflow_ui import show_qc_lite_dashboard
from qc_result_model import build_qc_result_model
from toolkit_version import get_toolkit_version_label
from ui_close_profiler import is_ui_perf_debug_enabled


config = load_config(CONFIG_PATH)
VERSION = config["version"]
CONFIG_META = config.get("_config_meta", {})
ACTIVE_CONFIG_PATH = CONFIG_META.get("active_config_path", CONFIG_PATH)
ACTIVE_CONFIG_FILE = CONFIG_META.get(
    "active_config_file",
    os.path.basename(ACTIVE_CONFIG_PATH)
)
ACTIVE_PRESET_NAME = CONFIG_META.get("preset_name", u"Default QC")
ACTIVE_CONFIG_DISPLAY = u"{0} ({1})".format(
    ACTIVE_PRESET_NAME,
    ACTIVE_CONFIG_FILE
)
doc = revit.doc
selected_export_options = request_export_options(REPORTS_DIR, quick_mode=True)

if selected_export_options is None:
    script.exit()

run_time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
view_config = config["view_qc"]
parameter_config = config["parameter_qc"]
sheets = collect_sheets(doc)
placed_view_ids = collect_placed_view_ids(sheets)
checked_views = collect_views(doc, view_config["supported_view_types"])
parameter_collections = collect_parameter_elements(
    doc,
    parameter_config["rules"]
)

issue_rows = []
run_sheet_checks(sheets, issue_rows, config["sheet_qc"])
run_view_checks(checked_views, placed_view_ids, issue_rows, view_config)
checked_parameter_elements = run_parameter_checks(
    doc,
    parameter_collections,
    issue_rows
)

issue_group_rows = build_issue_group_rows(issue_rows)
compact_issue_group_rows = build_issue_group_rows(
    issue_rows,
    shorten_samples=False,
    sample_max_length=config["display"]["group_sample_max_length"],
    sample_limit=3
)
key_issue_rows = build_key_issue_rows(
    issue_rows,
    view_config["temporary_keywords"],
    key_issue_limit=3,
    item_max_length=config["display"]["key_item_max_length"]
)
representative_issue_rows = build_representative_issue_rows(
    issue_rows,
    item_max_length=max(
        80,
        config["display"]["key_item_max_length"]
    )
)
summary_data = build_summary_data(issue_rows, len(sheets), len(checked_views))
qc_status = get_qc_status(summary_data)
timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")
export_time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
report_context = {
    "project": to_text(doc.Title),
    "active_config": ACTIVE_CONFIG_PATH,
    "active_config_display": ACTIVE_CONFIG_DISPLAY,
    "active_preset": ACTIVE_PRESET_NAME,
    "run_mode": u"QC Lite",
    "checked_parameter_elements": checked_parameter_elements,
    "review_group_count": len(issue_group_rows),
    "run_time": run_time,
    "export_time": export_time,
    "key_issue_rows": key_issue_rows,
    "external_python_path": config["export"].get(
        "external_python_path",
        u""
    ),
    "debug_keep_temp_json": config["export"].get(
        "debug_keep_temp_json",
        False
    ),
    "reports_dir": REPORTS_DIR
}
result_model = build_qc_result_model(
    summary_data,
    qc_status,
    compact_issue_group_rows,
    representative_issue_rows,
    {
        "project": report_context["project"],
        "run_mode": report_context["run_mode"],
        "tool_version": VERSION,
        "active_config": ACTIVE_CONFIG_DISPLAY,
        "run_time": run_time,
        "export_time": export_time,
        "checked_parameter_elements": checked_parameter_elements
    }
)
report_context["result_model"] = result_model
report_context["key_issue_rows"] = [
    [
        item["category"],
        item["item_type"],
        item["item_name"],
        item["severity"],
        item["qc_item"],
        item["message"]
    ]
    for item in result_model["representative_items"]
]
saved_full_csv_path = u""
saved_summary_csv_path = u""
saved_styled_xlsx_path = u""
saved_compact_html_path = u""
saved_compact_pdf_path = u""
full_csv_error = u""
summary_csv_error = u""
styled_xlsx_error = u""
compact_html_error = u""
compact_pdf_error = u""
history_error = u""

if selected_export_options["full_csv"]:
    try:
        saved_full_csv_path = save_full_csv(
            issue_rows,
            summary_data,
            qc_status,
            timestamp,
            VERSION,
            config["export"]["file_prefix"],
            selected_export_options["folder"]
        )
    except Exception as ex:
        full_csv_error = to_text(ex)

if selected_export_options["summary_csv"]:
    try:
        saved_summary_csv_path = save_summary_csv(
            issue_group_rows,
            summary_data,
            qc_status,
            timestamp,
            VERSION,
            config["export"]["file_prefix"],
            selected_export_options["folder"]
        )
    except Exception as ex:
        summary_csv_error = to_text(ex)

if selected_export_options["styled_xlsx"]:
    try:
        saved_styled_xlsx_path, styled_xlsx_error = export_styled_xlsx(
            issue_rows,
            issue_group_rows,
            summary_data,
            qc_status,
            timestamp,
            VERSION,
            config["export"]["file_prefix"],
            selected_export_options["folder"],
            report_context
        )
    except Exception as ex:
        styled_xlsx_error = to_text(ex)

if selected_export_options.get("compact_html", False):
    try:
        saved_compact_html_path = save_compact_summary_html(
            result_model,
            timestamp,
            config["export"]["file_prefix"],
            selected_export_options["folder"]
        )
    except Exception as ex:
        compact_html_error = to_text(ex)

if selected_export_options.get("compact_pdf", False):
    try:
        saved_compact_pdf_path, compact_pdf_error = export_compact_summary_pdf(
            result_model,
            timestamp,
            config["export"]["file_prefix"],
            selected_export_options["folder"],
            report_context
        )
    except Exception as ex:
        compact_pdf_error = to_text(ex)

latest_report_path = select_latest_report_path(
    saved_styled_xlsx_path,
    saved_summary_csv_path,
    saved_full_csv_path
)
latest_report_path = (
    saved_compact_pdf_path
    or saved_compact_html_path
    or latest_report_path
)

if latest_report_path:
    try:
        write_latest_report_path(REPORTS_DIR, latest_report_path)
    except Exception as ex:
        history_error = to_text(ex)

output_state = {"output": None, "rendered": False}


def show_detailed_output():
    existing_output = output_state.get("output")
    if output_state.get("rendered", False):
        if existing_output is not None:
            try:
                existing_output.show()
            except Exception:
                pass
        return

    output = script.get_output()
    output_state["output"] = output
    output.set_title(
        "Revit QC Lite Details {0}".format(get_toolkit_version_label())
    )
    if CONFIG_META.get("warning", u""):
        output.print_html(
            u"<div style='padding:8px; background:#FFF1E6; color:#263645;'>"
            u"QC Preset warning: {0}</div>".format(
                html_escape(CONFIG_META["warning"])
            )
        )
    render_quick_report(
        output,
        get_toolkit_version_label(),
        summary_data,
        qc_status,
        len(issue_group_rows),
        key_issue_rows,
        saved_full_csv_path,
        full_csv_error,
        saved_summary_csv_path,
        summary_csv_error,
        saved_styled_xlsx_path,
        styled_xlsx_error,
        saved_compact_html_path,
        compact_html_error,
        saved_compact_pdf_path,
        compact_pdf_error,
        selected_export_options
    )
    if history_error:
        output.print_html(
            u"<div style='color:#b71c1c;'>마지막 리포트 경로 저장 실패: "
            u"{0}</div>".format(html_escape(history_error))
        )
    output_state["rendered"] = True


dashboard_diagnostic_log_path = None
if is_ui_perf_debug_enabled():
    dashboard_diagnostic_log_path = os.path.join(
        REPORTS_DIR,
        "qc_lite_dashboard_runtime.log"
    )
    try:
        if not os.path.isdir(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)
        with io.open(
            dashboard_diagnostic_log_path,
            "a",
            encoding="utf-8"
        ) as runtime_log:
            runtime_log.write(
                u"[{0}] module={1};class={2};call={3};styled_xlsx={4};"
                u"build={5}\n".format(
                    DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    getattr(qc_lite_dashboard, "__file__", u"N/A"),
                    qc_lite_dashboard.QcLiteDashboardForm.__name__,
                    u"show_qc_lite_dashboard",
                    selected_export_options.get("styled_xlsx", False),
                    qc_lite_dashboard.QC_LITE_DASHBOARD_BUILD
                )
            )
    except Exception:
        dashboard_diagnostic_log_path = None

show_qc_lite_dashboard(
    to_text(doc.Title),
    summary_data,
    key_issue_rows,
    latest_report_path,
    show_detailed_output,
    dashboard_diagnostic_log_path
)
