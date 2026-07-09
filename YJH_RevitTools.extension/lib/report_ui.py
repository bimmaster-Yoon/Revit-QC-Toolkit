# -*- coding: utf-8 -*-

from collectors import is_empty, to_text


PORTFOLIO_OUTPUT_STYLE = u"""
body {
    color: #263645;
    font-family: "Segoe UI", "Malgun Gothic", Arial, sans-serif;
}
h1, h2, h3, h4 {
    color: #263645;
}
table {
    color: #263645;
}
table, th, td {
    border-bottom-color: #D6DDE3;
}
th {
    background-color: #536777;
    border-bottom: 1px solid #4A5B6A;
    color: #FFFFFF;
}
tr:nth-child(odd) {
    background-color: #F4F6F8;
}
"""


def apply_portfolio_output_style(output):
    output.add_style(PORTFOLIO_OUTPUT_STYLE)


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
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    export_options
):
    apply_portfolio_output_style(output)

    compact_summary_rows = [
        [u"Checked Sheets", summary_data["checked_sheets"]],
        [u"Checked Views", summary_data["checked_views"]],
        [u"Checked Parameter Elements", checked_parameter_elements],
        [u"Total Review Items", summary_data["total_issues"]],
        [u"Issue Groups", issue_group_count],
        [u"QC Status", qc_status],
        [
            u"Export",
            u" / ".join(export_options["selected_formats"]) or u"None"
        ]
    ]

    output.print_html(
        u"""
        <div style="font-family:Segoe UI, Arial, sans-serif;">
            <h2 style="color:#263645;">Revit QC Report Automation</h2>
            <div style="color:#5F6F7D; margin-bottom:10px;">{0}</div>
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
            <div style="margin-top:12px; padding:10px; border:1px solid #CFE3D4;
                background-color:#F2F8F3; color:#1E7A3A; font-weight:bold;">
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
            <div style="margin-top:12px; color:#5F6F7D;">
                <strong>Review Item Samples</strong><br>
                표시할 핵심 Issue가 없습니다.
            </div>
            """
        )

    render_export_results(
        output,
        export_options,
        saved_full_csv_path,
        full_csv_error,
        saved_summary_csv_path,
        summary_csv_error,
        saved_styled_xlsx_path,
        styled_xlsx_error
    )


def render_quick_report(
    output,
    version,
    summary_data,
    qc_status,
    issue_group_count,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    export_options
):
    """Sheet + View QC Lite용 간결한 Summary를 출력한다."""
    apply_portfolio_output_style(output)

    compact_summary_rows = [
        [u"Checked Sheets", summary_data["checked_sheets"]],
        [u"Checked Views", summary_data["checked_views"]],
        [u"Total Review Items", summary_data["total_issues"]],
        [u"Issue Groups", issue_group_count],
        [u"QC Status", qc_status],
        [
            u"Export",
            u" / ".join(export_options["selected_formats"]) or u"None"
        ]
    ]

    output.print_html(
        u"""
        <div style="font-family:Segoe UI, Arial, sans-serif;">
            <h2 style="color:#263645;">Revit QC Lite</h2>
            <div style="color:#5F6F7D; margin-bottom:10px;">{0}</div>
            <div style="color:#5F6F7D; margin-bottom:10px;">
                Sheet QC + View QC / Parameter QC 제외
            </div>
        </div>
        """.format(html_escape(version))
    )

    output.print_html_table(
        table_data=compact_summary_rows,
        title="QC Lite Compact Summary",
        columns=["Summary", "Value"],
        column_widths=["260px", "220px"],
        table_width_style="width:500px",
        row_striping=True
    )

    render_export_results(
        output,
        export_options,
        saved_full_csv_path,
        full_csv_error,
        saved_summary_csv_path,
        summary_csv_error,
        saved_styled_xlsx_path,
        styled_xlsx_error
    )


def render_export_results(
    output,
    export_options,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error
):
    if not export_options["selected_formats"]:
        output.print_html(
            u"""
            <div style="margin-top:12px; padding:10px; border:1px solid #D6DDE3;
                border-left:3px solid #536777; background-color:#F4F6F8;
                color:#263645;">
                <strong>Export: None</strong><br>
                No file export selected. QC results are shown in this window only.<br>
                <span style="color:#5F6F7D;">Last saved report was not changed.</span>
            </div>
            """
        )
        return

    full_csv_result = _get_export_result(
        saved_full_csv_path,
        full_csv_error,
        export_options["full_csv"]
    )
    summary_csv_result = _get_export_result(
        saved_summary_csv_path,
        summary_csv_error,
        export_options["summary_csv"]
    )
    styled_xlsx_result = _get_export_result(
        saved_styled_xlsx_path,
        styled_xlsx_error,
        export_options["styled_xlsx"]
    )

    output.print_html(
        u"""
        <div style="margin-top:12px; padding:10px; border:1px solid #D6DDE3;
            border-left:3px solid #536777; background-color:#F4F6F8;
            color:#263645;">
            <strong>Export Results</strong><br>
            <strong>Folder:</strong> {0}<br>
            <strong>Selected:</strong> {1}<br>
            <strong>Full CSV:</strong> {2}<br>
            <strong>Summary CSV:</strong> {3}<br>
            <strong>Styled XLSX Report:</strong> {4}<br>
            <span style="color:#5F6F7D;">
                Export 실패가 발생해도 QC 검사는 완료됩니다.
            </span>
        </div>
        """.format(
            html_escape(export_options["folder"]),
            html_escape(u" / ".join(export_options["selected_formats"])),
            full_csv_result,
            summary_csv_result,
            styled_xlsx_result
        )
    )

    if export_options.get("folder_history_error"):
        output.print_html(
            u"<div style='color:#C85F1A; background:#FFF3E8; padding:6px;'>마지막 저장 폴더 기록 실패: {0}</div>".format(
                html_escape(export_options["folder_history_error"])
            )
        )


def _get_export_result(saved_path, error_message, is_selected):
    if not is_selected:
        return u"선택하지 않음"

    if not is_empty(saved_path):
        return html_escape(saved_path)

    return u"Warning: {0}".format(html_escape(error_message))
