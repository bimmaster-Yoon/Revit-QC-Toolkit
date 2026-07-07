# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import (
    BuiltInParameter,
    Color,
    Curve,
    ElementTypeGroup,
    FilteredElementCollector,
    HorizontalTextAlignment,
    Line,
    LinePatternElement,
    OverrideGraphicSettings,
    Revision,
    RevisionCloud,
    SubTransaction,
    TextElementBackground,
    TextNote,
    TextNoteOptions,
    TextNoteType,
    Transaction,
    TransactionStatus,
    UnitTypeId,
    UnitUtils,
    XYZ
)
from System.Collections.Generic import List

from scan_qc.analysis_scope import (
    ANALYSIS_SCOPE_SELECTED_WALLS,
    PLAN_VIEW_TYPES
)
REVIEW_LABEL = u"MAX 24mm / REVIEW"
CRITICAL_LABEL = u"MAX 52mm / CRITICAL"
PREVIEW_REVISION_DESCRIPTION = u"SCAN QC PREVIEW - NOT DEVIATION DATA"
PREVIEW_ID_TEXT_TYPE_NAME = u"SCAN_QC_PREVIEW_ID"
REVIEW_COLOR = Color(243, 126, 32)
CRITICAL_COLOR = Color(220, 40, 40)
REVIEW_LINE_WEIGHT = 6
CRITICAL_LINE_WEIGHT = 7
REVISION_CLOUD_HALF_SIZE_MM = 650.0
PREVIEW_ID_TEXT_SIZE_MM = 5.0
MIN_PREVIEW_SPACING_MM = 1000.0
DEFAULT_PREVIEW_SPACING_MM = 1500.0
MAX_PREVIEW_SPACING_MM = 3000.0


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def _mm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(float(value), UnitTypeId.Millimeters)


def _offset_point(point, right, up, right_distance, up_distance):
    return (
        point
        .Add(right.Multiply(right_distance))
        .Add(up.Multiply(up_distance))
    )


def _get_view_basis(view):
    return view.RightDirection.Normalize(), view.UpDirection.Normalize()


def _get_view_plane_origin(plan_view):
    try:
        level = plan_view.GenLevel
        if level is not None:
            return XYZ(0.0, 0.0, level.Elevation)
    except Exception:
        pass

    try:
        return plan_view.Origin
    except Exception:
        return XYZ.Zero


def _project_to_view_plane(plan_view, point):
    origin = _get_view_plane_origin(plan_view)
    right, up = _get_view_basis(plan_view)
    delta = point.Subtract(origin)
    return _offset_point(
        origin,
        right,
        up,
        delta.DotProduct(right),
        delta.DotProduct(up)
    )


def _get_box_center(bounding_box):
    minimum = bounding_box.Min
    maximum = bounding_box.Max
    local_center = XYZ(
        (minimum.X + maximum.X) / 2.0,
        (minimum.Y + maximum.Y) / 2.0,
        (minimum.Z + maximum.Z) / 2.0
    )
    try:
        return bounding_box.Transform.OfPoint(local_center)
    except Exception:
        return local_center


def _get_box_center_and_span(plan_view, bounding_box):
    minimum = bounding_box.Min
    maximum = bounding_box.Max
    return (
        _project_to_view_plane(plan_view, _get_box_center(bounding_box)),
        abs(maximum.X - minimum.X),
        abs(maximum.Y - minimum.Y)
    )


def _get_plan_drawing_frame(plan_view, analysis_scope_result):
    try:
        if plan_view.CropBoxActive:
            crop_box = plan_view.CropBox
            if crop_box is not None:
                center, width, height = _get_box_center_and_span(
                    plan_view,
                    crop_box
                )
                return center, width, height, u"QC Plan View Crop Box"
    except Exception:
        pass

    section_box = analysis_scope_result.get("section_box")
    if section_box is not None:
        try:
            center, width, height = _get_box_center_and_span(
                plan_view,
                section_box
            )
            return center, width, height, u"Analysis Scope Extent"
        except Exception:
            pass

    center = _project_to_view_plane(
        plan_view,
        _get_view_plane_origin(plan_view)
    )
    default_span = _mm_to_internal(10000.0)
    return center, default_span, default_span, u"QC Plan View Origin"


