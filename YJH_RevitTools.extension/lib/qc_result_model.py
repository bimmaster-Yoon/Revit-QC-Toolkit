# -*- coding: utf-8 -*-

from __future__ import print_function

import re


try:
    text_type = unicode
except NameError:
    text_type = str


SEVERITY_RANK = {u"High": 3, u"Medium": 2, u"Low": 1}


def to_text(value):
    if value is None:
        return u""
    if isinstance(value, text_type):
        return value
    try:
        return text_type(value)
    except Exception:
        return u"{0}".format(value)


def to_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def sanitize_display_text(value):
    text = to_text(value)
    text = re.sub(u"\\s*\\[Id:\\s*\\d+\\]", u"", text, flags=re.IGNORECASE)
    text = re.sub(u"[A-Za-z]:\\\\[^,;]+", u"", text)
    return text.strip(u" ,;")


def _build_group(group_row, sample_limit):
    count = to_int(group_row[4])
    displayed_count = min(count, sample_limit)
    remaining_count = max(0, count - displayed_count)
    sample_display = sanitize_display_text(group_row[5])
    if remaining_count > 0:
        sample_display = u"{0} + {1} more".format(
            sample_display,
            remaining_count
        )
    return {
        "category": to_text(group_row[0]),
        "item_type": to_text(group_row[1]),
        "qc_item": to_text(group_row[2]),
        "severity": to_text(group_row[3]),
        "count": count,
        "sample_display": sample_display,
        "remaining_count": remaining_count
    }


def _build_representative_item(key_row):
    return {
        "category": to_text(key_row[0]),
        "item_type": to_text(key_row[1]),
        "item_name": sanitize_display_text(key_row[2]),
        "severity": to_text(key_row[3]),
        "qc_item": to_text(key_row[4]),
        "message": to_text(key_row[5])
    }


def validate_result_model(result_model):
    kpi = result_model["kpi"]
    issue_counts = result_model["issue_count_by_qc"]
    severity_counts = result_model["severity_counts"]
    total_by_qc = sum(issue_counts.values())
    total_by_severity = sum(severity_counts.values())
    total_findings = kpi["total_findings"]

    if total_by_qc != total_findings:
        raise ValueError(
            u"QC category count mismatch: {0} != {1}".format(
                total_by_qc,
                total_findings
            )
        )
    if total_by_severity != total_findings:
        raise ValueError(
            u"Severity count mismatch: {0} != {1}".format(
                total_by_severity,
                total_findings
            )
        )
    if kpi["critical_items"] != severity_counts["high"]:
        raise ValueError(u"Critical Items must equal High severity count.")
    return True


def build_qc_result_model(
    summary_data,
    qc_status,
    issue_group_rows,
    key_issue_rows,
    metadata=None,
    top_group_limit=5,
    representative_limit=3,
    group_sample_limit=3
):
    checked_sheets = to_int(summary_data.get("checked_sheets", 0))
    checked_views = to_int(summary_data.get("checked_views", 0))
    checked_parameter_elements = to_int(
        (metadata or {}).get("checked_parameter_elements", 0)
    )
    total_findings = to_int(summary_data.get("total_issues", 0))

    review_groups = [
        _build_group(row, group_sample_limit)
        for row in issue_group_rows
    ]
    review_groups = sorted(
        review_groups,
        key=lambda item: (
            -SEVERITY_RANK.get(item["severity"], 0),
            -item["count"],
            item["category"],
            item["item_type"],
            item["qc_item"]
        )
    )
    representative_items = [
        _build_representative_item(row)
        for row in key_issue_rows[:representative_limit]
    ]

    result_model = {
        "schema_version": "1.0",
        "metadata": dict(metadata or {}),
        "qc_status": to_text(qc_status),
        "kpi": {
            "checked_items": (
                checked_sheets
                + checked_views
                + checked_parameter_elements
            ),
            "checked_sheets": checked_sheets,
            "checked_views": checked_views,
            "checked_parameter_elements": checked_parameter_elements,
            "total_findings": total_findings,
            "critical_items": to_int(summary_data.get("high_count", 0))
        },
        "issue_count_by_qc": {
            "sheet_qc": to_int(summary_data.get("sheet_issues", 0)),
            "view_qc": to_int(summary_data.get("view_issues", 0)),
            "parameter_qc": to_int(summary_data.get("parameter_issues", 0))
        },
        "severity_counts": {
            "high": to_int(summary_data.get("high_count", 0)),
            "medium": to_int(summary_data.get("medium_count", 0)),
            "low": to_int(summary_data.get("low_count", 0))
        },
        "review_group_count": len(review_groups),
        "review_groups": review_groups,
        "top_review_groups": review_groups[:top_group_limit],
        "representative_items": representative_items,
        "representative_remaining": max(
            0,
            total_findings - len(representative_items)
        ),
        "summary_data": dict(summary_data)
    }
    validate_result_model(result_model)
    return result_model
