# -*- coding: utf-8 -*-

from pyrevit import script


output = script.get_output()
output.set_title("Revit QC Toolkit Help")
output.print_html(
    u"""
    <div style="font-family:Segoe UI, Arial, sans-serif;">
        <h2>Revit QC Toolkit</h2>
        <p>Revit 2026 도면과 Parameter를 모델 수정 없이 점검하는 read-only pyRevit 도구입니다.</p>
        <table style="border-collapse:collapse; width:100%;">
            <tr><td style="padding:8px; font-weight:bold;">Run Full QC</td><td>Sheet + View + Parameter QC, Full CSV, Summary CSV</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Quick QC</td><td>Sheet + View QC, Summary CSV</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">QC Settings</td><td>회사별 QC 기준 JSON 확인 및 수정</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Open Last Report</td><td>마지막 Summary CSV 열기</td></tr>
        </table>
        <div style="margin-top:12px; padding:10px; background:#e8f5e9; color:#2e7d32;">
            모든 검사는 Transaction 없이 실행되며 Revit 모델을 수정하지 않습니다.
        </div>
        <p>Full CSV는 상세 Review Item 전체를, Summary CSV는 반복 항목을 그룹화한 결과를 저장합니다.</p>
    </div>
    """
)
