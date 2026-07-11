# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os
import sys

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


INK = HexColor("#2D3237")
MUTED = HexColor("#7E858C")
LINE = HexColor("#DFE2E4")
PANEL = HexColor("#F7F7F6")
ORANGE = HexColor("#D98725")
GREEN_SOFT = HexColor("#E8F3E8")
ORANGE_SOFT = HexColor("#F8EAD8")
RED_SOFT = HexColor("#F7E4E2")
GREEN_INK = HexColor("#417348")
REVIEW_INK = HexColor("#A5651D")
RED_INK = HexColor("#A44F48")


def load_payload(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        return json.load(input_file)


def register_fonts():
    regular_path = r"C:\Windows\Fonts\malgun.ttf"
    bold_path = r"C:\Windows\Fonts\malgunbd.ttf"
    if os.path.isfile(regular_path) and os.path.isfile(bold_path):
        pdfmetrics.registerFont(TTFont("QcBody", regular_path))
        pdfmetrics.registerFont(TTFont("QcBold", bold_path))
        return "QcBody", "QcBold"
    return "Helvetica", "Helvetica-Bold"


def shorten(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def set_text(pdf, font_name, size, color=INK):
    pdf.setFont(font_name, size)
    pdf.setFillColor(color)


def draw_label(pdf, x, y, text, body_font, size=7, color=MUTED):
    set_text(pdf, body_font, size, color)
    pdf.drawString(x, y, str(text or ""))


def draw_kpi_card(pdf, x, y, width, height, label, value, note, fill, accent, body_font, bold_font):
    pdf.setFillColor(fill)
    pdf.setStrokeColor(LINE)
    pdf.rect(x, y, width, height, fill=1, stroke=1)
    pdf.setFillColor(accent)
    pdf.rect(x, y, 4, height, fill=1, stroke=0)
    set_text(pdf, bold_font, 7, MUTED)
    pdf.drawString(x + 16, y + height - 20, label.upper())
    set_text(pdf, bold_font, 24, INK)
    pdf.drawString(x + 16, y + 27, "{:,}".format(int(value)))
    draw_label(pdf, x + 16, y + 11, shorten(note, 48), body_font, 6.5)


def draw_status_pill(pdf, x, y, severity, body_font, bold_font):
    if severity == "High":
        fill, ink = RED_SOFT, RED_INK
    elif severity == "Medium":
        fill, ink = ORANGE_SOFT, REVIEW_INK
    else:
        fill, ink = GREEN_SOFT, GREEN_INK
    pdf.setFillColor(fill)
    pdf.roundRect(x, y, 42, 14, 2, fill=1, stroke=0)
    set_text(pdf, bold_font, 6, ink)
    pdf.drawCentredString(x + 21, y + 4.2, severity.upper())


def draw_category_panel(pdf, x, y, width, height, model, body_font, bold_font):
    pdf.setStrokeColor(LINE)
    pdf.setFillColor(Color(1, 1, 1))
    pdf.rect(x, y, width, height, fill=1, stroke=1)
    set_text(pdf, bold_font, 8, INK)
    pdf.drawString(x + 14, y + height - 19, "ISSUE COUNT BY QC")
    counts = model["issue_count_by_qc"]
    items = [
        ("Sheet QC", counts["sheet_qc"]),
        ("View QC", counts["view_qc"]),
        ("Parameter QC", counts["parameter_qc"]),
    ]
    row_height = 37
    row_top = y + height - 32
    for index, item in enumerate(items):
        row_y = row_top - ((index + 1) * row_height)
        if index:
            pdf.setStrokeColor(LINE)
            pdf.line(x + 14, row_y + row_height, x + width - 14, row_y + row_height)
        set_text(pdf, bold_font, 7.5, INK)
        pdf.drawString(x + 14, row_y + 14, item[0])
        set_text(pdf, bold_font, 16, ORANGE)
        pdf.drawRightString(x + width - 14, row_y + 10, "{:,}".format(item[1]))


def draw_groups_panel(pdf, x, y, width, height, model, body_font, bold_font):
    pdf.setStrokeColor(LINE)
    pdf.setFillColor(Color(1, 1, 1))
    pdf.rect(x, y, width, height, fill=1, stroke=1)
    set_text(pdf, bold_font, 8, INK)
    pdf.drawString(x + 14, y + height - 19, "REVIEW GROUP SUMMARY")
    draw_label(pdf, x + width - 95, y + height - 19, "TOP 5", body_font, 6.5)
    header_y = y + height - 38
    pdf.setFillColor(PANEL)
    pdf.rect(x, header_y, width, 16, fill=1, stroke=0)
    headers = [("NO.", 14), ("CATEGORY", 46), ("QC ITEM", 125), ("STATUS", 230), ("COUNT", 292), ("REPRESENTATIVE ITEMS", 340)]
    for label, offset in headers:
        set_text(pdf, bold_font, 5.5, MUTED)
        pdf.drawString(x + offset, header_y + 5, label)
    row_height = 20
    groups = model.get("top_review_groups", [])
    for index, group in enumerate(groups):
        row_y = header_y - ((index + 1) * row_height)
        pdf.setStrokeColor(LINE)
        pdf.line(x, row_y, x + width, row_y)
        set_text(pdf, bold_font, 6.5, MUTED)
        pdf.drawString(x + 14, row_y + 7, "{:02d}".format(index + 1))
        set_text(pdf, body_font, 6.5, INK)
        pdf.drawString(x + 46, row_y + 7, shorten(group["category"], 16))
        set_text(pdf, bold_font, 6.5, INK)
        pdf.drawString(x + 125, row_y + 7, shorten(group["qc_item"], 21))
        draw_status_pill(pdf, x + 230, row_y + 3, group["severity"], body_font, bold_font)
        set_text(pdf, bold_font, 8, ORANGE)
        pdf.drawRightString(x + 322, row_y + 6, "{:,}".format(group["count"]))
        set_text(pdf, body_font, 5.7, MUTED)
        pdf.drawString(x + 340, row_y + 7, shorten(group["sample_display"], 58))


def draw_sample_cards(pdf, x, y, width, height, model, body_font, bold_font):
    pdf.setStrokeColor(LINE)
    pdf.setFillColor(Color(1, 1, 1))
    pdf.rect(x, y, width, height, fill=1, stroke=1)
    set_text(pdf, bold_font, 8, INK)
    pdf.drawString(x + 14, y + height - 18, "REPRESENTATIVE ITEM SAMPLES")
    cards = model.get("representative_items", [])[:3]
    card_top = y + height - 29
    card_width = width / 3.0
    for index in range(3):
        card_x = x + (index * card_width)
        if index:
            pdf.setStrokeColor(LINE)
            pdf.line(card_x, y, card_x, card_top)
        if index >= len(cards):
            continue
        item = cards[index]
        set_text(pdf, bold_font, 6.2, MUTED)
        pdf.drawString(card_x + 14, card_top - 14, shorten(item["category"], 18))
        draw_status_pill(pdf, card_x + card_width - 56, card_top - 19, item["severity"], body_font, bold_font)
        set_text(pdf, bold_font, 8, INK)
        pdf.drawString(card_x + 14, card_top - 38, shorten(item["item_name"], 38))
        draw_label(pdf, card_x + 14, card_top - 51, "{0} / {1}".format(item["item_type"], item["qc_item"]), body_font, 6.2)
        pdf.setStrokeColor(LINE)
        pdf.line(card_x + 14, card_top - 59, card_x + card_width - 14, card_top - 59)
        set_text(pdf, body_font, 6.5, INK)
        pdf.drawString(card_x + 14, card_top - 73, shorten(item["message"], 48))


def create_pdf(result_model, output_pdf_path):
    body_font, bold_font = register_fonts()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(output_pdf_path, pagesize=(page_width, page_height))
    pdf.setTitle("DOC QC Compact Summary")

    margin = 34
    content_width = page_width - (margin * 2)
    pdf.setFillColor(ORANGE)
    pdf.rect(margin, page_height - 36, content_width * 0.18, 2, fill=1, stroke=0)
    pdf.setFillColor(LINE)
    pdf.rect(margin + content_width * 0.18, page_height - 36, content_width * 0.82, 2, fill=1, stroke=0)

    metadata = result_model.get("metadata", {})
    set_text(pdf, bold_font, 8, ORANGE)
    pdf.drawString(margin, page_height - 55, "REVIT QC TOOLKIT / DOCUMENTATION QUALITY CONTROL")
    set_text(pdf, bold_font, 19, INK)
    pdf.drawString(margin, page_height - 78, "DOC QC COMPACT SUMMARY")
    draw_label(pdf, margin, page_height - 91, "Sheet, View and Parameter QC result overview", body_font, 7)
    set_text(pdf, body_font, 6.5, MUTED)
    pdf.drawRightString(page_width - margin, page_height - 58, shorten(metadata.get("project", ""), 52))
    pdf.drawRightString(page_width - margin, page_height - 70, "{0} / {1}".format(metadata.get("run_mode", "QC"), metadata.get("tool_version", "")))
    pdf.drawRightString(page_width - margin, page_height - 82, metadata.get("export_time", metadata.get("run_time", "")))
    set_text(pdf, bold_font, 6.5, RED_INK)
    pdf.drawRightString(page_width - margin, page_height - 94, "STATUS / " + result_model.get("qc_status", ""))

    kpi = result_model["kpi"]
    card_gap = 10
    card_width = (content_width - (card_gap * 2)) / 3.0
    card_y = page_height - 175
    checked_note = "Sheets {0} + Views {1}".format(kpi["checked_sheets"], kpi["checked_views"])
    draw_kpi_card(pdf, margin, card_y, card_width, 64, "Checked Items", kpi["checked_items"], checked_note, GREEN_SOFT, GREEN_INK, body_font, bold_font)
    draw_kpi_card(pdf, margin + card_width + card_gap, card_y, card_width, 64, "Total Findings", kpi["total_findings"], "All findings from the current QC run", ORANGE_SOFT, ORANGE, body_font, bold_font)
    draw_kpi_card(pdf, margin + ((card_width + card_gap) * 2), card_y, card_width, 64, "Critical Items", kpi["critical_items"], "High severity findings", RED_SOFT, RED_INK, body_font, bold_font)

    middle_y = page_height - 345
    left_width = 202
    draw_category_panel(pdf, margin, middle_y, left_width, 154, result_model, body_font, bold_font)
    draw_groups_panel(pdf, margin + left_width + 10, middle_y, content_width - left_width - 10, 154, result_model, body_font, bold_font)

    draw_sample_cards(pdf, margin, 58, content_width, 140, result_model, body_font, bold_font)
    pdf.setStrokeColor(LINE)
    pdf.line(margin, 44, page_width - margin, 44)
    draw_label(pdf, margin, 31, "Generated from the same QC result data used by HTML, PDF and XLSX reports", body_font, 6)
    set_text(pdf, bold_font, 6, ORANGE)
    pdf.drawRightString(page_width - margin, 31, "REVIT QC TOOLKIT")

    pdf.showPage()
    pdf.save()
    return output_pdf_path


def main(arguments):
    if len(arguments) != 3:
        print("Usage: make_compact_summary_pdf.py <input_json_path> <output_pdf_path>", file=sys.stderr)
        return 2
    input_json_path = os.path.abspath(arguments[1])
    output_pdf_path = os.path.abspath(arguments[2])
    try:
        result_model = load_payload(input_json_path)
        create_pdf(result_model, output_pdf_path)
        print(output_pdf_path)
        return 0
    except Exception as exc:
        print("Compact Summary PDF export failed: {0}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