def _get_preview_spacing(width, height):
    minimum_spacing = _mm_to_internal(MIN_PREVIEW_SPACING_MM)
    maximum_spacing = _mm_to_internal(MAX_PREVIEW_SPACING_MM)
    default_spacing = _mm_to_internal(DEFAULT_PREVIEW_SPACING_MM)
    usable_spans = [value for value in (width, height) if value > 0.0]
    if not usable_spans:
        return default_spacing

    spacing = min(usable_spans) * 0.15
    return max(minimum_spacing, min(spacing, maximum_spacing))


def _get_plan_preview_locations(plan_view, analysis_scope_result):
    center, width, height, source = _get_plan_drawing_frame(
        plan_view,
        analysis_scope_result
    )
    right, up = _get_view_basis(plan_view)
    spacing = _get_preview_spacing(width, height)
    return (
        [
            _offset_point(center, right, up, -spacing, spacing * 0.35),
            center,
            _offset_point(center, right, up, spacing, -spacing * 0.35)
        ],
        source,
        (center, width, height)
    )


def _get_element_bounding_box_center(element):
    try:
        bounding_box = element.get_BoundingBox(None)
        if bounding_box is not None:
            return _get_box_center(bounding_box)
    except Exception:
        pass
    return None


def _get_wall_midpoint(plan_view, wall):
    try:
        location_curve = wall.Location.Curve
        if location_curve is not None:
            return _project_to_view_plane(
                plan_view,
                location_curve.Evaluate(0.5, True)
            )
    except Exception:
        pass

    center = _get_element_bounding_box_center(wall)
    if center is None:
        return None
    try:
        return _project_to_view_plane(plan_view, center)
    except Exception:
        return None


def _get_selected_wall_locations(plan_view, selected_walls):
    locations = []
    for wall in selected_walls[:3]:
        location = _get_wall_midpoint(plan_view, wall)
        if location is not None:
            locations.append(location)

    if len(locations) == 1:
        right, up = _get_view_basis(plan_view)
        offset = _mm_to_internal(MIN_PREVIEW_SPACING_MM)
        locations.append(
            _offset_point(locations[0], right, up, offset, offset * 0.25)
        )
    return locations[:3]


def _create_line_override(color, line_weight):
    override = OverrideGraphicSettings()
    override.SetProjectionLineColor(color)
    override.SetProjectionLineWeight(line_weight)
    override.SetProjectionLinePatternId(LinePatternElement.GetSolidPatternId())
    override.SetCutLineColor(color)
    override.SetCutLineWeight(line_weight)
    override.SetCutLinePatternId(LinePatternElement.GetSolidPatternId())
    return override


def _apply_line_override(view, element, color, line_weight):
    override = _create_line_override(color, line_weight)
    try:
        view.SetElementOverrides(element.Id, override)
    finally:
        try:
            override.Dispose()
        except Exception:
            pass


