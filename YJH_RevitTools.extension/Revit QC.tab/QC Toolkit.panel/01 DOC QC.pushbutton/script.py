# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible
# Read-only QC entry point: no Transaction and no model modification.

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
from exporters import export_styled_xlsx, save_full_csv, save_summary_csv
from grouping import (
    build_issue_group_rows,
    build_key_issue_rows,
    build_summary_data,
    get_qc_status
)
from report_history import select_latest_report_path, write_latest_report_path
from report_ui import html_escape, render_report


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
output = script.get_output()
output.set_title("Revit QC Report {0}".format(VERSION))
if CONFIG_META.get("warning", u""):
    output.print_html(
        u"<div style='padding:8px; background:#FFF1E6; color:#263645;'>"
        u"QC Preset warning: {0}</div>".format(
            html_escape(CONFIG_META["warning"])
        )
    )

selected_export_options = request_export_options(REPORTS_DIR, quick_mode=False)

if selected_export_options is None:
    output.print_html(
        u"<h2>Revit QC Report</h2><p>Export cancelled by user</p>"
    )
    script.exit()

run_time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
sheet_config = config["sheet_qc"]
view_config = config["view_qc"]
parameter_config = config["parameter_qc"]
display_config = config["display"]
export_config = config["export"]

sheets = collect_sheets(doc)
placed_view_ids = collect_placed_view_ids(sheets)
checked_views = collect_views(
    doc,
    view_config["supported_view_types"]
)
parameter_collections = collect_parameter_elements(
    doc,
    parameter_config["rules"]
)

issue_rows = []
run_sheet_checks(sheets, issue_rows, sheet_config)
run_view_checks(
    checked_views,
    placed_view_ids,
    issue_rows,
    view_config
)
checked_parameter_elements = run_parameter_checks(
    doc,
    parameter_collections,
    issue_rows
)

issue_group_rows = build_issue_group_rows(issue_rows)
display_issue_group_rows = build_issue_group_rows(
    issue_rows,
    shorten_samples=True,
    sample_max_length=display_config["group_sample_max_length"],
    sample_limit=display_config["group_sample_limit"]
)
key_issue_rows = build_key_issue_rows(
    issue_rows,
    view_config["temporary_keywords"],
    key_issue_limit=display_config["key_issue_limit"],
    item_max_length=display_config["key_item_max_length"]
)
summary_data = build_summary_data(
    issue_rows,
    len(sheets),
    len(checked_views)
)
qc_status = get_qc_status(summary_data)

csv_timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")
export_time = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
report_context = {
    "project": to_text(doc.Title),
    "active_config": ACTIVE_CONFIG_PATH,
    "active_config_display": ACTIVE_CONFIG_DISPLAY,
    "active_preset": ACTIVE_PRESET_NAME,
    "run_mode": u"DOC QC",
    "checked_parameter_elements": checked_parameter_elements,
    "review_group_count": len(issue_group_rows),
    "run_time": run_time,
    "export_time": export_time,
    "key_issue_rows": key_issue_rows,
    "external_python_path": export_config.get("external_python_path", u""),
    "debug_keep_temp_json": export_config.get("debug_keep_temp_json", False),
    "reports_dir": REPORTS_DIR
}
saved_full_csv_path = u""
saved_summary_csv_path = u""
saved_styled_xlsx_path = u""
full_csv_error = u""
summary_csv_error = u""
styled_xlsx_error = u""
history_error = u""

if selected_export_options["full_csv"]:
    try:
        saved_full_csv_path = save_full_csv(
            issue_rows,
            summary_data,
            qc_status,
            csv_timestamp,
            VERSION,
            export_config["file_prefix"],
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
            csv_timestamp,
            VERSION,
            export_config["file_prefix"],
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
            csv_timestamp,
            VERSION,
            export_config["file_prefix"],
            selected_export_options["folder"],
            report_context
        )
    except Exception as ex:
        styled_xlsx_error = to_text(ex)

latest_report_path = select_latest_report_path(
    saved_styled_xlsx_path,
    saved_summary_csv_path,
    saved_full_csv_path
)

if latest_report_path:
    try:
        write_latest_report_path(REPORTS_DIR, latest_report_path)
    except Exception as ex:
        history_error = to_text(ex)

render_report(
    output,
    VERSION,
    summary_data,
    checked_parameter_elements,
    qc_status,
    len(issue_group_rows),
    display_issue_group_rows,
    key_issue_rows,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    selected_export_options
)

if history_error:
    output.print_html(
        u"""
        <div style="margin-top:10px; color:#b71c1c;">
            마지막 리포트 경로 저장 실패: {0}
        </div>
        """.format(html_escape(history_error))
    )
