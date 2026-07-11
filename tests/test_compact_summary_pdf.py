# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import tempfile
import unittest

from pypdf import PdfReader


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TOOLS_DIR = os.path.join(ROOT, "YJH_RevitTools.extension", "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from make_compact_summary_pdf import create_pdf


class CompactSummaryPdfTests(unittest.TestCase):
    def test_creates_single_page_pdf_from_result_model(self):
        model = {
            "metadata": {"project": "Portfolio", "run_mode": "QC Lite", "tool_version": "v2.9", "export_time": "2026-07-11 10:00:00"},
            "qc_status": "Review Required",
            "kpi": {"checked_items": 407, "checked_sheets": 105, "checked_views": 302, "total_findings": 365, "critical_items": 69},
            "issue_count_by_qc": {"sheet_qc": 4, "view_qc": 46, "parameter_qc": 315},
            "top_review_groups": [
                {"category": "Parameter QC", "item_type": "Rooms", "qc_item": "RoomType", "severity": "High", "count": 69, "sample_display": "C-15, C-16, C-17 + 66 more"}
            ],
            "representative_items": [
                {"category": "Parameter QC", "item_type": "Rooms", "item_name": "C-15", "severity": "High", "qc_item": "RoomType", "message": "Shared Parameter 없음"}
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "summary.pdf")
            create_pdf(model, output_path)
            self.assertTrue(os.path.isfile(output_path))
            self.assertGreater(os.path.getsize(output_path), 5000)
            reader = PdfReader(output_path)
            self.assertEqual(1, len(reader.pages))


if __name__ == "__main__":
    unittest.main()