def _collect_revisions(doc):
    return (
        FilteredElementCollector(doc)
        .OfClass(Revision)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def _find_or_create_preview_revision(doc):
    revisions = _collect_revisions(doc)
    existing_descriptions = set()
    exact_revision = None
    for revision in revisions:
        try:
            description = _to_text(revision.Description)
            existing_descriptions.add(description)
            if description == PREVIEW_REVISION_DESCRIPTION:
                exact_revision = revision
                if not revision.Issued:
                    return revision, False, u""
        except Exception:
            pass

    description = PREVIEW_REVISION_DESCRIPTION
    if exact_revision is not None:
        suffix = 2
        while description in existing_descriptions:
            description = u"{0} {1}".format(
                PREVIEW_REVISION_DESCRIPTION,
                suffix
            )
            suffix += 1

    subtransaction = SubTransaction(doc)
    subtransaction_started = False
    try:
        subtransaction.Start()
        subtransaction_started = True
        revision = Revision.Create(doc)
        revision.Description = description
        status = subtransaction.Commit()
        subtransaction_started = False
        if status != TransactionStatus.Committed:
            return None, False, u"Revision setup ended with status: {0}".format(
                status
            )
        warning = u""
        if description != PREVIEW_REVISION_DESCRIPTION:
            warning = (
                u"The existing Scan QC preview Revision was issued; an unissued "
                u"preview Revision was created as: {0}."
            ).format(description)
        return revision, True, warning
    except Exception as ex:
        if subtransaction_started:
            try:
                subtransaction.RollBack()
            except Exception:
                pass
        return None, False, u"Preview Revision setup failed: {0}".format(
            _to_text(ex)
        )


def _get_text_type_name(text_type):
    try:
        name_parameter = text_type.get_Parameter(
            BuiltInParameter.SYMBOL_NAME_PARAM
        )
        if name_parameter is not None:
            name_value = name_parameter.AsString()
            if name_value:
                return _to_text(name_value)
    except Exception:
        pass

    try:
        return _to_text(text_type.Name)
    except Exception:
        return u""


def _find_preview_text_type(doc):
    text_types = (
        FilteredElementCollector(doc)
        .OfClass(TextNoteType)
        .WhereElementIsElementType()
        .ToElements()
    )
    for text_type in text_types:
        if _get_text_type_name(text_type) == PREVIEW_ID_TEXT_TYPE_NAME:
            return text_type
    return None


def _set_opaque_text_background(doc, text_type):
    subtransaction = SubTransaction(doc)
    subtransaction_started = False
    try:
        background_parameter = text_type.get_Parameter(
            BuiltInParameter.TEXT_BACKGROUND
        )
        if background_parameter is None or background_parameter.IsReadOnly:
            return False, u"Preview TextNote background parameter was not editable."

        subtransaction.Start()
        subtransaction_started = True
        background_parameter.Set(int(TextElementBackground.TBGR_OPAQUE))
        status = subtransaction.Commit()
        subtransaction_started = False
        if status != TransactionStatus.Committed:
            return False, u"Opaque TextNote setup ended with status: {0}".format(
                status
            )
        return True, u""
    except Exception as ex:
        if subtransaction_started:
            try:
                subtransaction.RollBack()
            except Exception:
                pass
        return False, u"Opaque TextNote background could not be applied: {0}".format(
            _to_text(ex)
        )


def _set_preview_text_size(doc, text_type):
    subtransaction = SubTransaction(doc)
    subtransaction_started = False
    try:
        size_parameter = text_type.get_Parameter(BuiltInParameter.TEXT_SIZE)
        if size_parameter is None or size_parameter.IsReadOnly:
            return False, u"Preview ID TextNote size parameter was not editable."

        subtransaction.Start()
        subtransaction_started = True
        size_parameter.Set(_mm_to_internal(PREVIEW_ID_TEXT_SIZE_MM))
        status = subtransaction.Commit()
        subtransaction_started = False
        if status != TransactionStatus.Committed:
            return False, u"Preview ID text size setup ended with status: {0}".format(
                status
            )
        return True, u""
    except Exception as ex:
        if subtransaction_started:
            try:
                subtransaction.RollBack()
            except Exception:
                pass
        return False, u"Preview ID text size could not be applied: {0}".format(
            _to_text(ex)
        )


def _get_or_create_preview_text_type(doc):
    default_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)
    text_type = _find_preview_text_type(doc)
    warning = u""
    if text_type is None:
        default_type = doc.GetElement(default_type_id)
        if default_type is None:
            return default_type_id, False, u"Default TextNote type was unavailable."

        subtransaction = SubTransaction(doc)
        subtransaction_started = False
        try:
            subtransaction.Start()
            subtransaction_started = True
            text_type = default_type.Duplicate(PREVIEW_ID_TEXT_TYPE_NAME)
            status = subtransaction.Commit()
            subtransaction_started = False
            if status != TransactionStatus.Committed:
                text_type = None
                warning = u"Preview TextNote type setup did not commit."
        except Exception as ex:
            if subtransaction_started:
                try:
                    subtransaction.RollBack()
                except Exception:
                    pass
            text_type = _find_preview_text_type(doc)
            if text_type is None:
                warning = (
                    u"Preview TextNote type could not be created; the default type "
                    u"will be used: {0}"
                ).format(_to_text(ex))

    if text_type is None:
        return default_type_id, False, warning

    opaque_applied, opaque_warning = _set_opaque_text_background(doc, text_type)
    if opaque_warning:
        warning = u"{0} {1}".format(warning, opaque_warning).strip()
    text_size_applied, text_size_warning = _set_preview_text_size(doc, text_type)
    if text_size_warning:
        warning = u"{0} {1}".format(warning, text_size_warning).strip()
    return text_type.Id, opaque_applied, warning


