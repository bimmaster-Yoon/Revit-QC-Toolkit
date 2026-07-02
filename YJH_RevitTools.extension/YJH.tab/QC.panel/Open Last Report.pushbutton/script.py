# -*- coding: utf-8 -*-

import os
import sys

from pyrevit import script


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
REPORTS_DIR = os.path.join(EXTENSION_DIR, "reports")

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


from report_history import open_file, read_latest_report_path
from report_ui import html_escape


output = script.get_output()
output.set_title("Open Last QC Report")
report_path, read_error = read_latest_report_path(REPORTS_DIR)

if read_error:
    output.print_html(
        u"""
        <div style="padding:10px; border-left:4px solid #ef6c00; background:#fff8e1;">
            <strong>마지막 리포트를 열 수 없습니다.</strong><br>{0}
        </div>
        """.format(html_escape(read_error))
    )
else:
    opened, open_error = open_file(report_path)

    if opened:
        output.print_html(
            u"<h2>Open Last Report</h2><p>파일을 열었습니다.<br>{0}</p>".format(
                html_escape(report_path)
            )
        )
    else:
        output.print_html(
            u"<h2>Open Last Report</h2><p>{0}</p>".format(
                html_escape(open_error)
            )
        )
