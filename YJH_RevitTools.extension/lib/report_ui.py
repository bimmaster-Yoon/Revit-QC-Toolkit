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
    key_issue_rows,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    saved_compact_html_path,
    compact_html_error,
    saved_compact_pdf_path,
    compact_pdf_error,
    export_options
):
    """사용자가 요청한 경우에만 QC Lite 상세 Output을 렌더링한다."""
    apply_portfolio_output_style(output)

    compact_summary_rows = [
        [u"Checked Sheets", summary_data["checked_sheets"]],
        [u"Checked Views", summary_data["checked_views"]],
        [u"Parameter QC Findings", summary_data["parameter_issues"]],
        [u"Total Review Items", summary_data["total_issues"]],
        [u"Issue Groups", issue_group_count],
        [u"QC Status", qc_status],
        [
            u"Export",
            u" / ".join(export_options["selected_formats"]) or u"None"
        ]
    ]
    top_issue_rows = key_issue_rows[:5]
    export_html = _build_export_results_html(
        export_options,
        saved_full_csv_path,
        full_csv_error,
        saved_summary_csv_path,
        summary_csv_error,
        saved_styled_xlsx_path,
        styled_xlsx_error,
        saved_compact_html_path,
        compact_html_error,
        saved_compact_pdf_path,
        compact_pdf_error
    )
    top_issues_html = (
        _build_output_table(
            [u"Severity", u"Category", u"Item", u"QC Item"],
            [[row[3], row[0], row[2], row[4]] for row in top_issue_rows]
        )
        if top_issue_rows
        else u"<div class='qc-empty'>표시할 주요 Issue가 없습니다.</div>"
    )
    detailed_html = (
        _build_output_table(
            [
                u"Category", u"Item Type", u"Item Name",
                u"Severity", u"QC Item", u"Issue Message"
            ],
            key_issue_rows
        )
        if key_issue_rows
        else u"<div class='qc-empty'>상세 표시 대상이 없습니다.</div>"
    )

    output.print_html(
        u"""
        <div class="qc-lite-details">
            <style>
                .qc-lite-details {{font-family:Segoe UI, Arial, sans-serif;
                    color:#263645; max-width:1200px;}}
                .qc-lite-details h2 {{margin:0 0 3px 0;}}
                .qc-version {{color:#5F6F7D; margin-bottom:14px;}}
                .qc-section {{margin:0 0 10px 0; border:1px solid #D6DDE3;
                    background:#FFFFFF;}}
                .qc-section summary {{cursor:pointer; padding:10px 12px;
                    font-weight:600; background:#F4F6F8;
                    border-left:3px solid #DE712F;}}
                .qc-section-body {{padding:10px 12px 12px 12px;}}
                .qc-output-table {{width:100%; border-collapse:collapse;
                    table-layout:fixed;}}
                .qc-output-table th, .qc-output-table td {{padding:7px 8px;
                    border-bottom:1px solid #E2E7EB; text-align:left;
                    overflow-wrap:anywhere;}}
                .qc-output-table th {{background:#536777; color:#FFFFFF;}}
                .qc-output-table tr:nth-child(even) td {{background:#F7F9FB;}}
                .qc-empty {{padding:8px; color:#5F6F7D;}}
                .qc-next {{margin-top:12px; padding:10px 12px; color:#5F6F7D;
                    border-left:3px solid #DE712F; background:#F8F9FA;}}
            </style>
            <h2>QC Lite Detailed Report</h2>
            <div class="qc-version">{0}</div>
            <details class="qc-section" open>
                <summary>Compact Summary</summary>
                <div class="qc-section-body">{1}</div>
            </details>
            <details class="qc-section" open>
                <summary>Top Issues</summary>
                <div class="qc-section-body">{2}</div>
            </details>
            <details class="qc-section">
                <summary>Detailed QC Results</summary>
                <div class="qc-section-body">{3}</div>
            </details>
            <details class="qc-section">
                <summary>Export Results</summary>
                <div class="qc-section-body">{4}</div>
            </details>
            <div class="qc-next"><b>Next Actions</b><br>
                전체 검토는 <b>DOC QC</b>, 저장된 결과 확인은
                <b>Report</b> 버튼을 사용하세요.
            </div>
        </div>
        """.format(
            html_escape(version),
            _build_output_table([u"Summary", u"Value"], compact_summary_rows),
            top_issues_html,
            detailed_html,
            export_html
        )
    )


