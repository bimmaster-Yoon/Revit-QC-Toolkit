# -*- coding: utf-8 -*-

"""DOC QC setup and QC Lite dashboard presentation only."""

import io
import os
from datetime import datetime

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Color, ContentAlignment, FontStyle, Point, Size
from System.Windows.Forms import (
    AutoScaleMode, AutoSizeMode, BorderStyle, Button, CheckBox, ColumnStyle, ComboBox,
    ComboBoxStyle, DialogResult, DockStyle, FlowDirection, FlowLayoutPanel,
    FolderBrowserDialog, Form, FormBorderStyle, FormStartPosition,
    GroupBox, Label, MessageBox, MessageBoxButtons, MessageBoxIcon, Padding,
    Panel, RowStyle, Screen, SizeType, TableLayoutPanel,
    TableLayoutPanelCellBorderStyle, TextBox, ToolTip
)

from export_options import (
    read_latest_export_folder, validate_export_folder,
    write_latest_export_folder
)
from report_history import open_file
from ui_close_profiler import create_ui_close_profile
from qc_ui_style import (
    BUTTON_GAP,
    CONTROL_HEIGHT,
    FOOTER_BUTTON_HEIGHT,
    FOOTER_BUTTON_WIDTH,
    FOOTER_HEIGHT,
    GROUP_INNER_PADDING,
    HEADER_BOTTOM_MARGIN,
    HEADER_TOP_PADDING,
    HELP_BACKGROUND_COLOR as HELP,
    LIGHT_FILL_COLOR as LIGHT,
    MUTED_COLOR as MUTED,
    NAVY_COLOR as NAVY,
    ORANGE_COLOR as ORANGE,
    OUTER_MARGIN,
    SECTION_GAP,
    WINDOW_PADDING,
    WARNING_BACKGROUND_COLOR as ORANGE_LIGHT,
    attach_border_hover,
    apply_primary_button_style,
    apply_secondary_button_style,
    configure_content_scroll,
    configure_tooltip,
    detach_border_hover,
    dispose_tooltip,
    get_preferred_font as get_font
)


RED_LIGHT = Color.FromArgb(253, 239, 238)
TABLE_HEADER_COLOR = Color.FromArgb(241, 244, 247)
SEPARATOR_COLOR = Color.FromArgb(224, 229, 234)
QC_LITE_DASHBOARD_BUILD = u"qc-lite-dashboard-step03"


class QcFormBase(Form):
    def cleanup(self):
        if getattr(self, "_cleanup_done", False):
            return
        self._cleanup_done = True
        dispose_tooltip(getattr(self, "tool_tip", None))
        self.tool_tip = None

    def make_group(self, text):
        group = GroupBox()
        group.Text = text
        group.Dock = DockStyle.Fill
        group.AutoSize = True
        group.AutoSizeMode = AutoSizeMode.GrowAndShrink
        group.ForeColor = NAVY
        group.Font = get_font(10.5, FontStyle.Bold)
        group.Padding = Padding(
            GROUP_INNER_PADDING,
            8,
            GROUP_INNER_PADDING,
            8
        )
        group.Margin = Padding(0, 0, 0, SECTION_GAP)
        return group

    def make_check(self, text, checked=True, enabled=True):
        check = CheckBox()
        check.Text = text
        check.Dock = DockStyle.Fill
        check.AutoSize = False
        check.MinimumSize = Size(0, 36)
        check.TextAlign = ContentAlignment.MiddleLeft
        check.Margin = Padding(8, 4, 8, 4)
        check.ForeColor = NAVY
        check.Font = get_font(9.5)
        check.Checked = checked
        check.Enabled = enabled
        return check

    def make_info_badge(self, text):
        badge = Label()
        badge.Text = text
        badge.Dock = DockStyle.Fill
        badge.AutoSize = False
        badge.MinimumSize = Size(0, CONTROL_HEIGHT)
        badge.TextAlign = ContentAlignment.MiddleLeft
        badge.Margin = Padding(8, 4, 8, 4)
        badge.Padding = Padding(10, 0, 10, 0)
        badge.ForeColor = MUTED
        badge.BackColor = LIGHT
        badge.BorderStyle = BorderStyle.FixedSingle
        badge.Font = get_font(9.0)
        return badge

    def set_tip(self, control, text):
        try:
            self.tool_tip.SetToolTip(control, text)
        except Exception:
            pass

    def style_button(self, button, primary=False):
        if primary:
            apply_primary_button_style(button)
        else:
            apply_secondary_button_style(button)


