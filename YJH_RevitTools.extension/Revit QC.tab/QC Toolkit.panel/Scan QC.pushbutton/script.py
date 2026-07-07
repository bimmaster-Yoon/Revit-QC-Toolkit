# -*- coding: utf-8 -*-

# Revit 2026 + pyRevit + IronPython compatible.
# Initial Scan QC UI entry point: no Transaction and no model modification.

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


from scan_qc.collectors import collect_point_cloud_instances, collect_selected_walls
from scan_qc.dialog import request_scan_qc_options
from scan_qc.reporting import render_scan_qc_summary
from scan_qc.settings import load_scan_qc_settings
from scan_qc.standards import check_scan_qc_standards


doc = revit.doc
uidoc = revit.uidoc

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

standards_check = check_scan_qc_standards(doc, scan_qc_settings)

render_scan_qc_summary(
    script.get_output(),
    len(selected_walls),
    selected_options,
    standards_check
)
