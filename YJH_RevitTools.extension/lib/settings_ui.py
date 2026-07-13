# -*- coding: utf-8 -*-

import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Diagnostics import Process, ProcessStartInfo
from System.Drawing import (
    Color,
    ContentAlignment,
    FontStyle,
    Point,
    Size
)
from System.Windows.Forms import (
    AnchorStyles,
    AutoScaleMode,
    AutoSizeMode,
    Button,
    ColumnStyle,
    ComboBox,
    ComboBoxStyle,
    DialogResult,
    DockStyle,
    FlatStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    FlowDirection,
    FlowLayoutPanel,
    GroupBox,
    Label,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    OpenFileDialog,
    Padding,
    Panel,
    RowStyle,
    Screen,
    SizeType,
    TableLayoutPanel,
    ToolTip
)

from config_loader import (
    calculate_rule_summary,
    duplicate_qc_preset,
    list_qc_presets,
    load_config,
    save_local_active_config,
    save_local_external_python_path
)
from exporters import get_xlsx_environment_status, probe_external_python_path
from report_history import open_file
from report_ui import html_escape
from ui_close_profiler import create_ui_close_profile, log_section_snapshots
from qc_ui_style import (
    BUTTON_GAP,
    BUTTON_HEIGHT,
    HEADER_TOP_PADDING,
    OUTER_MARGIN,
    ROW_GAP,
    SETTINGS_FOOTER_BUTTON_HEIGHT,
    SETTINGS_FOOTER_BUTTON_WIDTH,
    SECTION_GAP,
    apply_scan_reference_section_style,
    apply_primary_button_style,
    apply_secondary_button_style,
    configure_content_scroll,
    get_preferred_font
)


WARNING_FILL_COLOR = Color.FromArgb(255, 243, 232)
SETTINGS_NAVY_COLOR = Color.FromArgb(30, 45, 61)
SETTINGS_MUTED_COLOR = Color.FromArgb(100, 116, 135)
SETTINGS_ORANGE_COLOR = Color.FromArgb(242, 140, 40)
SETTINGS_ORANGE_LIGHT_COLOR = Color.FromArgb(255, 244, 234)
SETTINGS_CARD_COLOR = Color.FromArgb(246, 248, 250)
SETTINGS_BORDER_COLOR = Color.FromArgb(216, 222, 229)
READY_COLOR = Color.FromArgb(22, 136, 58)
WARNING_COLOR = Color.FromArgb(200, 95, 26)
SETTINGS_FOOTER_HEIGHT = 64
SETTINGS_FOOTER_BUTTON_GAP = 12
SETTINGS_INNER_PADDING = 14

def is_codex_runtime_path(python_path):
    normalized_path = (python_path or u"").replace(u"/", u"\\").lower()
    return (
        u"\\codex-runtimes\\" in normalized_path
        or u"\\.cache\\codex" in normalized_path
    )


def open_folder(folder_path):
    if not folder_path or not os.path.isdir(folder_path):
        return False, u"Folder was not found: {0}".format(folder_path)

    try:
        start_info = ProcessStartInfo()
        start_info.FileName = folder_path
        start_info.UseShellExecute = True
        Process.Start(start_info)
        return True, u""
    except Exception as ex:
        return False, u"Folder could not be opened: {0}".format(ex)


