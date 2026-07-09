# -*- coding: utf-8 -*-

import copy
import io
import json
import os


DEFAULT_SETTINGS = {
    "tolerance_mm": {
        "ok_max": 30,
        "review_max": 80,
        "critical_min": 80
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
        "max_process_walls": 50,
        "top_n_callouts": 7,
        "max_active_level_walls": 20
    },
    "target_wall_filter": {
        "interior_walls_only": False,
        "new_construction_only": False,
        "exclude_exterior_walls": False,
        "only_scan_qc_target_yes": False
    },
    "report": {
        "paper_size": u"A3 Landscape",
        "output_folder": u"reports/scan_qc",
        "last_pdf_folder": u"",
        "export_image": False
    },
    "output": {
        "create_plan_view": True,
        "create_3d_view": True,
        "create_pdf_report": False,
        "export_csv": False,
        "create_preview_callouts_when_no_deviation_data": False
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
        "max_process_walls": _safe_positive_int(
            deviation.get("max_process_walls"),
            defaults["max_process_walls"]
        ),
        "top_n_callouts": _safe_positive_int(
            deviation.get("top_n_callouts"),
            defaults["top_n_callouts"]
        ),
        "max_active_level_walls": _safe_positive_int(
            deviation.get("max_active_level_walls"),
            defaults["max_active_level_walls"]
        )
    }


def get_target_wall_filter_defaults(settings):
    target_wall_filter = _get_section(settings, "target_wall_filter")
    defaults = DEFAULT_SETTINGS["target_wall_filter"]
    return {
        "interior_walls_only": _safe_bool(
            target_wall_filter.get("interior_walls_only"),
            defaults["interior_walls_only"]
        ),
        "new_construction_only": _safe_bool(
            target_wall_filter.get("new_construction_only"),
            defaults["new_construction_only"]
        ),
        "exclude_exterior_walls": _safe_bool(
            target_wall_filter.get("exclude_exterior_walls"),
            defaults["exclude_exterior_walls"]
        ),
        "only_scan_qc_target_yes": _safe_bool(
            target_wall_filter.get("only_scan_qc_target_yes"),
            defaults["only_scan_qc_target_yes"]
        )
    }


def get_report_options(settings):
    report = _get_section(settings, "report")
    defaults = DEFAULT_SETTINGS["report"]
    paper_size = _safe_text(
        report.get("paper_size"),
        defaults["paper_size"]
    )
    if paper_size not in (u"A3 Landscape", u"A2 Landscape"):
        paper_size = defaults["paper_size"]

    output_folder = _safe_text(
        report.get("output_folder"),
        defaults["output_folder"]
    )

    if os.path.isabs(output_folder):
        output_folder = defaults["output_folder"]

    normalized_output_folder = os.path.normpath(output_folder)
    if (
        normalized_output_folder == os.pardir
        or normalized_output_folder.startswith(os.pardir + os.sep)
    ):
        normalized_output_folder = defaults["output_folder"]

    return {
        "paper_size": paper_size,
        "output_folder": normalized_output_folder,
        "last_pdf_folder": _safe_text(
            report.get("last_pdf_folder"),
            defaults["last_pdf_folder"]
        ),
        "export_image": _safe_bool(
            report.get("export_image"),
            defaults["export_image"]
        )
    }


def get_report_output_folder(settings):
    report_options = get_report_options(settings)
    return os.path.abspath(
        os.path.join(get_extension_dir(), report_options["output_folder"])
    )


def get_report_state_path(settings):
    return os.path.join(
        get_report_output_folder(settings),
        "scan_qc_report_state.json"
    )


def load_report_state(settings):
    state_path = get_report_state_path(settings)
    try:
        with io.open(state_path, "r", encoding="utf-8-sig") as state_file:
            state = json.load(state_file)
        if isinstance(state, dict):
            return state
    except Exception:
        pass
    return {
        "last_pdf_folder": get_report_options(settings).get("last_pdf_folder", u"")
    }


def save_report_state(settings, state):
    if not isinstance(state, dict):
        return False, u"Report state was not a dictionary."

    state_path = get_report_state_path(settings)
    try:
        state_folder = os.path.dirname(state_path)
        if not os.path.isdir(state_folder):
            os.makedirs(state_folder)
        with io.open(state_path, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file, ensure_ascii=False, indent=2)
        return True, u""
    except Exception as ex:
        try:
            return False, unicode(ex)
        except NameError:
            return False, str(ex)


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
