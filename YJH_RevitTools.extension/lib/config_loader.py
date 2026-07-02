# -*- coding: utf-8 -*-

import copy
import io
import json
import os


DEFAULT_CONFIG = {
    "version": "v2.3 - QC Toolkit Buttons",
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
        "file_prefix": "Revit_QC_v2.3"
    }
}


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


def load_config(config_path):
    """UTF-8 JSON 설정을 읽고 누락된 항목은 안전한 기본값으로 채운다."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not os.path.isfile(config_path):
        raise IOError(
            "QC config file was not found: {0}".format(config_path)
        )

    with io.open(config_path, "r", encoding="utf-8-sig") as config_file:
        loaded_config = json.load(config_file)

    if not isinstance(loaded_config, dict):
        raise ValueError("QC config root must be a JSON object.")

    _merge_dict(config, loaded_config)
    return config
