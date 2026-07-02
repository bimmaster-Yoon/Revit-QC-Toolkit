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

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from report_history import open_file
from report_ui import html_escape


output = script.get_output()
output.set_title("Revit QC Settings")
opened, open_error = open_file(CONFIG_PATH)

if opened:
    status_text = u"기본 연결 프로그램으로 config 파일을 열었습니다."
else:
    status_text = u"자동으로 열지 못했습니다. 아래 경로의 JSON 파일을 직접 수정하세요.<br>{0}".format(
        html_escape(open_error)
    )

output.print_html(
    u"""
    <div style="font-family:Segoe UI, Arial, sans-serif;">
        <h2>QC Settings</h2>
        <p><strong>현재 config 경로</strong><br>{0}</p>
        <p>{1}</p>
        <div style="padding:10px; background:#fff8e1; border-left:4px solid #ef6c00;">
            회사별 Sheet, View, Parameter QC 기준은 이 JSON 파일에서 수정할 수 있습니다.<br>
            변경 전 Git 기준점을 남기고 JSON 문법과 Revit Category 이름을 확인하세요.
        </div>
    </div>
    """.format(html_escape(CONFIG_PATH), status_text)
)
