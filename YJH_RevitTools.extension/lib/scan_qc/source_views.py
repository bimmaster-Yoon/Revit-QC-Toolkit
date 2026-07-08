# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import FilteredElementCollector, View, ViewDuplicateOption

from scan_qc.analysis_scope import PLAN_VIEW_TYPES
from scan_qc.collectors import get_element_id_value


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def _can_duplicate_plan_view(view):
    try:
        if view is None or view.IsTemplate:
            return False
        if view.ViewType not in PLAN_VIEW_TYPES:
            return False
        return view.CanViewBeDuplicated(ViewDuplicateOption.Duplicate)
    except Exception:
        return False


def _plan_view_sort_key(view):
    view_type_text = _to_text(view.ViewType)
    floor_priority = 0 if view_type_text == u"FloorPlan" else 1
    try:
        level_name = _to_text(view.GenLevel.Name).lower()
    except Exception:
        level_name = u""
    return (
        floor_priority,
        view_type_text,
        level_name,
        _to_text(view.Name).lower(),
        get_element_id_value(view.Id)
    )


def collect_source_plan_views(doc):
    """Return duplicable plan-type views that can be used as Scan QC source views."""
    source_views = []
    try:
        views = (
            FilteredElementCollector(doc)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for view in views:
            if _can_duplicate_plan_view(view):
                source_views.append(view)
    except Exception:
        return []

    return sorted(source_views, key=_plan_view_sort_key)


def get_default_source_plan_view(source_plan_views, active_view):
    """Prefer valid ActiveView, otherwise use the first sorted Floor Plan candidate."""
    if _can_duplicate_plan_view(active_view):
        active_view_id = get_element_id_value(active_view.Id)
        for source_view in source_plan_views:
            if get_element_id_value(source_view.Id) == active_view_id:
                return source_view

    return source_plan_views[0] if source_plan_views else None


def get_source_plan_view_by_id(source_plan_views, source_plan_view_id):
    for source_view in source_plan_views:
        try:
            if (
                get_element_id_value(source_view.Id) == source_plan_view_id
                or _to_text(get_element_id_value(source_view.Id)) == _to_text(source_plan_view_id)
            ):
                return source_view
        except Exception:
            pass
    return None


def get_source_plan_view_name(source_plan_view):
    try:
        return _to_text(source_plan_view.Name)
    except Exception:
        return u"N/A"


def get_source_plan_view_label(source_plan_view):
    view_name = get_source_plan_view_name(source_plan_view)
    try:
        level_name = _to_text(source_plan_view.GenLevel.Name)
    except Exception:
        level_name = u"N/A"
    try:
        view_type = _to_text(source_plan_view.ViewType)
    except Exception:
        view_type = u"Plan"

    return u"{0}  [{1} / Level: {2} / ElementId: {3}]".format(
        view_name,
        view_type,
        level_name or u"N/A",
        get_element_id_value(source_plan_view.Id)
    )
