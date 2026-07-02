# -*- coding: utf-8 -*-

from collectors import is_empty, to_text


def html_escape(value):
    return (
        to_text(value)
        .replace(u"&", u"&amp;")
        .replace(u"<", u"&lt;")
        .replace(u">", u"&gt;")
        .replace(u'"', u"&quot;")
    )


def render_report(
    output,
    version,
    summary_data,
    checked_parameter_elements,
    qc_status,
    issue_group_count,
    display_issue_group_rows,
    key_issue_rows,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error
):
    compact_summary_rows = [
        [u"Checked Sheets", summary_data["checked_sheets"]],
        [u"Checked Views", summary_data["checked_views"]],
        [u"Checked Parameter Elements", checked_parameter_elements],
        [u"Total Review Items", summary_data["total_issues"]],
        [u"Issue Groups", issue_group_count],
        [u"QC Status", qc_status],
        [u"Export", u"Full CSV / Summary CSV"]
    ]

    output.print_html(
        u"""
        <div style="font-family:Segoe UI, Arial, sans-serif;">
            <h2>Revit QC Report Automation</h2>
            <div style="color:#616161; margin-bottom:10px;">{0}</div>
        </div>
        """.format(html_escape(version))
    )

    output.print_html_table(
        table_data=compact_summary_rows,
        title="Compact Summary",
        columns=["Summary", "Value"],
        column_widths=["260px", "220px"],
        table_width_style="width:500px",
        row_striping=True
    )

    if display_issue_group_rows:
        output.print_html_table(
            table_data=display_issue_group_rows,
            title="Review Group Summary",
            columns=[
                "Category",
                "Item Type",
                "QC Item",
                "Severity",
                "Count",
                "Sample Items"
            ],
            column_widths=["100px", "160px", "180px", "80px", "70px", "360px"],
            table_width_style="width:100%",
            row_striping=True
        )
    else:
        output.print_html(
            u"""
            <div style="margin-top:12px; padding:10px; border:1px solid #81c784;
                background-color:#e8f5e9; color:#2e7d32; font-weight:bold;">
                <strong>Review Group Summary</strong><br>
                QC 항목이 발견되지 않았습니다.
            </div>
            """
        )

    if key_issue_rows:
        output.print_html_table(
            table_data=key_issue_rows,
            title="Review Item Samples",
            columns=[
                "Category",
                "Item Type",
                "Item Name",
                "Severity",
                "QC Item",
                "Issue Message"
            ],
            column_widths=["100px", "150px", "280px", "80px", "160px", "220px"],
            table_width_style="width:100%",
            row_striping=True
        )
    else:
        output.print_html(
            u"""
            <div style="margin-top:12px; color:#616161;">
                <strong>Review Item Samples</strong><br>
                표시할 핵심 Issue가 없습니다.
            </div>
            """
        )

    full_csv_result = _get_export_result(saved_full_csv_path, full_csv_error)
    summary_csv_result = _get_export_result(
        saved_summary_csv_path,
        summary_csv_error
    )

    output.print_html(
        u"""
        <div style="margin-top:12px; padding:10px; border-left:4px solid #ef6c00;
            background-color:#fff8e1;">
            <strong>CSV Export Path</strong><br>
            <strong>Full CSV:</strong> {0}<br>
            <strong>Summary CSV:</strong> {1}<br>
            <span style="color:#616161;">
                CSV 저장 실패가 발생해도 QC 검사는 완료됩니다.
            </span>
        </div>
        """.format(full_csv_result, summary_csv_result)
    )


def render_quick_report(
    output,
    version,
    summary_data,
    qc_status,
    issue_group_count,
    saved_summary_csv_path,
    summary_csv_error
):
    """Sheet + View Quick QC용 간결한 Summary를 출력한다."""
    compact_summary_rows = [
        [u"Checked Sheets", summary_data["checked_sheets"]],
        [u"Checked Views", summary_data["checked_views"]],
        [u"Total Review Items", summary_data["total_issues"]],
        [u"Issue Groups", issue_group_count],
        [u"QC Status", qc_status],
        [u"Export", u"Summary CSV"]
    ]

    output.print_html(
        u"""
        <div style="font-family:Segoe UI, Arial, sans-serif;">
            <h2>Revit Quick QC</h2>
            <div style="color:#616161; margin-bottom:10px;">{0}</div>
            <div style="color:#ef6c00; margin-bottom:10px;">
                Sheet QC + View QC / Parameter QC 제외
            </div>
        </div>
        """.format(html_escape(version))
    )

    output.print_html_table(
        table_data=compact_summary_rows,
        title="Quick QC Compact Summary",
        columns=["Summary", "Value"],
        column_widths=["260px", "220px"],
        table_width_style="width:500px",
        row_striping=True
    )

    summary_csv_result = _get_export_result(
        saved_summary_csv_path,
        summary_csv_error
    )

    output.print_html(
        u"""
        <div style="margin-top:12px; padding:10px; border-left:4px solid #ef6c00;
            background-color:#fff8e1;">
            <strong>Summary CSV:</strong> {0}<br>
            <span style="color:#616161;">
                Quick QC는 Parameter QC와 Full CSV를 생성하지 않습니다.
            </span>
        </div>
        """.format(summary_csv_result)
    )


def _get_export_result(saved_path, error_message):
    if not is_empty(saved_path):
        return html_escape(saved_path)

    return u"저장 실패: {0}".format(html_escape(error_message))