def create_text_label(
    doc,
    plan_view,
    position,
    label_text,
    text_type_id,
    alignment
):
    """Create one opaque-capable view-specific preview label."""
    options = TextNoteOptions(text_type_id)
    try:
        options.HorizontalAlignment = alignment
        return TextNote.Create(
            doc,
            plan_view.Id,
            position,
            label_text,
            options
        )
    finally:
        try:
            options.Dispose()
        except Exception:
            pass


def _create_revision_cloud_outline(doc, plan_view, revision, center):
    right, up = _get_view_basis(plan_view)
    size = _mm_to_internal(REVISION_CLOUD_HALF_SIZE_MM)
    upper_left = _offset_point(center, right, up, -size, size)
    upper_right = _offset_point(center, right, up, size, size)
    lower_right = _offset_point(center, right, up, size, -size)
    lower_left = _offset_point(center, right, up, -size, -size)
    curves = List[Curve]()
    for start_point, end_point in (
        (upper_left, upper_right),
        (upper_right, lower_right),
        (lower_right, lower_left),
        (lower_left, upper_left)
    ):
        curves.Add(Line.CreateBound(start_point, end_point))
    return RevisionCloud.Create(doc, plan_view, revision.Id, curves)


def _try_create_revision_cloud(
    doc,
    plan_view,
    center,
    revision,
    color,
    line_weight
):
    if revision is None:
        return None, u"Preview Revision was unavailable."

    subtransaction = SubTransaction(doc)
    subtransaction_started = False
    try:
        subtransaction.Start()
        subtransaction_started = True
        revision_cloud = _create_revision_cloud_outline(
            doc,
            plan_view,
            revision,
            center
        )
        _apply_line_override(plan_view, revision_cloud, color, line_weight)
        status = subtransaction.Commit()
        subtransaction_started = False
        if status != TransactionStatus.Committed:
            return None, u"Revision Cloud setup ended with status: {0}".format(
                status
            )
        return revision_cloud, u""
    except Exception as ex:
        if subtransaction_started:
            try:
                subtransaction.RollBack()
            except Exception:
                pass
        return None, u"Revision Cloud creation failed: {0}".format(_to_text(ex))


def _get_view_bounding_box_center(element, view):
    try:
        bounding_box = element.get_BoundingBox(view)
        if bounding_box is not None:
            return _project_to_view_plane(view, _get_box_center(bounding_box))
    except Exception:
        pass
    return None


def _center_text_note_on_point(doc, plan_view, text_note, target_center):
    """Move a TextNote until its visible bounding-box center matches the target."""
    right, up = _get_view_basis(plan_view)
    tolerance = _mm_to_internal(0.5)
    for unused_iteration in range(2):
        doc.Regenerate()
        text_center = _get_view_bounding_box_center(text_note, plan_view)
        if text_center is None:
            return False, u"Center ID TextNote bounding box was unavailable."

        delta = target_center.Subtract(text_center)
        right_offset = delta.DotProduct(right)
        up_offset = delta.DotProduct(up)
        if abs(right_offset) <= tolerance and abs(up_offset) <= tolerance:
            return True, u""

        text_note.Coord = _offset_point(
            text_note.Coord,
            right,
            up,
            right_offset,
            up_offset
        )

    doc.Regenerate()
    final_center = _get_view_bounding_box_center(text_note, plan_view)
    if final_center is None:
        return False, u"Center ID TextNote final bounding box was unavailable."
    final_delta = target_center.Subtract(final_center)
    if (
        abs(final_delta.DotProduct(right)) <= tolerance
        and abs(final_delta.DotProduct(up)) <= tolerance
    ):
        return True, u""
    return False, u"Center ID TextNote could not be centered within 0.5mm."


