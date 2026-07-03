# -*- coding: utf-8 -*-

import os
import sys

from pyrevit import script


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
CONFIG_PATH = os.path.join(EXTENSION_DIR, "config", "qc_config_default.json")
LOCAL_CONFIG_PATH = os.path.join(EXTENSION_DIR, "config", "qc_config_local.json")
REPORTS_DIR = os.path.join(EXTENSION_DIR, "reports")

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from settings_ui import show_settings_dialog


output = script.get_output()
output.set_title("Revit QC Settings")
show_settings_dialog(
    output,
    CONFIG_PATH,
    LOCAL_CONFIG_PATH,
    EXTENSION_DIR,
    REPORTS_DIR
)
