# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TOOLS_DIR = os.path.join(ROOT, "YJH_RevitTools.extension", "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from make_styled_xlsx import create_workbook


class StyledXlsxSummaryTests(unittest.TestCase):
    def test_first_sheet_uses_common_result_model(self):
        payload = {
            "result_model": {
                "qc_status": "Review Required",
                "kpi": {"checked_items": 407, "total_findings": 365, "critical_items": 69},
                "issue_count_by_qc": {"sheet_qc": 4, "view_qc": 46, "parameter_qc": 315},
                "review_group_count": 13,
            },
            "summary_data": {
                "checked_sheets": 105,
                "checked_views": 302,
                "total_issues": 365,
                "high_count": 69,
                "medium_count": 293,
                "low_count": 3,
                "sheet_issues": 4,
                "view_issues": 46,
                "parameter_issues": 315,
            },
            "metadata": {"project": "Portfolio", "run_mode": "QC Lite", "export_time": "2026-07-11", "tool_version": "v2.9", "active_config": "Default", "export_folder": "38_DOC_QC"},
            "review_groups": [],
            "key_samples": [],
            "full_detail": [],
        }
        workbook = create_workbook(payload)
        self.assertEqual("SUMMARY", workbook.sheetnames[0])
        self.assertIn("Full Detail", workbook.sheetnames)
        values = [cell.value for row in workbook["SUMMARY"].iter_rows() for cell in row]
        self.assertIn(407, values)
        self.assertIn(365, values)
        self.assertIn(69, values)
        self.assertIn(315, values)


if __name__ == "__main__":
    unittest.main()
