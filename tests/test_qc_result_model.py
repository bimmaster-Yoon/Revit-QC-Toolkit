# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LIB_DIR = os.path.join(ROOT, "YJH_RevitTools.extension", "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from qc_result_model import build_qc_result_model
from compact_summary import build_compact_summary_html


class QcResultModelTests(unittest.TestCase):
    def setUp(self):
        self.summary_data = {
            "checked_sheets": 105,
            "checked_views": 302,
            "sheet_issues": 4,
            "view_issues": 46,
            "parameter_issues": 315,
            "total_issues": 365,
            "high_count": 69,
            "medium_count": 293,
            "low_count": 3,
        }
        self.group_rows = [
            ["View QC", "Detail", "Sheet Placement", "Medium", 24, "A, B, C"],
            ["Parameter QC", "Rooms", "RoomType", "High", 69, "C-15 [Id: 1], C-16 [Id: 2], C-17 [Id: 3]"],
            ["Sheet QC", "L-001", "Placed Views", "Medium", 1, "Sheet List"],
            ["View QC", "Floor Plan", "Sheet Placement", "Medium", 6, "D, E, F"],
            ["View QC", "Elevation", "View Template", "Medium", 5, "G, H, I"],
            ["View QC", "3D View", "View Name", "Low", 3, "J, K, L"],
        ]
        self.key_rows = [
            ["Parameter QC", "Rooms", "C-15 [Id: 8581802]", "High", "RoomType", "Shared Parameter 없음"],
            ["Sheet QC", "L-001", "시트목록#1", "Medium", "Placed Views", "배치된 View 없음"],
            ["View QC", "Ceiling Plan", "1F CF.L", "Medium", "Sheet Placement", "미배치"],
            ["View QC", "3D View", "Copy", "Low", "View Name", "임시 키워드"],
        ]

    def test_builds_reconciled_kpis_and_top_groups(self):
        model = build_qc_result_model(
            self.summary_data,
            "Review Required",
            self.group_rows,
            self.key_rows,
            {"project": "Portfolio", "run_mode": "QC Lite"},
        )
        self.assertEqual(407, model["kpi"]["checked_items"])
        self.assertEqual(365, model["kpi"]["total_findings"])
        self.assertEqual(69, model["kpi"]["critical_items"])
        self.assertEqual(
            {"sheet_qc": 4, "view_qc": 46, "parameter_qc": 315},
            model["issue_count_by_qc"],
        )
        self.assertEqual(5, len(model["top_review_groups"]))
        self.assertEqual("RoomType", model["top_review_groups"][0]["qc_item"])
        self.assertEqual(69, model["top_review_groups"][0]["count"])

    def test_limits_samples_and_removes_element_ids(self):
        model = build_qc_result_model(
            self.summary_data,
            "Review Required",
            self.group_rows,
            self.key_rows,
            {},
        )
        self.assertEqual(3, len(model["representative_items"]))
        self.assertNotIn("[Id:", model["representative_items"][0]["item_name"])
        self.assertIn("+ 66 more", model["top_review_groups"][0]["sample_display"])
        self.assertNotIn("[Id:", model["top_review_groups"][0]["sample_display"])

    def test_official_html_uses_only_model_values(self):
        model = build_qc_result_model(
            self.summary_data,
            "Review Required",
            self.group_rows,
            self.key_rows,
            {"project": "Portfolio", "run_mode": "QC Lite", "tool_version": "v2.9"},
        )
        html = build_compact_summary_html(model)
        self.assertIn("Checked Items", html)
        self.assertIn("Total Findings", html)
        self.assertIn(">407<", html)
        self.assertIn(">365<", html)
        self.assertIn(">69<", html)
        self.assertNotIn("PORTFOLIO CAPTURE / DEVELOPMENT ONLY", html)
        self.assertNotIn("DEV / PORTFOLIO_CAPTURE", html)
        self.assertNotIn("[Id:", html)


if __name__ == "__main__":
    unittest.main()