class QCSettingsForm(Form):
    def __init__(
        self,
        output,
        default_config_path,
        local_config_path,
        extension_dir,
        reports_dir
    ):
        Form.__init__(self)
        self.SuspendLayout()
        self.output = output
        self.default_config_path = default_config_path
        self.local_config_path = local_config_path
        self.config_folder = os.path.dirname(default_config_path)
        self.extension_dir = extension_dir
        self.reports_dir = reports_dir
        self.helper_path = os.path.join(
            extension_dir,
            "tools",
            "make_styled_xlsx.py"
        )
        self.debug_log_path = os.path.join(
            reports_dir,
            "xlsx_helper_debug.log"
        )
        self.presets = []
        self.selected_python_path = u""
        self._secondary_buttons = []
        self._apply_rule_button = None
        self._cleanup_done = False

        self.title_font = get_preferred_font(17.0, FontStyle.Bold)
        self.subtitle_font = get_preferred_font(9.5, FontStyle.Regular)
        self.section_font = get_preferred_font(10.5, FontStyle.Bold)
        self.label_font = get_preferred_font(10.0, FontStyle.Regular)
        self.label_bold_font = get_preferred_font(10.0, FontStyle.Bold)
        self.helper_font = get_preferred_font(9.0, FontStyle.Regular)
        self.button_font = get_preferred_font(9.5, FontStyle.Regular)
        self.status_font = get_preferred_font(13.0, FontStyle.Bold)
        self.rule_count_font = get_preferred_font(21.0, FontStyle.Bold)
        self.active_header_font = get_preferred_font(8.5, FontStyle.Bold)
        self.tooltip = ToolTip()
        self.tooltip.AutoPopDelay = 9000
        self.tooltip.InitialDelay = 450
        self.tooltip.ReshowDelay = 120
        self.tooltip.ShowAlways = True

        self.Text = "Revit QC Settings"
        self.ClientSize = Size(1120, 980)
        self.MinimumSize = Size(1040, 900)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = SETTINGS_NAVY_COLOR
        self.Font = self.label_font
        self.AutoScaleMode = AutoScaleMode.Dpi

        self.root_layout = TableLayoutPanel()
        self.root_layout.Dock = DockStyle.Fill
        self.root_layout.Padding = Padding(
            OUTER_MARGIN,
            HEADER_TOP_PADDING,
            OUTER_MARGIN,
            OUTER_MARGIN
        )
        self.root_layout.ColumnCount = 1
        self.root_layout.RowCount = 3
        self.root_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 100.0)
        )
        self.root_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.main_row_style = RowStyle(SizeType.AutoSize)
        self.root_layout.RowStyles.Add(self.main_row_style)
        self.root_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.Controls.Add(self.root_layout)

        header_panel = TableLayoutPanel()
        header_panel.Dock = DockStyle.Fill
        header_panel.AutoSize = True
        header_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header_panel.Margin = Padding(0)
        header_panel.Padding = Padding(0)
        header_panel.ColumnCount = 1
        header_panel.RowCount = 2
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.root_layout.Controls.Add(header_panel, 0, 0)

        title_label = Label()
        title_label.Text = u"QC Settings"
        title_label.Dock = DockStyle.Fill
        title_label.AutoSize = True
        title_label.Font = self.title_font
        title_label.ForeColor = SETTINGS_NAVY_COLOR
        title_label.Margin = Padding(0)
        header_panel.Controls.Add(title_label, 0, 0)

        subtitle_label = Label()
        subtitle_label.Text = u"Excel Report 실행 환경과 QC Rule Set을 관리합니다."
        subtitle_label.Dock = DockStyle.Fill
        subtitle_label.AutoSize = True
        subtitle_label.Font = self.subtitle_font
        subtitle_label.ForeColor = SETTINGS_MUTED_COLOR
        subtitle_label.Margin = Padding(0, 6, 0, 0)
        header_panel.Controls.Add(subtitle_label, 0, 1)

        self.main_panel = Panel()
        self.main_panel.Dock = DockStyle.Top
        self.main_panel.AutoSize = True
        self.main_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        self.main_panel.AutoScroll = False
        self.main_panel.BackColor = Color.White
        self.main_panel.Margin = Padding(0, 20, 0, 0)
        self.root_layout.Controls.Add(self.main_panel, 0, 1)

        self.main_layout = TableLayoutPanel()
        self.main_layout.Dock = DockStyle.Top
        self.main_layout.AutoSize = True
        self.main_layout.Padding = Padding(0)
        self.main_layout.ColumnCount = 1
        self.main_layout.RowCount = 3
        self.main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        self.main_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.main_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.main_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.main_panel.Controls.Add(self.main_layout)

        self._build_report_setup()
        self._build_preset_section()
        self._build_rule_summary()
        self._build_advanced_actions()
        self._reload_all()
        self.Shown += self._configure_scroll_fallback
        self.ResumeLayout(True)
        self.PerformLayout()

    def _build_report_setup(self):
        group = self._create_group("Excel Report")
        group.MinimumSize = Size(0, 0)
        self.main_layout.Controls.Add(group, 0, 0)
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.AutoSize = True
        layout.Margin = Padding(0)
        layout.Padding = Padding(
            SETTINGS_INNER_PADDING, 8, SETTINGS_INNER_PADDING, 8
        )
        layout.ColumnCount = 1
        layout.RowCount = 4
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 52.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 122.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 46.0))
        self.warning_row_style = RowStyle(SizeType.Absolute, 48.0)
        layout.RowStyles.Add(self.warning_row_style)
        group.Controls.Add(layout)

        path_layout = TableLayoutPanel()
        path_layout.Dock = DockStyle.Fill
        path_layout.Margin = Padding(0)
        path_layout.ColumnCount = 3
        path_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 100.0))
        path_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        path_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 132.0))
        layout.Controls.Add(path_layout, 0, 0)

        path_label = self._create_label("Python:", True)
        path_layout.Controls.Add(path_label, 0, 0)
        self.current_python_name = Label()
        self.current_python_name.Dock = DockStyle.Fill
        self.current_python_name.AutoSize = False
        self.current_python_name.AutoEllipsis = True
        self.current_python_name.Font = self.label_bold_font
        self.current_python_name.ForeColor = SETTINGS_NAVY_COLOR
        self.current_python_name.TextAlign = ContentAlignment.MiddleLeft
        self.current_python_name.Padding = Padding(4, 0, 4, 0)
        path_layout.Controls.Add(self.current_python_name, 1, 0)

        browse_button = self._create_button("Set Python", self._browse_python)
        browse_button.Dock = getattr(DockStyle, "None")
        browse_button.Anchor = getattr(AnchorStyles, "None")
        browse_button.Size = Size(132, 40)
        browse_button.Margin = Padding(0)
        self.tooltip.SetToolTip(
            browse_button,
            u"Styled Excel Report 생성에 사용할 외부 Python 경로를 지정합니다."
        )
        path_layout.Controls.Add(browse_button, 2, 0)

        status_layout = TableLayoutPanel()
        status_layout.Dock = DockStyle.Fill
        status_layout.Margin = Padding(0)
        status_layout.ColumnCount = 3
        status_layout.RowCount = 1
        for column_index in range(3):
            status_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 33.333))
        layout.Controls.Add(status_layout, 0, 1)
        self.python_status = self._add_status_card(status_layout, 0, "Python")
        self.openpyxl_status = self._add_status_card(
            status_layout,
            1,
            "Excel Library"
        )
        self.excel_status = self._add_status_card(status_layout, 2, "Excel Report")

        self.python_warning = Label()
        self.python_warning.Dock = DockStyle.Fill
        self.python_warning.AutoSize = False
        self.python_warning.AutoEllipsis = False
        self.python_warning.Font = self.helper_font
        self.python_warning.ForeColor = WARNING_COLOR
        self.python_warning.Padding = Padding(8, 8, 8, 0)
        self.python_warning.Margin = Padding(0, 0, 0, 12)
        layout.Controls.Add(self.python_warning, 0, 3)

        action_layout = TableLayoutPanel()
        action_layout.Dock = DockStyle.Fill
        action_layout.Margin = Padding(0)
        action_layout.ColumnCount = 4
        action_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        action_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, 112.0)
        )
        action_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, float(BUTTON_GAP))
        )
        action_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, 112.0)
        )
        layout.Controls.Add(action_layout, 0, 2)
        test_button = self._create_button("Test", self._test_environment)
        test_button.Dock = getattr(DockStyle, "None")
        test_button.Anchor = AnchorStyles.Top | AnchorStyles.Left
        test_button.Size = Size(112, 40)
        test_button.Margin = Padding(0, 6, 0, 0)
        self.tooltip.SetToolTip(
            test_button,
            u"현재 Python과 Excel Library 실행 상태를 검사합니다."
        )
        action_layout.Controls.Add(test_button, 1, 0)
        clear_button = self._create_button("Clear", self._clear_python_path)
        clear_button.Dock = getattr(DockStyle, "None")
        clear_button.Anchor = AnchorStyles.Top | AnchorStyles.Left
        clear_button.Size = Size(112, 40)
        clear_button.Margin = Padding(0, 6, 0, 0)
        self.tooltip.SetToolTip(
            clear_button,
            u"저장된 외부 Python 경로를 해제하고 자동 검색 상태로 되돌립니다."
        )
        action_layout.Controls.Add(clear_button, 3, 0)

    def _build_preset_section(self):
        group = self._create_group("QC Rules")
        group.MinimumSize = Size(0, 300)
        self.main_layout.Controls.Add(group, 0, 1)
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.AutoSize = True
        layout.Margin = Padding(0)
        layout.Padding = Padding(
            SETTINGS_INNER_PADDING, 8, SETTINGS_INNER_PADDING, 8
        )
        layout.ColumnCount = 1
        layout.RowCount = 6
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 54.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 32.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 12.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 96.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 16.0))
        layout.RowStyles.Add(RowStyle(SizeType.Absolute, 56.0))
        group.Controls.Add(layout)

        preset_layout = TableLayoutPanel()
        preset_layout.Dock = DockStyle.Fill
        preset_layout.Margin = Padding(0)
        preset_layout.ColumnCount = 3
        preset_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 110.0))
        preset_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        preset_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 126.0))
        layout.Controls.Add(preset_layout, 0, 0)
        preset_layout.Controls.Add(
            self._create_label("Rule Set:", True),
            0,
            0
        )
        self.preset_combo = ComboBox()
        self.preset_combo.AutoSize = False
        self.preset_combo.Dock = DockStyle.Fill
        self.preset_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.preset_combo.Font = self.label_font
        self.preset_combo.IntegralHeight = False
        self.preset_combo.ItemHeight = 24
        self.preset_combo.MinimumSize = Size(0, 38)
        self.preset_combo.Height = 38
        self.preset_combo.Margin = Padding(0, 8, 12, 8)
        self.preset_combo.SelectedIndexChanged += self._preset_selection_changed
        preset_layout.Controls.Add(self.preset_combo, 1, 0)
        set_active_button = self._create_button(
            "Apply Rule",
            self._set_active_preset
        )
        self._apply_rule_button_style(set_active_button)
        set_active_button.Dock = getattr(DockStyle, "None")
        set_active_button.Anchor = getattr(AnchorStyles, "None")
        set_active_button.Size = Size(126, 40)
        set_active_button.Margin = Padding(0)
        self.tooltip.SetToolTip(
            set_active_button,
            u"선택한 Rule Set을 현재 QC 실행 기준으로 적용합니다."
        )
        preset_layout.Controls.Add(set_active_button, 2, 0)

        instruction_label = Label()
        instruction_label.Text = "Choose the rule set before running QC."
        instruction_label.Dock = DockStyle.Fill
        instruction_label.AutoSize = False
        instruction_label.ForeColor = SETTINGS_MUTED_COLOR
        instruction_label.Font = self.helper_font
        instruction_label.Padding = Padding(4, 4, 4, 0)
        layout.Controls.Add(instruction_label, 0, 1)

        active_rule_card = self._create_active_rule_card()
        layout.Controls.Add(active_rule_card, 0, 3)

        buttons = FlowLayoutPanel()
        buttons.Dock = DockStyle.Fill
        buttons.FlowDirection = FlowDirection.LeftToRight
        buttons.WrapContents = False
        buttons.Padding = Padding(0, ROW_GAP, 0, 0)
        buttons.Margin = Padding(0)
        layout.Controls.Add(buttons, 0, 5)
        dock_none = getattr(DockStyle, "None")
        copy_button = self._create_button("Copy", self._duplicate_preset)
        copy_button.Dock = dock_none
        copy_button.Size = Size(150, 40)
        copy_button.Margin = Padding(0, 0, 12, 0)
        self.tooltip.SetToolTip(
            copy_button,
            u"선택한 Rule Set을 새 사용자 preset으로 복사합니다."
        )
        buttons.Controls.Add(copy_button)
        open_folder_button = self._create_button(
            "Open Rule Folder",
            self._open_config_folder
        )
        open_folder_button.Dock = dock_none
        open_folder_button.Size = Size(180, 40)
        open_folder_button.Margin = Padding(0, 0, 12, 0)
        self.tooltip.SetToolTip(
            open_folder_button,
            u"사용자 Rule Set JSON이 저장된 폴더를 엽니다."
        )
        buttons.Controls.Add(open_folder_button)
        reload_button = self._create_button("Reload", self._reload_presets_click)
        reload_button.Dock = dock_none
        reload_button.Size = Size(150, 40)
        reload_button.Margin = Padding(0)
        self.tooltip.SetToolTip(
            reload_button,
            u"Rule Set 파일을 다시 읽어 목록과 상태를 갱신합니다."
        )
        buttons.Controls.Add(reload_button)

    def _build_rule_summary(self):
        group = self._create_group("Rule Count")
        group.MinimumSize = Size(0, 184)
        group.Margin = Padding(0, 0, 0, 22)
        self.main_layout.Controls.Add(group, 0, 2)
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.AutoSize = True
        layout.Margin = Padding(0)
        layout.Padding = Padding(
            SETTINGS_INNER_PADDING, 8, SETTINGS_INNER_PADDING, 8
        )
        layout.ColumnCount = 4
        layout.RowCount = 1
        for column_index in range(4):
            layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25.0))
        group.Controls.Add(layout)
        self.sheet_rules_value = self._add_rule_card(layout, 0, "Sheet Rules")
        self.view_rules_value = self._add_rule_card(layout, 1, "View Rules")
        self.parameter_rules_value = self._add_rule_card(
            layout,
            2,
            "Parameter Rules"
        )
        self.required_parameters_value = self._add_rule_card(
            layout,
            3,
            "Required Params"
        )

    def _build_advanced_actions(self):
        footer_panel = Panel()
        footer_panel.Dock = DockStyle.Bottom
        footer_panel.AutoSize = False
        footer_panel.Height = SETTINGS_FOOTER_HEIGHT
        footer_panel.MinimumSize = Size(0, SETTINGS_FOOTER_HEIGHT)
        footer_panel.MaximumSize = Size(0, SETTINGS_FOOTER_HEIGHT)
        footer_panel.Padding = Padding(0, 8, 0, 14)
        footer_panel.Margin = Padding(0)
        self.root_layout.Controls.Add(footer_panel, 0, 2)

        button_strip = FlowLayoutPanel()
        button_strip.Dock = DockStyle.Right
        button_strip.AutoSize = False
        button_strip.Width = (
            SETTINGS_FOOTER_BUTTON_WIDTH * 3
            + SETTINGS_FOOTER_BUTTON_GAP * 2
        )
        button_strip.FlowDirection = FlowDirection.LeftToRight
        button_strip.WrapContents = False
        button_strip.Padding = Padding(0)
        button_strip.Margin = Padding(0)
        footer_panel.Controls.Add(button_strip)

        dock_none = getattr(DockStyle, "None")
        self.show_details_button = self._create_button(
            "Details",
            self._show_details
        )
        self.show_details_button.Dock = dock_none
        self.show_details_button.Size = Size(
            SETTINGS_FOOTER_BUTTON_WIDTH,
            SETTINGS_FOOTER_BUTTON_HEIGHT
        )
        self.show_details_button.Margin = Padding(
            0,
            0,
            SETTINGS_FOOTER_BUTTON_GAP,
            0
        )
        self.tooltip.SetToolTip(
            self.show_details_button,
            u"현재 QC 설정과 Excel 실행 환경의 상세 정보를 표시합니다."
        )
        button_strip.Controls.Add(self.show_details_button)

        open_log_button = self._create_button(
            "Open Log",
            self._open_debug_log
        )
        open_log_button.Dock = dock_none
        open_log_button.Size = Size(
            SETTINGS_FOOTER_BUTTON_WIDTH,
            SETTINGS_FOOTER_BUTTON_HEIGHT
        )
        open_log_button.Margin = Padding(
            0,
            0,
            SETTINGS_FOOTER_BUTTON_GAP,
            0
        )
        self.tooltip.SetToolTip(
            open_log_button,
            u"최근 Excel Report 실행 로그를 엽니다."
        )
        button_strip.Controls.Add(open_log_button)

        close_button = self._create_button("Close", self._close_form)
        self._apply_primary_button_style(close_button)
        close_button.Dock = dock_none
        close_button.Size = Size(
            SETTINGS_FOOTER_BUTTON_WIDTH,
            SETTINGS_FOOTER_BUTTON_HEIGHT
        )
        close_button.Margin = Padding(0)
        button_strip.Controls.Add(close_button)
        self.CancelButton = close_button

    def _create_group(self, title):
        group = GroupBox()
        apply_scan_reference_section_style(
            group,
            title,
            self.section_font,
            SECTION_GAP
        )
        return group

    def _configure_scroll_fallback(self, sender, event_args):
        self.PerformLayout()
        header = self.root_layout.GetControlFromPosition(0, 0)
        preferred_height = (
            self.root_layout.Padding.Vertical
            + header.PreferredSize.Height
            + self.main_panel.Margin.Vertical
            + self.main_layout.PreferredSize.Height
            + SETTINGS_FOOTER_HEIGHT
        )
        working_area = Screen.FromControl(self).WorkingArea
        maximum_height = int(working_area.Height * 0.94)
        target_height = min(max(preferred_height, 880), maximum_height)
        content_fits = preferred_height <= maximum_height
        if content_fits:
            self.main_row_style.SizeType = SizeType.AutoSize
            self.main_panel.AutoSize = True
            self.main_panel.Dock = DockStyle.Top
            self.main_panel.AutoScroll = False
        else:
            self.main_row_style.SizeType = SizeType.Percent
            self.main_row_style.Height = 100.0
            self.main_panel.AutoSize = False
            self.main_panel.Dock = DockStyle.Fill
        if target_height > 0 and self.ClientSize.Height != target_height:
            self.ClientSize = Size(self.ClientSize.Width, target_height)
        if not content_fits:
            configure_content_scroll(
                self,
                self.main_panel,
                self.main_layout,
                0.94
            )
        log_section_snapshots(u"QC Settings", self)

    def _create_label(self, text, bold=False):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.ForeColor = SETTINGS_NAVY_COLOR
        label.Font = self.label_bold_font if bold else self.label_font
        label.TextAlign = ContentAlignment.MiddleLeft
        label.Padding = Padding(2, 0, 6, 0)
        return label

    def _create_button(self, text, handler):
        button = Button()
        button.Text = text
        button.AutoSize = False
        button.Dock = DockStyle.Fill
        button.Margin = Padding(0)
        button.MinimumSize = Size(0, BUTTON_HEIGHT)
        button.Font = self.button_font
        button.TextAlign = ContentAlignment.MiddleCenter
        button.UseCompatibleTextRendering = False
        button.Padding = Padding(0)
        apply_secondary_button_style(button)
        button.FlatAppearance.BorderColor = SETTINGS_BORDER_COLOR
        button.FlatAppearance.MouseOverBackColor = Color.White
        button.MouseEnter += self._secondary_button_mouse_enter
        button.MouseLeave += self._secondary_button_mouse_leave
        self._secondary_buttons.append(button)
        button.Click += handler
        return button

    def _apply_primary_button_style(self, button):
        self._remove_secondary_hover(button)
        apply_primary_button_style(button)

    def _apply_rule_button_style(self, button):
        self._remove_secondary_hover(button)
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = SETTINGS_ORANGE_COLOR
        button.FlatAppearance.MouseOverBackColor = SETTINGS_ORANGE_COLOR
        button.FlatAppearance.MouseDownBackColor = SETTINGS_ORANGE_COLOR
        button.BackColor = SETTINGS_ORANGE_LIGHT_COLOR
        button.ForeColor = SETTINGS_NAVY_COLOR
        button.UseVisualStyleBackColor = False
        button.MouseEnter += self._apply_rule_mouse_enter
        button.MouseLeave += self._apply_rule_mouse_leave
        self._apply_rule_button = button

    def _secondary_button_mouse_enter(self, sender, event_args):
        sender.FlatAppearance.BorderColor = SETTINGS_ORANGE_COLOR

    def _secondary_button_mouse_leave(self, sender, event_args):
        sender.FlatAppearance.BorderColor = SETTINGS_BORDER_COLOR

    def _apply_rule_mouse_enter(self, sender, event_args):
        sender.BackColor = SETTINGS_ORANGE_COLOR
        sender.ForeColor = Color.White

    def _apply_rule_mouse_leave(self, sender, event_args):
        sender.BackColor = SETTINGS_ORANGE_LIGHT_COLOR
        sender.ForeColor = SETTINGS_NAVY_COLOR

    def _remove_secondary_hover(self, button):
        try:
            button.MouseEnter -= self._secondary_button_mouse_enter
            button.MouseLeave -= self._secondary_button_mouse_leave
        except Exception:
            pass
        if button in self._secondary_buttons:
            self._secondary_buttons.remove(button)

    def _create_active_rule_card(self):
        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.Margin = Padding(0)
        card.Padding = Padding(0)
        card.BackColor = SETTINGS_CARD_COLOR
        card.ColumnCount = 2
        card.RowCount = 1
        card.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 4.0))
        card.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        card.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))

        accent = Panel()
        accent.Dock = DockStyle.Fill
        accent.Margin = Padding(0)
        accent.BackColor = SETTINGS_ORANGE_COLOR
        card.Controls.Add(accent, 0, 0)

        content = TableLayoutPanel()
        content.Dock = DockStyle.Fill
        content.Margin = Padding(0)
        content.Padding = Padding(14, 8, 14, 8)
        content.BackColor = SETTINGS_CARD_COLOR
        content.ColumnCount = 1
        content.RowCount = 3
        content.RowStyles.Add(RowStyle(SizeType.Absolute, 22.0))
        content.RowStyles.Add(RowStyle(SizeType.Absolute, 26.0))
        content.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        card.Controls.Add(content, 1, 0)

        header = Label()
        header.Text = u"ACTIVE RULE SET"
        header.Dock = DockStyle.Fill
        header.AutoSize = False
        header.Font = self.active_header_font
        header.ForeColor = SETTINGS_ORANGE_COLOR
        header.TextAlign = ContentAlignment.MiddleLeft
        content.Controls.Add(header, 0, 0)

        self.active_rule_name = Label()
        self.active_rule_name.Text = u"Default QC"
        self.active_rule_name.Dock = DockStyle.Fill
        self.active_rule_name.AutoSize = False
        self.active_rule_name.Font = self.label_bold_font
        self.active_rule_name.ForeColor = SETTINGS_NAVY_COLOR
        self.active_rule_name.TextAlign = ContentAlignment.MiddleLeft
        content.Controls.Add(self.active_rule_name, 0, 1)

        self.preset_description = Label()
        self.preset_description.Text = (
            u"General Sheet, View, and Parameter QC preset."
        )
        self.preset_description.Dock = DockStyle.Fill
        self.preset_description.AutoSize = False
        self.preset_description.AutoEllipsis = True
        self.preset_description.Font = self.helper_font
        self.preset_description.ForeColor = SETTINGS_MUTED_COLOR
        self.preset_description.TextAlign = ContentAlignment.MiddleLeft
        content.Controls.Add(self.preset_description, 0, 2)
        return card

    def _add_status_card(self, layout, column_index, title):
        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.BackColor = SETTINGS_CARD_COLOR
        half_gap = 5
        left_margin = 0 if column_index == 0 else half_gap
        right_margin = 0 if column_index == 2 else half_gap
        card.Margin = Padding(left_margin, 6, right_margin, 6)
        card.MinimumSize = Size(0, 110)
        card.Padding = Padding(0, 10, 0, 10)
        card.ColumnCount = 1
        card.RowCount = 2
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 36.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 54.0))
        layout.Controls.Add(card, column_index, 0)
        title_label = Label()
        title_label.Text = title
        title_label.Dock = DockStyle.Fill
        title_label.AutoSize = False
        title_label.TextAlign = ContentAlignment.MiddleCenter
        title_label.Font = self.label_bold_font
        title_label.ForeColor = SETTINGS_NAVY_COLOR
        title_label.UseCompatibleTextRendering = False
        card.Controls.Add(title_label, 0, 0)
        value_label = Label()
        value_label.Dock = DockStyle.Fill
        value_label.AutoSize = False
        value_label.TextAlign = ContentAlignment.MiddleCenter
        value_label.Font = self.status_font
        value_label.ForeColor = SETTINGS_MUTED_COLOR
        value_label.Padding = Padding(0)
        value_label.UseCompatibleTextRendering = False
        card.Controls.Add(value_label, 0, 1)
        return value_label

    def _add_rule_card(self, layout, column_index, title):
        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.BackColor = SETTINGS_CARD_COLOR
        half_gap = 5
        left_margin = 0 if column_index == 0 else half_gap
        right_margin = 0 if column_index == 3 else half_gap
        card.Margin = Padding(left_margin, 6, right_margin, 6)
        card.MinimumSize = Size(0, 120)
        card.Padding = Padding(0)
        card.ColumnCount = 1
        card.RowCount = 3
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 2.0))
        card.RowStyles.Add(RowStyle(SizeType.Absolute, 40.0))
        card.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        layout.Controls.Add(card, column_index, 0)
        accent = Panel()
        accent.Dock = DockStyle.Fill
        accent.Margin = Padding(0)
        accent.BackColor = SETTINGS_ORANGE_COLOR
        card.Controls.Add(accent, 0, 0)
        title_label = Label()
        title_label.Text = title
        title_label.Dock = DockStyle.Fill
        title_label.AutoSize = False
        title_label.TextAlign = ContentAlignment.MiddleCenter
        title_label.Font = self.label_bold_font
        title_label.ForeColor = SETTINGS_NAVY_COLOR
        title_label.UseCompatibleTextRendering = False
        card.Controls.Add(title_label, 0, 1)
        value_label = Label()
        value_label.Dock = DockStyle.Fill
        value_label.AutoSize = False
        value_label.TextAlign = ContentAlignment.MiddleCenter
        value_label.Font = self.rule_count_font
        value_label.ForeColor = SETTINGS_NAVY_COLOR
        value_label.Padding = Padding(0)
        value_label.UseCompatibleTextRendering = False
        card.Controls.Add(value_label, 0, 2)
        return value_label

    def _get_environment_status(self, python_path):
        if python_path:
            status = probe_external_python_path(python_path)
            status["helper_path"] = self.helper_path
            status["helper_exists"] = os.path.isfile(self.helper_path)
            status["debug_log_path"] = self.debug_log_path
            return status

        status = get_xlsx_environment_status(
            u"",
            self.extension_dir,
            self.reports_dir
        )
        version_text = u""
        python_detail = status.get("python_detail", u"")
        if u"|" in python_detail:
            version_text = python_detail.split(u"|", 1)[1]
        status["openpyxl_version"] = version_text
        return status

    def _update_report_status(self, status):
        python_ready = status.get("external_python_detected", u"No") == u"Yes"
        openpyxl_ready = status.get("openpyxl_available", u"No") == u"Yes"
        helper_ready = status.get("helper_exists", False)
        self._set_status_value(
            self.python_status,
            u"Ready" if python_ready else u"Not Found",
            python_ready
        )
        openpyxl_text = u"Ready" if openpyxl_ready else u"Need Setup"
        self._set_status_value(
            self.openpyxl_status,
            openpyxl_text,
            openpyxl_ready
        )
        excel_ready = python_ready and openpyxl_ready and helper_ready
        self._set_status_value(
            self.excel_status,
            u"Ready" if excel_ready else u"Need Setup",
            excel_ready
        )
        python_path = self.selected_python_path
        if is_codex_runtime_path(python_path):
            self.python_warning.Text = (
                u"Temporary Python path detected. Select a stable Python for long-term use."
            )
            self.python_warning.BackColor = WARNING_FILL_COLOR
            self.python_warning.Visible = True
            self.warning_row_style.Height = 44.0
        else:
            self.python_warning.Text = u""
            self.python_warning.BackColor = Color.White
            self.python_warning.Visible = False
            self.warning_row_style.Height = 0.0

    def _set_status_value(self, label, text, is_ready):
        label.Text = text
        label.ForeColor = READY_COLOR if is_ready else WARNING_COLOR

    def _update_current_python_name(self):
        if self.selected_python_path:
            self.current_python_name.Text = os.path.basename(
                self.selected_python_path
            )
        else:
            self.current_python_name.Text = "Automatic detection"

    def _mark_environment_not_tested(self):
        self._set_status_value(self.python_status, "Not Tested", False)
        self._set_status_value(self.openpyxl_status, "Not Tested", False)
        self._set_status_value(self.excel_status, "Need Setup", False)
        if is_codex_runtime_path(self.selected_python_path):
            self.python_warning.Text = (
                u"Temporary Python path detected. Select a stable Python for long-term use."
            )
            self.python_warning.BackColor = WARNING_FILL_COLOR
            self.python_warning.Visible = True
            self.warning_row_style.Height = 44.0
        else:
            self.python_warning.Text = u""
            self.python_warning.BackColor = Color.White
            self.python_warning.Visible = False
            self.warning_row_style.Height = 0.0

    def _reload_all(self):
        try:
            config = load_config(
                self.default_config_path,
                self.local_config_path
            )
        except Exception as ex:
            MessageBox.Show(
                self,
                u"Settings could not be loaded: {0}".format(ex),
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return

        self.current_config = config
        self.config_meta = config.get("_config_meta", {})
        python_path = config.get("export", {}).get(
            "external_python_path",
            u""
        )
        self.selected_python_path = python_path
        self._update_current_python_name()
        self.current_environment_status = self._get_environment_status(
            python_path
        )
        self._update_report_status(self.current_environment_status)
        self._reload_presets(
            self.config_meta.get("active_config_file", u"")
        )
        if self.config_meta.get("warning", u""):
            self.preset_description.Text = u"Warning: {0}".format(
                self.config_meta["warning"]
            )
            self.preset_description.BackColor = WARNING_FILL_COLOR
        self._update_rule_summary(config)

    def _reload_presets(self, selected_file_name=None):
        self.presets = list_qc_presets(self.config_folder)
        selected_index = -1
        self.preset_combo.BeginUpdate()
        try:
            self.preset_combo.Items.Clear()
            for preset_index, preset in enumerate(self.presets):
                display_name = preset.get("preset_name", preset["file_name"])
                self.preset_combo.Items.Add(display_name)
                if preset["file_name"] == selected_file_name:
                    selected_index = preset_index
        finally:
            self.preset_combo.EndUpdate()

        if selected_index < 0 and self.presets:
            selected_index = 0
        if selected_index >= 0:
            self.preset_combo.SelectedIndex = selected_index

    def _get_selected_preset(self):
        index = self.preset_combo.SelectedIndex
        if index < 0 or index >= len(self.presets):
            return None
        return self.presets[index]

    def _preset_selection_changed(self, sender, event_args):
        preset = self._get_selected_preset()
        if preset is None:
            self.active_rule_name.Text = u"No preset"
            self.preset_description.Text = "No preset available."
            self.preset_description.BackColor = WARNING_FILL_COLOR
            return
        self.active_rule_name.Text = preset.get(
            "preset_name",
            preset.get("file_name", u"Rule Set")
        )
        description = preset.get("preset_description", u"")
        if preset.get("error", u""):
            description = u"Invalid preset: {0}".format(preset["error"])
            self.preset_description.BackColor = WARNING_FILL_COLOR
        else:
            self.preset_description.BackColor = SETTINGS_CARD_COLOR
        self.preset_description.Text = description

    def _update_rule_summary(self, config):
        summary = calculate_rule_summary(config)
        self.sheet_rules_value.Text = str(summary["sheet_rules"])
        self.view_rules_value.Text = str(summary["view_rules"])
        self.parameter_rules_value.Text = str(summary["parameter_rules"])
        self.required_parameters_value.Text = str(
            summary["required_parameters"]
        )

    def _browse_python(self, sender, event_args):
        dialog = OpenFileDialog()
        dialog.Title = "Select external Python executable"
        dialog.Filter = (
            "Python executable (python.exe)|python.exe|All files (*.*)|*.*"
        )
        dialog.CheckFileExists = True
        current_path = self.selected_python_path
        if os.path.isfile(current_path):
            dialog.InitialDirectory = os.path.dirname(current_path)
            dialog.FileName = os.path.basename(current_path)
        if dialog.ShowDialog(self) == DialogResult.OK:
            self.selected_python_path = dialog.FileName
            self._update_current_python_name()
            self._mark_environment_not_tested()
            try:
                save_local_external_python_path(
                    self.local_config_path,
                    self.selected_python_path
                )
                self._reload_all()
            except Exception as ex:
                self._show_message(
                    u"Python path could not be saved: {0}".format(ex),
                    MessageBoxIcon.Error
                )
        dialog.Dispose()

    def _test_environment(self, sender, event_args):
        status = self._get_environment_status(
            self.selected_python_path
        )
        self.current_environment_status = status
        self._update_report_status(status)
        python_ready = status.get("external_python_detected", u"No") == u"Yes"
        openpyxl_ready = status.get("openpyxl_available", u"No") == u"Yes"
        if python_ready and openpyxl_ready:
            message = u"Python and Excel Library are ready. Version: {0}".format(
                status.get("openpyxl_version", u"") or u"unknown"
            )
            icon = MessageBoxIcon.Information
        else:
            target = self.selected_python_path or u"python"
            message = (
                u"Styled Excel Report needs setup.\n\n{0}\n\n"
                u"Install:\n\"{1}\" -m pip install openpyxl"
            ).format(status.get("probe_error", u""), target)
            icon = MessageBoxIcon.Warning
        self._show_message(message, icon)
        self._print_environment_result(status)

    def _clear_python_path(self, sender, event_args):
        if MessageBox.Show(
            self,
            "Clear the saved Python path?",
            "Revit QC Settings",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Question
        ) != DialogResult.Yes:
            return
        try:
            save_local_external_python_path(self.local_config_path, u"")
            self._reload_all()
        except Exception as ex:
            self._show_message(
                u"Python path could not be cleared: {0}".format(ex),
                MessageBoxIcon.Error
            )

    def _set_active_preset(self, sender, event_args):
        preset = self._get_selected_preset()
        if preset is None or preset.get("error", u""):
            self._show_message(
                "Select a valid Rule Set.",
                MessageBoxIcon.Warning
            )
            return
        try:
            save_local_active_config(
                self.local_config_path,
                preset["file_name"]
            )
            self._reload_all()
            self._show_message(
                u"Active Rule Set changed to {0}.".format(
                    preset["preset_name"]
                ),
                MessageBoxIcon.Information
            )
        except Exception as ex:
            self._show_message(
                u"Rule Set could not be activated: {0}".format(ex),
                MessageBoxIcon.Error
            )

    def _duplicate_preset(self, sender, event_args):
        preset = self._get_selected_preset()
        if preset is None or preset.get("error", u""):
            self._show_message(
                "Select a valid Rule Set to copy.",
                MessageBoxIcon.Warning
            )
            return
        try:
            destination_path = duplicate_qc_preset(
                preset["path"],
                self.config_folder
            )
            self._reload_presets(
                self.config_meta.get("active_config_file", u"")
            )
            self._show_message(
                u"Rule Set copied: {0}".format(
                    os.path.basename(destination_path)
                ),
                MessageBoxIcon.Information
            )
        except Exception as ex:
            self._show_message(
                u"Rule Set could not be copied: {0}".format(ex),
                MessageBoxIcon.Error
            )

    def _reload_presets_click(self, sender, event_args):
        self._reload_all()

    def _open_config_folder(self, sender, event_args):
        opened, open_error = open_folder(self.config_folder)
        if not opened:
            self._show_message(open_error, MessageBoxIcon.Warning)

    def _open_debug_log(self, sender, event_args):
        if not os.path.isfile(self.debug_log_path):
            self._show_message("No debug log found.", MessageBoxIcon.Information)
            return
        opened, open_error = open_file(self.debug_log_path)
        if not opened:
            self._show_message(open_error, MessageBoxIcon.Warning)

    def _show_details(self, sender, event_args):
        status = self.current_environment_status or {}
        active_config_path = self.config_meta.get(
            "active_config_path",
            self.config_meta.get("active_config_file", u"")
        )
        python_path = self.selected_python_path or u"(automatic detection)"
        probe_error = status.get("probe_error", u"") or u"(none)"
        python_detail = status.get("python_detail", u"") or u"(none)"
        openpyxl_detail = u"{0} (version {1})".format(
            status.get("openpyxl_available", u"No"),
            status.get("openpyxl_version", u"") or u"unknown"
        )
        self.output.print_html(
            u"""
            <div style="font-family:Segoe UI,Arial,sans-serif; margin-top:10px;
                padding:12px; border:1px solid #D6DDE3;
                border-left:3px solid #536777;
                background:#F4F6F8; color:#263645; line-height:1.55;">
                <strong>Revit QC Settings - Details</strong><br>
                Default config path: {0}<br>
                Local config path: {1}<br>
                Active config file: {2}<br>
                Python full path: {3}<br>
                Helper script: {4}<br>
                Last debug log: {5}<br>
                Probe error: {6}<br>
                Python detail: {7}<br>
                openpyxl detail: {8}
            </div>
            """.format(
                html_escape(self.default_config_path),
                html_escape(self.local_config_path),
                html_escape(active_config_path or u"(none)"),
                html_escape(python_path),
                html_escape(self.helper_path),
                html_escape(self.debug_log_path),
                html_escape(probe_error),
                html_escape(python_detail),
                html_escape(openpyxl_detail)
            )
        )
        self._show_message(
            "Details were printed to the pyRevit output.",
            MessageBoxIcon.Information
        )

    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        try:
            self.Shown -= self._configure_scroll_fallback
        except Exception:
            pass
        try:
            self.preset_combo.SelectedIndexChanged -= (
                self._preset_selection_changed
            )
        except Exception:
            pass
        for button in list(self._secondary_buttons):
            try:
                button.MouseEnter -= self._secondary_button_mouse_enter
                button.MouseLeave -= self._secondary_button_mouse_leave
            except Exception:
                pass
        self._secondary_buttons = []
        if self._apply_rule_button is not None:
            try:
                self._apply_rule_button.MouseEnter -= (
                    self._apply_rule_mouse_enter
                )
                self._apply_rule_button.MouseLeave -= (
                    self._apply_rule_mouse_leave
                )
            except Exception:
                pass
        try:
            self.tooltip.Dispose()
        except Exception:
            pass
        for font in (
            self.title_font,
            self.subtitle_font,
            self.section_font,
            self.label_font,
            self.label_bold_font,
            self.helper_font,
            self.button_font,
            self.status_font,
            self.rule_count_font,
            self.active_header_font
        ):
            try:
                font.Dispose()
            except Exception:
                pass

    def _close_form(self, sender, event_args):
        self.Close()

    def _show_message(self, message, icon):
        MessageBox.Show(
            self,
            message,
            "Revit QC Settings",
            MessageBoxButtons.OK,
            icon
        )

    def _print_environment_result(self, status):
        self.output.print_html(
            u"""
            <div style="font-family:Segoe UI,Arial,sans-serif; margin-top:10px;
                padding:10px; border:1px solid #D6DDE3;
                border-left:3px solid #536777;
                background:#F4F6F8; color:#263645;">
                <strong>Styled Excel Report Test</strong><br>
                Python: {0}<br>
                openpyxl: {1}<br>
                Version: {2}<br>
                Result: {3}
            </div>
            """.format(
                html_escape(status.get("external_python_detected", u"No")),
                html_escape(status.get("openpyxl_available", u"No")),
                html_escape(status.get("openpyxl_version", u"") or u"(none)"),
                html_escape(status.get("probe_error", u"") or u"Ready")
            )
        )


def show_settings_dialog(
    output,
    default_config_path,
    local_config_path,
    extension_dir,
    reports_dir
):
    close_profile = create_ui_close_profile(u"QC Settings")
    settings_form = QCSettingsForm(
        output,
        default_config_path,
        local_config_path,
        extension_dir,
        reports_dir
    )
    close_profile.attach(settings_form)
    try:
        close_profile.show_dialog()
    finally:
        close_profile.dispose()
