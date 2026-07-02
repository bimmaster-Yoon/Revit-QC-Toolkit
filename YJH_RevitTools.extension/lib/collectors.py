# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import (
    BuiltInCategory,
    FilteredElementCollector,
    View,
    ViewSheet,
    ViewType
)


try:
    text_type = unicode
except NameError:
    text_type = str


VIEW_TYPE_NAMES = {
    ViewType.FloorPlan: u"Floor Plan",
    ViewType.CeilingPlan: u"Ceiling Plan",
    ViewType.Elevation: u"Elevation",
    ViewType.Section: u"Section",
    ViewType.Detail: u"Detail",
    ViewType.DraftingView: u"Drafting View",
    ViewType.ThreeD: u"3D View"
}


def to_text(value):
    """값을 IronPython과 CPython에서 안전하게 문자열로 변환한다."""
    if value is None:
        return u""

    try:
        return text_type(value)
    except Exception:
        return text_type(str(value))


def is_empty(value):
    return not to_text(value).strip()


def get_element_id_value(element_id):
    """Revit 2026 및 이전 ElementId API를 함께 지원한다."""
    try:
        return element_id.Value
    except Exception:
        return element_id.IntegerValue


def get_view_type_name(view):
    if view.ViewType in VIEW_TYPE_NAMES:
        return VIEW_TYPE_NAMES[view.ViewType]

    return to_text(view.ViewType)


def resolve_view_types(type_names):
    resolved_types = []

    for type_name in type_names:
        try:
            view_type = getattr(ViewType, type_name)
        except Exception:
            continue

        if view_type not in resolved_types:
            resolved_types.append(view_type)

    return tuple(resolved_types)


def collect_sheets(doc):
    sheets = list(
        FilteredElementCollector(doc)
        .OfClass(ViewSheet)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    return sorted(
        sheets,
        key=lambda sheet: to_text(sheet.SheetNumber)
    )


def collect_placed_view_ids(sheets):
    placed_view_ids = set()

    for sheet in sheets:
        for placed_view_id in sheet.GetAllPlacedViews():
            placed_view_ids.add(get_element_id_value(placed_view_id))

    return placed_view_ids


def collect_views(doc, supported_view_type_names):
    supported_view_types = resolve_view_types(supported_view_type_names)
    all_views = (
        FilteredElementCollector(doc)
        .OfClass(View)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    checked_views = []

    for view in all_views:
        if view.IsTemplate:
            continue

        if view.ViewType not in supported_view_types:
            continue

        checked_views.append(view)

    return sorted(
        checked_views,
        key=lambda view: (
            get_view_type_name(view),
            to_text(view.Name)
        )
    )


def collect_parameter_elements(doc, parameter_rules):
    """설정된 Category별 요소와 규칙을 함께 반환한다."""
    collections = []

    for rule in parameter_rules:
        category_key = rule.get("built_in_category", "")

        try:
            built_in_category = getattr(BuiltInCategory, category_key)
        except Exception:
            continue

        elements = list(
            FilteredElementCollector(doc)
            .OfCategory(built_in_category)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        collections.append(
            {
                "category_name": to_text(rule.get("category_name", "")),
                "parameter_name": to_text(rule.get("parameter_name", "")),
                "elements": elements
            }
        )

    return collections
