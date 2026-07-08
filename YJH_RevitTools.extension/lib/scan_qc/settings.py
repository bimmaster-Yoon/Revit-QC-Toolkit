# -*- coding: utf-8 -*-

import copy
import io
import json
import os


DEFAULT_SETTINGS = {
    "tolerance_mm": {
        "ok_max": 10,
        "review_max": 30,
        "critical_min": 30
    },
    "view_templates": {
        "plan": u"VT_SCAN_QC_PLAN",
        "view3d": u"VT_SCAN_QC_3D"
    },
    "base_views": {
        "view3d": u"SCAN_QC_3D_BASE"
    },
    "standards": {
        "standards_rvt": u"resources/standards/ScanQC_Standards.rvt"
    },
    "point_cloud": {
        "selection_mode": u"user_select",
        "remember_last_selection": True
    },
    "view_creation": {
        "section_box_margin_mm": 1000
    },
    "deviation": {
        "point_search_margin_mm": 300,
        "point_sample_spacing_mm": 50,
        "max_points_per_wall": 5000,
        "max_active_level_walls": 20
    },
    "output": {
        "create_plan_view": True,
        "create_3d_view": True,
        "create_pdf_report": True,
        "export_csv": False,
        "create_preview_callouts_when_no_deviation_data": True
    }
}


try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)

try:
    NUMBER_TYPES = (int, long, float)
except NameError:
    NUMBER_TYPES = (int, float)


def get_extension_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
    )


def get_default_config_path():
    return os.path.join(get_extension_dir(), "config", "scan_qc_defaults.json")


def _merge_dict(target, source):
    if not isinstance(source, dict):
        return target

    for key, value in source.items():
        if isinstance(target.get(key), dict):
            if isinstance(value, dict):
                _merge_dict(target[key], value)
        else:
            target[key] = value

    return target


def load_scan_qc_settings(config_path=None):
    """Load Scan QC settings, falling back safely for missing or invalid JSON."""
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    resolved_config_path = config_path or get_default_config_path()

    try:
        with io.open(resolved_config_path, "r", encoding="utf-8-sig") as config_file:
            loaded_settings = json.load(config_file)

        if isinstance(loaded_settings, dict):
            _merge_dict(settings, loaded_settings)
    except (IOError, OSError, ValueError, TypeError):
        pass

    return settings


def _get_section(settings, section_name):
    merged_settings = copy.deepcopy(DEFAULT_SETTINGS)
    if isinstance(settings, dict):
        _merge_dict(merged_settings, settings)
    return merged_settings[section_name]


def _safe_number(value, fallback):
    if isinstance(value, bool) or not isinstance(value, NUMBER_TYPES):
        return fallback
    return value


def _safe_text(value, fallback):
    if not isinstance(value, STRING_TYPES) or not value.strip():
        return fallback
    return value.strip()


def _safe_bool(value, fallback):
    if not isinstance(value, bool):
        return fallback
    return value


def get_tolerance_mm(settings):
    tolerance = _get_section(settings, "tolerance_mm")
    defaults = DEFAULT_SETTINGS["tolerance_mm"]
    return {
        "ok_max": _safe_number(tolerance.get("ok_max"), defaults["ok_max"]),
        "review_max": _safe_number(
            tolerance.get("review_max"),
            defaults["review_max"]
        ),
        "critical_min": _safe_number(
            tolerance.get("critical_min"),
            defaults["critical_min"]
        )
    }


def get_view_template_names(settings):
    templates = _get_section(settings, "view_templates")
    defaults = DEFAULT_SETTINGS["view_templates"]
    return {
        "plan": _safe_text(templates.get("plan"), defaults["plan"]),
        "view3d": _safe_text(templates.get("view3d"), defaults["view3d"])
    }


def get_base_view_names(settings):
    base_views = _get_section(settings, "base_views")
    defaults = DEFAULT_SETTINGS["base_views"]
    return {
        "view3d": _safe_text(base_views.get("view3d"), defaults["view3d"])
    }


def get_standards_relative_path(settings):
    standards = _get_section(settings, "standards")
    default_path = DEFAULT_SETTINGS["standards"]["standards_rvt"]
    relative_path = _safe_text(standards.get("standards_rvt"), default_path)

    if os.path.isabs(relative_path):
        return default_path

    normalized_path = os.path.normpath(relative_path)
    if normalized_path == os.pardir or normalized_path.startswith(os.pardir + os.sep):
        return default_path

    return normalized_path


def get_standards_path(settings):
    """Resolve the portable standards path relative to the extension root."""
    return os.path.abspath(
        os.path.join(get_extension_dir(), get_standards_relative_path(settings))
    )


def get_point_cloud_options(settings):
    point_cloud = _get_section(settings, "point_cloud")
    defaults = DEFAULT_SETTINGS["point_cloud"]
    return {
        "selection_mode": _safe_text(
            point_cloud.get("selection_mode"),
            defaults["selection_mode"]
        ),
        "remember_last_selection": _safe_bool(
            point_cloud.get("remember_last_selection"),
            defaults["remember_last_selection"]
        )
    }


def get_view_creation_options(settings):
    view_creation = _get_section(settings, "view_creation")
    defaults = DEFAULT_SETTINGS["view_creation"]
    section_box_margin_mm = _safe_number(
        view_creation.get("section_box_margin_mm"),
        defaults["section_box_margin_mm"]
    )
    if section_box_margin_mm < 0:
        section_box_margin_mm = defaults["section_box_margin_mm"]

    return {
        "section_box_margin_mm": section_box_margin_mm
    }


def _safe_positive_number(value, fallback):
    safe_value = _safe_number(value, fallback)
    if safe_value <= 0:
        return fallback
    return safe_value


def _safe_positive_int(value, fallback):
    safe_value = _safe_positive_number(value, fallback)
    try:
        return int(safe_value)
    except (TypeError, ValueError):
        return fallback


def get_deviation_options(settings):
    deviation = _get_section(settings, "deviation")
    defaults = DEFAULT_SETTINGS["deviation"]
    return {
        "point_search_margin_mm": _safe_positive_number(
            deviation.get("point_search_margin_mm"),
            defaults["point_search_margin_mm"]
        ),
        "point_sample_spacing_mm": _safe_positive_number(
            deviation.get("point_sample_spacing_mm"),
            defaults["point_sample_spacing_mm"]
        ),
        "max_points_per_wall": _safe_positive_int(
            deviation.get("max_points_per_wall"),
            defaults["max_points_per_wall"]
        ),
        "max_active_level_walls": _safe_positive_int(
            deviation.get("max_active_level_walls"),
            defaults["max_active_level_walls"]
        )
    }


def get_output_options(settings):
    output = _get_section(settings, "output")
    defaults = DEFAULT_SETTINGS["output"]
    return {
        "create_plan_view": _safe_bool(
            output.get("create_plan_view"),
            defaults["create_plan_view"]
        ),
        "create_3d_view": _safe_bool(
            output.get("create_3d_view"),
            defaults["create_3d_view"]
        ),
        "create_pdf_report": _safe_bool(
            output.get("create_pdf_report"),
            defaults["create_pdf_report"]
        ),
        "export_csv": _safe_bool(
            output.get("export_csv"),
            defaults["export_csv"]
        ),
        "create_preview_callouts_when_no_deviation_data": _safe_bool(
            output.get("create_preview_callouts_when_no_deviation_data"),
            defaults["create_preview_callouts_when_no_deviation_data"]
        )
    }