def _try_create_center_id(
    doc,
    plan_view,
    center,
    text_type_id,
    preview_id,
    revision_cloud
):
    subtransaction = SubTransaction(doc)
    subtransaction_started = False
    try:
        subtransaction.Start()
        subtransaction_started = True
        doc.Regenerate()
        cloud_center = _get_view_bounding_box_center(
            revision_cloud,
            plan_view
        ) if revision_cloud is not None else None
        positioning_warning = u""
        if cloud_center is None:
            cloud_center = center
            positioning_warning = (
                u"Revision Cloud bounding box was unavailable; the requested "
                u"marker center was used for ID {0}."
            ).format(preview_id)
        text_note = create_text_label(
            doc,
            plan_view,
            cloud_center,
            preview_id,
            text_type_id,
            HorizontalTextAlignment.Center
        )
        _centered, centering_warning = _center_text_note_on_point(
            doc,
            plan_view,
            text_note,
            cloud_center
        )
        if centering_warning:
            positioning_warning = u"{0} {1}".format(
                positioning_warning,
                centering_warning
            ).strip()
        status = subtransaction.Commit()
        subtransaction_started = False
        if status != TransactionStatus.Committed:
            return None, u"", u"TextNote setup ended with status: {0}".format(
                status
            )
        return text_note, positioning_warning, u""
    except Exception as ex:
        if subtransaction_started:
            try:
                subtransaction.RollBack()
            except Exception:
                pass
        return None, u"", u"Center ID TextNote creation failed: {0}".format(
            _to_text(ex)
        )


def _create_marker_callout(
    doc,
    plan_view,
    center,
    revision,
    text_type_id,
    preview_id,
    label_text,
    severity,
    color,
    line_weight
):
    revision_cloud, cloud_error = _try_create_revision_cloud(
        doc,
        plan_view,
        center,
        revision,
        color,
        line_weight
    )
    text_note, text_warning, text_error = _try_create_center_id(
        doc,
        plan_view,
        center,
        text_type_id,
        preview_id,
        revision_cloud
    )
    return {
        "preview_id": preview_id,
        "label": label_text,
        "severity": severity,
        "revision_cloud": revision_cloud,
        "text_note": text_note,
        "cloud_error": cloud_error,
        "text_warning": text_warning,
        "text_error": text_error
    }


def create_review_marker(
    doc,
    plan_view,
    center,
    revision,
    text_type_id,
    preview_id
):
    """Create an isolated Review cloud with a centered alphabet ID."""
    return _create_marker_callout(
        doc,
        plan_view,
        center,
        revision,
        text_type_id,
        preview_id,
        REVIEW_LABEL,
        u"REVIEW",
        REVIEW_COLOR,
        REVIEW_LINE_WEIGHT
    )


def create_critical_marker(
    doc,
    plan_view,
    center,
    revision,
    text_type_id,
    preview_id
):
    """Create an isolated Critical cloud with a centered alphabet ID."""
    return _create_marker_callout(
        doc,
        plan_view,
        center,
        revision,
        text_type_id,
        preview_id,
        CRITICAL_LABEL,
        u"CRITICAL",
        CRITICAL_COLOR,
        CRITICAL_LINE_WEIGHT
    )


def _create_plan_preview_result(requested):
    return {
        "requested": requested,
        "attempted": False,
        "created": False,
        "preview_only": True,
        "target_view_name": u"",
        "placement_source": u"Unavailable",
        "revision_description": PREVIEW_REVISION_DESCRIPTION,
        "revision_created": False,
        "opaque_text_background": False,
        "revision_cloud_count": 0,
        "text_note_count": 0,
        "leader_count": 0,
        "textnote_label_count": 0,
        "textnote_leader_count": 0,
        "preview_id_mappings": [],
        "preview_created": False,
        "preview_warnings": [],
        "preview_errors": [],
        "3d_preview_status": u"Disabled",
        "review_count": 0,
        "critical_count": 0,
        "revision_cloud_failures": [],
        "text_note_failures": [],
        "leader_failures": [],
        "warnings": [],
        "error": u""
    }


def _message_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [item for item in value if item]
    return [value]


