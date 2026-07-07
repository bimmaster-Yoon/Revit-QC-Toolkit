# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import (
    BoundingBoxXYZ,
    FilteredElementCollector,
    Floor,
    Level,
    Transform,
    UnitTypeId,
    UnitUtils,
    ViewType,
    Wall,
    XYZ
)
from Autodesk.Revit.Exceptions import OperationCanceledException
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

from scan_qc.collectors import get_element_id_value


ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL = u"active_plan_level"
ANALYSIS_SCOPE_SELECTED_WALLS = u"selected_walls"
ANALYSIS_SCOPE_LABELS = {
    ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL: u"Active Plan Level",
    ANALYSIS_SCOPE_SELECTED_WALLS: u"Selected Walls"
}

PLAN_VIEW_TYPES = (
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.EngineeringPlan,
    ViewType.AreaPlan
)

LEVEL_Z_BELOW_MM = 200.0
LEVEL_Z_ABOVE_MM = 1500.0


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


class WallSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        return isinstance(element, Wall)

    def AllowReference(self, reference, position):
        return False


def prompt_for_walls(uidoc):
    """Prompt for multiple Walls using Revit's Finish/Cancel selection workflow."""
    try:
        references = uidoc.Selection.PickObjects(
            ObjectType.Element,
            WallSelectionFilter(),
            "Select Walls for Scan QC, then click Finish"
        )
        walls = []
        for reference in references:
            element = uidoc.Document.GetElement(reference.ElementId)
            if isinstance(element, Wall):
                walls.append(element)
        return walls, u""
    except OperationCanceledException:
        return [], u"Wall selection was cancelled."
    except Exception as ex:
        return [], u"Wall selection failed: {0}".format(_to_text(ex))


def resolve_selected_walls(uidoc, analysis_scope, current_selected_walls):
    """Use current Walls first, then prompt only for Selected Walls scope."""
    if analysis_scope != ANALYSIS_SCOPE_SELECTED_WALLS:
        return current_selected_walls, u""
    if current_selected_walls:
        return current_selected_walls, u""
    return prompt_for_walls(uidoc)


def _get_bounding_box_corners(bounding_box):
    minimum = bounding_box.Min
    maximum = bounding_box.Max
    transform = bounding_box.Transform or Transform.Identity
    corners = []

    for x_value in (minimum.X, maximum.X):
        for y_value in (minimum.Y, maximum.Y):
            for z_value in (minimum.Z, maximum.Z):
                corners.append(
                    transform.OfPoint(XYZ(x_value, y_value, z_value))
                )

    return corners


def _collect_element_points(elements):
    points = []
    for element in elements:
        try:
            bounding_box = element.get_BoundingBox(None)
            if bounding_box is not None:
                points.extend(_get_bounding_box_corners(bounding_box))
        except Exception:
            pass
    return points


def _create_section_box_from_ranges(min_x, max_x, min_y, max_y, min_z, max_z):
    section_box = BoundingBoxXYZ()
    section_box.Transform = Transform.Identity
    section_box.Min = XYZ(min_x, min_y, min_z)
    section_box.Max = XYZ(max_x, max_y, max_z)
    return section_box


def _internal_to_mm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Millimeters)


def _mm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(float(value), UnitTypeId.Millimeters)


def _get_active_plan_level(doc, active_view):
    if active_view is None or active_view.IsTemplate:
        return None
    if active_view.ViewType not in PLAN_VIEW_TYPES:
        return None

    try:
        level = active_view.GenLevel
        if isinstance(level, Level):
            return level
    except Exception:
        pass

    try:
        level = doc.GetElement(active_view.LevelId)
        if isinstance(level, Level):
            return level
    except Exception:
        pass

    return None


def _get_crop_box_xy_points(active_view):
    try:
        if not active_view.CropBoxActive:
            return []
        crop_box = active_view.CropBox
        if crop_box is None:
            return []
        return _get_bounding_box_corners(crop_box)
    except Exception:
        return []


def _element_is_on_level(element, level):
    try:
        return get_element_id_value(element.LevelId) == get_element_id_value(level.Id)
    except Exception:
        return False


