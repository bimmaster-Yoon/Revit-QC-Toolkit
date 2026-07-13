# -*- coding: utf-8 -*-

import io
import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import Guid
from System.Drawing import (
    Color, ContentAlignment, Font, FontFamily, FontStyle, Point, Size
)
from System.Windows.Forms import (
    AnchorStyles, AutoScaleMode, AutoSizeMode, Button, CheckBox, ColumnStyle,
    ComboBoxStyle, DialogResult, DockStyle, FlatStyle, FlowDirection,
    FlowLayoutPanel, FolderBrowserDialog, Form, FormBorderStyle,
    FormStartPosition, Label, MessageBox, MessageBoxButtons, MessageBoxIcon,
    GroupBox, Padding, Panel, RowStyle, SizeType, TableLayoutPanel, TextBox,
    ToolTip
)

from qc_ui_style import (
    apply_scan_reference_section_style,
    attach_border_hover,
    configure_content_scroll,
    configure_tooltip,
    detach_border_hover,
    dispose_tooltip
)
from ui_close_profiler import create_ui_close_profile, log_section_snapshots


LATEST_EXPORT_FOLDER_FILE = "latest_export_folder.txt"

NAVY_COLOR = Color.FromArgb(30, 45, 61)
BUTTON_NAVY_COLOR = Color.FromArgb(83, 103, 119)
BUTTON_HOVER_COLOR = Color.FromArgb(70, 88, 103)
MUTED_COLOR = Color.FromArgb(100, 116, 135)
ORANGE_COLOR = Color.FromArgb(242, 140, 40)
ORANGE_LIGHT_COLOR = Color.FromArgb(255, 244, 234)
BORDER_COLOR = Color.FromArgb(216, 222, 229)
INNER_BORDER_COLOR = Color.FromArgb(228, 233, 238)
LIGHT_BACKGROUND_COLOR = Color.FromArgb(246, 248, 250)
WARNING_COLOR = Color.FromArgb(200, 95, 26)

WINDOW_OUTER_MARGIN = 28
SECTION_GAP = 14
SECTION_INNER_PADDING = 16
ROW_GAP = 10
CONTROL_HEIGHT = 36
FOOTER_HEIGHT = 64
FOOTER_BUTTON_WIDTH = 112
FOOTER_BUTTON_HEIGHT = 40
FOOTER_BUTTON_GAP = 12


def get_preferred_font(size, style=FontStyle.Regular):
    preferred_names = [u"Segoe UI", u"Malgun Gothic", u"Pretendard", u"SUIT"]

    try:
        available_names = [family.Name.lower() for family in FontFamily.Families]
        for font_name in preferred_names:
            if font_name.lower() in available_names:
                return Font(font_name, size, style)
    except Exception:
        pass

    return Font(u"Segoe UI", size, style)


def get_latest_export_folder_pointer(reports_dir):
    return os.path.join(reports_dir, LATEST_EXPORT_FOLDER_FILE)


def read_latest_export_folder(reports_dir):
    pointer_path = get_latest_export_folder_pointer(reports_dir)

    if not os.path.isfile(pointer_path):
        return u""

    try:
        with io.open(pointer_path, "r", encoding="utf-8-sig") as pointer_file:
            folder_path = pointer_file.read().strip()

        if os.path.isdir(folder_path):
            return folder_path
    except Exception:
        pass

    return u""


def write_latest_export_folder(reports_dir, folder_path):
    if not os.path.isdir(reports_dir):
        os.makedirs(reports_dir)

    pointer_path = get_latest_export_folder_pointer(reports_dir)

    with io.open(pointer_path, "w", encoding="utf-8") as pointer_file:
        pointer_file.write(folder_path)

    return pointer_path


def validate_export_folder(folder_path):
    if not folder_path or not folder_path.strip():
        return False, u"저장 폴더를 선택하세요."

    folder_path = folder_path.strip()

    if not os.path.isdir(folder_path):
        return False, u"선택한 폴더를 찾을 수 없습니다: {0}".format(folder_path)

    test_path = os.path.join(
        folder_path,
        u".revit_qc_write_test_{0}.tmp".format(Guid.NewGuid().ToString("N"))
    )

    try:
        with io.open(test_path, "w", encoding="utf-8") as test_file:
            test_file.write(u"write test")
    except Exception as ex:
        return False, u"선택한 폴더에 파일을 저장할 수 없습니다: {0}".format(ex)
    finally:
        try:
            if os.path.isfile(test_path):
                os.remove(test_path)
        except Exception:
            pass

    return True, u""