def _finalize_plan_preview_result(result):
    result["textnote_label_count"] = result.get("text_note_count", 0)
    result["textnote_leader_count"] = result.get("leader_count", 0)
    result["preview_created"] = bool(result.get("created", False))
    result["preview_warnings"] = _message_list(result.get("warnings"))

    errors = []
    errors.extend(_message_list(result.get("error")))
    errors.extend(_message_list(result.get("revision_cloud_failures")))
    errors.extend(_message_list(result.get("text_note_failures")))
    errors.extend(_message_list(result.get("leader_failures")))
    result["preview_errors"] = errors
    result["3d_preview_status"] = u"Disabled"
    if not isinstance(result.get("preview_id_mappings"), list):
        result["preview_id_mappings"] = []
    return result


def create_plan_marker_preview(
    doc,
    plan_view,
    selected_walls,
    analysis_scope_result,
    requested=True
):
    """Create Revision Clouds with centered alphabet IDs in a generated QC Plan View."""
    result = _create_plan_preview_result(requested)
    if not requested:
        return _finalize_plan_preview_result(result)
    if plan_view is None:
        result["error"] = u"Generated Scan QC Plan View was not available."
        return _finalize_plan_preview_result(result)

    try:
        result["target_view_name"] = _to_text(plan_view.Name)
        if plan_view.IsTemplate or plan_view.ViewType not in PLAN_VIEW_TYPES:
            result["error"] = u"Plan preview requires a generated plan-type view."
            return _finalize_plan_preview_result(result)
        if not result["target_view_name"].startswith(u"SCAN_QC_PLAN_"):
            result["error"] = (
                u"Plan preview was blocked because the target is not a generated "
                u"SCAN_QC_PLAN_* view."
            )
            return _finalize_plan_preview_result(result)
    except Exception as ex:
        result["error"] = u"Plan preview target validation failed: {0}".format(
            _to_text(ex)
        )
        return _finalize_plan_preview_result(result)

    try:
        fallback_locations, placement_source, drawing_frame = (
            _get_plan_preview_locations(plan_view, analysis_scope_result)
        )
        is_selected_walls = (
            analysis_scope_result.get("analysis_scope")
            == ANALYSIS_SCOPE_SELECTED_WALLS
        )
        locations = []
        if is_selected_walls and selected_walls:
            locations = _get_selected_wall_locations(plan_view, selected_walls)
            result["placement_source"] = u"Selected Wall Midpoints"
        if not locations:
            locations = fallback_locations
            result["placement_source"] = placement_source
            if is_selected_walls:
                result["warnings"].append(
                    u"No usable selected Wall midpoint was available; Plan preview "
                    u"callouts used the generated QC Plan View drawing area."
                )
    except Exception as ex:
        result["error"] = u"Plan preview placement failed: {0}".format(_to_text(ex))
        return _finalize_plan_preview_result(result)

    transaction = Transaction(doc, "Create Scan QC Plan Revision Cloud Preview")
    transaction_started = False
    revision_cloud_count = 0
    text_note_count = 0
    leader_count = 0
    review_count = 0
    critical_count = 0
    preview_id_mappings = []

    try:
        transaction.Start()
        transaction_started = True
        result["attempted"] = True
        revision, revision_created, revision_warning = (
            _find_or_create_preview_revision(doc)
        )
        result["revision_created"] = revision_created
        if revision_warning:
            result["warnings"].append(revision_warning)
        text_type_id, opaque_applied, text_warning = (
            _get_or_create_preview_text_type(doc)
        )
        result["opaque_text_background"] = opaque_applied
        if text_warning:
            result["warnings"].append(text_warning)

        for index, location in enumerate(locations[:3]):
            preview_id = u"ABC"[index]
            if index % 2 == 0:
                marker_result = create_review_marker(
                    doc,
                    plan_view,
                    location,
                    revision,
                    text_type_id,
                    preview_id
                )
                review_count += 1
            else:
                marker_result = create_critical_marker(
                    doc,
                    plan_view,
                    location,
                    revision,
                    text_type_id,
                    preview_id
                )
                critical_count += 1
            revision_cloud = marker_result["revision_cloud"]
            text_note = marker_result["text_note"]
            if revision_cloud is not None:
                revision_cloud_count += 1
            elif marker_result["cloud_error"]:
                result["revision_cloud_failures"].append(
                    marker_result["cloud_error"]
                )
            if text_note is not None:
                text_note_count += 1
            elif marker_result["text_error"]:
                result["text_note_failures"].append(
                    marker_result["text_error"]
                )
            if marker_result.get("text_warning"):
                result["warnings"].append(
                    u"ID {0} positioning: {1}".format(
                        preview_id,
                        marker_result.get("text_warning")
                    )
                )
            preview_id_mappings.append({
                "id": marker_result.get("preview_id", preview_id),
                "label": marker_result.get("label", u""),
                "severity": marker_result.get("severity", u""),
                "revision_cloud_created": revision_cloud is not None,
                "id_textnote_created": text_note is not None,
                "id_centered_on_cloud": (
                    text_note is not None
                    and not marker_result.get("text_warning")
                )
            })

        status = transaction.Commit()
        transaction_started = False
        if status != TransactionStatus.Committed:
            result["error"] = u"Plan preview transaction ended with status: {0}".format(
                status
            )
            return _finalize_plan_preview_result(result)

        result["revision_cloud_count"] = revision_cloud_count
        result["text_note_count"] = text_note_count
        result["leader_count"] = leader_count
        result["review_count"] = review_count
        result["critical_count"] = critical_count
        result["preview_id_mappings"] = preview_id_mappings
        result["created"] = revision_cloud_count > 0 or text_note_count > 0
        if not result["created"]:
            result["error"] = u"No 2D preview annotation elements were created."
    except Exception as ex:
        result["error"] = _to_text(ex)
        if transaction_started:
            try:
                transaction.RollBack()
            except Exception:
                pass

    return _finalize_plan_preview_result(result)


