# -*- coding: utf-8 -*-

from __future__ import print_function

import io
import os


def html_escape(value):
    return (
        u"{0}".format(value if value is not None else u"")
        .replace(u"&", u"&amp;")
        .replace(u"<", u"&lt;")
        .replace(u">", u"&gt;")
        .replace(u'"', u"&quot;")
    )


def _status_class(severity):
    if severity == u"High":
        return u"critical"
    if severity == u"Medium":
        return u"review"
    return u"checked"


def _build_group_rows(result_model):
    rows = []
    for index, group in enumerate(result_model["top_review_groups"], 1):
        rows.append(
            u"""
            <tr>
              <td class="rank">{0:02d}</td>
              <td><span class="category-tag">{1}</span></td>
              <td><strong>{2}</strong><span class="subline">{3}</span></td>
              <td><span class="status-pill {4}">{5}</span></td>
              <td class="count">{6}</td>
              <td class="sample-text">{7}</td>
            </tr>
            """.format(
                index,
                html_escape(group["category"]),
                html_escape(group["qc_item"]),
                html_escape(group["item_type"]),
                _status_class(group["severity"]),
                html_escape(group["severity"]),
                group["count"],
                html_escape(group["sample_display"])
            )
        )
    if not rows:
        rows.append(
            u'<tr><td colspan="6" class="empty-row">No findings.</td></tr>'
        )
    return u"".join(rows)


def _build_sample_cards(result_model):
    cards = []
    for sample in result_model["representative_items"]:
        cards.append(
            u"""
            <article class="sample-card">
              <div class="sample-head">
                <span class="category-tag">{0}</span>
                <span class="status-pill {1}">{2}</span>
              </div>
              <h3>{3}</h3>
              <p class="sample-meta">{4} / {5}</p>
              <p class="sample-message">{6}</p>
            </article>
            """.format(
                html_escape(sample["category"]),
                _status_class(sample["severity"]),
                html_escape(sample["severity"]),
                html_escape(sample["item_name"]),
                html_escape(sample["item_type"]),
                html_escape(sample["qc_item"]),
                html_escape(sample["message"])
            )
        )
    if not cards:
        cards.append(
            u'<article class="sample-card empty-card">No representative findings.</article>'
        )
    return u"".join(cards)


