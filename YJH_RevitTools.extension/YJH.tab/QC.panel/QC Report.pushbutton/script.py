# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible
# Read-only QC entry point: no Transaction and no model modification.

import os
import sys

from pyrevit import revit, script
from System import DateTime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, "lib")
CONFIG_PATH = os.path.join(
    SCRIPT_DIR,
    "config",
    "qc_config_default.json"
)

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
from exporters import save_full_csv, save_summary_csv
from grouping import (
    build_issue_group_rows,
    build_key_issue_rows,
    build_summary_data,
    get_qc_status
)
from report_ui import render_report


config = load_config(CONFIG_PATH)
VERSION = config["version"]

doc = revit.doc
output = script.get_output()
output.set_title("Revit QC Report {0}".format(VERSION))

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
saved_full_csv_path = u""
saved_summary_csv_path = u""
full_csv_error = u""
summary_csv_error = u""

try:
    saved_full_csv_path = save_full_csv(
        issue_rows,
        summary_data,
        qc_status,
        csv_timestamp,
        VERSION,
        export_config["file_prefix"]
    )
except Exception as ex:
    full_csv_error = to_text(ex)

try:
    saved_summary_csv_path = save_summary_csv(
        issue_group_rows,
        summary_data,
        qc_status,
        csv_timestamp,
        VERSION,
        export_config["file_prefix"]
    )
except Exception as ex:
    summary_csv_error = to_text(ex)

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
    summary_csv_error
)