def _get_level_element_points(doc, level):
    elements = []
    try:
        walls = (
            FilteredElementCollector(doc)
            .OfClass(Wall)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        elements.extend(wall for wall in walls if _element_is_on_level(wall, level))
    except Exception:
        pass

    try:
        floors = (
            FilteredElementCollector(doc)
            .OfClass(Floor)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        elements.extend(floor for floor in floors if _element_is_on_level(floor, level))
    except Exception:
        pass

    return _collect_element_points(elements)


def _create_scope_result(analysis_scope, selected_wall_count, margin_mm):
    return {
        "analysis_scope": analysis_scope,
        "analysis_scope_label": ANALYSIS_SCOPE_LABELS.get(
            analysis_scope,
            u"Unknown"
        ),
        "selected_wall_count": selected_wall_count,
        "active_level_name": u"",
        "active_level_elevation_mm": None,
        "section_box": None,
        "section_box_source": u"Unavailable",
        "section_box_margin_mm": margin_mm,
        "z_min_mm": None,
        "z_max_mm": None,
        "warnings": [],
        "error": u""
    }


def _build_active_plan_level_scope(doc, active_view, result):
    level = _get_active_plan_level(doc, active_view)
    if level is None:
        result["error"] = (
            u"Active Plan Level scope requires a valid plan-type active view "
            u"with an associated Level."
        )
        return result

    result["active_level_name"] = _to_text(level.Name)
    result["active_level_elevation_mm"] = _internal_to_mm(level.Elevation)
    min_z = level.Elevation - _mm_to_internal(LEVEL_Z_BELOW_MM)
    max_z = level.Elevation + _mm_to_internal(LEVEL_Z_ABOVE_MM)

    xy_points = _get_crop_box_xy_points(active_view)
    if xy_points:
        result["section_box_source"] = u"Active Plan Crop Box"
    else:
        xy_points = _get_level_element_points(doc, level)
        if xy_points:
            result["section_box_source"] = u"Active Level Elements Bounding Box"

    if not xy_points:
        result["error"] = (
            u"No active Crop Box or Wall/Floor bounding boxes were available "
            u"for the active Level."
        )
        return result

    result["section_box"] = _create_section_box_from_ranges(
        min(point.X for point in xy_points),
        max(point.X for point in xy_points),
        min(point.Y for point in xy_points),
        max(point.Y for point in xy_points),
        min_z,
        max_z
    )
    result["z_min_mm"] = _internal_to_mm(min_z)
    result["z_max_mm"] = _internal_to_mm(max_z)
    return result


def _build_selected_walls_scope(selected_walls, result):
    if not selected_walls:
        result["error"] = (
            u"Selected Walls scope requires one or more Wall elements."
        )
        return result

    points = _collect_element_points(selected_walls)
    if not points:
        result["error"] = u"Selected Walls did not provide usable bounding boxes."
        return result

    try:
        margin_internal = _mm_to_internal(result["section_box_margin_mm"])
    except Exception as ex:
        result["error"] = u"Invalid section box margin: {0}".format(_to_text(ex))
        return result

    min_z = min(point.Z for point in points) - margin_internal
    max_z = max(point.Z for point in points) + margin_internal
    result["section_box"] = _create_section_box_from_ranges(
        min(point.X for point in points) - margin_internal,
        max(point.X for point in points) + margin_internal,
        min(point.Y for point in points) - margin_internal,
        max(point.Y for point in points) + margin_internal,
        min_z,
        max_z
    )
    result["section_box_source"] = u"Selected Walls Bounding Box"
    result["z_min_mm"] = _internal_to_mm(min_z)
    result["z_max_mm"] = _internal_to_mm(max_z)
    return result


def build_analysis_scope_result(
    doc,
    active_view,
    selected_walls,
    analysis_scope,
    section_box_margin_mm
):
    """Build a read-only section box and user-facing scope metadata."""
    result = _create_scope_result(
        analysis_scope,
        len(selected_walls),
        section_box_margin_mm
    )

    if analysis_scope == ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL:
        return _build_active_plan_level_scope(doc, active_view, result)
    if analysis_scope == ANALYSIS_SCOPE_SELECTED_WALLS:
        return _build_selected_walls_scope(selected_walls, result)

    result["error"] = u"Unsupported Analysis Scope: {0}".format(analysis_scope)
    return result