def _build_output_table(columns, rows):
    header_cells = u"".join(
        [u"<th>{0}</th>".format(html_escape(column)) for column in columns]
    )
    body_rows = []
    for row in rows:
        cells = u"".join(
            [u"<td>{0}</td>".format(html_escape(value)) for value in row]
        )
        body_rows.append(u"<tr>{0}</tr>".format(cells))
    return u"<table class='qc-output-table'><thead><tr>{0}</tr></thead>" \
        u"<tbody>{1}</tbody></table>".format(
            header_cells,
            u"".join(body_rows)
        )


def _build_export_results_html(
    export_options,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    saved_compact_html_path,
    compact_html_error,
    saved_compact_pdf_path,
    compact_pdf_error
):
    if not export_options["selected_formats"]:
        return u"<div class='qc-empty'>선택한 파일 출력 형식이 없습니다.</div>"

    rows = [
        [u"Folder", export_options["folder"]],
        [u"Selected", u" / ".join(export_options["selected_formats"])],
        [u"Full CSV", _get_export_result(
            saved_full_csv_path, full_csv_error, export_options["full_csv"]
        )],
        [u"Summary CSV", _get_export_result(
            saved_summary_csv_path,
            summary_csv_error,
            export_options["summary_csv"]
        )],
        [u"Styled XLSX Report", _get_export_result(
            saved_styled_xlsx_path,
            styled_xlsx_error,
            export_options["styled_xlsx"]
        )],
        [u"Compact Summary HTML", _get_export_result(
            saved_compact_html_path,
            compact_html_error,
            export_options.get("compact_html", False)
        )],
        [u"Compact Summary PDF", _get_export_result(
            saved_compact_pdf_path,
            compact_pdf_error,
            export_options.get("compact_pdf", False)
        )]
    ]
    safe_rows = []
    for label, value in rows:
        if label in [u"Folder", u"Selected"]:
            safe_rows.append([label, value])
        else:
            safe_rows.append([label, _strip_preescaped_value(value)])
    result = _build_output_table([u"Export", u"Result"], safe_rows)
    if export_options.get("folder_history_error"):
        result += u"<div style='color:#C85F1A; padding-top:8px;'>" \
            u"마지막 저장 폴더 기록 실패: {0}</div>".format(
                html_escape(export_options["folder_history_error"])
            )
    return result


def _strip_preescaped_value(value):
    return to_text(value).replace(u"&amp;", u"&").replace(
        u"&lt;", u"<"
    ).replace(u"&gt;", u">").replace(u"&quot;", u'"')


def render_export_results(
    output,
    export_options,
    saved_full_csv_path,
    full_csv_error,
    saved_summary_csv_path,
    summary_csv_error,
    saved_styled_xlsx_path,
    styled_xlsx_error,
    saved_compact_html_path=u"",
    compact_html_error=u"",
    saved_compact_pdf_path=u"",
    compact_pdf_error=u""
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
    compact_html_result = _get_export_result(
        saved_compact_html_path,
        compact_html_error,
        export_options.get("compact_html", False)
    )
    compact_pdf_result = _get_export_result(
        saved_compact_pdf_path,
        compact_pdf_error,
        export_options.get("compact_pdf", False)
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
            <strong>Compact Summary HTML:</strong> {5}<br>
            <strong>Compact Summary PDF:</strong> {6}<br>
            <span style="color:#5F6F7D;">
                Export 실패가 발생해도 QC 검사는 완료됩니다.
            </span>
        </div>
        """.format(
            html_escape(export_options["folder"]),
            html_escape(u" / ".join(export_options["selected_formats"])),
            full_csv_result,
            summary_csv_result,
            styled_xlsx_result,
            compact_html_result,
            compact_pdf_result
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
