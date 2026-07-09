# -*- coding: utf-8 -*-

try:
    from Autodesk.Revit.DB import BuiltInParameter, ElementId, StorageType
except Exception:
    BuiltInParameter = None
    ElementId = None
    StorageType = None


SCAN_QC_TARGET_PARAMETER_NAME = u"SCAN_QC_TARGET"


def _to_text(value):
    if value is None:
        return u""
    try:
        return unicode(value)
    except NameError:
        return str(value)


def _safe_bool(value, fallback=False):
    if isinstance(value, bool):
        return value
    return fallback


def get_default_target_wall_filter_options(settings=None):
    defaults = {
        "interior_walls_only": False,
        "new_construction_only": False,
        "exclude_exterior_walls": False,
        "only_scan_qc_target_yes": False
    }
    if not isinstance(settings, dict):
        return defaults

    configured = settings.get("target_wall_filter")
    if not isinstance(configured, dict):
        return defaults

    return {
        "interior_walls_only": _safe_bool(
            configured.get("interior_walls_only"),
            defaults["interior_walls_only"]
        ),
        "new_construction_only": _safe_bool(
            configured.get("new_construction_only"),
            defaults["new_construction_only"]
        ),
        "exclude_exterior_walls": _safe_bool(
            configured.get("exclude_exterior_walls"),
            defaults["exclude_exterior_walls"]
        ),
        "only_scan_qc_target_yes": _safe_bool(
            configured.get("only_scan_qc_target_yes"),
            defaults["only_scan_qc_target_yes"]
        )
    }


def get_target_wall_filter_options(selected_options=None, settings=None):
    defaults = get_default_target_wall_filter_options(settings)
    if not isinstance(selected_options, dict):
        return defaults

    selected = selected_options.get("target_wall_filter")
    if not isinstance(selected, dict):
        return defaults

    return {
        "interior_walls_only": _safe_bool(
            selected.get("interior_walls_only"),
            defaults["interior_walls_only"]
        ),
        "new_construction_only": _safe_bool(
            selected.get("new_construction_only"),
            defaults["new_construction_only"]
        ),
        "exclude_exterior_walls": _safe_bool(
            selected.get("exclude_exterior_walls"),
            defaults["exclude_exterior_walls"]
        ),
        "only_scan_qc_target_yes": _safe_bool(
            selected.get("only_scan_qc_target_yes"),
            defaults["only_scan_qc_target_yes"]
        )
    }


def _get_parameter_value_text(parameter):
    if parameter is None:
        return u""
    try:
        value_text = parameter.AsValueString()
        if value_text:
            return _to_text(value_text)
    except Exception:
        pass
    try:
        return _to_text(parameter.AsString())
    except Exception:
        pass
    try:
        return _to_text(parameter.AsInteger())
    except Exception:
        return u""


def _parameter_is_yes(parameter):
    if parameter is None:
        return False

    try:
        if StorageType is not None and parameter.StorageType == StorageType.Integer:
            return parameter.AsInteger() == 1
    except Exception:
        pass

    value_text = _get_parameter_value_text(parameter).strip().lower()
    return value_text in (
        u"yes",
        u"y",
        u"true",
        u"1",
        u"예",
        u"네",
        u"사용",
        u"대상",
        u"checked"
    )


def _get_wall_type(wall):
    try:
        return wall.WallType
    except Exception:
        pass
    try:
        return wall.Document.GetElement(wall.GetTypeId())
    except Exception:
        return None


def _get_wall_function_parameter(wall):
    wall_type = _get_wall_type(wall)
    if wall_type is None:
        return None

    if BuiltInParameter is not None:
        try:
            return wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
        except Exception:
            pass

    try:
        return wall_type.LookupParameter(u"Function")
    except Exception:
        return None


def _is_exterior_wall(wall):
    parameter = _get_wall_function_parameter(wall)
    value_text = _get_parameter_value_text(parameter).strip().lower()
    if value_text:
        if u"exterior" in value_text or u"외부" in value_text or u"외벽" in value_text:
            return True
        if value_text in (u"1",):
            return True

    try:
        return parameter.AsInteger() == 1
    except Exception:
        return False