class ExportOptionsForm(Form):
    def __init__(self, last_folder, quick_mode):
        Form.__init__(self)
        self.SuspendLayout()
        self.result = None
        self._cleanup_done = False
        self._border_hover_bindings = []

        self.title_font = get_preferred_font(17.0, FontStyle.Bold)
        self.subtitle_font = get_preferred_font(9.5, FontStyle.Regular)
        self.section_font = get_preferred_font(10.5, FontStyle.Bold)
        self.body_font = get_preferred_font(9.5, FontStyle.Regular)
        self.card_title_font = get_preferred_font(9.5, FontStyle.Bold)
        self.helper_font = get_preferred_font(8.5, FontStyle.Regular)
        self.badge_font = get_preferred_font(8.0, FontStyle.Bold)
        self.button_font = get_preferred_font(9.5, FontStyle.Regular)
        self.tool_tip = configure_tooltip(ToolTip())

        self.Text = "Revit QC - QC Lite Export"
        self.ClientSize = Size(900, 680)
        self.MinimumSize = Size(860, 650)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = self.body_font
        self.AutoScaleMode = AutoScaleMode.Dpi

        self._build_layout(last_folder, quick_mode)
        self.Shown += self._configure_scroll_fallback
        self.ResumeLayout(True)

    def _build_layout(self, last_folder, quick_mode):
        root = TableLayoutPanel()
        root.Dock = DockStyle.Fill
        root.BackColor = Color.White
        root.Padding = Padding(
            WINDOW_OUTER_MARGIN,
            24,
            WINDOW_OUTER_MARGIN,
            0
        )
        root.ColumnCount = 1
        root.RowCount = 3
        root.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        root.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))
        self.Controls.Add(root)

        root.Controls.Add(self._build_header(), 0, 0)

        self.main_panel = Panel()
        self.main_panel.Dock = DockStyle.Fill
        self.main_panel.Margin = Padding(0, 20, 0, 0)
        self.main_panel.Padding = Padding(0)
        self.main_panel.BackColor = Color.White
        self.main_panel.AutoScroll = False
        root.Controls.Add(self.main_panel, 0, 1)

        content = TableLayoutPanel()
        content.Dock = DockStyle.Top
        content.AutoSize = True
        content.AutoSizeMode = AutoSizeMode.GrowAndShrink
        content.Margin = Padding(0)
        content.Padding = Padding(0)
        content.ColumnCount = 1
        content.RowCount = 2
        content.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        content.RowStyles.Add(RowStyle(SizeType.AutoSize))
        content.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.main_panel.Controls.Add(content)
        self.content_layout = content

        location_section = self._build_location_section(last_folder)
        location_section.Margin = Padding(0, 0, 0, SECTION_GAP)
        content.Controls.Add(location_section, 0, 0)

        formats_section = self._build_formats_section(quick_mode)
        formats_section.Margin = Padding(0)
        content.Controls.Add(formats_section, 0, 1)

        root.Controls.Add(self._build_footer(), 0, 2)

    def _build_header(self):
        header = TableLayoutPanel()
        header.Dock = DockStyle.Fill
        header.AutoSize = True
        header.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header.Margin = Padding(0)
        header.Padding = Padding(0)
        header.ColumnCount = 1
        header.RowCount = 2
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))

        title = Label()
        title.Text = u"QC Lite Export"
        title.Dock = DockStyle.Fill
        title.AutoSize = True
        title.Font = self.title_font
        title.ForeColor = NAVY_COLOR
        title.Margin = Padding(0)
        header.Controls.Add(title, 0, 0)

        subtitle = Label()
        subtitle.Text = u"빠른 QC 결과의 저장 위치와 출력 형식을 선택합니다."
        subtitle.Dock = DockStyle.Fill
        subtitle.AutoSize = True
        subtitle.Font = self.subtitle_font
        subtitle.ForeColor = MUTED_COLOR
        subtitle.Margin = Padding(0, 6, 0, 0)
        header.Controls.Add(subtitle, 0, 1)
        return header

    def _build_location_section(self, last_folder):
        section = TableLayoutPanel()
        section.Dock = DockStyle.Top
        section.AutoSize = True
        section.AutoSizeMode = AutoSizeMode.GrowAndShrink
        section.Padding = Padding(14, 8, 14, 8)
        section.BackColor = Color.White
        section.ColumnCount = 1
        section.RowCount = 2
        section.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        section.RowStyles.Add(RowStyle(SizeType.Absolute, 48.0))

        last_label = Label()
        if last_folder:
            last_label.Text = u"최근 저장 위치: {0}".format(last_folder)
        else:
            last_label.Text = u"최근 저장 위치: 없음"
        last_label.Dock = DockStyle.Fill
        last_label.AutoSize = False
        last_label.AutoEllipsis = True
        last_label.Font = self.helper_font
        last_label.ForeColor = MUTED_COLOR
        last_label.TextAlign = ContentAlignment.MiddleLeft
        section.Controls.Add(last_label, 0, 0)
        self.tool_tip.SetToolTip(last_label, last_label.Text)

        path_row = TableLayoutPanel()
        path_row.Dock = DockStyle.Fill
        path_row.Margin = Padding(0)
        path_row.Padding = Padding(0)
        path_row.ColumnCount = 3
        path_row.RowCount = 1
        path_row.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        path_row.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 12.0))
        path_row.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 112.0))
        path_row.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        section.Controls.Add(path_row, 0, 1)

        self.folder_text = TextBox()
        self.folder_text.Text = last_folder or u""
        self.folder_text.Dock = DockStyle.Fill
        self.folder_text.AutoSize = False
        self.folder_text.Height = CONTROL_HEIGHT
        self.folder_text.Margin = Padding(0, 6, 0, 6)
        self.folder_text.WordWrap = False
        self.folder_text.Font = self.body_font
        self.folder_text.TextChanged += self._update_folder_tooltip
        path_row.Controls.Add(self.folder_text, 0, 0)
        self.tool_tip.SetToolTip(self.folder_text, self.folder_text.Text)

        self.browse_button = Button()
        self.browse_button.Text = u"Browse"
        self.browse_button.AutoSize = False
        self.browse_button.Dock = getattr(DockStyle, "None")
        self.browse_button.Anchor = getattr(AnchorStyles, "None")
        self.browse_button.Size = Size(112, 40)
        self.browse_button.Margin = Padding(0)
        self.browse_button.Font = self.button_font
        self._apply_secondary_button_style(self.browse_button)
        self._border_hover_bindings.append(
            attach_border_hover(self.browse_button)
        )
        self.browse_button.Click += self._browse_folder
        path_row.Controls.Add(self.browse_button, 2, 0)
        self.tool_tip.SetToolTip(
            self.browse_button,
            u"보고서를 저장할 폴더를 선택합니다."
        )
        return self._wrap_section_frame(section, u"EXPORT LOCATION")

    def _build_formats_section(self, quick_mode):
        section = TableLayoutPanel()
        section.Dock = DockStyle.Top
        section.AutoSize = True
        section.AutoSizeMode = AutoSizeMode.GrowAndShrink
        section.Padding = Padding(14, 8, 14, 8)
        section.BackColor = Color.White
        section.ColumnCount = 1
        section.RowCount = 2
        section.RowStyles.Add(RowStyle(SizeType.Absolute, 246.0))
        section.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))

        grid = TableLayoutPanel()
        grid.Dock = DockStyle.Fill
        grid.Margin = Padding(0)
        grid.Padding = Padding(0)
        grid.BackColor = Color.White
        grid.ColumnCount = 2
        grid.RowCount = 3
        grid.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        grid.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        for row_index in range(3):
            grid.RowStyles.Add(RowStyle(SizeType.Percent, 33.333))
        section.Controls.Add(grid, 0, 0)

        styled_card, self.styled_xlsx_check = self._create_format_card(
            u"Styled XLSX Report",
            True,
            u"서식 적용 상세 Excel 보고서",
            True,
            0,
            0
        )
        grid.Controls.Add(styled_card, 0, 0)

        summary_card, self.summary_csv_check = self._create_format_card(
            u"Summary CSV",
            True,
            u"그룹별 QC 요약 CSV",
            False,
            1,
            0
        )
        grid.Controls.Add(summary_card, 1, 0)

        html_card, self.compact_html_check = self._create_format_card(
            u"Compact Summary HTML",
            quick_mode,
            u"브라우저용 요약 보고서",
            False,
            0,
            1
        )
        grid.Controls.Add(html_card, 0, 1)

        full_card, self.full_csv_check = self._create_format_card(
            u"Full CSV",
            not quick_mode,
            u"전체 QC 상세 데이터 CSV",
            False,
            1,
            1
        )
        grid.Controls.Add(full_card, 1, 1)

        pdf_card, self.compact_pdf_check = self._create_format_card(
            u"Compact Summary PDF",
            False,
            u"간결한 PDF 요약 보고서",
            False,
            0,
            2
        )
        grid.Controls.Add(pdf_card, 0, 2)

        empty = self._create_empty_format_card(1, 2)
        grid.Controls.Add(empty, 1, 2)

        self.export_note_label = Label()
        self.export_note_label.Dock = DockStyle.Fill
        self.export_note_label.AutoSize = False
        self.export_note_label.Font = self.subtitle_font
        self.export_note_label.ForeColor = MUTED_COLOR
        self.export_note_label.TextAlign = ContentAlignment.MiddleLeft
        self.export_note_label.Padding = Padding(2, 2, 0, 0)
        section.Controls.Add(self.export_note_label, 0, 1)

        self.export_checks = [
            self.full_csv_check,
            self.summary_csv_check,
            self.styled_xlsx_check,
            self.compact_html_check,
            self.compact_pdf_check
        ]
        for check_box in self.export_checks:
            check_box.CheckedChanged += self._update_export_state
        return self._wrap_section_frame(section, u"OUTPUT FORMATS")

    def _create_format_card(
        self,
        title_text,
        checked,
        description,
        recommended,
        column_index,
        row_index
    ):
        outer = TableLayoutPanel()
        outer.Dock = DockStyle.Fill
        outer.Margin = Padding(
            0 if column_index == 0 else 5,
            0 if row_index == 0 else 5,
            5 if column_index == 0 else 0,
            5 if row_index < 2 else 0
        )
        outer.Padding = Padding(1)
        outer.BackColor = ORANGE_COLOR if recommended else INNER_BORDER_COLOR
        outer.ColumnCount = 1
        outer.RowCount = 1
        outer.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        outer.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))

        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.Margin = Padding(0)
        card.Padding = Padding(12, 8, 12, 8)
        card.BackColor = ORANGE_LIGHT_COLOR if recommended else LIGHT_BACKGROUND_COLOR
        card.ColumnCount = 1
        card.RowCount = 2
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 32.0))
        card.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        outer.Controls.Add(card, 0, 0)

        header = TableLayoutPanel()
        header.Dock = DockStyle.Fill
        header.Margin = Padding(0)
        header.ColumnCount = 2
        header.RowCount = 1
        header.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        header.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, 48.0 if recommended else 0.0)
        )
        header.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        card.Controls.Add(header, 0, 0)

        check_box = CheckBox()
        check_box.Text = title_text
        check_box.Dock = DockStyle.Fill
        check_box.AutoSize = False
        check_box.Margin = Padding(0)
        check_box.Font = self.card_title_font
        check_box.ForeColor = NAVY_COLOR
        check_box.TextAlign = ContentAlignment.MiddleLeft
        check_box.Checked = checked
        header.Controls.Add(check_box, 0, 0)

        if recommended:
            badge = Label()
            badge.Text = u"권장"
            badge.Dock = DockStyle.Fill
            badge.AutoSize = False
            badge.Margin = Padding(4, 5, 0, 5)
            badge.BackColor = Color.White
            badge.ForeColor = ORANGE_COLOR
            badge.Font = self.badge_font
            badge.TextAlign = ContentAlignment.MiddleCenter
            header.Controls.Add(badge, 1, 0)

        helper = Label()
        helper.Text = description
        helper.Dock = DockStyle.Fill
        helper.AutoSize = False
        helper.AutoEllipsis = False
        helper.Margin = Padding(22, 0, 0, 0)
        helper.Font = self.helper_font
        helper.ForeColor = MUTED_COLOR
        helper.TextAlign = ContentAlignment.MiddleLeft
        helper.UseCompatibleTextRendering = True
        card.Controls.Add(helper, 0, 1)

        self.tool_tip.SetToolTip(check_box, description)
        self.tool_tip.SetToolTip(helper, description)
        return outer, check_box

    def _create_empty_format_card(self, column_index, row_index):
        outer = Panel()
        outer.Dock = DockStyle.Fill
        outer.Margin = Padding(
            0 if column_index == 0 else 5,
            0 if row_index == 0 else 5,
            5 if column_index == 0 else 0,
            5 if row_index < 2 else 0
        )
        outer.BackColor = Color.White
        return outer

    def _wrap_section_frame(self, section, title):
        frame = GroupBox()
        section.Margin = Padding(0)
        frame.Controls.Add(section)
        apply_scan_reference_section_style(
            frame,
            title,
            self.section_font,
            SECTION_GAP
        )
        return frame

    def _build_footer(self):
        footer = Panel()
        footer.Dock = DockStyle.Fill
        footer.AutoSize = False
        footer.Margin = Padding(0)
        footer.Padding = Padding(0, 0, 0, 24)

        strip = FlowLayoutPanel()
        strip.Dock = DockStyle.Right
        strip.AutoSize = False
        strip.Width = (
            FOOTER_BUTTON_WIDTH * 2 + FOOTER_BUTTON_GAP
        )
        strip.FlowDirection = FlowDirection.LeftToRight
        strip.WrapContents = False
        strip.Margin = Padding(0)
        strip.Padding = Padding(0)
        footer.Controls.Add(strip)

        cancel_button = Button()
        cancel_button.Text = u"Cancel"
        cancel_button.AutoSize = False
        cancel_button.Dock = getattr(DockStyle, "None")
        cancel_button.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        cancel_button.Margin = Padding(0, 0, FOOTER_BUTTON_GAP, 0)
        cancel_button.Font = self.button_font
        cancel_button.TextAlign = ContentAlignment.MiddleCenter
        cancel_button.UseCompatibleTextRendering = False
        self._apply_secondary_button_style(cancel_button)
        self.cancel_button = cancel_button
        self._border_hover_bindings.append(
            attach_border_hover(cancel_button)
        )
        cancel_button.DialogResult = DialogResult.Cancel
        strip.Controls.Add(cancel_button)

        self.ok_button = Button()
        self.ok_button.Text = u"Run QC"
        self.ok_button.AutoSize = False
        self.ok_button.Dock = getattr(DockStyle, "None")
        self.ok_button.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        self.ok_button.Margin = Padding(0)
        self.ok_button.Font = self.button_font
        self.ok_button.TextAlign = ContentAlignment.MiddleCenter
        self.ok_button.UseCompatibleTextRendering = False
        self._apply_primary_button_style(self.ok_button)
        self.ok_button.Click += self._confirm
        strip.Controls.Add(self.ok_button)

        self.tool_tip.SetToolTip(
            self.ok_button,
            u"선택한 형식으로 QC를 실행하고 보고서를 저장합니다."
        )
        self.AcceptButton = self.ok_button
        self.CancelButton = cancel_button
        self._update_export_state(None, None)
        return footer

    def _apply_secondary_button_style(self, button):
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = BORDER_COLOR
        button.FlatAppearance.MouseOverBackColor = ORANGE_LIGHT_COLOR
        button.FlatAppearance.MouseDownBackColor = BORDER_COLOR
        button.BackColor = Color.White
        button.ForeColor = NAVY_COLOR
        button.UseVisualStyleBackColor = False

    def _apply_primary_button_style(self, button):
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = BUTTON_NAVY_COLOR
        button.FlatAppearance.MouseOverBackColor = BUTTON_HOVER_COLOR
        button.FlatAppearance.MouseDownBackColor = NAVY_COLOR
        button.BackColor = BUTTON_NAVY_COLOR
        button.ForeColor = Color.White
        button.UseVisualStyleBackColor = False

    def _has_selected_export(self):
        return any(check_box.Checked for check_box in self.export_checks)

    def _configure_scroll_fallback(self, sender, event_args):
        configure_content_scroll(
            self,
            self.main_panel,
            self.content_layout,
            0.94
        )
        log_section_snapshots(u"QC Lite Export", self)

    def _update_export_state(self, sender, event_args):
        if not hasattr(self, "export_checks"):
            return
        selected_count = sum(
            1 for check_box in self.export_checks if check_box.Checked
        )
        has_selected_export = selected_count > 0
        self.folder_text.Enabled = has_selected_export
        self.browse_button.Enabled = has_selected_export
        if hasattr(self, "ok_button"):
            self.ok_button.Enabled = has_selected_export

        if has_selected_export:
            self.export_note_label.Text = u"선택된 출력 형식  {0}개".format(
                selected_count
            )
            self.export_note_label.ForeColor = MUTED_COLOR
        else:
            self.export_note_label.Text = (
                u"선택된 출력 형식  0개 · 하나 이상의 출력 형식을 선택하세요."
            )
            self.export_note_label.ForeColor = WARNING_COLOR

    def _update_folder_tooltip(self, sender, event_args):
        if getattr(self, "tool_tip", None) is not None:
            self.tool_tip.SetToolTip(self.folder_text, self.folder_text.Text)

    def _browse_folder(self, sender, event_args):
        dialog = FolderBrowserDialog()
        dialog.Description = "Select the Revit QC export folder"
        dialog.ShowNewFolderButton = True

        current_folder = self.folder_text.Text.strip()
        if os.path.isdir(current_folder):
            dialog.SelectedPath = current_folder

        try:
            if dialog.ShowDialog(self) == DialogResult.OK:
                self.folder_text.Text = dialog.SelectedPath
        finally:
            dialog.Dispose()

    def _confirm(self, sender, event_args):
        has_selected_export = self._has_selected_export()
        if not has_selected_export:
            MessageBox.Show(
                self,
                u"하나 이상의 출력 형식을 선택하세요.",
                "QC Lite Export",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        folder_path = self.folder_text.Text.strip()
        is_valid, validation_error = validate_export_folder(folder_path)
        if not is_valid:
            MessageBox.Show(
                self,
                validation_error,
                "QC Lite Export",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        selected_formats = []
        if self.full_csv_check.Checked:
            selected_formats.append(u"Full CSV")
        if self.summary_csv_check.Checked:
            selected_formats.append(u"Summary CSV")
        if self.styled_xlsx_check.Checked:
            selected_formats.append(u"Styled XLSX Report")
        if self.compact_html_check.Checked:
            selected_formats.append(u"Compact Summary HTML")
        if self.compact_pdf_check.Checked:
            selected_formats.append(u"Compact Summary PDF")

        self.result = {
            "folder": folder_path,
            "full_csv": self.full_csv_check.Checked,
            "summary_csv": self.summary_csv_check.Checked,
            "styled_xlsx": self.styled_xlsx_check.Checked,
            "compact_html": self.compact_html_check.Checked,
            "compact_pdf": self.compact_pdf_check.Checked,
            "selected_formats": selected_formats,
            "folder_history_error": u""
        }
        self.DialogResult = DialogResult.OK
        self.Close()

    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        for binding in self._border_hover_bindings:
            detach_border_hover(binding)
        self._border_hover_bindings = []
        try:
            self.Shown -= self._configure_scroll_fallback
        except Exception:
            pass
        try:
            self.folder_text.TextChanged -= self._update_folder_tooltip
        except Exception:
            pass
        try:
            self.browse_button.Click -= self._browse_folder
        except Exception:
            pass
        if hasattr(self, "export_checks"):
            for check_box in self.export_checks:
                try:
                    check_box.CheckedChanged -= self._update_export_state
                except Exception:
                    pass
        try:
            self.ok_button.Click -= self._confirm
        except Exception:
            pass
        dispose_tooltip(getattr(self, "tool_tip", None))
        self.tool_tip = None
        for font in (
            self.title_font,
            self.subtitle_font,
            self.section_font,
            self.body_font,
            self.card_title_font,
            self.helper_font,
            self.badge_font,
            self.button_font
        ):
            try:
                font.Dispose()
            except Exception:
                pass


def request_export_options(reports_dir, quick_mode=False):
    close_profile = create_ui_close_profile(u"Report Export Options")
    last_folder = read_latest_export_folder(reports_dir)
    options_form = ExportOptionsForm(last_folder, quick_mode)
    close_profile.attach(options_form)
    try:
        dialog_result = close_profile.show_dialog()
        selected_options = options_form.result
    finally:
        close_profile.dispose()

    if dialog_result != DialogResult.OK or selected_options is None:
        return None

    if selected_options["selected_formats"]:
        try:
            write_latest_export_folder(reports_dir, selected_options["folder"])
        except Exception as ex:
            selected_options["folder_history_error"] = u"{0}".format(ex)

    return selected_options
