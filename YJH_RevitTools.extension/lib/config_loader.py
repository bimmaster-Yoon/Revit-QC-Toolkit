# -*- coding: utf-8 -*-

import copy
import datetime
import io
import json
import os


DEFAULT_CONFIG = {
    "version": "v2.10.0",
    "preset_name": "Default QC",
    "preset_description": "General Sheet, View, and Parameter QC preset.",
    "sheet_qc": {
        "require_sheet_number": True,
        "require_sheet_name": True,
        "require_placed_view": True
    },
    "view_qc": {
        "supported_view_types": [
            "FloorPlan",
            "CeilingPlan",
            "Elevation",
            "Section",
            "Detail",
            "DraftingView",
            "ThreeD"
        ],
        "template_required_view_types": [
            "FloorPlan",
            "CeilingPlan",
            "Elevation",
            "Section"
        ],
        "sheet_required_view_types": [
            "FloorPlan",
            "CeilingPlan",
            "Elevation",
            "Section",
            "Detail",
            "DraftingView"
        ],
        "temporary_keywords": [
            u"Copy",
            u"복사",
            u"Temp",
            u"임시",
            u"Working",
            u"TEST"
        ]
    },
    "parameter_qc": {
        "rules": []
    },
    "display": {
        "group_sample_max_length": 25,
        "group_sample_limit": 3,
        "key_issue_limit": 8,
        "key_item_max_length": 35
    },
    "export": {
        "file_prefix": "Revit_QC",
        "external_python_path": "",
        "debug_keep_temp_json": False
    }
}

LOCAL_CONFIG_FILE = "qc_config_local.json"


def _merge_dict(target, source):
    """JSON 설정을 기본 설정 위에 재귀적으로 병합한다."""
    for key in source:
        value = source[key]

        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            _merge_dict(target[key], value)
        else:
            target[key] = value


def get_local_config_path(default_config_path):
    return os.path.join(
        os.path.dirname(default_config_path),
        LOCAL_CONFIG_FILE
    )


def _load_json_object(config_path, config_label):
    if not os.path.isfile(config_path):
        raise IOError(
            "{0} config file was not found: {1}".format(
                config_label,
                config_path
            )
        )

    with io.open(config_path, "r", encoding="utf-8-sig") as config_file:
        loaded_config = json.load(config_file)

    if not isinstance(loaded_config, dict):
        raise ValueError(
            "{0} config root must be a JSON object.".format(config_label)
        )

    return loaded_config


def _normalize_local_config(local_config):
    """간단한 local 전용 키를 export 섹션 override로 변환한다."""
    normalized = copy.deepcopy(local_config)
    export_overrides = normalized.get("export", {})

    if not isinstance(export_overrides, dict):
        raise ValueError("Local config 'export' must be a JSON object.")

    for key in ["external_python_path", "debug_keep_temp_json"]:
        if key in normalized:
            export_overrides[key] = normalized.pop(key)

    normalized.pop("active_config", None)

    if export_overrides:
        normalized["export"] = export_overrides

    return normalized


def _write_json_object(config_path, config_object):
    serialized_config = json.dumps(
        config_object,
        ensure_ascii=True,
        indent=2,
        sort_keys=True
    )
    if not isinstance(serialized_config, type(u"")):
        serialized_config = serialized_config.decode("utf-8")

    config_folder = os.path.dirname(config_path)
    if not os.path.isdir(config_folder):
        os.makedirs(config_folder)

    with io.open(config_path, "w", encoding="utf-8") as config_file:
        config_file.write(serialized_config)
        config_file.write(u"\n")


def _get_preset_display_name(config_object, file_name):
    preset_name = config_object.get("preset_name", u"")
    if preset_name:
        return preset_name

    stem = os.path.splitext(file_name)[0]
    stem = stem.replace("qc_config_", "").replace("_", " ")
    return stem.title() + u" QC"


def list_qc_presets(config_folder):
    presets = []

    if not os.path.isdir(config_folder):
        return presets

    for file_name in sorted(os.listdir(config_folder)):
        lower_name = file_name.lower()
        if not lower_name.startswith("qc_config_"):
            continue
        if not lower_name.endswith(".json"):
            continue
        if lower_name == LOCAL_CONFIG_FILE.lower():
            continue

        preset_path = os.path.join(config_folder, file_name)
        try:
            preset_config = _load_json_object(preset_path, "QC Preset")
            presets.append(
                {
                    "file_name": file_name,
                    "path": preset_path,
                    "preset_name": _get_preset_display_name(
                        preset_config,
                        file_name
                    ),
                    "preset_description": preset_config.get(
                        "preset_description",
                        u""
                    ),
                    "config": preset_config,
                    "error": u""
                }
            )
        except Exception as ex:
            presets.append(
                {
                    "file_name": file_name,
                    "path": preset_path,
                    "preset_name": file_name,
                    "preset_description": u"Invalid preset file.",
                    "config": {},
                    "error": u"{0}".format(ex)
                }
            )

    return presets


