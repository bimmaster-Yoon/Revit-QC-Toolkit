# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import FilteredElementCollector, PointCloudInstance, Wall


def to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def get_element_id_value(element_id):
    """Return an ElementId value for Revit 2026 with legacy fallback."""
    try:
        return element_id.Value
    except AttributeError:
        return element_id.IntegerValue


def collect_selected_walls(uidoc):
    """Collect only Wall elements from the current Revit selection."""
    selected_walls = []

    for element_id in uidoc.Selection.GetElementIds():
        element = uidoc.Document.GetElement(element_id)
        if isinstance(element, Wall):
            selected_walls.append(element)

    return selected_walls


def get_point_cloud_name(point_cloud):
    """Return a stable display name for a PointCloudInstance."""
    name = u""

    try:
        name = to_text(point_cloud.Name).strip()
    except Exception:
        pass

    if not name:
        try:
            point_cloud_type = point_cloud.Document.GetElement(point_cloud.GetTypeId())
            name = to_text(point_cloud_type.Name).strip()
        except Exception:
            pass

    if not name:
        name = u"Point Cloud {0}".format(get_element_id_value(point_cloud.Id))

    return name


def collect_point_cloud_instances(doc):
    """Collect every PointCloudInstance in the active document."""
    point_clouds = list(
        FilteredElementCollector(doc)
        .OfClass(PointCloudInstance)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    return sorted(
        point_clouds,
        key=lambda item: (
            get_point_cloud_name(item).lower(),
            get_element_id_value(item.Id)
        )
    )