def create_3d_marker_preview(
    view3d,
    requested=True
):
    """Return an explicit disabled result without modifying the generated 3D View."""
    target_view_name = u""
    if view3d is not None:
        try:
            target_view_name = _to_text(view3d.Name)
        except Exception:
            pass
    return {
        "requested": requested,
        "attempted": False,
        "created": False,
        "disabled": True,
        "preview_only": True,
        "target_view_name": target_view_name,
        "display_mode": u"Disabled",
        "preview_count": 0,
        "review_count": 0,
        "critical_count": 0,
        "warnings": [],
        "error": u"",
        "revision_cloud_count": 0,
        "textnote_label_count": 0,
        "textnote_leader_count": 0,
        "preview_id_mappings": [],
        "preview_created": False,
        "preview_warnings": [],
        "preview_errors": [],
        "3d_preview_status": u"Disabled"
    }


def build_marker_preview_result(plan_preview=None, view3d_preview=None):
    """Return a stable reporting payload even when preview creation partly fails."""
    if not hasattr(plan_preview, "get"):
        plan_preview = _create_plan_preview_result(False)
    if not hasattr(view3d_preview, "get"):
        view3d_preview = create_3d_marker_preview(None, requested=False)
    plan_preview = _finalize_plan_preview_result(plan_preview)

    warnings = []
    warnings.extend(_message_list(plan_preview.get("preview_warnings")))
    warnings.extend(_message_list(view3d_preview.get("preview_warnings")))
    warnings.extend(_message_list(view3d_preview.get("warnings")))

    errors = []
    errors.extend(_message_list(plan_preview.get("preview_errors")))
    errors.extend(_message_list(view3d_preview.get("preview_errors")))
    errors.extend(_message_list(view3d_preview.get("error")))

    return {
        "preview_only": True,
        "plan": plan_preview,
        "view3d": view3d_preview,
        "revision_cloud_count": plan_preview.get("revision_cloud_count", 0),
        "textnote_label_count": plan_preview.get("textnote_label_count", 0),
        "textnote_leader_count": plan_preview.get("textnote_leader_count", 0),
        "preview_id_mappings": plan_preview.get("preview_id_mappings", []),
        "preview_created": bool(plan_preview.get("preview_created", False)),
        "preview_warnings": warnings,
        "preview_errors": errors,
        "3d_preview_status": view3d_preview.get(
            "3d_preview_status",
            view3d_preview.get("display_mode", u"Disabled")
        )
    }
