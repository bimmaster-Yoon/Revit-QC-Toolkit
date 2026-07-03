# -*- coding: utf-8 -*-

import copy
import io
import json
import os


DEFAULT_CONFIG = {
    "version": "v2.5 - Styled XLSX Report",
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

    if export_overrides:
        normalized["export"] = export_overrides

    return normalized


def load_config(config_path, local_config_path=None):
    """default JSON 로드 후 선택적 local JSON override를 재귀 병합한다."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    loaded_config = _load_json_object(config_path, "Default QC")

    _merge_dict(config, loaded_config)

    if local_config_path is None:
        local_config_path = get_local_config_path(config_path)

    if os.path.isfile(local_config_path):
        local_config = _load_json_object(local_config_path, "Local QC")
        _merge_dict(config, _normalize_local_config(local_config))

    return config


def save_local_external_python_path(local_config_path, python_path):
    """local config의 다른 값을 보존하고 개인 Python 경로만 저장한다."""
    local_config = {}

    if os.path.isfile(local_config_path):
        local_config = _load_json_object(local_config_path, "Local QC")

    local_config["external_python_path"] = python_path or ""
    config_folder = os.path.dirname(local_config_path)

    if not os.path.isdir(config_folder):
        os.makedirs(config_folder)

    serialized_config = json.dumps(
        local_config,
        ensure_ascii=True,
        indent=2,
        sort_keys=True
    )
    if not isinstance(serialized_config, type(u"")):
        serialized_config = serialized_config.decode("utf-8")

    with io.open(local_config_path, "w", encoding="utf-8") as config_file:
        config_file.write(serialized_config)
        config_file.write(u"\n")

    return local_config_path