class DocQcSetupForm(QcFormBase):
    def __init__(self, last_folder, active_config_display):
        Form.__init__(self)
        self.SuspendLayout()
        self.result = None
        self.folder_path = last_folder or u""
        self.Text = "Revit QC - DOC QC Setup"
        self.ClientSize = Size(1220, 1040)
        self.MinimumSize = Size(1100, 920)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY
        self.Font = get_font(9.5)
        self.AutoScaleMode = AutoScaleMode.Dpi
        self.AutoScroll = False
        self.tool_tip = configure_tooltip(ToolTip())

        main = TableLayoutPanel()
        main.Dock = DockStyle.Fill
        main.Padding = Padding(
            OUTER_MARGIN,
            HEADER_TOP_PADDING,
            OUTER_MARGIN,
            OUTER_MARGIN
        )
        main.ColumnCount = 1
        main.RowCount = 3
        main.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        main.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))
        self.Controls.Add(main)

        header_panel = Panel()
        header_panel.Dock = DockStyle.Fill
        header_panel.AutoSize = True
        header_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        main.Controls.Add(header_panel, 0, 0)
        title = Label()
        title.Text = "DOC QC Setup"
        title.Dock = DockStyle.Top
        title.AutoSize = True
        title.MinimumSize = Size(0, 58)
        title.Font = get_font(16.0, FontStyle.Bold)
        title.Padding = Padding(0, 5, 0, 0)
        header_panel.Controls.Add(title)

        content_panel = Panel()
        content_panel.Dock = DockStyle.Fill
        content_panel.AutoScroll = False
        content_panel.Margin = Padding(0, HEADER_BOTTOM_MARGIN, 0, 0)
        main.Controls.Add(content_panel, 0, 1)

        content = TableLayoutPanel()
        content.Dock = DockStyle.Top
        content.AutoSize = True
        content.ColumnCount = 1
        content.RowCount = 5
        content.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        for _index in range(5):
            content.RowStyles.Add(RowStyle(SizeType.AutoSize))
        content_panel.Controls.Add(content)
        self.content_panel = content_panel
        self.content_layout = content
        self.Shown += self._configure_scroll_fallback

        scope_group = self.make_group("Review Scope")
        scope = TableLayoutPanel()
        scope.Dock = DockStyle.Fill
        scope.AutoSize = True
        scope.Padding = Padding(12, 10, 12, 10)
        scope.ColumnCount = 2
        scope.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 180.0))
        scope.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        scope_group.Controls.Add(scope)
        content.Controls.Add(scope_group, 0, 0)
        scope_label = Label()
        scope_label.Text = "Review Scope"
        scope_label.Dock = DockStyle.Fill
        scope_label.TextAlign = ContentAlignment.MiddleLeft
        scope_label.Font = get_font(9.5, FontStyle.Bold)
        scope.Controls.Add(scope_label, 0, 0)
        self.scope_combo = ComboBox()
        self.scope_combo.Dock = DockStyle.Fill
        self.scope_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.scope_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.scope_combo.Margin = Padding(8, 12, 8, 12)
        self.scope_combo.BeginUpdate()
        try:
            for item in [
                "Current Project", "Current Sheet Set", "Selected Sheets",
                "Active View Only"
            ]:
                self.scope_combo.Items.Add(item)
        finally:
            self.scope_combo.EndUpdate()
        self.scope_combo.SelectedIndex = 0
        scope.Controls.Add(self.scope_combo, 1, 0)
        self.set_tip(
            self.scope_combo,
            u"검토 범위를 선택합니다. 현재 검사 엔진은 Current Project 범위를 "
            u"유지하며, 나머지 항목은 후속 범위 연결을 위해 표시됩니다."
        )

        category_group = self.make_group("QC Categories")
        categories = TableLayoutPanel()
        categories.Dock = DockStyle.Fill
        categories.AutoSize = True
        categories.Padding = Padding(12, 10, 12, 10)
        categories.ColumnCount = 2
        categories.RowCount = 3
        categories.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        categories.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        for _index in range(3):
            categories.RowStyles.Add(RowStyle(SizeType.AutoSize))
        category_group.Controls.Add(categories)
        content.Controls.Add(category_group, 0, 1)
        self.sheet_check = self.make_check("Sheet QC")
        self.view_check = self.make_check("View QC")
        self.parameter_check = self.make_check("Parameter QC")
        naming_badge = self.make_info_badge(
            "Naming QC  |  Included in Sheet / View QC"
        )
        placement_badge = self.make_info_badge(
            "View Placement QC  |  Included in Sheet / View QC"
        )
        category_note = Label()
        category_note.Text = "Included checks are shown below."
        category_note.Dock = DockStyle.Fill
        category_note.AutoSize = False
        category_note.MinimumSize = Size(0, CONTROL_HEIGHT)
        category_note.TextAlign = ContentAlignment.MiddleLeft
        category_note.Margin = Padding(8, 4, 8, 4)
        category_note.Padding = Padding(10, 0, 10, 0)
        category_note.ForeColor = MUTED
        category_note.Font = get_font(9.0)
        for control, column, row in [
            (self.sheet_check, 0, 0), (self.view_check, 1, 0),
            (self.parameter_check, 0, 1), (category_note, 1, 1),
            (placement_badge, 0, 2), (naming_badge, 1, 2)
        ]:
            categories.Controls.Add(control, column, row)
        self.set_tip(
            self.sheet_check,
            u"Sheet Number, Sheet Name, View Placement 상태를 검토합니다."
        )
        self.set_tip(
            self.view_check,
            u"View Name, Scale, View Template, Sheet 배치 여부를 검토합니다."
        )
        self.set_tip(
            self.parameter_check,
            u"필수 파라미터 입력 여부와 빈 값을 검토합니다."
        )
        self.set_tip(
            naming_badge,
            u"Naming QC는 현재 Sheet QC와 View QC 규칙에 포함되어 함께 실행됩니다."
        )
        self.set_tip(
            placement_badge,
            u"View Placement QC는 현재 Sheet QC와 View QC 규칙에 포함됩니다."
        )

        rule_group = self.make_group("Rule Set")
        rule = TableLayoutPanel()
        rule.Dock = DockStyle.Fill
        rule.AutoSize = True
        rule.Padding = Padding(14, 10, 14, 10)
        rule.ColumnCount = 2
        rule.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 180.0))
        rule.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        rule_group.Controls.Add(rule)
        content.Controls.Add(rule_group, 0, 2)
        rule_name = Label()
        rule_name.Text = "Active Rule Set"
        rule_name.Dock = DockStyle.Fill
        rule_name.TextAlign = ContentAlignment.MiddleLeft
        rule_name.Font = get_font(9.5, FontStyle.Bold)
        rule.Controls.Add(rule_name, 0, 0)
        rule_value = Label()
        rule_value.Text = active_config_display
        rule_value.Dock = DockStyle.Fill
        rule_value.AutoEllipsis = True
        rule_value.TextAlign = ContentAlignment.MiddleLeft
        rule_value.ForeColor = MUTED
        rule.Controls.Add(rule_value, 1, 0)
        self.set_tip(rule_value, u"QC Settings에서 선택한 Rule Set을 사용합니다.")

        output_group = self.make_group("Output Options / Report Style")
        output = TableLayoutPanel()
        output.Dock = DockStyle.Fill
        output.AutoSize = True
        output.Padding = Padding(12, 10, 12, 10)
        output.ColumnCount = 2
        output.RowCount = 4
        output.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        output.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        for _index in range(4):
            output.RowStyles.Add(RowStyle(SizeType.AutoSize))
        output_group.Controls.Add(output)
        content.Controls.Add(output_group, 0, 3)
        self.summary_check = self.make_check("pyRevit Output Summary", True, False)
        self.xlsx_check = self.make_check("XLSX Report", True, True)
        self.pdf_check = self.make_check("PDF Summary", False, False)
        self.open_check = self.make_check("Open Report After Run", False, True)
        output.Controls.Add(self.summary_check, 0, 0)
        output.Controls.Add(self.xlsx_check, 1, 0)
        output.Controls.Add(self.pdf_check, 0, 1)
        output.Controls.Add(self.open_check, 1, 1)
        self.set_tip(self.summary_check, u"QC 결과를 pyRevit Output 창에 표시합니다.")
        self.set_tip(self.xlsx_check, u"기존 Styled XLSX Report를 생성합니다.")
        self.set_tip(self.pdf_check, u"DOC QC PDF Summary는 아직 비활성화되어 있습니다.")
        self.set_tip(self.open_check, u"생성된 Report를 실행 후 기본 프로그램으로 엽니다.")
        style_label = Label()
        style_label.Text = "Report Style"
        style_label.Dock = DockStyle.Fill
        style_label.TextAlign = ContentAlignment.MiddleLeft
        style_label.Font = get_font(9.5, FontStyle.Bold)
        style_label.Margin = Padding(8, 4, 8, 4)
        output.Controls.Add(style_label, 0, 2)
        self.style_combo = ComboBox()
        self.style_combo.Dock = DockStyle.Fill
        self.style_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.style_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.style_combo.Margin = Padding(8, 8, 8, 8)
        self.style_combo.BeginUpdate()
        try:
            self.style_combo.Items.Add("Full + Summary")
            self.style_combo.Items.Add("Summary Only")
        finally:
            self.style_combo.EndUpdate()
        self.style_combo.SelectedIndex = 0
        output.Controls.Add(self.style_combo, 1, 2)
        self.set_tip(
            self.style_combo,
            u"Full + Summary는 Full CSV와 Summary CSV를 함께 생성합니다."
        )
        folder = TableLayoutPanel()
        folder.Dock = DockStyle.Fill
        folder.ColumnCount = 3
        folder.RowCount = 1
        folder.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        folder.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 12.0))
        folder.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 116.0))
        folder.RowStyles.Add(RowStyle(SizeType.Absolute, 36.0))
        folder.MinimumSize = Size(0, 36)
        folder.MaximumSize = Size(0, 36)
        output.Controls.Add(folder, 0, 3)
        output.SetColumnSpan(folder, 2)
        self.folder_text = TextBox()
        self.folder_text.Text = last_folder or u""
        self.folder_text.Dock = DockStyle.Fill
        self.folder_text.ReadOnly = True
        self.folder_text.WordWrap = False
        self.folder_text.AutoSize = False
        self.folder_text.Height = 36
        self.folder_text.MinimumSize = Size(0, 36)
        self.folder_text.MaximumSize = Size(0, 36)
        self.folder_text.BackColor = Color.White
        self.folder_text.ForeColor = MUTED
        self.folder_text.Margin = Padding(0)
        folder.Controls.Add(self.folder_text, 0, 0)
        self.set_tip(self.folder_text, self.folder_text.Text)
        browse = Button()
        browse.Text = "Browse..."
        browse.Dock = getattr(DockStyle, "None")
        browse.AutoSize = False
        browse.Size = Size(116, 36)
        browse.MinimumSize = Size(116, 36)
        browse.MaximumSize = Size(116, 36)
        browse.Margin = Padding(0)
        self.style_button(browse)
        browse.Click += self._browse
        folder.Controls.Add(browse, 2, 0)

        note = Label()
        note.Text = (
            "DOC QC는 기존 Rule Set으로 Sheet / View / Parameter 품질을 검토합니다. "
            "Naming과 View Placement는 현재 Sheet QC와 View QC에 포함됩니다. "
            "검사 및 Report 생성 로직은 기존 방식으로 유지됩니다."
        )
        note.Dock = DockStyle.Fill
        note.AutoSize = True
        note.MinimumSize = Size(0, 70)
        note.UseCompatibleTextRendering = True
        note.ForeColor = MUTED
        note.BackColor = HELP
        note.BorderStyle = BorderStyle.FixedSingle
        note.TextAlign = ContentAlignment.MiddleLeft
        note.Padding = Padding(14, 10, 14, 10)
        note.Margin = Padding(0, 10, 0, 20)
        content.Controls.Add(note, 0, 4)

        footer_panel = Panel()
        footer_panel.Dock = DockStyle.Bottom
        footer_panel.AutoSize = False
        footer_panel.Height = FOOTER_HEIGHT
        footer_panel.MinimumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.MaximumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.Padding = Padding(0, 10, 0, 14)
        main.Controls.Add(footer_panel, 0, 2)
        buttons = FlowLayoutPanel()
        buttons.Dock = DockStyle.Right
        buttons.AutoSize = False
        buttons.Width = FOOTER_BUTTON_WIDTH * 2 + BUTTON_GAP
        buttons.FlowDirection = FlowDirection.LeftToRight
        buttons.WrapContents = False
        buttons.Margin = Padding(0)
        buttons.Padding = Padding(0)
        footer_panel.Controls.Add(buttons)
        dock_none = getattr(DockStyle, "None")
        run_button = Button()
        run_button.Text = "Run"
        run_button.AutoSize = False
        run_button.Dock = dock_none
        run_button.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        run_button.Margin = Padding(0)
        self.style_button(run_button, True)
        run_button.Click += self._confirm
        cancel = Button()
        cancel.Text = "Cancel"
        cancel.AutoSize = False
        cancel.Dock = dock_none
        cancel.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        cancel.Margin = Padding(0, 0, BUTTON_GAP, 0)
        self.style_button(cancel)
        cancel.DialogResult = DialogResult.Cancel
        buttons.Controls.Add(cancel)
        self.CancelButton = cancel
        buttons.Controls.Add(run_button)
        self.AcceptButton = run_button
        self.ResumeLayout(True)
        self.PerformLayout()

    def _configure_scroll_fallback(self, sender, event_args):
        configure_content_scroll(
            self,
            self.content_panel,
            self.content_layout,
            0.94
        )

    def _browse(self, sender, event_args):
        dialog = FolderBrowserDialog()
        dialog.Description = "Select the DOC QC report folder"
        dialog.ShowNewFolderButton = True
        if os.path.isdir(self.folder_path):
            dialog.SelectedPath = self.folder_path
        dialog_result = dialog.ShowDialog(self)
        if dialog_result == DialogResult.OK:
            self.folder_path = dialog.SelectedPath
            self.folder_text.Text = self.folder_path
            self.folder_text.SelectionStart = len(self.folder_path)
            self.folder_text.ScrollToCaret()
            self.set_tip(self.folder_text, self.folder_path)
            try:
                write_latest_export_folder(self.reports_dir, self.folder_path)
            except Exception:
                pass
        else:
            self.result = None
            self.DialogResult = DialogResult.Cancel
            self.Close()
        dialog.Dispose()

    def _confirm(self, sender, event_args):
        if self.scope_combo.SelectedIndex != 0:
            MessageBox.Show(
                self,
                u"현재 DOC QC 검사 엔진은 Current Project 범위만 지원합니다.",
                "Review Scope", MessageBoxButtons.OK, MessageBoxIcon.Information
            )
            self.scope_combo.SelectedIndex = 0
            return
        if not (
            self.sheet_check.Checked or self.view_check.Checked
            or self.parameter_check.Checked
        ):
            MessageBox.Show(
                self, u"하나 이상의 QC Category를 선택하세요.",
                "QC Categories", MessageBoxButtons.OK, MessageBoxIcon.Warning
            )
            return
        full_csv = self.style_combo.SelectedIndex == 0
        summary_csv = True
        styled_xlsx = self.xlsx_check.Checked
        valid, error = validate_export_folder(self.folder_path)
        if not valid:
            MessageBox.Show(
                self, error, "Output Options",
                MessageBoxButtons.OK, MessageBoxIcon.Warning
            )
            return
        formats = []
        if full_csv:
            formats.append(u"Full CSV")
        formats.append(u"Summary CSV")
        if styled_xlsx:
            formats.append(u"Styled XLSX Report")
        self.result = {
            "folder": self.folder_path,
            "full_csv": full_csv,
            "summary_csv": summary_csv,
            "styled_xlsx": styled_xlsx,
            "selected_formats": formats,
            "folder_history_error": u"",
            "review_scope": u"Current Project",
            "qc_categories": {
                "sheet_qc": self.sheet_check.Checked,
                "view_qc": self.view_check.Checked,
                "parameter_qc": self.parameter_check.Checked,
                "naming_qc": True,
                "view_placement_qc": True
            },
            "report_style": (
                u"Full + Summary" if full_csv else u"Summary Only"
            ),
            "open_report_after_run": self.open_check.Checked,
            "pdf_summary": False
        }
        self.DialogResult = DialogResult.OK
        self.Close()


