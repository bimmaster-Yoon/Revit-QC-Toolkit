# -*- coding: utf-8 -*-

"""Runtime-only QC Lite Dashboard WinForms view."""

import io
import os
from datetime import datetime

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Color, ContentAlignment, FontStyle, Point, Size
from System.Windows.Forms import (
    AutoScaleMode, AutoSizeMode, BorderStyle, Button, ColumnStyle,
    DataGridView, DataGridViewAutoSizeColumnMode,
    DataGridViewCellBorderStyle, DataGridViewCellStyle,
    DataGridViewColumnSortMode, DataGridViewContentAlignment,
    DataGridViewColumnHeadersHeightSizeMode, DataGridViewHeaderBorderStyle,
    DataGridViewSelectionMode, DataGridViewTextBoxColumn, DialogResult,
    DataGridViewTriState, DockStyle, FlowDirection, FlowLayoutPanel, Form, FormBorderStyle,
    FormStartPosition, Label, MessageBox, MessageBoxButtons, MessageBoxIcon,
    Padding, Panel, RowStyle, Screen, ScrollBars, SizeType, TableLayoutPanel,
    ToolTip
)

from qc_ui_style import (
    BORDER_COLOR,
    BUTTON_GAP,
    FOOTER_BUTTON_HEIGHT,
    FOOTER_BUTTON_WIDTH,
    FOOTER_HEIGHT,
    MUTED_COLOR,
    NAVY_COLOR,
    ORANGE_HOVER_COLOR,
    apply_primary_button_style,
    apply_secondary_button_style,
    attach_border_hover,
    configure_tooltip,
    detach_border_hover,
    dispose_tooltip,
    get_preferred_font
)
from report_history import open_file


QC_LITE_DASHBOARD_BUILD = u"qc-lite-dashboard-datagrid-v3"
OUTER_MARGIN = 24
SECTION_GAP = 14
CARD_GAP = 10
CARD_HEIGHT = 118
STATS_HEIGHT = 84
TOP_HEADER_HEIGHT = 42
TOP_HELPER_HEIGHT = 28
TOP_TABLE_GAP = 8
TOP_BOTTOM_PADDING = 12
TABLE_HEADER_HEIGHT = 38
TABLE_ROW_HEIGHT = 52

CARD_BACKGROUND = Color.FromArgb(246, 248, 250)
ORANGE_LIGHT = Color.FromArgb(255, 244, 234)
TABLE_HEADER_BACKGROUND = Color.FromArgb(241, 244, 247)
TABLE_TEXT_COLOR = Color.FromArgb(51, 71, 91)
VALUE_ORANGE = Color.FromArgb(232, 117, 22)
SELECTION_BACKGROUND = Color.FromArgb(248, 249, 250)