def _get_invalid_element_id_value():
    if ElementId is None:
        return None
    try:
        return ElementId.InvalidElementId
    except Exception:
        pass
    try:
        return ElementId(-1)
    except Exception:
        return None


def _element_id_value(element_id):
    if element_id is None:
        return None
    try:
        return element_id.IntegerValue
    except Exception:
        pass
    try:
        return element_id.Value
    except Exception:
        pass
    try:
        return int(element_id)
    except Exception:
        return None


def _is_valid_element_id(element_id):
    if element_id is None:
        return False
    invalid_id = _get_invalid_element_id_value()
    if invalid_id is not None:
        try:
            return _element_id_value(element_id) != _element_id_value(invalid_id)
        except Exception:
            pass
    value = _element_id_value(element_id)
    return value is not None and value >= 0


def _get_phase_id(wall, built_in_parameter_name):
    if BuiltInParameter is None:
        return None
    try:
        built_in_parameter = getattr(BuiltInParameter, built_in_parameter_name)
        parameter = wall.get_Parameter(built_in_parameter)
        if parameter is None:
            return None
        return parameter.AsElementId()
    except Exception:
        return None


def _get_latest_phase_id(doc):
    try:
        phases = doc.Phases
        if phases is None or phases.Size <= 0:
            return None
        return phases.get_Item(phases.Size - 1).Id
    except Exception:
        pass

    try:
        phases = list(doc.Phases)
        if phases:
            return phases[-1].Id
    except Exception:
        pass

    return None


def _is_existing_or_demolished_wall(wall, doc):
    demolished_phase_id = _get_phase_id(wall, "PHASE_DEMOLISHED")
    if _is_valid_element_id(demolished_phase_id):
        return True

    created_phase_id = _get_phase_id(wall, "PHASE_CREATED")
    latest_phase_id = _get_latest_phase_id(doc)
    if not _is_valid_element_id(created_phase_id) or latest_phase_id is None:
        return False

    try:
        return _element_id_value(created_phase_id) != _element_id_value(latest_phase_id)
    except Exception:
        return False


def _has_scan_qc_target_yes(wall):
    try:
        parameter = wall.LookupParameter(SCAN_QC_TARGET_PARAMETER_NAME)
    except Exception:
        parameter = None
    return _parameter_is_yes(parameter)


def _build_filter_summary(options):
    enabled_labels = []
    if options.get("interior_walls_only"):
        enabled_labels.append(u"Interior(Type Function)")
    if options.get("new_construction_only"):
        enabled_labels.append(u"New(Phase)")
    if options.get("exclude_exterior_walls"):
        enabled_labels.append(u"No Exterior(Type Function)")
    if options.get("only_scan_qc_target_yes"):
        enabled_labels.append(u"SCAN_QC_TARGET=Yes")
    if not enabled_labels:
        return u"None"
    return u", ".join(enabled_labels)


def apply_target_wall_filters(walls, selected_options=None, settings=None, doc=None):
    options = get_target_wall_filter_options(selected_options, settings)
    result = {
        "target_wall_filter_options": options,
        "target_wall_filter_summary": _build_filter_summary(options),
        "unfiltered_target_wall_count": len(walls or []),
        "filtered_target_wall_count": 0,
        "excluded_exterior_count": 0,
        "excluded_existing_count": 0,
        "excluded_demolished_count": 0,
        "excluded_by_parameter_count": 0,
        "warnings": []
    }

    filtered_walls = []
    for wall in walls or []:
        if (
            options.get("exclude_exterior_walls")
            or options.get("interior_walls_only")
        ) and _is_exterior_wall(wall):
            result["excluded_exterior_count"] += 1
            continue

        if options.get("new_construction_only") and _is_existing_or_demolished_wall(
            wall,
            doc
        ):
            result["excluded_existing_count"] += 1
            continue

        if options.get("only_scan_qc_target_yes") and not _has_scan_qc_target_yes(
            wall
        ):
            result["excluded_by_parameter_count"] += 1
            continue

        filtered_walls.append(wall)

    result["filtered_target_wall_count"] = len(filtered_walls)
    return filtered_walls, result