def build_compact_summary_html(result_model):
    metadata = result_model.get("metadata", {})
    kpi = result_model["kpi"]
    issue_counts = result_model["issue_count_by_qc"]
    checked_note = u"Sheets {0} + Views {1}".format(
        kpi["checked_sheets"],
        kpi["checked_views"]
    )
    if kpi.get("checked_parameter_elements", 0):
        checked_note += u" + Parameters {0}".format(
            kpi["checked_parameter_elements"]
        )

    return u"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DOC QC Compact Summary</title>
  <style>
    :root {{ --ink:#2d3237; --muted:#7e858c; --line:#dfe2e4; --panel:#f7f7f6;
      --orange:#d98725; --orange-soft:#f8ead8; --green-soft:#e8f3e8;
      --green-ink:#417348; --red-soft:#f7e4e2; --red-ink:#a44f48;
      --review-ink:#a5651d; }}
    * {{ box-sizing:border-box; }}
    html,body {{ margin:0; min-width:1600px; background:#ececea; color:var(--ink); }}
    body {{ font-family:"Segoe UI","Malgun Gothic",Arial,sans-serif; }}
    .canvas {{ width:1600px; min-height:980px; margin:0 auto; padding:58px 68px 46px; background:#fff; }}
    .topline {{ width:100%; height:2px; background:linear-gradient(90deg,var(--orange) 0 18%,#e8e8e6 18% 100%); }}
    header {{ display:flex; justify-content:space-between; align-items:flex-end; padding:20px 0 22px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--orange); font-size:12px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; }}
    h1 {{ margin:8px 0 4px; font-size:31px; line-height:1.05; letter-spacing:.01em; }}
    .subtitle {{ margin:0; color:var(--muted); font-size:14px; }}
    .header-meta {{ text-align:right; color:var(--muted); font-size:12px; line-height:1.7; }}
    .status-line {{ color:var(--red-ink); font-weight:700; }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:22px; }}
    .kpi {{ position:relative; min-height:118px; padding:18px 22px; border:1px solid var(--line); background:#fff; overflow:hidden; }}
    .kpi:before {{ content:""; position:absolute; inset:0 auto 0 0; width:5px; background:var(--tone); }}
    .kpi.checked {{ --tone:#8fbd94; background:linear-gradient(90deg,var(--green-soft),#fff 38%); }}
    .kpi.review {{ --tone:#dfa55d; background:linear-gradient(90deg,var(--orange-soft),#fff 38%); }}
    .kpi.critical {{ --tone:#d58982; background:linear-gradient(90deg,var(--red-soft),#fff 38%); }}
    .kpi-label {{ color:var(--muted); font-size:12px; font-weight:700; letter-spacing:.11em; text-transform:uppercase; }}
    .kpi-value {{ margin-top:6px; font-size:40px; line-height:1; font-weight:650; font-variant-numeric:tabular-nums; }}
    .kpi-note {{ margin-top:9px; color:var(--muted); font-size:12px; }}
    .middle-grid {{ display:grid; grid-template-columns:1fr 2.18fr; gap:18px; margin-top:18px; }}
    .panel {{ border:1px solid var(--line); background:#fff; }}
    .panel-head {{ display:flex; justify-content:space-between; align-items:baseline; padding:15px 18px 12px; border-bottom:1px solid var(--line); }}
    .panel-head h2 {{ margin:0; font-size:14px; letter-spacing:.055em; }}
    .panel-note {{ color:var(--muted); font-size:11px; }}
    .category-list {{ padding:6px 18px 8px; }}
    .category-row {{ display:grid; grid-template-columns:1fr 82px; align-items:center; gap:18px; padding:15px 0; border-bottom:1px solid #eceeed; }}
    .category-row:last-child {{ border-bottom:0; }}
    .category-name {{ font-size:14px; font-weight:600; }}
    .category-sub {{ margin-top:4px; color:var(--muted); font-size:11px; }}
    .category-count {{ text-align:right; color:var(--orange); font-size:28px; font-weight:650; font-variant-numeric:tabular-nums; }}
    table {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
    th {{ padding:10px 9px; color:var(--muted); background:var(--panel); font-size:10px; letter-spacing:.08em; text-align:left; text-transform:uppercase; }}
    td {{ padding:10px 9px; border-top:1px solid #eceeed; font-size:11px; vertical-align:middle; }}
    th:nth-child(1),td:nth-child(1) {{ width:48px; }} th:nth-child(2),td:nth-child(2) {{ width:112px; }}
    th:nth-child(3),td:nth-child(3) {{ width:168px; }} th:nth-child(4),td:nth-child(4) {{ width:78px; }}
    th:nth-child(5),td:nth-child(5) {{ width:66px; text-align:right; }}
    .rank {{ color:#b4b8bc; font-weight:700; }} .subline {{ display:block; margin-top:2px; color:var(--muted); font-size:10px; }}
    .count {{ color:var(--orange); font-size:17px; font-weight:700; font-variant-numeric:tabular-nums; }}
    .sample-text {{ color:#62686e; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    .category-tag {{ display:inline-block; color:#646a70; font-size:10px; font-weight:700; letter-spacing:.03em; }}
    .status-pill {{ display:inline-block; min-width:54px; padding:4px 7px; border-radius:2px; text-align:center; font-size:9px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }}
    .status-pill.checked {{ color:var(--green-ink); background:var(--green-soft); }}
    .status-pill.review {{ color:var(--review-ink); background:var(--orange-soft); }}
    .status-pill.critical {{ color:var(--red-ink); background:var(--red-soft); }}
    .samples-panel {{ margin-top:18px; }} .sample-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:0; }}
    .sample-card {{ min-height:145px; padding:16px 18px; border-right:1px solid var(--line); }}
    .sample-card:last-child {{ border-right:0; }} .sample-head {{ display:flex; justify-content:space-between; align-items:center; }}
    .sample-card h3 {{ margin:14px 0 4px; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    .sample-meta {{ margin:0; color:var(--muted); font-size:11px; }}
    .sample-message {{ margin:13px 0 0; padding-top:10px; border-top:1px solid #eceeed; color:#50565b; font-size:12px; }}
    .empty-row,.empty-card {{ color:var(--green-ink); text-align:center; }}
    footer {{ display:flex; justify-content:space-between; margin-top:18px; padding-top:12px; border-top:1px solid var(--line); color:#92979b; font-size:10px; letter-spacing:.03em; }}
    .footer-accent {{ color:var(--orange); font-weight:700; }}
    @media print {{ html,body {{ min-width:0; background:#fff; }} .canvas {{ width:100%; min-height:0; padding:24px; }} }}
  </style>
</head>
<body>
  <main class="canvas">
    <div class="topline"></div>
    <header>
      <div><div class="eyebrow">Revit QC Toolkit / Documentation Quality Control</div>
        <h1>DOC QC COMPACT SUMMARY</h1><p class="subtitle">Sheet, View and Parameter QC result overview</p></div>
      <div class="header-meta"><div>{project}</div><div>{run_mode} / {tool_version}</div>
        <div>{generated_at}</div><div class="status-line">STATUS / {qc_status}</div></div>
    </header>
    <section class="kpi-grid">
      <article class="kpi checked"><div class="kpi-label">Checked Items</div><div class="kpi-value">{checked_items}</div><div class="kpi-note">{checked_note}</div></article>
      <article class="kpi review"><div class="kpi-label">Total Findings</div><div class="kpi-value">{total_findings}</div><div class="kpi-note">All findings from the current QC run</div></article>
      <article class="kpi critical"><div class="kpi-label">Critical Items</div><div class="kpi-value">{critical_items}</div><div class="kpi-note">High severity findings</div></article>
    </section>
    <section class="middle-grid">
      <article class="panel"><div class="panel-head"><h2>ISSUE COUNT BY QC</h2><span class="panel-note">Current result</span></div>
        <div class="category-list">
          <div class="category-row"><div><div class="category-name">Sheet QC</div><div class="category-sub">Sheet information and placement</div></div><div class="category-count">{sheet_issues}</div></div>
          <div class="category-row"><div><div class="category-name">View QC</div><div class="category-sub">Name, template, scale and placement</div></div><div class="category-count">{view_issues}</div></div>
          <div class="category-row"><div><div class="category-name">Parameter QC</div><div class="category-sub">Required parameters and empty values</div></div><div class="category-count">{parameter_issues}</div></div>
        </div></article>
      <article class="panel"><div class="panel-head"><h2>REVIEW GROUP SUMMARY</h2><span class="panel-note">Top 5 / severity then count</span></div>
        <table><thead><tr><th>No.</th><th>Category</th><th>QC Item</th><th>Status</th><th>Count</th><th>Representative items</th></tr></thead><tbody>{group_rows}</tbody></table></article>
    </section>
    <section class="panel samples-panel"><div class="panel-head"><h2>REPRESENTATIVE ITEM SAMPLES</h2><span class="panel-note">Maximum 3 findings</span></div>
      <div class="sample-grid">{sample_cards}</div></section>
    <footer><span>Generated from the same QC result data used by HTML, PDF and XLSX reports</span><span class="footer-accent">REVIT QC TOOLKIT</span></footer>
  </main>
</body>
</html>""".format(
        project=html_escape(metadata.get("project", u"")),
        run_mode=html_escape(metadata.get("run_mode", u"QC")),
        tool_version=html_escape(metadata.get("tool_version", u"")),
        generated_at=html_escape(metadata.get("export_time", metadata.get("run_time", u""))),
        qc_status=html_escape(result_model.get("qc_status", u"")),
        checked_items=kpi["checked_items"],
        checked_note=html_escape(checked_note),
        total_findings=kpi["total_findings"],
        critical_items=kpi["critical_items"],
        sheet_issues=issue_counts["sheet_qc"],
        view_issues=issue_counts["view_qc"],
        parameter_issues=issue_counts["parameter_qc"],
        group_rows=_build_group_rows(result_model),
        sample_cards=_build_sample_cards(result_model)
    )


def save_compact_summary_html(
    result_model,
    timestamp,
    file_prefix,
    export_folder
):
    if not export_folder or not os.path.isdir(export_folder):
        raise ValueError(u"Compact Summary export folder is not available.")
    output_path = os.path.join(
        export_folder,
        u"{0}_Compact_Summary_{1}.html".format(file_prefix, timestamp)
    )
    with io.open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(build_compact_summary_html(result_model))
    return output_path
