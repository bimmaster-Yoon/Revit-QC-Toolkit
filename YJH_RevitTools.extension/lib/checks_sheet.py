# -*- coding: utf-8 -*-

from collectors import is_empty, to_text
from grouping import add_issue


def run_sheet_checks(sheets, issue_rows, sheet_config):
    """v2.1 Sheet QC 규칙을 설정값에 따라 실행한다."""
    for sheet in sheets:
        sheet_number = to_text(sheet.SheetNumber)
        sheet_name = to_text(sheet.Name)
        display_number = sheet_number
        display_name = sheet_name

        if is_empty(display_number):
            display_number = u"(비어 있음)"

        if is_empty(display_name):
            display_name = u"(비어 있음)"

        if sheet_config.get("require_sheet_number", True) and is_empty(sheet_number):
            add_issue(
                issue_rows,
                u"Sheet QC",
                display_number,
                display_name,
                u"High",
                u"Sheet Number 누락"
            )

        if sheet_config.get("require_sheet_name", True) and is_empty(sheet_name):
            add_issue(
                issue_rows,
                u"Sheet QC",
                display_number,
                display_name,
                u"High",
                u"Sheet Name 누락"
            )

        if sheet_config.get("require_placed_view", True):
            sheet_view_ids = sheet.GetAllPlacedViews()

            if sheet_view_ids.Count == 0:
                add_issue(
                    issue_rows,
                    u"Sheet QC",
                    display_number,
                    display_name,
                    u"Medium",
                    u"배치된 View 없음"
                )