def load_config(config_path, local_config_path=None):
    """default, active preset, local machine override 순서로 설정을 병합한다."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    default_config = _load_json_object(config_path, "Default QC")
    _merge_dict(config, default_config)

    config_folder = os.path.dirname(config_path)
    default_file_name = os.path.basename(config_path)
    active_file_name = default_file_name
    active_config_path = config_path
    config_warning = u""
    local_config = {}

    if local_config_path is None:
        local_config_path = get_local_config_path(config_path)

    if os.path.isfile(local_config_path):
        local_config = _load_json_object(local_config_path, "Local QC")
        requested_active = local_config.get("active_config", u"")
        requested_file_name = os.path.basename(requested_active)

        if requested_active and requested_file_name != requested_active:
            config_warning = (
                u"Invalid active_config path. Default QC is being used."
            )
        elif requested_file_name:
            requested_path = os.path.join(config_folder, requested_file_name)
            if os.path.isfile(requested_path):
                try:
                    preset_config = _load_json_object(
                        requested_path,
                        "Active QC Preset"
                    )
                    _merge_dict(config, preset_config)
                    active_file_name = requested_file_name
                    active_config_path = requested_path
                except Exception as ex:
                    config_warning = (
                        u"Active preset could not be loaded. Default QC is being "
                        u"used: {0}".format(ex)
                    )
            else:
                config_warning = (
                    u"Active preset was not found. Default QC is being used: {0}"
                    .format(requested_file_name)
                )

        _merge_dict(config, _normalize_local_config(local_config))

    config["_config_meta"] = {
        "default_config_path": config_path,
        "local_config_path": local_config_path,
        "active_config_path": active_config_path,
        "active_config_file": active_file_name,
        "preset_name": _get_preset_display_name(config, active_file_name),
        "preset_description": config.get("preset_description", u""),
        "warning": config_warning
    }
    return config


def save_local_external_python_path(local_config_path, python_path):
    """local config의 다른 값을 보존하고 개인 Python 경로만 저장한다."""
    local_config = {}

    if os.path.isfile(local_config_path):
        local_config = _load_json_object(local_config_path, "Local QC")

    local_config["external_python_path"] = python_path or ""
    _write_json_object(local_config_path, local_config)

    return local_config_path


def save_local_active_config(local_config_path, active_config_file):
    local_config = {}

    if os.path.isfile(local_config_path):
        local_config = _load_json_object(local_config_path, "Local QC")

    local_config["active_config"] = os.path.basename(active_config_file or "")
    _write_json_object(local_config_path, local_config)
    return local_config_path


def duplicate_qc_preset(source_path, config_folder):
    source_config = _load_json_object(source_path, "Source QC Preset")
    source_name = source_config.get("preset_name", u"Custom QC")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = "qc_config_custom_{0}.json".format(timestamp)
    destination_path = os.path.join(config_folder, file_name)
    source_config["preset_name"] = u"{0} Copy".format(source_name)
    source_config["preset_description"] = (
        u"Custom preset duplicated from {0}.".format(source_name)
    )
    _write_json_object(destination_path, source_config)
    return destination_path


def calculate_rule_summary(config):
    sheet_config = config.get("sheet_qc", {})
    view_config = config.get("view_qc", {})
    parameter_rules = config.get("parameter_qc", {}).get("rules", [])
    sheet_rule_count = 0
    view_rule_count = 0

    for key in sheet_config:
        if sheet_config.get(key):
            sheet_rule_count += 1

    for key in view_config:
        if view_config.get(key):
            view_rule_count += 1

    required_parameters = set()
    for rule in parameter_rules:
        parameter_name = rule.get("parameter_name", u"")
        if parameter_name:
            required_parameters.add(parameter_name)

    return {
        "sheet_rules": sheet_rule_count,
        "view_rules": view_rule_count,
        "parameter_rules": len(parameter_rules),
        "required_parameters": len(required_parameters)
    }
