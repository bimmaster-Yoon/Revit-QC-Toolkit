# -*- coding: utf-8 -*-

# Quick read-only QC: Sheet + View only. No Transaction.

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


from checks_sheet import run_sheet_checks
from checks_view import run_view_checks
from collectors import collect_placed_view_ids, collect_sheets, collect_views, to_text
from config_loader import load_config
from exporters import save_summary_csv
from grouping import build_issue_group_rows, build_summary_data, get_qc_status
from report_history import write_latest_report_path
from report_ui import html_escape, render_quick_report


config = load_config(CONFIG_PATH)
VERSION = config["version"]
doc = revit.doc
output = script.get_output()
output.set_title("Revit Quick QC {0}".format(VERSION))

view_config = config["view_qc"]
sheets = collect_sheets(doc)
placed_view_ids = collect_placed_view_ids(sheets)
checked_views = collect_views(doc, view_config["supported_view_types"])

issue_rows = []
run_sheet_checks(sheets, issue_rows, config["sheet_qc"])
run_view_checks(checked_views, placed_view_ids, issue_rows, view_config)

issue_group_rows = build_issue_group_rows(issue_rows)
summary_data = build_summary_data(issue_rows, len(sheets), len(checked_views))
qc_status = get_qc_status(summary_data)
timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")
saved_summary_csv_path = u""
summary_csv_error = u""
history_error = u""

try:
    saved_summary_csv_path = save_summary_csv(
        issue_group_rows,
        summary_data,
        qc_status,
        timestamp,
        VERSION,
        u"{0}_Quick".format(config["export"]["file_prefix"])
    )
except Exception as ex:
    summary_csv_error = to_text(ex)

if saved_summary_csv_path:
    try:
        write_latest_report_path(REPORTS_DIR, saved_summary_csv_path)
    except Exception as ex:
        history_error = to_text(ex)

render_quick_report(
    output,
    VERSION,
    summary_data,
    qc_status,
    len(issue_group_rows),
    saved_summary_csv_path,
    summary_csv_error
)

if history_error:
    output.print_html(
        u"<div style='color:#b71c1c;'>마지막 리포트 경로 저장 실패: {0}</div>".format(
            html_escape(history_error)
        )
    )