class QcLiteDashboardForm(Form):
    def __init__(
        self,
        project_name,
        summary_data,
        key_issue_rows,
        report_path,
        details_callback=None,
        diagnostic_log_path=None
    ):
        Form.__init__(self)
        self.SuspendLayout()
        self.report_path = report_path
        self.details_callback = details_callback
        self.diagnostic_log_path = diagnostic_log_path
        self._cleanup_done = False
        self._hover_bindings = []
        self._fonts = [
            get_preferred_font(17.0, FontStyle.Bold),
            get_preferred_font(12.0, FontStyle.Bold),
            get_preferred_font(9.5, FontStyle.Bold),
            get_preferred_font(18.0, FontStyle.Bold),
            get_preferred_font(9.0),
            get_preferred_font(14.0, FontStyle.Bold),
            get_preferred_font(11.0, FontStyle.Bold),
            get_preferred_font(9.5)
        ]
        self.title_font = self._fonts[0]
        self.project_font = self._fonts[1]
        self.card_title_font = self._fonts[2]
        self.card_value_font = self._fonts[3]
        self.helper_font = self._fonts[4]
        self.stat_value_font = self._fonts[5]
        self.section_title_font = self._fonts[6]
        self.table_body_font = self._fonts[7]
        self.tool_tip = configure_tooltip(ToolTip())

        self.Text = u"Revit QC - QC Lite Dashboard"
        self.ClientSize = Size(1320, 820)
        self.MinimumSize = Size(1240, 740)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = self.table_body_font
        self.AutoScaleMode = AutoScaleMode.Dpi

        self.root_layout = self._build_dashboard_layout(
            project_name,
            summary_data,
            key_issue_rows
        )
        self.Controls.Add(self.root_layout)
        self.ResumeLayout(False)
        self.PerformLayout()
        self._fit_to_content()
        if self.diagnostic_log_path:
            self._write_runtime_diagnostics()

    def _build_dashboard_layout(self, project_name, summary_data, issue_rows):
        root = TableLayoutPanel()
        root.Dock = DockStyle.Fill
        root.Padding = Padding(OUTER_MARGIN)
        root.Margin = Padding(0)
        root.ColumnCount = 1
        root.RowCount = 7
        root.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        root.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(CARD_HEIGHT)))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(SECTION_GAP)))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(STATS_HEIGHT)))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(SECTION_GAP)))
        root.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))

        self.header_panel = self._build_header(project_name)
        root.Controls.Add(self.header_panel, 0, 0)
        self.summary_cards = self._build_summary_cards(summary_data)
        root.Controls.Add(self.summary_cards, 0, 1)
        self.issue_stats = self._build_issue_stats(summary_data)
        root.Controls.Add(self.issue_stats, 0, 3)
        self.top_issues_group = self._build_top_issues(issue_rows[:5])
        root.Controls.Add(self.top_issues_group, 0, 5)
        self.dashboard_footer = self._build_footer()
        root.Controls.Add(self.dashboard_footer, 0, 6)
        return root

    def _build_header(self, project_name):
        header = TableLayoutPanel()
        header.Dock = DockStyle.Top
        header.AutoSize = True
        header.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header.Margin = Padding(0, 0, 0, 20)
        header.ColumnCount = 1
        header.RowCount = 2
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))

        title = Label()
        title.Text = u"QC Lite Dashboard"
        title.Dock = DockStyle.Fill
        title.AutoSize = True
        title.Font = self.title_font
        title.ForeColor = NAVY_COLOR
        title.Margin = Padding(0)
        header.Controls.Add(title, 0, 0)

        project = Label()
        project.Text = u"{0}".format(project_name)
        project.Dock = DockStyle.Fill
        project.AutoSize = True
        project.AutoEllipsis = True
        project.Font = self.project_font
        project.ForeColor = MUTED_COLOR
        project.Margin = Padding(0, 6, 0, 0)
        header.Controls.Add(project, 0, 1)
        self.tool_tip.SetToolTip(project, project.Text)
        return header

    def _build_summary_cards(self, summary_data):
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.Margin = Padding(0)
        layout.ColumnCount = 4
        layout.RowCount = 1
        for _index in range(4):
            layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25.0))
        cards = [
            (u"SHEET QC", summary_data.get("sheet_issues", 0),
             u"{0} sheets".format(summary_data.get("checked_sheets", 0)), True),
            (u"VIEW QC", summary_data.get("view_issues", 0),
             u"{0} views".format(summary_data.get("checked_views", 0)), True),
            (u"PARAMETER QC", summary_data.get("parameter_issues", 0),
             u"QC Lite 포함", True),
            (u"SCAN QC", u"—", u"Not Run", False)
        ]
        for index, card_data in enumerate(cards):
            card = self._create_summary_card(*card_data)
            card.Margin = Padding(
                0 if index == 0 else CARD_GAP // 2,
                0,
                0 if index == 3 else CARD_GAP // 2,
                0
            )
            layout.Controls.Add(card, index, 0)
        return layout

    def _create_summary_card(self, title, value, helper, emphasized):
        border = Panel()
        border.Dock = DockStyle.Fill
        border.Padding = Padding(1)
        border.BackColor = BORDER_COLOR

        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.Margin = Padding(0)
        card.Padding = Padding(12, 8, 12, 8)
        card.BackColor = CARD_BACKGROUND
        card.ColumnCount = 1
        card.RowCount = 3
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 30.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 40.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 30.0))
        border.Controls.Add(card)

        title_label = self._make_fixed_label(
            title, self.card_title_font, NAVY_COLOR, ContentAlignment.MiddleLeft
        )
        value_label = self._make_fixed_label(
            value,
            self.card_value_font,
            VALUE_ORANGE if emphasized else MUTED_COLOR,
            ContentAlignment.MiddleLeft
        )
        helper_label = self._make_fixed_label(
            helper, self.helper_font, MUTED_COLOR, ContentAlignment.MiddleLeft
        )
        card.Controls.Add(title_label, 0, 0)
        card.Controls.Add(value_label, 0, 1)
        card.Controls.Add(helper_label, 0, 2)
        return border

    def _build_issue_stats(self, summary_data):
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.Margin = Padding(0)
        layout.ColumnCount = 7
        layout.RowCount = 1
        layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        layout.BackColor = ORANGE_LIGHT
        for index in range(7):
            if index % 2 == 0:
                layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25.0))
            else:
                layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 1.0))
        values = [
            (u"ISSUE COUNT", summary_data.get("total_issues", 0)),
            (u"HIGH", summary_data.get("high_count", 0)),
            (u"MEDIUM", summary_data.get("medium_count", 0)),
            (u"LOW", summary_data.get("low_count", 0))
        ]
        for index, value in enumerate(values):
            layout.Controls.Add(self._create_stat_cell(*value), index * 2, 0)
            if index < 3:
                divider = Panel()
                divider.Dock = DockStyle.Fill
                divider.Margin = Padding(0, 12, 0, 12)
                divider.BackColor = BORDER_COLOR
                layout.Controls.Add(divider, index * 2 + 1, 0)
        return layout

    def _create_stat_cell(self, title, value):
        cell = TableLayoutPanel()
        cell.Dock = DockStyle.Fill
        cell.Margin = Padding(0)
        cell.Padding = Padding(18, 8, 18, 8)
        cell.BackColor = ORANGE_LIGHT
        cell.ColumnCount = 2
        cell.RowCount = 1
        cell.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        cell.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 62.0))
        cell.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 38.0))
        title_label = self._make_fixed_label(
            title, self.card_title_font, NAVY_COLOR, ContentAlignment.MiddleLeft
        )
        value_label = self._make_fixed_label(
            value,
            self.stat_value_font,
            VALUE_ORANGE,
            ContentAlignment.MiddleRight
        )
        cell.Controls.Add(title_label, 0, 0)
        cell.Controls.Add(value_label, 1, 0)
        return cell

    def _build_top_issues(self, issue_rows):
        border = TableLayoutPanel()
        border.Dock = DockStyle.Top
        border.AutoSize = True
        border.AutoSizeMode = AutoSizeMode.GrowAndShrink
        border.Margin = Padding(0, 0, 0, SECTION_GAP)
        border.Padding = Padding(1)
        border.BackColor = BORDER_COLOR
        border.ColumnCount = 1
        border.RowCount = 1

        content = TableLayoutPanel()
        content.Dock = DockStyle.Top
        content.AutoSize = True
        content.AutoSizeMode = AutoSizeMode.GrowAndShrink
        content.Margin = Padding(0)
        content.Padding = Padding(16)
        content.BackColor = Color.White
        content.ColumnCount = 1
        content.RowCount = 5
        content.RowStyles.Add(RowStyle(SizeType.Absolute, float(TOP_HEADER_HEIGHT)))
        content.RowStyles.Add(RowStyle(SizeType.Absolute, float(TOP_HELPER_HEIGHT)))
        content.RowStyles.Add(RowStyle(SizeType.Absolute, float(TOP_TABLE_GAP)))
        content.RowStyles.Add(RowStyle(SizeType.AutoSize))
        content.RowStyles.Add(RowStyle(SizeType.Absolute, float(TOP_BOTTOM_PADDING)))
        border.Controls.Add(content, 0, 0)

        header = TableLayoutPanel()
        header.Dock = DockStyle.Fill
        header.Margin = Padding(0)
        header.ColumnCount = 2
        header.RowCount = 1
        header.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        header.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 96.0))
        content.Controls.Add(header, 0, 0)

        title = self._make_fixed_label(
            u"Top Issues",
            self.section_title_font,
            NAVY_COLOR,
            ContentAlignment.MiddleLeft
        )
        header.Controls.Add(title, 0, 0)

        details = Button()
        details.Text = u"Details"
        details.AutoSize = False
        details.Dock = getattr(DockStyle, "None")
        details.Size = Size(96, 36)
        details.Margin = Padding(0, 2, 0, 2)
        details.TextAlign = ContentAlignment.MiddleCenter
        details.UseCompatibleTextRendering = False
        details.Enabled = callable(self.details_callback)
        apply_secondary_button_style(details)
        self._hover_bindings.append(attach_border_hover(details))
        details.Click += self._show_details
        header.Controls.Add(details, 1, 0)
        self.details_button = details
        self.tool_tip.SetToolTip(
            details,
            u"pyRevit Output에서 상세 QC 결과와 Export 상태를 확인합니다."
        )

        helper = self._make_fixed_label(
            u"심각도가 높은 주요 항목을 최대 5개 표시",
            self.helper_font,
            MUTED_COLOR,
            ContentAlignment.MiddleLeft
        )
        content.Controls.Add(helper, 0, 1)

        self.issues_grid = self._create_issues_grid(issue_rows)
        content.Controls.Add(self.issues_grid, 0, 3)
        return border

    def _create_issues_grid(self, issue_rows):
        grid = DataGridView()
        grid.SuspendLayout()
        grid.Dock = DockStyle.Fill
        grid.AutoSize = False
        grid.Margin = Padding(0)
        grid.ReadOnly = True
        grid.AllowUserToAddRows = False
        grid.AllowUserToDeleteRows = False
        grid.AllowUserToResizeRows = False
        grid.AllowUserToResizeColumns = False
        grid.RowHeadersVisible = False
        grid.MultiSelect = False
        grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        grid.BorderStyle = getattr(BorderStyle, "None")
        grid.CellBorderStyle = getattr(DataGridViewCellBorderStyle, "None")
        grid.ColumnHeadersBorderStyle = getattr(
            DataGridViewHeaderBorderStyle,
            "None"
        )
        grid.BackgroundColor = Color.White
        grid.EnableHeadersVisualStyles = False
        grid.AutoGenerateColumns = False
        grid.ScrollBars = getattr(ScrollBars, "None")
        grid.ColumnHeadersHeight = TABLE_HEADER_HEIGHT
        grid.ColumnHeadersHeightSizeMode = (
            DataGridViewColumnHeadersHeightSizeMode.DisableResizing
        )
        grid.RowTemplate.Height = TABLE_ROW_HEIGHT
        grid.Font = self.table_body_font

        header_style = DataGridViewCellStyle()
        header_style.BackColor = TABLE_HEADER_BACKGROUND
        header_style.ForeColor = TABLE_TEXT_COLOR
        header_style.Font = self.card_title_font
        header_style.Alignment = DataGridViewContentAlignment.MiddleLeft
        header_style.WrapMode = getattr(DataGridViewTriState, "False")
        header_style.Padding = Padding(10, 0, 10, 0)
        grid.ColumnHeadersDefaultCellStyle = header_style

        body_style = DataGridViewCellStyle()
        body_style.BackColor = Color.White
        body_style.ForeColor = NAVY_COLOR
        body_style.Font = self.table_body_font
        body_style.Alignment = DataGridViewContentAlignment.MiddleLeft
        body_style.SelectionBackColor = SELECTION_BACKGROUND
        body_style.SelectionForeColor = NAVY_COLOR
        body_style.WrapMode = getattr(DataGridViewTriState, "False")
        body_style.Padding = Padding(10, 0, 8, 0)
        grid.DefaultCellStyle = body_style

        definitions = [
            (u"severity", u"SEVERITY", 130, False),
            (u"category", u"CATEGORY", 155, False),
            (u"item", u"ITEM", 480, True),
            (u"qc_item", u"QC ITEM", 190, False)
        ]
        for name, header, width, fill in definitions:
            column = DataGridViewTextBoxColumn()
            column.Name = name
            column.HeaderText = header
            column.SortMode = DataGridViewColumnSortMode.NotSortable
            column.MinimumWidth = width
            if fill:
                column.AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill
                item_style = DataGridViewCellStyle()
                item_style.WrapMode = getattr(DataGridViewTriState, "True")
                column.DefaultCellStyle = item_style
            else:
                column.Width = width
                column.AutoSizeMode = getattr(
                    DataGridViewAutoSizeColumnMode,
                    "None"
                )
            grid.Columns.Add(column)

        for issue_row in issue_rows:
            row_index = grid.Rows.Add()
            row = grid.Rows[row_index]
            row.Height = TABLE_ROW_HEIGHT
            values = [issue_row[3], issue_row[0], issue_row[2], issue_row[4]]
            for column_index, value in enumerate(values):
                row.Cells[column_index].Value = u"{0}".format(value)
            row.Cells[2].ToolTipText = u"{0}".format(issue_row[2])
        grid.Height = TABLE_HEADER_HEIGHT + TABLE_ROW_HEIGHT * len(issue_rows)
        grid.MinimumSize = Size(0, grid.Height)
        grid.MaximumSize = Size(0, grid.Height)
        grid.ResumeLayout(False)
        return grid

    def _build_footer(self):
        footer = Panel()
        footer.Dock = DockStyle.Fill
        footer.Margin = Padding(0)
        # Match the Close button right edge to the Details button right edge:
        # one-pixel Top Issues border plus its 16 px content padding.
        footer.Padding = Padding(0, 10, 17, 14)

        strip = FlowLayoutPanel()
        strip.Dock = DockStyle.Right
        strip.AutoSize = False
        strip.Width = FOOTER_BUTTON_WIDTH * 3 + BUTTON_GAP * 2
        strip.FlowDirection = FlowDirection.LeftToRight
        strip.WrapContents = False
        strip.Margin = Padding(0)
        strip.Padding = Padding(0)
        footer.Controls.Add(strip)

        self.doc_qc_button = self._create_footer_button(
            u"DOC QC", self._doc_qc_guide, False
        )
        self.report_button = self._create_footer_button(
            u"Report", self._open_report, False
        )
        self.report_button.Enabled = bool(self.report_path)
        self.close_button = self._create_footer_button(
            u"Close", self._close, True
        )
        self.close_button.DialogResult = DialogResult.OK
        for index, button in enumerate([
            self.doc_qc_button, self.report_button, self.close_button
        ]):
            button.Margin = Padding(
                0,
                0,
                BUTTON_GAP if index < 2 else 0,
                0
            )
            strip.Controls.Add(button)
        self.AcceptButton = self.close_button
        return footer

    def _create_footer_button(self, text, handler, primary):
        button = Button()
        button.Text = text
        button.AutoSize = False
        button.Dock = getattr(DockStyle, "None")
        button.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        button.TextAlign = ContentAlignment.MiddleCenter
        button.UseCompatibleTextRendering = False
        if primary:
            apply_primary_button_style(button)
        else:
            apply_secondary_button_style(button)
            self._hover_bindings.append(attach_border_hover(button))
        button.Click += handler
        return button

    def _make_fixed_label(self, text, font, color, alignment):
        label = Label()
        label.Text = u"{0}".format(text)
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.AutoEllipsis = False
        label.UseCompatibleTextRendering = False
        label.Font = font
        label.ForeColor = color
        label.TextAlign = alignment
        label.Margin = Padding(0)
        return label

    def _fit_to_content(self):
        try:
            preferred = self.root_layout.GetPreferredSize(Size(0, 0))
            working = Screen.PrimaryScreen.WorkingArea
            maximum_width = int(working.Width * 0.96)
            maximum_height = int(working.Height * 0.96)
            width = max(1240, min(maximum_width, max(1320, preferred.Width)))
            height = min(maximum_height, max(740, preferred.Height + 24))
            self.ClientSize = Size(width, height)
            left = working.Left + max(0, (working.Width - self.Width) // 2)
            top = working.Top + max(0, (working.Height - self.Height) // 2)
            self.Location = Point(left, top)
        except Exception:
            pass

    def _write_runtime_diagnostics(self):
        try:
            folder = os.path.dirname(self.diagnostic_log_path)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            preferred = self.root_layout.GetPreferredSize(Size(0, 0))
            line = (
                u"[{0}] module={1};class={2};builder={3};build={4};"
                u"client={5}x{6};preferred={7}x{8};dpi={9};scale={10}\n"
            ).format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                __file__,
                self.__class__.__name__,
                u"_build_dashboard_layout",
                QC_LITE_DASHBOARD_BUILD,
                self.ClientSize.Width,
                self.ClientSize.Height,
                preferred.Width,
                preferred.Height,
                getattr(self, "DeviceDpi", u"N/A"),
                self.AutoScaleMode
            )
            with io.open(
                self.diagnostic_log_path, "a", encoding="utf-8"
            ) as log_file:
                log_file.write(line)
        except Exception:
            pass

    def _show_details(self, sender, event_args):
        if not callable(self.details_callback):
            return
        try:
            self.details_callback()
        except Exception as ex:
            MessageBox.Show(
                self,
                u"상세 QC 결과를 열 수 없습니다.\r\n{0}".format(ex),
                u"QC Lite Details",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _open_report(self, sender, event_args):
        opened, error = open_file(self.report_path)
        if not opened:
            MessageBox.Show(
                self,
                error,
                u"Open Report",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _doc_qc_guide(self, sender, event_args):
        MessageBox.Show(
            self,
            u"전체 검토는 Revit QC 탭의 DOC QC 버튼을 실행하세요.",
            u"DOC QC",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _close(self, sender, event_args):
        self.Close()

    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        for binding in self._hover_bindings:
            detach_border_hover(binding)
        self._hover_bindings = []
        for button, handler in [
            (getattr(self, "details_button", None), self._show_details),
            (getattr(self, "doc_qc_button", None), self._doc_qc_guide),
            (getattr(self, "report_button", None), self._open_report),
            (getattr(self, "close_button", None), self._close)
        ]:
            if button is not None:
                try:
                    button.Click -= handler
                except Exception:
                    pass
        dispose_tooltip(self.tool_tip)
        self.tool_tip = None
        for font in self._fonts:
            try:
                font.Dispose()
            except Exception:
                pass
        self._fonts = []