class QcLiteDashboardForm(QcFormBase):
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
        self._dashboard_cleanup_done = False
        self._dashboard_hover_bindings = []
        self._dashboard_fonts = [
            get_font(17.0, FontStyle.Bold),
            get_font(12.0, FontStyle.Bold),
            get_font(9.5, FontStyle.Bold),
            get_font(20.0, FontStyle.Bold),
            get_font(13.5, FontStyle.Bold),
            get_font(9.0),
            get_font(11.0, FontStyle.Bold),
            get_font(18.0, FontStyle.Bold),
            get_font(9.5)
        ]
        self.title_font = self._dashboard_fonts[0]
        self.project_font = self._dashboard_fonts[1]
        self.card_title_font = self._dashboard_fonts[2]
        self.card_count_font = self._dashboard_fonts[3]
        self.stat_font = self._dashboard_fonts[4]
        self.small_font = self._dashboard_fonts[5]
        self.issue_title_font = self._dashboard_fonts[6]
        self.neutral_count_font = self._dashboard_fonts[7]
        self.table_body_font = self._dashboard_fonts[8]
        display_issue_count = min(5, len(key_issue_rows))
        self.Text = "Revit QC - QC Lite Dashboard"
        self.ClientSize = Size(
            1120,
            760 + max(0, display_issue_count - 3) * 20
        )
        self.MinimumSize = Size(980, 720)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY
        self.Font = self.small_font
        self.AutoScaleMode = AutoScaleMode.Dpi
        self.tool_tip = configure_tooltip(ToolTip())

        main = TableLayoutPanel()
        self.root_layout = main
        main.Dock = DockStyle.Fill
        main.Padding = Padding(
            OUTER_MARGIN,
            HEADER_TOP_PADDING,
            OUTER_MARGIN,
            OUTER_MARGIN
        )
        main.ColumnCount = 1
        main.RowCount = 5
        main.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))
        self.Controls.Add(main)
        header_panel = TableLayoutPanel()
        header_panel.Dock = DockStyle.Fill
        header_panel.AutoSize = True
        header_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header_panel.ColumnCount = 1
        header_panel.RowCount = 2
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        main.Controls.Add(header_panel, 0, 0)
        title = Label()
        title.Text = u"QC Lite Dashboard"
        title.Dock = DockStyle.Fill
        title.AutoSize = True
        title.Font = self.title_font
        title.ForeColor = NAVY
        title.Margin = Padding(0)
        header_panel.Controls.Add(title, 0, 0)
        project = Label()
        project.Text = u"{0}".format(project_name)
        project.Dock = DockStyle.Fill
        project.AutoSize = True
        project.AutoEllipsis = True
        project.Font = self.project_font
        project.ForeColor = MUTED
        project.Margin = Padding(0, 5, 0, 0)
        header_panel.Controls.Add(project, 0, 1)
        self.set_tip(project, project.Text)

        cards = TableLayoutPanel()
        self.summary_cards = cards
        cards.Dock = DockStyle.Top
        cards.AutoSize = True
        cards.AutoSizeMode = AutoSizeMode.GrowAndShrink
        cards.Margin = Padding(0, 22, 0, 0)
        cards.ColumnCount = 4
        for _index in range(4):
            cards.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25.0))
        main.Controls.Add(cards, 0, 1)
        cards.Controls.Add(self._card(
            "SHEET QC", summary_data.get("sheet_issues", 0),
            u"{0} sheets".format(summary_data.get("checked_sheets", 0))
        ), 0, 0)
        cards.Controls.Add(self._card(
            "VIEW QC", summary_data.get("view_issues", 0),
            u"{0} views".format(summary_data.get("checked_views", 0))
        ), 1, 0)
        cards.Controls.Add(self._card(
            "PARAMETER QC",
            summary_data.get("parameter_issues", 0),
            "QC Lite에 포함"
        ), 2, 0)
        scan_card = self._card("SCAN QC", u"—", "Not Run", False)
        cards.Controls.Add(scan_card, 3, 0)
        self.set_tip(scan_card, u"Scan QC에서 별도 검토합니다.")

        counts = TableLayoutPanel()
        self.issue_stats = counts
        counts.Dock = DockStyle.Top
        counts.AutoSize = True
        counts.AutoSizeMode = AutoSizeMode.GrowAndShrink
        counts.MinimumSize = Size(0, 64)
        counts.MaximumSize = Size(0, 64)
        counts.ColumnCount = 7
        counts.RowCount = 1
        counts.Margin = Padding(4, 0, 4, 0)
        counts.BackColor = ORANGE_LIGHT
        for column_index in range(7):
            if column_index % 2 == 0:
                counts.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25.0))
            else:
                counts.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 1.0))
        count_values = [
            (u"ISSUE COUNT", summary_data.get("total_issues", 0)),
            (u"HIGH", summary_data.get("high_count", 0)),
            (u"MEDIUM", summary_data.get("medium_count", 0)),
            (u"LOW", summary_data.get("low_count", 0))
        ]
        for column_index, count_value in enumerate(count_values):
            counts.Controls.Add(
                self._stat_cell(count_value[0], count_value[1]),
                column_index * 2,
                0
            )
            if column_index < 3:
                separator = Panel()
                separator.Dock = DockStyle.Fill
                separator.Margin = Padding(0, 12, 0, 12)
                separator.BackColor = SEPARATOR_COLOR
                counts.Controls.Add(separator, column_index * 2 + 1, 0)
        main.Controls.Add(counts, 0, 2)

        issue_group = self.make_group(u"")
        self.top_issues_group = issue_group
        issue_group.Margin = Padding(0, 0, 0, 18)
        issue_content = TableLayoutPanel()
        issue_content.Dock = DockStyle.Top
        issue_content.AutoSize = True
        issue_content.AutoSizeMode = AutoSizeMode.GrowAndShrink
        issue_content.Padding = Padding(14, 8, 14, 10)
        issue_content.ColumnCount = 1
        issue_content.RowCount = 2
        issue_content.RowStyles.Add(RowStyle(SizeType.Absolute, 70.0))
        issue_content.RowStyles.Add(RowStyle(SizeType.AutoSize))
        issue_group.Controls.Add(issue_content)
        main.Controls.Add(issue_group, 0, 3)

        issue_actions = TableLayoutPanel()
        self.top_issues_header = issue_actions
        issue_actions.Dock = DockStyle.Fill
        issue_actions.ColumnCount = 2
        issue_actions.RowCount = 2
        issue_actions.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        issue_actions.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 96.0))
        issue_actions.RowStyles.Add(RowStyle(SizeType.Absolute, 44.0))
        issue_actions.RowStyles.Add(RowStyle(SizeType.Absolute, 26.0))
        issue_actions.Margin = Padding(0)
        issue_content.Controls.Add(issue_actions, 0, 0)
        issue_title = Label()
        issue_title.Text = u"Top Issues"
        issue_title.Dock = DockStyle.Fill
        issue_title.Font = self.issue_title_font
        issue_title.ForeColor = NAVY
        issue_title.TextAlign = ContentAlignment.MiddleLeft
        issue_title.Margin = Padding(0)
        issue_actions.Controls.Add(issue_title, 0, 0)
        issue_note = Label()
        issue_note.Text = u"심각도가 높은 주요 항목을 최대 5개 표시"
        issue_note.Dock = DockStyle.Fill
        issue_note.ForeColor = MUTED
        issue_note.Font = self.small_font
        issue_note.TextAlign = ContentAlignment.MiddleLeft
        issue_note.Margin = Padding(0)
        issue_note.AutoSize = True
        issue_actions.Controls.Add(issue_note, 0, 1)
        issue_actions.SetColumnSpan(issue_note, 2)
        details = Button()
        details.Text = u"Details"
        details.AutoSize = False
        details.Dock = getattr(DockStyle, "None")
        details.Size = Size(96, 36)
        details.Margin = Padding(0, 4, 0, 4)
        details.Enabled = callable(details_callback)
        self.style_button(details)
        self._dashboard_hover_bindings.append(
            attach_border_hover(details)
        )
        details.Click += self._show_details
        issue_actions.Controls.Add(details, 1, 0)
        self.set_tip(details, u"pyRevit Output에서 상세 QC 결과와 Export 상태를 확인합니다.")

        issue_layout = TableLayoutPanel()
        self.top_issues_table = issue_layout
        self.top_issues_header_labels = []
        issue_layout.Dock = DockStyle.Top
        issue_layout.AutoSize = True
        issue_layout.AutoSizeMode = AutoSizeMode.GrowAndShrink
        issue_layout.Padding = Padding(0)
        issue_layout.Margin = Padding(0)
        issue_layout.ColumnCount = 4
        issue_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 96.0))
        issue_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 126.0))
        issue_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        issue_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 150.0))
        rows = key_issue_rows[:5]
        issue_layout.RowCount = 1 + max(1, len(rows))
        issue_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 38.0))
        for _index in range(max(1, len(rows))):
            issue_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 46.0))
        issue_content.Controls.Add(issue_layout, 0, 1)
        for column_index, header_text in enumerate([
            u"SEVERITY", u"CATEGORY", u"ITEM", u"QC ITEM"
        ]):
            header_label = Label()
            header_label.Text = header_text
            header_label.Dock = DockStyle.Fill
            header_label.AutoSize = False
            header_label.AutoEllipsis = False
            header_label.UseCompatibleTextRendering = False
            header_label.Font = self.card_title_font
            header_label.ForeColor = MUTED
            header_label.BackColor = TABLE_HEADER_COLOR
            header_label.TextAlign = ContentAlignment.MiddleLeft
            header_label.Padding = Padding(10, 0, 8, 0)
            header_label.Margin = Padding(1)
            issue_layout.Controls.Add(header_label, column_index, 0)
            self.top_issues_header_labels.append(header_label)
        if rows:
            for index, row in enumerate(rows):
                values = [row[3], row[0], row[2], row[4]]
                for column_index, value in enumerate(values):
                    label = Label()
                    label.Text = u"{0}".format(value)
                    label.Dock = DockStyle.Fill
                    label.AutoSize = False
                    label.AutoEllipsis = column_index == 2
                    label.UseCompatibleTextRendering = False
                    label.TextAlign = ContentAlignment.MiddleLeft
                    label.Padding = Padding(10, 0, 8, 0)
                    label.Margin = Padding(1)
                    label.BackColor = (
                        RED_LIGHT
                        if column_index == 0 and row[3] == u"High"
                        else Color.White
                    )
                    label.Font = (
                        self.card_title_font
                        if column_index == 0
                        else self.table_body_font
                    )
                    issue_layout.Controls.Add(label, column_index, index + 1)
                    self.set_tip(label, label.Text)
        else:
            label = Label()
            label.Text = "표시할 주요 Issue가 없습니다."
            label.Dock = DockStyle.Fill
            label.TextAlign = ContentAlignment.MiddleCenter
            label.ForeColor = MUTED
            issue_layout.Controls.Add(label, 0, 1)
            issue_layout.SetColumnSpan(label, 4)

        footer_panel = Panel()
        self.dashboard_footer = footer_panel
        footer_panel.Dock = DockStyle.Bottom
        footer_panel.AutoSize = False
        footer_panel.Height = FOOTER_HEIGHT
        footer_panel.MinimumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.MaximumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.Padding = Padding(0, 10, 0, 14)
        main.Controls.Add(footer_panel, 0, 4)
        buttons = FlowLayoutPanel()
        buttons.Dock = DockStyle.Right
        buttons.AutoSize = False
        buttons.Width = FOOTER_BUTTON_WIDTH * 3 + BUTTON_GAP * 2
        buttons.FlowDirection = FlowDirection.LeftToRight
        buttons.WrapContents = False
        buttons.Padding = Padding(0)
        footer_panel.Controls.Add(buttons)
        dock_none = getattr(DockStyle, "None")
        doc_qc = Button()
        doc_qc.Text = "DOC QC"
        doc_qc.AutoSize = False
        doc_qc.Dock = dock_none
        doc_qc.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        doc_qc.Margin = Padding(0, 0, BUTTON_GAP, 0)
        doc_qc.TextAlign = ContentAlignment.MiddleCenter
        doc_qc.UseCompatibleTextRendering = False
        self.style_button(doc_qc)
        self._dashboard_hover_bindings.append(
            attach_border_hover(doc_qc)
        )
        doc_qc.Click += self._doc_qc_guide
        buttons.Controls.Add(doc_qc)
        report = Button()
        report.Text = "Report"
        report.AutoSize = False
        report.Dock = dock_none
        report.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        report.Margin = Padding(0, 0, BUTTON_GAP, 0)
        report.TextAlign = ContentAlignment.MiddleCenter
        report.UseCompatibleTextRendering = False
        report.Enabled = bool(report_path)
        self.style_button(report)
        self._dashboard_hover_bindings.append(
            attach_border_hover(report)
        )
        report.Click += self._open_report
        buttons.Controls.Add(report)
        close = Button()
        close.Text = "Close"
        close.AutoSize = False
        close.Dock = dock_none
        close.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        close.Margin = Padding(0)
        close.TextAlign = ContentAlignment.MiddleCenter
        close.UseCompatibleTextRendering = False
        close.DialogResult = DialogResult.OK
        self.style_button(close, True)
        buttons.Controls.Add(close)
        self.AcceptButton = close
        self.Shown += self._dashboard_shown
        self.ResumeLayout(True)
        self.PerformLayout()

    def cleanup(self):
        if self._dashboard_cleanup_done:
            return
        self._dashboard_cleanup_done = True
        try:
            self.Shown -= self._dashboard_shown
        except Exception:
            pass
        for binding in self._dashboard_hover_bindings:
            detach_border_hover(binding)
        self._dashboard_hover_bindings = []
        QcFormBase.cleanup(self)
        for font in self._dashboard_fonts:
            try:
                font.Dispose()
            except Exception:
                pass
        self._dashboard_fonts = []

    def _dashboard_shown(self, sender, event_args):
        try:
            self.PerformLayout()
            root_preferred = self.root_layout.GetPreferredSize(Size(0, 0))
            working_area = Screen.FromControl(self).WorkingArea
            maximum_width = int(working_area.Width * 0.92)
            maximum_height = int(working_area.Height * 0.92)
            desired_width = min(
                maximum_width,
                max(1120, root_preferred.Width + OUTER_MARGIN * 2)
            )
            desired_height = min(
                maximum_height,
                max(760, root_preferred.Height + OUTER_MARGIN)
            )
            if (
                self.ClientSize.Width != desired_width
                or self.ClientSize.Height != desired_height
            ):
                self.ClientSize = Size(desired_width, desired_height)
                self.PerformLayout()
            left = min(
                max(self.Left, working_area.Left),
                max(working_area.Left, working_area.Right - self.Width)
            )
            top = min(
                max(self.Top, working_area.Top),
                max(working_area.Top, working_area.Bottom - self.Height)
            )
            if self.Left != left or self.Top != top:
                self.Location = Point(left, top)
        except Exception:
            pass
        if self.diagnostic_log_path:
            self._write_layout_diagnostics(sender, event_args)

    def _write_layout_diagnostics(self, sender, event_args):
        if not self.diagnostic_log_path:
            return
        try:
            self.PerformLayout()
            log_folder = os.path.dirname(self.diagnostic_log_path)
            if log_folder and not os.path.isdir(log_folder):
                os.makedirs(log_folder)
            lines = [
                u"[{0}] dashboard_layout".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                u"module={0}".format(__file__),
                u"class={0}".format(self.__class__.__name__),
                u"build={0}".format(QC_LITE_DASHBOARD_BUILD),
                u"client_size={0}x{1}".format(
                    self.ClientSize.Width,
                    self.ClientSize.Height
                ),
                u"device_dpi={0}".format(getattr(self, "DeviceDpi", u"N/A")),
                u"auto_scale_mode={0}".format(self.AutoScaleMode)
            ]
            root_preferred = self.root_layout.GetPreferredSize(Size(0, 0))
            lines.append(
                u"root_preferred={0}x{1}".format(
                    root_preferred.Width,
                    root_preferred.Height
                )
            )
            for row_index, row_style in enumerate(self.root_layout.RowStyles):
                lines.append(
                    u"root_row_{0}=type:{1},height:{2}".format(
                        row_index,
                        row_style.SizeType,
                        row_style.Height
                    )
                )
            for name, control in [
                (u"root", self.root_layout),
                (u"summary_cards", self.summary_cards),
                (u"issue_stats", self.issue_stats),
                (u"top_issues_group", self.top_issues_group),
                (u"top_issues_header", self.top_issues_header),
                (u"top_issues_table", self.top_issues_table),
                (u"footer", self.dashboard_footer)
            ]:
                lines.append(self._diagnostic_control_line(name, control))
            for index, label in enumerate(self.top_issues_header_labels):
                lines.append(
                    self._diagnostic_control_line(
                        u"table_header_{0}".format(index),
                        label
                    )
                )
            label_index = 0
            for control in self._walk_controls(self.root_layout):
                if isinstance(control, Label):
                    lines.append(
                        self._diagnostic_control_line(
                            u"label_{0}:{1}".format(
                                label_index,
                                control.Text
                            ),
                            control
                        )
                    )
                    label_index += 1
            root_screen_left = self.root_layout.PointToScreen(Point(0, 0)).X
            rightmost = 0
            for control in self._walk_controls(self.root_layout):
                control_right = control.PointToScreen(
                    Point(control.Width, 0)
                ).X - root_screen_left
                rightmost = max(rightmost, control_right)
            lines.append(u"rightmost_child={0}".format(rightmost))
            with io.open(
                self.diagnostic_log_path,
                "a",
                encoding="utf-8"
            ) as log_file:
                log_file.write(u"\n".join(lines) + u"\n")
        except Exception:
            pass

    def _diagnostic_control_line(self, name, control):
        bounds = control.Bounds
        preferred = control.PreferredSize
        return (
            u"{0}=bounds:{1},{2},{3},{4};preferred:{5}x{6};"
            u"autosize:{7};dock:{8};anchor:{9}"
        ).format(
            name,
            bounds.X,
            bounds.Y,
            bounds.Width,
            bounds.Height,
            preferred.Width,
            preferred.Height,
            control.AutoSize,
            control.Dock,
            control.Anchor
        )

    def _walk_controls(self, parent):
        for control in parent.Controls:
            yield control
            for child in self._walk_controls(control):
                yield child

    def _card(self, title, count, note, emphasize_count=True):
        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.MinimumSize = Size(0, 110)
        card.MaximumSize = Size(0, 110)
        card.Margin = Padding(5, 6, 5, 8)
        card.Padding = Padding(12, 10, 12, 10)
        card.BackColor = LIGHT
        card.CellBorderStyle = TableLayoutPanelCellBorderStyle.Single
        card.ColumnCount = 1
        card.RowCount = 3
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 34.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 26.0))
        title_label = Label()
        title_label.Text = title
        title_label.Dock = DockStyle.Fill
        title_label.AutoSize = False
        title_label.AutoEllipsis = False
        title_label.UseCompatibleTextRendering = False
        title_label.Font = self.card_title_font
        title_label.TextAlign = ContentAlignment.MiddleLeft
        card.Controls.Add(title_label, 0, 0)
        count_label = Label()
        count_label.Text = u"{0}".format(count)
        count_label.Dock = DockStyle.Fill
        count_label.AutoSize = False
        count_label.AutoEllipsis = False
        count_label.UseCompatibleTextRendering = False
        count_label.Font = (
            self.card_count_font if emphasize_count else self.neutral_count_font
        )
        count_label.ForeColor = ORANGE if emphasize_count else MUTED
        count_label.TextAlign = ContentAlignment.MiddleLeft
        card.Controls.Add(count_label, 0, 1)
        note_label = Label()
        note_label.Text = note
        note_label.Dock = DockStyle.Fill
        note_label.AutoSize = False
        note_label.AutoEllipsis = False
        note_label.UseCompatibleTextRendering = False
        note_label.ForeColor = MUTED
        note_label.Font = self.small_font
        note_label.TextAlign = ContentAlignment.MiddleLeft
        card.Controls.Add(note_label, 0, 2)
        return card

    def _stat_cell(self, title, value):
        cell = TableLayoutPanel()
        cell.Dock = DockStyle.Fill
        cell.AutoSize = True
        cell.AutoSizeMode = AutoSizeMode.GrowAndShrink
        cell.Padding = Padding(0, 20, 0, 20)
        cell.ColumnCount = 2
        cell.RowCount = 1
        cell.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 62.0))
        cell.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 38.0))
        cell.Margin = Padding(0)
        title_label = Label()
        title_label.Text = title
        title_label.Dock = DockStyle.Fill
        title_label.AutoSize = False
        title_label.AutoEllipsis = False
        title_label.UseCompatibleTextRendering = False
        title_label.Font = self.card_title_font
        title_label.TextAlign = ContentAlignment.MiddleLeft
        title_label.ForeColor = NAVY
        title_label.Padding = Padding(16, 0, 4, 0)
        cell.Controls.Add(title_label, 0, 0)
        value_label = Label()
        value_label.Text = u"{0}".format(value)
        value_label.Dock = DockStyle.Fill
        value_label.AutoSize = False
        value_label.AutoEllipsis = False
        value_label.UseCompatibleTextRendering = False
        value_label.Font = self.stat_font
        value_label.ForeColor = ORANGE
        value_label.TextAlign = ContentAlignment.MiddleRight
        value_label.Padding = Padding(4, 0, 16, 0)
        cell.Controls.Add(value_label, 1, 0)
        minimum_height = max(
            title_label.PreferredSize.Height,
            value_label.PreferredSize.Height
        ) + cell.Padding.Vertical
        cell.MinimumSize = Size(0, minimum_height)
        return cell

    def _show_details(self, sender, event_args):
        if not callable(self.details_callback):
            return
        try:
            self.details_callback()
        except Exception as ex:
            MessageBox.Show(
                self,
                u"상세 QC 결과를 열 수 없습니다.\r\n{0}".format(ex),
                "QC Lite Details",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _open_report(self, sender, event_args):
        opened, error = open_file(self.report_path)
        if not opened:
            MessageBox.Show(
                self, error, "Open Report",
                MessageBoxButtons.OK, MessageBoxIcon.Warning
            )

    def _doc_qc_guide(self, sender, event_args):
        MessageBox.Show(
            self,
            u"전체 검토는 Revit QC 탭의 DOC QC 버튼을 실행하세요.",
            "DOC QC", MessageBoxButtons.OK, MessageBoxIcon.Information
        )


def request_doc_qc_options(reports_dir, active_config_display):
    close_profile = create_ui_close_profile(u"DOC QC")
    form = DocQcSetupForm(
        read_latest_export_folder(reports_dir), active_config_display
    )
    form.reports_dir = reports_dir
    close_profile.attach(form)
    try:
        dialog_result = close_profile.show_dialog()
        result = form.result
    finally:
        close_profile.dispose()
    if dialog_result != DialogResult.OK or result is None:
        return None
    try:
        write_latest_export_folder(reports_dir, result["folder"])
    except Exception as ex:
        result["folder_history_error"] = u"{0}".format(ex)
    return result


def show_qc_lite_dashboard(
    project_name,
    summary_data,
    key_issue_rows,
    report_path,
    details_callback=None,
    diagnostic_log_path=None
):
    from qc_lite_dashboard import QcLiteDashboardForm as RuntimeDashboardForm

    close_profile = create_ui_close_profile(u"QC Lite")
    form = RuntimeDashboardForm(
        project_name,
        summary_data,
        key_issue_rows,
        report_path,
        details_callback,
        diagnostic_log_path
    )
    close_profile.attach(form)
    try:
        close_profile.show_dialog()
    finally:
        close_profile.dispose()
