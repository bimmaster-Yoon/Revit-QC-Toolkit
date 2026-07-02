# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import ElementId, ViewType

from collectors import (
    get_element_id_value,
    get_view_type_name,
    is_empty,
    resolve_view_types,
    to_text
)
from grouping import add_issue


def run_view_checks(checked_views, placed_view_ids, issue_rows, view_config):
    """v2.1 View QC 규칙을 설정값에 따라 실행한다."""
    temporary_keywords = view_config.get("temporary_keywords", [])
    template_required_types = resolve_view_types(
        view_config.get("template_required_view_types", [])
    )
    sheet_required_types = resolve_view_types(
        view_config.get("sheet_required_view_types", [])
    )

    for view in checked_views:
        view_name = to_text(view.Name)
        view_type_name = get_view_type_name(view)
        display_view_name = view_name

        if is_empty(display_view_name):
            display_view_name = u"(비어 있음)"

        if is_empty(view_name):
            add_issue(
                issue_rows,
                u"View QC",
                view_type_name,
                display_view_name,
                u"High",
                u"View Name 누락"
            )

        if not is_empty(view_name):
            lower_view_name = view_name.lower()
            matched_keywords = []

            for keyword in temporary_keywords:
                if to_text(keyword).lower() in lower_view_name:
                    matched_keywords.append(to_text(keyword))

            if matched_keywords:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"Low",
                    u"임시 키워드 포함: {0}".format(
                        u", ".join(matched_keywords)
                    )
                )

        should_check_scale = True

        if view.ViewType == ViewType.ThreeD:
            try:
                if view.IsPerspective:
                    should_check_scale = False
            except Exception:
                should_check_scale = True

        if should_check_scale:
            try:
                view_scale = view.Scale

                if view_scale <= 0:
                    add_issue(
                        issue_rows,
                        u"View QC",
                        view_type_name,
                        display_view_name,
                        u"High",
                        u"View Scale 비정상: {0}".format(view_scale)
                    )
            except Exception as ex:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"High",
                    u"View Scale 확인 불가: {0}".format(to_text(ex))
                )

        if view.ViewType in template_required_types:
            try:
                if view.ViewTemplateId == ElementId.InvalidElementId:
                    add_issue(
                        issue_rows,
                        u"View QC",
                        view_type_name,
                        display_view_name,
                        u"Medium",
                        u"View Template 미적용"
                    )
            except Exception as ex:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"Medium",
                    u"View Template 확인 불가: {0}".format(to_text(ex))
                )

        if view.ViewType in sheet_required_types:
            current_view_id = get_element_id_value(view.Id)

            if current_view_id not in placed_view_ids:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"Medium",
                    u"Sheet에 배치되지 않은 도면용 View"
                )
