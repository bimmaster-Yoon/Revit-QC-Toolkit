# -*- coding: utf-8 -*-

from collectors import to_text


def add_issue(issue_rows, category, item_type, item_name, severity, qc_item):
    issue_rows.append(
        [category, item_type, item_name, severity, qc_item]
    )


def get_severity_rank(severity):
    severity_ranks = {u"High": 3, u"Medium": 2, u"Low": 1}
    return severity_ranks.get(to_text(severity), 0)


def truncate_display_text(value, max_length):
    text = to_text(value)

    if len(text) <= max_length:
        return text

    if max_length <= 3:
        return text[:max_length]

    return u"{0}...".format(text[:max_length - 3])


def get_issue_group_fields(issue_row):
    category = issue_row[0]
    issue_detail = to_text(issue_row[4])
    qc_item = issue_detail
    issue_message = issue_detail

    if category == u"Sheet QC":
        if issue_detail == u"Sheet Number 누락":
            qc_item = u"Sheet Number"
            issue_message = u"누락"
        elif issue_detail == u"Sheet Name 누락":
            qc_item = u"Sheet Name"
            issue_message = u"누락"
        elif issue_detail == u"배치된 View 없음":
            qc_item = u"Placed Views"

    elif category == u"View QC":
        if issue_detail == u"View Name 누락":
            qc_item = u"View Name"
            issue_message = u"누락"
        elif issue_detail.startswith(u"임시 키워드 포함:"):
            qc_item = u"View Name"
            issue_message = u"임시 키워드 포함"
        elif issue_detail.startswith(u"View Scale 비정상:"):
            qc_item = u"View Scale"
            issue_message = u"비정상"
        elif issue_detail.startswith(u"View Scale 확인 불가:"):
            qc_item = u"View Scale"
            issue_message = u"확인 불가"
        elif issue_detail == u"View Template 미적용":
            qc_item = u"View Template"
            issue_message = u"미적용"
        elif issue_detail.startswith(u"View Template 확인 불가:"):
            qc_item = u"View Template"
            issue_message = u"확인 불가"
        elif issue_detail == u"Sheet에 배치되지 않은 도면용 View":
            qc_item = u"Sheet Placement"

    elif category == u"Parameter QC":
        missing_prefix = u"Shared Parameter 없음: "
        empty_marker = u" 값 비어 있음"

        if issue_detail.startswith(missing_prefix):
            qc_item = issue_detail[len(missing_prefix):]
            issue_message = u"Shared Parameter 없음"
        else:
            marker_index = issue_detail.find(empty_marker)

            if marker_index > 0:
                qc_item = issue_detail[:marker_index]
                issue_message = issue_detail[marker_index + 1:]

    return qc_item, issue_message


def build_issue_group_rows(
    issue_rows,
    shorten_samples=False,
    sample_max_length=35,
    sample_limit=5
):
    grouped_issues = {}

    for row in issue_rows:
        qc_item, issue_message = get_issue_group_fields(row)
        group_key = (row[0], row[1], qc_item, issue_message)

        if group_key not in grouped_issues:
            grouped_issues[group_key] = {
                "severity": row[3],
                "count": 0,
                "sample_items": []
            }

        group_data = grouped_issues[group_key]
        group_data["count"] += 1

        if get_severity_rank(row[3]) > get_severity_rank(group_data["severity"]):
            group_data["severity"] = row[3]

        sample_item = row[2]

        if shorten_samples:
            sample_item = truncate_display_text(sample_item, sample_max_length)

        if (
            sample_item not in group_data["sample_items"]
            and len(group_data["sample_items"]) < sample_limit
        ):
            group_data["sample_items"].append(sample_item)

    group_rows = []

    for group_key in grouped_issues:
        group_data = grouped_issues[group_key]
        group_rows.append(
            [
                group_key[0],
                group_key[1],
                group_key[2],
                group_data["severity"],
                group_data["count"],
                u", ".join(group_data["sample_items"])
            ]
        )

    return sorted(
        group_rows,
        key=lambda row: (
            -get_severity_rank(row[3]),
            to_text(row[0]),
            to_text(row[1]),
            to_text(row[2]),
            to_text(row[5])
        )
    )


def contains_temporary_keyword(value, temporary_keywords):
    lower_value = to_text(value).lower()

    for keyword in temporary_keywords:
        if to_text(keyword).lower() in lower_value:
            return True

    return False


def build_key_issue_rows(
    issue_rows,
    temporary_keywords,
    key_issue_limit=8,
    item_max_length=35
):
    candidates = []
    parameter_group_keys = set()

    for index, row in enumerate(issue_rows):
        category = row[0]
        issue_detail = row[4]
        qc_item, issue_message = get_issue_group_fields(row)

        if (
            category == u"View QC"
            and issue_detail == u"Sheet에 배치되지 않은 도면용 View"
        ):
            continue

        if (
            category == u"View QC"
            and contains_temporary_keyword(row[2], temporary_keywords)
            and issue_detail.startswith(u"임시 키워드 포함:")
        ):
            priority = 0
        elif category == u"Sheet QC" and issue_detail == u"배치된 View 없음":
            priority = 1
        elif category == u"Parameter QC":
            parameter_group_key = (category, row[1], qc_item, issue_message)

            if parameter_group_key in parameter_group_keys:
                continue

            parameter_group_keys.add(parameter_group_key)
            priority = 2
        elif row[3] == u"High":
            priority = 3
        elif row[3] == u"Medium":
            priority = 4
        else:
            priority = 5

        candidates.append((priority, index, row))

    candidates = sorted(candidates, key=lambda item: (item[0], item[1]))
    key_issue_rows = []

    for candidate in candidates[:key_issue_limit]:
        row = candidate[2]
        qc_item, issue_message = get_issue_group_fields(row)
        key_issue_rows.append(
            [
                row[0],
                row[1],
                truncate_display_text(row[2], item_max_length),
                row[3],
                qc_item,
                issue_message
            ]
        )

    return key_issue_rows


def build_summary_data(issue_rows, checked_sheet_count, checked_view_count):
    summary_data = {
        "checked_sheets": checked_sheet_count,
        "checked_views": checked_view_count,
        "sheet_issues": 0,
        "view_issues": 0,
        "parameter_issues": 0,
        "total_issues": len(issue_rows),
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0
    }

    for row in issue_rows:
        if row[0] == u"Sheet QC":
            summary_data["sheet_issues"] += 1
        elif row[0] == u"View QC":
            summary_data["view_issues"] += 1
        elif row[0] == u"Parameter QC":
            summary_data["parameter_issues"] += 1

        if row[3] == u"High":
            summary_data["high_count"] += 1
        elif row[3] == u"Medium":
            summary_data["medium_count"] += 1
        elif row[3] == u"Low":
            summary_data["low_count"] += 1

    return summary_data


def get_qc_status(summary_data):
    if summary_data["high_count"] > 0:
        return u"Review Required"

    if summary_data["medium_count"] > 0 or summary_data["low_count"] > 0:
        return u"Check Recommended"

    return u"No Issues Found"
