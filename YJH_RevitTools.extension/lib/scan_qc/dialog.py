# -*- coding: utf-8 -*-

import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import DateTime
from System.Diagnostics import Stopwatch
from System.Drawing import (
    Color,
    ContentAlignment,
    FontStyle,
    Point,
    Rectangle,
    Size,
    SizeF
)
from System.Windows.Forms import (
    AutoScaleMode,
    AutoSizeMode,
    BorderStyle,
    Button,
    CheckBox,
    ColumnStyle,
    ComboBox,
    ComboBoxStyle,
    DialogResult,
    DockStyle,
    FlowDirection,
    FlowLayoutPanel,
    FlatStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    FormWindowState,
    GroupBox,
    HorizontalAlignment,
    Keys,
    Label,
    Padding,
    Panel,
    RowStyle,
    SaveFileDialog,
    Screen,
    SizeType,
    TableLayoutPanel,
    TableLayoutPanelCellBorderStyle,
    TextBox,
    ToolTip
)

from scan_qc.collectors import get_element_id_value, get_point_cloud_name
from scan_qc.controls import TopNCalloutsSlider
from scan_qc.analysis_scope import (
    ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL,
    ANALYSIS_SCOPE_LABELS,
    ANALYSIS_SCOPE_SELECTED_WALLS
)
from scan_qc.settings import (
    get_deviation_options,
    get_output_options,
    get_report_options,
    get_report_output_folder,
    get_target_wall_filter_defaults,
    get_tolerance_mm,
    load_report_state,
    save_report_state
)
from scan_qc.source_views import (
    get_source_plan_view_label,
    get_source_plan_view_name
)
from scan_qc.startup_cache import get_runtime_diagnostics
from ui_close_profiler import (
    create_ui_close_profile, log_layout_snapshot, log_section_snapshots
)
from qc_ui_style import (
    BORDER_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_NAVY_COLOR,
    HELP_BACKGROUND_COLOR,
    NAVY_COLOR,
    OUTER_MARGIN,
    HEADER_TOP_PADDING,
    SECTION_GAP,
    SMALL_ACTION_BUTTON_WIDTH,
    SMALL_ACTION_BUTTON_HEIGHT,
    FOOTER_BUTTON_WIDTH,
    FOOTER_BUTTON_HEIGHT,
    FOOTER_HEIGHT,
    WARNING_BACKGROUND_COLOR,
    apply_scan_reference_section_style,
    attach_border_hover,
    apply_secondary_button_style,
    configure_content_scroll,
    configure_tooltip,
    detach_border_hover,
    dispose_tooltip,
    get_preferred_font
)


REPORT_SHEET_MODE_CREATE_NEW = u"create_new"
REPORT_SHEET_MODE_EXISTING = u"existing"
REPORT_SHEET_MODE_CREATE_NEW_LABEL = u"Create New Scan QC Report Sheet"
REPORT_SHEET_MODE_EXISTING_LABEL = u"Use Existing Sheet"

WINDOW_OUTER_PADDING = Padding(
    OUTER_MARGIN,
    HEADER_TOP_PADDING,
    OUTER_MARGIN,
    OUTER_MARGIN
)
GROUP_CONTENT_PADDING = Padding(
    14,
    8,
    14,
    8
)
CONTROL_HEIGHT = 32
FOOTER_BUTTON_GAP = 12
SCAN_FOOTER_HEIGHT = FOOTER_HEIGHT
REPORT_LABEL_COLUMN_WIDTH = 180
REPORT_BADGE_COLUMN_WIDTH = 44
REPORT_COLUMN_GAP = 12
REPORT_ROW_HEIGHT = 40
TOLERANCE_HEADER_HEIGHT = 30
TOLERANCE_VALUE_HEIGHT = 36
TOLERANCE_HEADER_VALUE_GAP = 6
TOLERANCE_CARD_GAP = 12
TOLERANCE_BORDER_COLOR = Color.FromArgb(216, 222, 229)
SECONDARY_TEXT_COLOR = Color.FromArgb(100, 116, 135)
WINDOW_STATE_KEY = "scan_qc_window_bounds"

def format_mm_value(value):
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return u"{0}".format(int(numeric_value))
    except (TypeError, ValueError):
        pass

    return u"{0}".format(value)


def clamp_window_bounds(
    x,
    y,
    width,
    height,
    working_left,
    working_top,
    working_width,
    working_height,
    minimum_width,
    minimum_height
):
    """Clamp persisted dialog bounds to an available monitor working area."""
    safe_working_width = max(1, int(working_width))
    safe_working_height = max(1, int(working_height))
    safe_width = min(
        max(int(width), int(minimum_width)),
        safe_working_width
    )
    safe_height = min(
        max(int(height), int(minimum_height)),
        safe_working_height
    )
    maximum_x = int(working_left) + safe_working_width - safe_width
    maximum_y = int(working_top) + safe_working_height - safe_height
    safe_x = min(max(int(x), int(working_left)), maximum_x)
    safe_y = min(max(int(y), int(working_top)), maximum_y)
    return safe_x, safe_y, safe_width, safe_height


def get_sheet_name(sheet):
    try:
        return unicode(sheet.Name)
    except NameError:
        try:
            return str(sheet.Name)
        except Exception:
            return u""
    except Exception:
        return u""


def get_sheet_label(sheet):
    sheet_number = u""
    try:
        sheet_number = unicode(sheet.SheetNumber)
    except NameError:
        try:
            sheet_number = str(sheet.SheetNumber)
        except Exception:
            sheet_number = u""
    except Exception:
        sheet_number = u""

    sheet_name = get_sheet_name(sheet)
    return u"{0} - {1}  [ElementId: {2}]".format(
        sheet_number or u"(No Number)",
        sheet_name or u"(No Name)",
        get_element_id_value(sheet.Id)
    )


class ScanQcForm(Form):
    def __init__(
        self,
        selected_wall_count,
        point_clouds,
        source_plan_views,
        existing_report_sheets,
        default_source_plan_view_id,
        settings,
        target_parameter_status=None,
        target_counts_by_view_id=None,
        initial_state=None,
        target_action_handler=None,
        existing_report_sheet_loader=None
    ):
        Form.__init__(self)
        self.SuspendLayout()
        self._is_initializing = True
        self.result = None
        self.point_clouds = point_clouds
        self.source_plan_views = source_plan_views
        self.existing_report_sheets = existing_report_sheets or []
        self.settings = settings
        self.target_parameter_status = target_parameter_status or {}
        self.target_counts_by_view_id = target_counts_by_view_id or {}
        self.initial_state = initial_state or {}
        self.target_action_handler = target_action_handler
        self.existing_report_sheet_loader = existing_report_sheet_loader
        self.existing_report_sheets_loaded = bool(existing_report_sheets)
        self.combo_population_ms = 0
        self.pdf_auto_enabled_plan_view = False
        self._window_bounds_applied = False
        self._window_bounds_saved = False
        self._secondary_hover_bindings = []
        tolerance_mm = get_tolerance_mm(settings)
        deviation_options = get_deviation_options(settings)
        self.default_tolerance_mm = tolerance_mm
        self._updating_tolerances = False
        self._last_valid_ok_max = float(tolerance_mm["ok_max"])
        self._last_valid_review_max = float(tolerance_mm["review_max"])
        if self._last_valid_review_max <= self._last_valid_ok_max:
            self._last_valid_review_max = self._last_valid_ok_max + 1.0
        self.default_top_n_callouts = deviation_options["top_n_callouts"]
        output_defaults = get_output_options(settings)
        report_defaults = get_report_options(settings)
        target_filter_defaults = get_target_wall_filter_defaults(settings)
        self.default_paper_size = report_defaults.get("paper_size", u"A3 Landscape")

        self.Text = "Revit QC - Scan QC"
        working_area = Screen.PrimaryScreen.WorkingArea
        maximum_client_width = int(working_area.Width * 0.94)
        maximum_client_height = int(working_area.Height * 0.93)
        client_width = max(900, min(1180, maximum_client_width))
        client_height = max(760, min(1120, maximum_client_height))
        self.ClientSize = Size(client_width, client_height)
        self.MinimumSize = Size(
            min(1040, client_width),
            min(900, client_height)
        )
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.Manual
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(9.5)
        self.AutoScaleMode = AutoScaleMode.Dpi
        self.AutoScaleDimensions = SizeF(96.0, 96.0)
        self.AutoScroll = False
        self.tool_tip = configure_tooltip(ToolTip())
        self.Load += self._apply_saved_window_bounds
        self.FormClosed += self._save_window_bounds_once

        root_layout = TableLayoutPanel()
        root_layout.Dock = DockStyle.Fill
        root_layout.Padding = WINDOW_OUTER_PADDING
        root_layout.ColumnCount = 1
        root_layout.RowCount = 3
        root_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        root_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        root_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.Controls.Add(root_layout)

        main_layout = TableLayoutPanel()
        main_layout.Dock = DockStyle.Top
        main_layout.AutoSize = True
        main_layout.Padding = Padding(0)
        main_layout.ColumnCount = 1
        main_layout.RowCount = 7
        main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        for _row_index in range(7):
            main_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))

        content_panel = Panel()
        content_panel.Dock = DockStyle.Fill
        content_panel.AutoScroll = False
        content_panel.Margin = Padding(0, 20, 0, 0)
        content_panel.Controls.Add(main_layout)
        root_layout.Controls.Add(content_panel, 0, 1)
        self.content_panel = content_panel
        self.main_layout = main_layout
        self.Shown += self._configure_scroll_fallback

        header_panel = TableLayoutPanel()
        header_panel.Dock = DockStyle.Fill
        header_panel.AutoSize = True
        header_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header_panel.ColumnCount = 1
        header_panel.RowCount = 2
        header_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root_layout.Controls.Add(header_panel, 0, 0)

        intro_label = Label()
        intro_label.Text = "Scan QC Setup"
        intro_label.Dock = DockStyle.Fill
        intro_label.ForeColor = NAVY_COLOR
        intro_label.Font = get_preferred_font(17.0, FontStyle.Bold)
        intro_label.Padding = Padding(0)
        intro_label.AutoSize = True
        intro_label.Margin = Padding(0)
        header_panel.Controls.Add(intro_label, 0, 0)

        subtitle_label = Label()
        subtitle_label.Text = (
            u"Point Cloud와 Revit 벽체 오차를 검토하고 QC View와 보고서를 생성합니다."
        )
        subtitle_label.Dock = DockStyle.Fill
        subtitle_label.AutoSize = True
        subtitle_label.ForeColor = SECONDARY_TEXT_COLOR
        subtitle_label.Font = get_preferred_font(9.5)
        subtitle_label.Margin = Padding(0, 6, 0, 0)
        header_panel.Controls.Add(subtitle_label, 0, 1)

        analysis_scope_group = self._create_group("Analysis Scope")
        main_layout.Controls.Add(analysis_scope_group, 0, 0)
        self._set_tooltip(
            analysis_scope_group,
            u"검토 범위를 선택합니다. Active Plan Level은 선택한 평면도 기준 "
            u"전체 벽을 검토하고, Selected Walls는 사용자가 선택한 벽만 "
            u"검토합니다."
        )

        analysis_scope_layout = TableLayoutPanel()
        analysis_scope_layout.Dock = DockStyle.Fill
        analysis_scope_layout.AutoSize = True
        analysis_scope_layout.Padding = GROUP_CONTENT_PADDING
        analysis_scope_layout.ColumnCount = 1
        analysis_scope_layout.RowCount = 2
        analysis_scope_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        analysis_scope_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.selected_walls_row_style = RowStyle(SizeType.Absolute, 0.0)
        analysis_scope_layout.RowStyles.Add(self.selected_walls_row_style)
        analysis_scope_group.Controls.Add(analysis_scope_layout)

        self.analysis_scope_combo = ComboBox()
        self.analysis_scope_combo.Dock = DockStyle.Fill
        self.analysis_scope_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.analysis_scope_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.analysis_scope_combo.Margin = Padding(0, 2, 0, 2)
        self.analysis_scope_combo.BeginUpdate()
        try:
            self.analysis_scope_combo.Items.Add(
                ANALYSIS_SCOPE_LABELS[ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL]
            )
            self.analysis_scope_combo.Items.Add(
                ANALYSIS_SCOPE_LABELS[ANALYSIS_SCOPE_SELECTED_WALLS]
            )
        finally:
            self.analysis_scope_combo.EndUpdate()
        self.analysis_scope_combo.SelectedIndex = 0
        analysis_scope_layout.Controls.Add(self.analysis_scope_combo, 0, 0)
        self._set_tooltip(
            self.analysis_scope_combo,
            u"검토 범위를 선택합니다. Active Plan Level은 선택한 Source Plan "
            u"View 기준 벽을 수집하고, Selected Walls는 현재 선택 또는 실행 중 "
            u"선택한 벽만 사용합니다."
        )

        self.selected_walls_group = Panel()
        self.selected_walls_group.Dock = DockStyle.Fill
        self.selected_walls_group.AutoSize = True
        self.selected_walls_group.Visible = False
        self.selected_walls_group.Margin = Padding(0, 4, 0, 0)
        analysis_scope_layout.Controls.Add(self.selected_walls_group, 0, 1)
        self._set_tooltip(
            self.selected_walls_group,
            u"Selected Walls 모드에서 검토할 Revit Wall 요소를 지정합니다. "
            u"Run 실행 시 선택된 벽이 없으면 Revit 선택 워크플로우로 벽을 "
            u"선택합니다."
        )

        selected_walls_layout = TableLayoutPanel()
        selected_walls_layout.Dock = DockStyle.Fill
        selected_walls_layout.AutoSize = True
        selected_walls_layout.Padding = Padding(0, 4, 0, 2)
        selected_walls_layout.ColumnCount = 2
        selected_walls_layout.RowCount = 1
        selected_walls_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 40.0))
        selected_walls_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 60.0))
        selected_walls_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        self.selected_walls_group.Controls.Add(selected_walls_layout)

        selected_wall_count_label = Label()
        selected_wall_count_label.Text = u"Current selected Wall count: {0}".format(
            selected_wall_count
        )
        selected_wall_count_label.Dock = DockStyle.Fill
        selected_wall_count_label.AutoSize = True
        selected_wall_count_label.MinimumSize = Size(0, 28)
        selected_wall_count_label.ForeColor = NAVY_COLOR
        selected_wall_count_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        selected_walls_layout.Controls.Add(selected_wall_count_label, 0, 0)

        selected_wall_instruction = Label()
        if selected_wall_count > 0:
            selected_wall_instruction.Text = "Run uses the current Revit Wall selection."
        else:
            selected_wall_instruction.Text = "Click Run to pick Walls in Revit."
        selected_wall_instruction.Dock = DockStyle.Fill
        selected_wall_instruction.AutoSize = True
        selected_wall_instruction.MinimumSize = Size(0, 32)
        selected_wall_instruction.ForeColor = SECONDARY_TEXT_COLOR
        selected_wall_instruction.Font = get_preferred_font(9.0)
        selected_wall_instruction.TextAlign = ContentAlignment.MiddleLeft
        selected_walls_layout.Controls.Add(selected_wall_instruction, 1, 0)

        self.analysis_scope_combo.SelectedIndexChanged += self._update_analysis_scope_ui
        self._update_analysis_scope_ui(None, None)

        source_plan_group = self._create_group("Source Plan View")
        main_layout.Controls.Add(source_plan_group, 0, 1)
        self._set_tooltip(
            source_plan_group,
            u"QC Plan View와 Active Plan Level 범위의 기준이 되는 평면도입니다. "
            u"원본 View는 수정하지 않고 복제된 Scan QC View만 생성합니다."
        )

        source_plan_layout = TableLayoutPanel()
        source_plan_layout.Dock = DockStyle.Fill
        source_plan_layout.AutoSize = True
        source_plan_layout.Padding = GROUP_CONTENT_PADDING
        source_plan_layout.ColumnCount = 1
        source_plan_layout.RowCount = 2
        source_plan_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        source_plan_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        source_plan_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        source_plan_group.Controls.Add(source_plan_layout)

        self.source_plan_combo = ComboBox()
        self.source_plan_combo.Dock = DockStyle.Fill
        self.source_plan_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.source_plan_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.source_plan_combo.DropDownWidth = 1400
        self.source_plan_combo.Margin = Padding(0, 2, 0, 8)
        self.source_plan_combo.SelectedIndexChanged += self._update_source_plan_view
        source_plan_layout.Controls.Add(self.source_plan_combo, 0, 0)
        self._set_tooltip(
            self.source_plan_combo,
            u"QC Plan View를 복제할 기준 평면도입니다. 긴 View 이름은 목록에서 "
            u"확인하고, 원본 View는 변경하지 않습니다."
        )

        self.selected_source_plan_label = Label()
        self.selected_source_plan_label.Dock = DockStyle.Fill
        self.selected_source_plan_label.AutoSize = False
        self.selected_source_plan_label.MinimumSize = Size(0, 22)
        self.selected_source_plan_label.ForeColor = SECONDARY_TEXT_COLOR
        self.selected_source_plan_label.Font = get_preferred_font(9.0)
        self.selected_source_plan_label.AutoEllipsis = True
        source_plan_layout.Controls.Add(self.selected_source_plan_label, 0, 1)

        selected_source_plan_index = 0
        combo_watch = Stopwatch.StartNew()
        self.source_plan_combo.BeginUpdate()
        try:
            for index, source_plan_view in enumerate(source_plan_views):
                self.source_plan_combo.Items.Add(
                    get_source_plan_view_label(source_plan_view)
                )
                if (
                    get_element_id_value(source_plan_view.Id)
                    == default_source_plan_view_id
                ):
                    selected_source_plan_index = index
        finally:
            self.source_plan_combo.EndUpdate()
            combo_watch.Stop()
            self.combo_population_ms += combo_watch.ElapsedMilliseconds

        if source_plan_views:
            self.source_plan_combo.SelectedIndex = selected_source_plan_index

        target_filter_group = self._create_group("Target Wall Filter")
        target_filter_group.AutoSize = True
        main_layout.Controls.Add(target_filter_group, 0, 2)
        self._set_tooltip(
            target_filter_group,
            u"검토 대상 벽을 제한합니다. Interior/Exterior 기준은 도면상 "
            u"위치가 아니라 Revit Wall Type의 Function 값을 기준으로 합니다. "
            u"여러 필터를 동시에 선택하면 모든 조건을 만족하는 벽만 검토합니다."
        )

        target_filter_layout = TableLayoutPanel()
        target_filter_layout.Dock = DockStyle.Fill
        target_filter_layout.AutoSize = True
        target_filter_layout.Padding = GROUP_CONTENT_PADDING
        target_filter_layout.ColumnCount = 2
        target_filter_layout.RowCount = 5
        target_filter_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 50.0)
        )
        target_filter_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 50.0)
        )
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        target_filter_group.Controls.Add(target_filter_layout)

        self.interior_walls_only_check = self._create_check_box(
            "Interior Walls Only",
            target_filter_defaults["interior_walls_only"]
        )
        self.new_construction_only_check = self._create_check_box(
            "New Construction Only",
            target_filter_defaults["new_construction_only"]
        )
        self.exclude_exterior_walls_check = self._create_check_box(
            "Exclude Exterior Walls",
            target_filter_defaults["exclude_exterior_walls"]
        )
        self.only_scan_qc_target_yes_check = self._create_check_box(
            "Only SCAN_QC_TARGET = Yes",
            target_filter_defaults["only_scan_qc_target_yes"]
        )
        target_filter_layout.Controls.Add(self.interior_walls_only_check, 0, 0)
        target_filter_layout.Controls.Add(self.new_construction_only_check, 1, 0)
        target_filter_layout.Controls.Add(self.exclude_exterior_walls_check, 0, 1)
        target_filter_layout.Controls.Add(self.only_scan_qc_target_yes_check, 1, 1)
        self._set_tooltip(
            self.interior_walls_only_check,
            u"Wall Type Function이 Interior인 벽만 검토합니다. 도면상 내부/"
            u"외곽 위치를 자동 판정하는 기능은 아닙니다. 다른 필터와 함께 "
            u"선택하면 AND 조건으로 적용됩니다."
        )
        self._set_tooltip(
            self.new_construction_only_check,
            u"Phase Created 정보를 기준으로 신설 벽 위주로 검토합니다. "
            u"프로젝트 Phase 설정에 따라 결과가 달라질 수 있으며, 다른 "
            u"필터와 함께 선택하면 AND 조건으로 적용됩니다."
        )
        self._set_tooltip(
            self.exclude_exterior_walls_check,
            u"Wall Type Function이 Exterior인 벽을 제외합니다. 외벽 타입이 "
            u"올바르게 지정되어 있어야 정확하며, 다른 필터와 함께 선택하면 "
            u"AND 조건으로 적용됩니다."
        )
        self._set_tooltip(
            self.only_scan_qc_target_yes_check,
            u"사용자 파라미터 SCAN_QC_TARGET 값이 Yes인 벽만 검토합니다. "
            u"실무에서 검토 대상 신설벽을 명확히 지정할 때 가장 안정적이며, "
            u"다른 필터와 함께 선택하면 AND 조건으로 적용됩니다."
        )

        self.target_status_label = Label()
        self.target_status_label.Dock = DockStyle.Fill
        self.target_status_label.AutoSize = True
        self.target_status_label.MinimumSize = Size(0, 24)
        self.target_status_label.ForeColor = NAVY_COLOR
        self.target_status_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        self.target_status_label.Padding = Padding(0, 6, 0, 2)
        target_filter_layout.Controls.Add(self.target_status_label, 0, 2)
        target_filter_layout.SetColumnSpan(self.target_status_label, 2)

        target_action_panel = FlowLayoutPanel()
        target_action_panel.Dock = DockStyle.Fill
        target_action_panel.AutoSize = True
        target_action_panel.FlowDirection = FlowDirection.LeftToRight
        target_action_panel.WrapContents = False
        target_action_panel.Padding = Padding(0, 6, 0, 4)
        target_filter_layout.Controls.Add(target_action_panel, 0, 3)
        target_filter_layout.SetColumnSpan(target_action_panel, 2)

        parameter_available = self.target_parameter_status.get(
            "available",
            False
        )
        mark_selected_button = self._create_target_action_button(
            "Pick & Mark",
            self._request_mark_selected
        )
        clear_selected_button = self._create_target_action_button(
            "Pick & Clear",
            self._request_clear_selected
        )
        select_targets_button = self._create_target_action_button(
            "Show Targets",
            self._request_select_targets
        )
        select_targets_button.Margin = Padding(0)
        for action_button in [
            mark_selected_button,
            clear_selected_button,
            select_targets_button
        ]:
            action_button.Enabled = parameter_available
            target_action_panel.Controls.Add(action_button)
            if not parameter_available:
                self._set_tooltip(
                    action_button,
                    u"SCAN_QC_TARGET Shared Parameter가 설치된 후 사용할 수 있습니다."
                )
        if parameter_available:
            self._set_tooltip(
                mark_selected_button,
                u"Revit 화면에서 벽을 선택하고 SCAN_QC_TARGET을 Yes로 설정합니다."
            )
            self._set_tooltip(
                clear_selected_button,
                u"선택한 벽의 SCAN_QC_TARGET 값을 해제합니다."
            )
            self._set_tooltip(
                select_targets_button,
                u"현재 Source Plan View의 Scan QC 대상 벽을 선택 상태로 표시합니다."
            )
        self._update_target_status_label()

        self.target_filter_help_label = Label()
        self.target_filter_help_label.Text = (
            "Target filters are optional and combined with AND conditions."
        )
        last_action_message = self.target_parameter_status.get(
            "last_action_message",
            u""
        )
        if last_action_message:
            self.target_filter_help_label.Text += u"  {0}".format(
                last_action_message
            )
        self.target_filter_help_label.Dock = DockStyle.Top
        self.target_filter_help_label.AutoSize = True
        self.target_filter_help_label.MaximumSize = Size(980, 0)
        self.target_filter_help_label.ForeColor = SECONDARY_TEXT_COLOR
        self.target_filter_help_label.Font = get_preferred_font(9.0)
        self.target_filter_help_label.TextAlign = ContentAlignment.MiddleLeft
        self.target_filter_help_label.Padding = Padding(0, 4, 0, 4)
        self.target_filter_help_label.UseCompatibleTextRendering = True
        target_filter_layout.Controls.Add(self.target_filter_help_label, 0, 4)
        target_filter_layout.SetColumnSpan(self.target_filter_help_label, 2)
        self._set_tooltip(
            self.target_filter_help_label,
            u"Target Wall Filter는 선택 사항입니다. 여러 필터를 동시에 "
            u"선택하면 AND 조건으로 적용되어 모든 조건을 만족하는 벽만 "
            u"검토합니다."
        )

        point_cloud_group = self._create_group("Analysis Point Cloud Source")
        main_layout.Controls.Add(point_cloud_group, 0, 3)
        self._set_tooltip(
            point_cloud_group,
            u"오차 계산에 사용할 Point Cloud Instance입니다. 선택한 Point "
            u"Cloud를 기준으로 Wall Deviation Sampling을 수행합니다."
        )

        point_cloud_layout = TableLayoutPanel()
        point_cloud_layout.Dock = DockStyle.Fill
        point_cloud_layout.AutoSize = True
        point_cloud_layout.Padding = GROUP_CONTENT_PADDING
        point_cloud_layout.ColumnCount = 1
        point_cloud_layout.RowCount = 3
        point_cloud_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        point_cloud_group.Controls.Add(point_cloud_layout)

        self.point_cloud_combo = ComboBox()
        self.point_cloud_combo.Dock = DockStyle.Fill
        self.point_cloud_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.point_cloud_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.point_cloud_combo.DropDownWidth = 1400
        self.point_cloud_combo.Margin = Padding(0, 2, 0, 8)
        self.point_cloud_combo.SelectedIndexChanged += self._update_selected_point_cloud
        point_cloud_layout.Controls.Add(self.point_cloud_combo, 0, 0)
        self._set_tooltip(
            self.point_cloud_combo,
            u"오차 계산에 사용할 Point Cloud Instance입니다. 선택한 Point "
            u"Cloud Source가 Wall Deviation Sampling의 기준입니다."
        )

        self.selected_point_cloud_label = Label()
        self.selected_point_cloud_label.Dock = DockStyle.Fill
        self.selected_point_cloud_label.AutoSize = False
        self.selected_point_cloud_label.MinimumSize = Size(0, 22)
        self.selected_point_cloud_label.ForeColor = SECONDARY_TEXT_COLOR
        self.selected_point_cloud_label.Font = get_preferred_font(9.0)
        self.selected_point_cloud_label.AutoEllipsis = True
        point_cloud_layout.Controls.Add(self.selected_point_cloud_label, 0, 1)

        point_cloud_help_label = Label()
        point_cloud_help_label.Text = (
            "Selected point cloud is used for wall deviation sampling."
        )
        point_cloud_help_label.Dock = DockStyle.Fill
        point_cloud_help_label.AutoSize = True
        point_cloud_help_label.ForeColor = SECONDARY_TEXT_COLOR
        point_cloud_help_label.Font = get_preferred_font(9.0)
        point_cloud_help_label.TextAlign = ContentAlignment.MiddleLeft
        point_cloud_help_label.Visible = False

        combo_watch = Stopwatch.StartNew()
        self.point_cloud_combo.BeginUpdate()
        try:
            for point_cloud in point_clouds:
                self.point_cloud_combo.Items.Add(
                    u"{0}  [ElementId: {1}]".format(
                        get_point_cloud_name(point_cloud),
                        get_element_id_value(point_cloud.Id)
                    )
                )
        finally:
            self.point_cloud_combo.EndUpdate()
            combo_watch.Stop()
            self.combo_population_ms += combo_watch.ElapsedMilliseconds

        tolerance_group = self._create_group("Default Tolerances")
        main_layout.Controls.Add(tolerance_group, 0, 4)
        self._set_tooltip(
            tolerance_group,
            u"Review / Critical 판정 기준입니다. 값은 mm 단위이며, 입력값은 "
            u"이번 실행에 적용됩니다."
        )

        tolerance_layout = TableLayoutPanel()
        tolerance_layout.Dock = DockStyle.Fill
        tolerance_layout.AutoSize = True
        tolerance_layout.Padding = GROUP_CONTENT_PADDING
        tolerance_layout.ColumnCount = 3
        tolerance_layout.RowCount = 1
        tolerance_layout.CellBorderStyle = getattr(
            TableLayoutPanelCellBorderStyle,
            "None"
        )
        for index in range(3):
            tolerance_layout.ColumnStyles.Add(
                ColumnStyle(SizeType.Percent, 100.0 / 3.0)
            )
        tolerance_layout.RowStyles.Add(
            RowStyle(
                SizeType.Absolute,
                TOLERANCE_HEADER_HEIGHT
                + TOLERANCE_HEADER_VALUE_GAP
                + TOLERANCE_VALUE_HEIGHT
            )
        )
        tolerance_group.Controls.Add(tolerance_layout)

        (
            ok_card,
            self.ok_max_border_panel,
            self.ok_max_text
        ) = self._create_tolerance_card(
            "OK Max (mm)",
            Color.FromArgb(234, 245, 236),
            tolerance_mm["ok_max"]
        )
        (
            review_card,
            self.review_max_border_panel,
            self.review_max_text
        ) = self._create_tolerance_card(
            "Review Max (mm)",
            Color.FromArgb(255, 241, 229),
            tolerance_mm["review_max"]
        )
        (
            critical_card,
            self.critical_value_border_panel,
            self.critical_value_text
        ) = self._create_tolerance_card(
            "Critical",
            Color.FromArgb(251, 234, 236),
            self._last_valid_review_max,
            True
        )
        half_gap = TOLERANCE_CARD_GAP // 2
        ok_card.Margin = Padding(0, 0, half_gap, 0)
        review_card.Margin = Padding(half_gap, 0, half_gap, 0)
        critical_card.Margin = Padding(half_gap, 0, 0, 0)
        tolerance_layout.Controls.Add(ok_card, 0, 0)
        tolerance_layout.Controls.Add(review_card, 1, 0)
        tolerance_layout.Controls.Add(critical_card, 2, 0)

        self.critical_value_text.ReadOnly = True
        self.critical_value_text.TabStop = False
        self.critical_value_text.BackColor = Color.White
        self._ok_tolerance_tooltip = (
            u"OK로 볼 수 있는 최대 오차값입니다. mm 단위이며 이번 실행에만 "
            u"적용됩니다."
        )
        self._review_tolerance_tooltip = (
            u"Review와 Critical을 나누는 최대 Review 기준값입니다. 이 값을 "
            u"초과하면 Critical로 분류됩니다."
        )
        self._set_tooltip(self.ok_max_text, self._ok_tolerance_tooltip)
        self._set_tooltip(self.review_max_text, self._review_tolerance_tooltip)
        self._set_tooltip(
            self.critical_value_text,
            u"Critical은 Review Max를 초과하는 오차입니다. Review Max 변경 시 "
            u"자동으로 갱신됩니다."
        )
        self.ok_max_text.TextChanged += self._handle_tolerance_text_changed
        self.review_max_text.TextChanged += self._handle_tolerance_text_changed
        self.ok_max_text.KeyDown += self._handle_tolerance_key_down
        self.review_max_text.KeyDown += self._handle_tolerance_key_down
        self.ok_max_text.Leave += self._handle_tolerance_leave
        self.review_max_text.Leave += self._handle_tolerance_leave
        self._update_critical_value_display()

        output_group = self._create_group("Output Options")
        main_layout.Controls.Add(output_group, 0, 5)
        self._set_tooltip(
            output_group,
            u"Scan QC 실행 후 생성할 결과물을 선택합니다. PDF Report를 선택하면 "
            u"필요한 QC Plan View는 자동으로 생성됩니다."
        )

        output_layout = TableLayoutPanel()
        output_layout.Dock = DockStyle.Fill
        output_layout.AutoSize = True
        output_layout.Padding = GROUP_CONTENT_PADDING
        output_layout.ColumnCount = 1
        output_layout.RowCount = 2
        output_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        for _index in range(2):
            output_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        output_group.Controls.Add(output_layout)

        output_check_layout = TableLayoutPanel()
        output_check_layout.Dock = DockStyle.Top
        output_check_layout.AutoSize = True
        output_check_layout.Margin = Padding(0)
        output_check_layout.ColumnCount = 2
        output_check_layout.RowCount = 3
        output_check_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 50.0)
        )
        output_check_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 50.0)
        )
        for _index in range(3):
            output_check_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        output_layout.Controls.Add(output_check_layout, 0, 0)

        self.create_plan_check = self._create_check_box(
            "Create QC Plan View",
            output_defaults["create_plan_view"]
        )
        self.create_3d_check = self._create_check_box(
            "Create QC 3D View",
            output_defaults["create_3d_view"]
        )
        self.create_pdf_check = self._create_check_box(
            "Create PDF Report",
            output_defaults["create_pdf_report"]
        )
        self.create_pdf_check.CheckedChanged += self._update_pdf_dependency_ui
        self.export_csv_check = self._create_check_box(
            "Export CSV Data (Planned)",
            False
        )
        self.export_csv_check.Enabled = False
        self.preview_callouts_check = self._create_check_box(
            "Create Preview Callouts When No Deviation Data",
            output_defaults["create_preview_callouts_when_no_deviation_data"]
        )
        output_check_layout.Controls.Add(self.create_plan_check, 0, 0)
        output_check_layout.Controls.Add(self.create_3d_check, 1, 0)
        output_check_layout.Controls.Add(self.create_pdf_check, 0, 1)
        output_check_layout.Controls.Add(self.export_csv_check, 1, 1)
        output_check_layout.Controls.Add(self.preview_callouts_check, 0, 2)
        self._set_tooltip(
            self.create_plan_check,
            u"선택한 Source Plan View를 복제해 작업용 평면도를 생성합니다. "
            u"원본 View는 수정하지 않습니다."
        )
        self._set_tooltip(
            self.create_3d_check,
            u"기준 3D View를 복제해 QC 검토용 3D View를 생성합니다."
        )
        self._set_tooltip(
            self.create_pdf_check,
            u"PDF Report requires QC Plan View and creates it automatically."
        )
        self._set_tooltip(
            self.preview_callouts_check,
            u"실제 deviation 데이터가 없을 때 테스트용 Revision Cloud Callout을 "
            u"생성합니다. 실제 오차 결과처럼 해석하면 안 됩니다."
        )

        report_settings_group = self._create_group("Report Settings")
        report_settings_group.Margin = Padding(0, SECTION_GAP, 0, 0)
        output_layout.Controls.Add(report_settings_group, 0, 1)

        report_settings_layout = TableLayoutPanel()
        report_settings_layout.Dock = DockStyle.Fill
        report_settings_layout.AutoSize = True
        report_settings_layout.Padding = GROUP_CONTENT_PADDING
        report_settings_layout.ColumnCount = 3
        report_settings_layout.RowCount = 3
        report_settings_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, REPORT_LABEL_COLUMN_WIDTH)
        )
        report_settings_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 100.0)
        )
        report_settings_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, REPORT_BADGE_COLUMN_WIDTH)
        )
        for _index in range(3):
            report_settings_layout.RowStyles.Add(
                RowStyle(SizeType.Absolute, REPORT_ROW_HEIGHT)
            )
        report_settings_group.Controls.Add(report_settings_layout)
        self.report_settings_layout = report_settings_layout

        report_sheet_mode_label = self._create_report_setting_label(
            "Report Sheet Mode"
        )
        report_settings_layout.Controls.Add(report_sheet_mode_label, 0, 0)

        report_sheet_mode_layout = TableLayoutPanel()
        report_sheet_mode_layout.Dock = DockStyle.Fill
        report_sheet_mode_layout.Margin = Padding(0)
        report_sheet_mode_layout.ColumnCount = 2
        report_sheet_mode_layout.RowCount = 1
        report_sheet_mode_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 45.0)
        )
        report_sheet_mode_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 55.0)
        )
        report_sheet_mode_layout.RowStyles.Add(
            RowStyle(SizeType.Absolute, REPORT_ROW_HEIGHT)
        )
        report_settings_layout.Controls.Add(report_sheet_mode_layout, 1, 0)
        report_settings_layout.SetColumnSpan(report_sheet_mode_layout, 2)
        self.report_sheet_mode_layout = report_sheet_mode_layout

        self.report_sheet_mode_combo = ComboBox()
        self.report_sheet_mode_combo.Dock = DockStyle.Fill
        self.report_sheet_mode_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.report_sheet_mode_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.report_sheet_mode_combo.Margin = Padding(0, 4, 0, 4)
        self.report_sheet_mode_combo.BeginUpdate()
        try:
            self.report_sheet_mode_combo.Items.Add(
                REPORT_SHEET_MODE_CREATE_NEW_LABEL
            )
            self.report_sheet_mode_combo.Items.Add(
                REPORT_SHEET_MODE_EXISTING_LABEL
            )
        finally:
            self.report_sheet_mode_combo.EndUpdate()
        self.report_sheet_mode_combo.SelectedIndex = 0
        self.report_sheet_mode_combo.SelectedIndexChanged += (
            self._update_report_sheet_ui
        )
        report_sheet_mode_layout.Controls.Add(self.report_sheet_mode_combo, 0, 0)
        self._set_tooltip(
            self.report_sheet_mode_combo,
            u"PDF Report Sheet 생성 방식을 선택합니다. 기본값은 Scan QC 전용 "
            u"Clean Report Sheet 생성입니다."
        )

        self.existing_report_sheet_combo = ComboBox()
        self.existing_report_sheet_combo.Dock = DockStyle.Fill
        self.existing_report_sheet_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.existing_report_sheet_combo.DropDownWidth = 1400
        self.existing_report_sheet_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.existing_report_sheet_combo.Margin = Padding(
            REPORT_COLUMN_GAP,
            4,
            0,
            4
        )
        self._populate_existing_report_sheet_combo()
        report_sheet_mode_layout.Controls.Add(
            self.existing_report_sheet_combo,
            1,
            0
        )

        top_n_label = self._create_report_setting_label("Top N Callouts")
        report_settings_layout.Controls.Add(top_n_label, 0, 1)

        self.top_n_callouts_slider = TopNCalloutsSlider(
            self.default_top_n_callouts
        )
        self.top_n_callouts_slider.Dock = DockStyle.Fill
        self.top_n_callouts_slider.Margin = Padding(0)
        self.top_n_callouts_slider.Font = get_preferred_font(
            9.5,
            FontStyle.Bold
        )
        self.top_n_callouts_value = self.top_n_callouts_slider.Value
        self.top_n_callouts_slider.set_value_changed_callback(
            self._update_top_n_callouts_value
        )
        report_settings_layout.Controls.Add(self.top_n_callouts_slider, 1, 1)
        report_settings_layout.SetColumnSpan(self.top_n_callouts_slider, 2)
        self._set_tooltip(
            self.top_n_callouts_slider,
            u"도면과 리포트에 표시할 Review/Critical 상위 항목 수를 설정합니다."
        )
        self._set_tooltip(
            self.top_n_callouts_slider.ValueTextBox,
            u"도면과 리포트에 표시할 Review/Critical 상위 항목 수를 설정합니다."
        )

        paper_size_label = self._create_report_setting_label("Paper Size")
        report_settings_layout.Controls.Add(paper_size_label, 0, 2)

        self.paper_size_combo = ComboBox()
        self.paper_size_combo.Dock = DockStyle.Fill
        self.paper_size_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.paper_size_combo.MinimumSize = Size(0, CONTROL_HEIGHT)
        self.paper_size_combo.Margin = Padding(0, 4, 0, 4)
        self.paper_size_combo.BeginUpdate()
        try:
            self.paper_size_combo.Items.Add("A3 Landscape")
            self.paper_size_combo.Items.Add("A2 Landscape")
        finally:
            self.paper_size_combo.EndUpdate()
        self.paper_size_combo.SelectedIndex = (
            1 if self.default_paper_size == u"A2 Landscape" else 0
        )
        report_settings_layout.Controls.Add(self.paper_size_combo, 1, 2)
        report_settings_layout.SetColumnSpan(self.paper_size_combo, 2)
        self._set_tooltip(
            self.paper_size_combo,
            u"PDF Report Sheet 크기입니다. A3 Landscape가 기본이며, 선택한 "
            u"크기에 맞춰 도면과 Summary 비율을 조정합니다."
        )
        self._update_report_sheet_ui(None, None)
        self._update_pdf_dependency_ui(None, None)

        phase_note = Label()
        phase_note.Text = (
            "Scan QC creates selected working views and reports; original views and "
            "Point Cloud graphics remain unchanged."
        )
        phase_note.Dock = DockStyle.Fill
        phase_note.AutoSize = True
        phase_note.MinimumSize = Size(0, 36)
        phase_note.UseCompatibleTextRendering = True
        phase_note.ForeColor = SECONDARY_TEXT_COLOR
        phase_note.Font = get_preferred_font(9.0)
        phase_note.BackColor = HELP_BACKGROUND_COLOR
        phase_note.BorderStyle = BorderStyle.FixedSingle
        phase_note.TextAlign = ContentAlignment.MiddleLeft
        phase_note.Padding = Padding(12, 6, 12, 6)
        phase_note.Margin = Padding(0, 7, 0, 7)
        self.phase_note = phase_note
        main_layout.Controls.Add(phase_note, 0, 6)
        self._set_tooltip(
            phase_note,
            u"선택한 옵션에 따라 Scan QC 작업용 View와 Report를 생성합니다. "
            u"원본 Source Plan View와 Point Cloud 그래픽은 변경하지 않습니다."
        )

        footer_panel = Panel()
        footer_panel.Dock = DockStyle.Bottom
        footer_panel.AutoSize = False
        footer_panel.Height = SCAN_FOOTER_HEIGHT
        footer_panel.MinimumSize = Size(0, SCAN_FOOTER_HEIGHT)
        footer_panel.MaximumSize = Size(0, SCAN_FOOTER_HEIGHT)
        footer_panel.Padding = Padding(0, 10, 0, 14)
        footer_panel.Margin = Padding(0)
        root_layout.Controls.Add(footer_panel, 0, 2)
        self.footer_panel = footer_panel

        footer_button_strip = FlowLayoutPanel()
        footer_button_strip.Dock = DockStyle.Right
        footer_button_strip.AutoSize = False
        footer_button_strip.Width = (
            FOOTER_BUTTON_WIDTH * 2 + FOOTER_BUTTON_GAP
        )
        footer_button_strip.FlowDirection = FlowDirection.LeftToRight
        footer_button_strip.WrapContents = False
        footer_button_strip.Padding = Padding(0)
        footer_button_strip.Margin = Padding(0)
        footer_panel.Controls.Add(footer_button_strip)

        dock_none = getattr(DockStyle, "None")

        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.AutoSize = False
        cancel_button.Dock = dock_none
        cancel_button.Size = Size(
            FOOTER_BUTTON_WIDTH,
            FOOTER_BUTTON_HEIGHT
        )
        cancel_button.Margin = Padding(0, 0, FOOTER_BUTTON_GAP, 0)
        self._apply_secondary_button_style(cancel_button)
        cancel_button.DialogResult = DialogResult.Cancel
        footer_button_strip.Controls.Add(cancel_button)
        self.CancelButton = cancel_button

        self.run_button = Button()
        self.run_button.Text = "Run"
        self.run_button.AutoSize = False
        self.run_button.Dock = dock_none
        self.run_button.Size = Size(
            FOOTER_BUTTON_WIDTH,
            FOOTER_BUTTON_HEIGHT
        )
        self.run_button.Margin = Padding(0)
        self._apply_primary_button_style(self.run_button)
        self.run_button.Click += self._confirm
        footer_button_strip.Controls.Add(self.run_button)
        self.AcceptButton = self.run_button

        if point_clouds:
            self.point_cloud_combo.SelectedIndex = 0
        else:
            self.point_cloud_combo.Items.Add("No Point Cloud instances found")
            self.point_cloud_combo.SelectedIndex = 0
            self.point_cloud_combo.Enabled = False
            self.run_button.Enabled = False
            self.selected_point_cloud_label.Text = (
                "Analysis Point Cloud Source: Not available"
            )

        self._restore_ui_state()
        self._is_initializing = False
        self.ResumeLayout(True)
        self.PerformLayout()

    def _center_on_primary_working_area(self):
        working_area = Screen.PrimaryScreen.WorkingArea
        width = min(max(self.Width, self.MinimumSize.Width), working_area.Width)
        height = min(
            max(self.Height, self.MinimumSize.Height),
            working_area.Height
        )
        x = working_area.Left + ((working_area.Width - width) // 2)
        y = working_area.Top + ((working_area.Height - height) // 2)
        self.Bounds = Rectangle(x, y, width, height)

    def _apply_saved_window_bounds(self, sender, event_args):
        if self._window_bounds_applied:
            return
        self._window_bounds_applied = True

        state = load_report_state(self.settings)
        saved_bounds = state.get(WINDOW_STATE_KEY, {})
        if not isinstance(saved_bounds, dict):
            self._center_on_primary_working_area()
            return

        try:
            x = int(saved_bounds.get("x"))
            y = int(saved_bounds.get("y"))
            width = int(saved_bounds.get("width"))
            height = int(saved_bounds.get("height"))
            if width <= 0 or height <= 0:
                raise ValueError()
        except Exception:
            self._center_on_primary_working_area()
            return

        probe_bounds = Rectangle(x, y, max(1, width), max(1, height))
        working_area = Screen.FromRectangle(probe_bounds).WorkingArea
        safe_bounds = clamp_window_bounds(
            x,
            y,
            width,
            height,
            working_area.Left,
            working_area.Top,
            working_area.Width,
            working_area.Height,
            self.MinimumSize.Width,
            self.MinimumSize.Height
        )
        self.Bounds = Rectangle(
            safe_bounds[0],
            safe_bounds[1],
            safe_bounds[2],
            safe_bounds[3]
        )

    def _save_window_bounds_once(self, sender, event_args):
        if self._window_bounds_saved:
            return
        self._window_bounds_saved = True
        if self.WindowState == FormWindowState.Minimized:
            return

        if self.WindowState == FormWindowState.Maximized:
            bounds = self.RestoreBounds
        else:
            bounds = self.Bounds
        if bounds.Width <= 0 or bounds.Height <= 0:
            return

        state = load_report_state(self.settings)
        state[WINDOW_STATE_KEY] = {
            "x": bounds.X,
            "y": bounds.Y,
            "width": bounds.Width,
            "height": bounds.Height
        }
        save_report_state(self.settings, state)

    def _create_group(self, text):
        group = GroupBox()
        apply_scan_reference_section_style(
            group,
            text,
            get_preferred_font(10.5, FontStyle.Bold),
            SECTION_GAP
        )
        return group

    def cleanup(self):
        if getattr(self, "_cleanup_done", False):
            return
        self._cleanup_done = True
        for binding in self._secondary_hover_bindings:
            detach_border_hover(binding)
        self._secondary_hover_bindings = []
        dispose_tooltip(getattr(self, "tool_tip", None))
        self.tool_tip = None

    def _configure_scroll_fallback(self, sender, event_args):
        configure_content_scroll(
            self,
            self.content_panel,
            self.main_layout,
            0.94
        )
        log_layout_snapshot(
            u"Scan QC",
            self,
            self.content_panel,
            self.main_layout
        )
        log_section_snapshots(u"Scan QC", self)

    def _set_tooltip(self, control, text):
        try:
            self.tool_tip.SetToolTip(control, text)
        except Exception:
            pass

    def _create_tolerance_label(self, title, value, background_color):
        label = Label()
        label.Text = u"{0}\r\n{1}".format(title, value)
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.MinimumSize = Size(0, CONTROL_HEIGHT)
        label.TextAlign = ContentAlignment.MiddleCenter
        label.MinimumSize = Size(0, CONTROL_HEIGHT)
        label.BackColor = background_color
        label.ForeColor = NAVY_COLOR
        label.Font = get_preferred_font(9.5, FontStyle.Bold)
        label.Padding = Padding(0)
        label.Margin = Padding(
            TOLERANCE_COLUMN_GAP // 2,
            0,
            TOLERANCE_COLUMN_GAP // 2,
            0
        )
        return label

    def _create_input_label(self, text, background_color):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.MinimumSize = Size(0, TOLERANCE_HEADER_HEIGHT)
        label.TextAlign = ContentAlignment.MiddleCenter
        label.BackColor = background_color
        label.ForeColor = Color.FromArgb(30, 45, 61)
        label.Font = get_preferred_font(9.0, FontStyle.Bold)
        label.Padding = Padding(0)
        label.Margin = Padding(0)
        label.BorderStyle = getattr(BorderStyle, "None")
        return label

    def _create_tolerance_card(
        self,
        title,
        header_color,
        value,
        read_only=False
    ):
        card = TableLayoutPanel()
        card.Dock = DockStyle.Fill
        card.AutoSize = False
        card.MinimumSize = Size(
            0,
            TOLERANCE_HEADER_HEIGHT
            + TOLERANCE_HEADER_VALUE_GAP
            + TOLERANCE_VALUE_HEIGHT
        )
        card.Padding = Padding(0)
        card.ColumnCount = 1
        card.RowCount = 3
        card.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        card.RowStyles.Add(
            RowStyle(SizeType.Absolute, TOLERANCE_HEADER_HEIGHT)
        )
        card.RowStyles.Add(
            RowStyle(SizeType.Absolute, TOLERANCE_HEADER_VALUE_GAP)
        )
        card.RowStyles.Add(
            RowStyle(SizeType.Absolute, TOLERANCE_VALUE_HEIGHT)
        )
        card.CellBorderStyle = getattr(
            TableLayoutPanelCellBorderStyle,
            "None"
        )

        header = self._create_input_label(title, header_color)
        card.Controls.Add(header, 0, 0)

        spacer = Panel()
        spacer.Dock = DockStyle.Fill
        spacer.Margin = Padding(0)
        spacer.BackColor = Color.White
        card.Controls.Add(spacer, 0, 1)

        border_panel = Panel()
        border_panel.Dock = DockStyle.Fill
        border_panel.Margin = Padding(0)
        border_panel.Padding = Padding(1)
        border_panel.BackColor = TOLERANCE_BORDER_COLOR
        card.Controls.Add(border_panel, 0, 2)

        value_layout = TableLayoutPanel()
        value_layout.Dock = DockStyle.Fill
        value_layout.AutoSize = False
        value_layout.Margin = Padding(0)
        value_layout.Padding = Padding(0)
        value_layout.BackColor = Color.White
        value_layout.ColumnCount = 1
        value_layout.RowCount = 3
        value_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        value_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
        value_layout.RowStyles.Add(RowStyle(SizeType.AutoSize))
        value_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
        value_layout.CellBorderStyle = getattr(
            TableLayoutPanelCellBorderStyle,
            "None"
        )
        border_panel.Controls.Add(value_layout)

        value_control = self._create_tolerance_text_box(value)
        value_control.ReadOnly = read_only
        value_control.TabStop = not read_only
        value_layout.Controls.Add(value_control, 0, 1)
        return card, border_panel, value_control

    def _create_report_setting_label(self, text):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.MinimumSize = Size(0, CONTROL_HEIGHT)
        label.TextAlign = ContentAlignment.MiddleLeft
        label.ForeColor = NAVY_COLOR
        label.Font = get_preferred_font(9.5, FontStyle.Bold)
        label.Margin = Padding(0, 4, REPORT_COLUMN_GAP, 4)
        return label

    def _create_tolerance_text_box(self, value):
        text_box = TextBox()
        text_box.Text = format_mm_value(value)
        text_box.Dock = DockStyle.Fill
        text_box.AutoSize = True
        text_box.Padding = Padding(0)
        text_box.Margin = Padding(0)
        text_box.BorderStyle = getattr(BorderStyle, "None")
        text_box.BackColor = Color.White
        text_box.ForeColor = Color.FromArgb(30, 45, 61)
        text_box.Font = get_preferred_font(11.0, FontStyle.Bold)
        text_box.TextAlign = HorizontalAlignment.Center
        return text_box

    def _create_check_box(self, text, checked):
        check_box = CheckBox()
        check_box.Text = text
        check_box.Dock = DockStyle.Fill
        check_box.AutoSize = False
        check_box.MinimumSize = Size(0, CONTROL_HEIGHT)
        check_box.TextAlign = ContentAlignment.MiddleLeft
        check_box.Margin = Padding(6, 4, 6, 4)
        check_box.ForeColor = NAVY_COLOR
        check_box.Font = get_preferred_font(9.5)
        check_box.Checked = checked
        try:
            check_box.AutoEllipsis = False
        except Exception:
            pass
        return check_box

    def _apply_secondary_button_style(self, button):
        apply_secondary_button_style(button)
        button.FlatAppearance.BorderColor = BORDER_COLOR
        button.FlatAppearance.MouseOverBackColor = Color.White
        button.FlatAppearance.MouseDownBackColor = Color.White
        self._secondary_hover_bindings.append(attach_border_hover(button))

    def _apply_primary_button_style(self, button):
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = BUTTON_NAVY_COLOR
        button.FlatAppearance.MouseOverBackColor = BUTTON_HOVER_COLOR
        button.FlatAppearance.MouseDownBackColor = NAVY_COLOR
        button.BackColor = BUTTON_NAVY_COLOR
        button.ForeColor = Color.White
        button.UseVisualStyleBackColor = False

    def _create_target_action_button(self, text, handler):
        button = Button()
        button.Text = text
        button.AutoSize = False
        button.Size = Size(
            SMALL_ACTION_BUTTON_WIDTH,
            SMALL_ACTION_BUTTON_HEIGHT
        )
        button.Margin = Padding(0, 0, 12, 0)
        self._apply_secondary_button_style(button)
        button.Click += handler
        return button

    def _request_target_parameter_action(self, action_name):
        if self.target_action_handler is None:
            return

        selected_index = self.source_plan_combo.SelectedIndex
        if 0 <= selected_index < len(self.source_plan_views):
            source_plan_view = self.source_plan_views[selected_index]
        else:
            source_plan_view = None

        action_result = {}
        self.Hide()
        try:
            action_result = self.target_action_handler(
                action_name,
                source_plan_view
            ) or {}
        except Exception as ex:
            action_result = {"error": u"{0}".format(ex)}
        finally:
            self.Show()
            self.Activate()
            self.BringToFront()

        if action_result.get("cancelled", False):
            return

        if source_plan_view is not None and "target_count" in action_result:
            source_view_id = get_element_id_value(source_plan_view.Id)
            self.target_counts_by_view_id[source_view_id] = action_result.get(
                "target_count",
                0
            )
        self._update_target_status_label()
        self._set_target_action_message(
            action_result.get("message", action_result.get("error", u""))
        )

    def _request_mark_selected(self, sender, event_args):
        self._request_target_parameter_action(u"mark_selected")

    def _request_clear_selected(self, sender, event_args):
        self._request_target_parameter_action(u"clear_selected")

    def _request_select_targets(self, sender, event_args):
        self._request_target_parameter_action(u"select_targets")

    def _set_target_action_message(self, message):
        base_text = u"Target filters are optional and combined with AND conditions."
        if message:
            self.target_filter_help_label.Text = u"{0}  {1}".format(
                base_text,
                message
            )
        else:
            self.target_filter_help_label.Text = base_text
        if not self._is_initializing:
            self.PerformLayout()
            self._configure_scroll_fallback(None, None)

    def _capture_ui_state(self):
        return {
            "analysis_scope_index": self.analysis_scope_combo.SelectedIndex,
            "source_plan_index": self.source_plan_combo.SelectedIndex,
            "interior_walls_only": self.interior_walls_only_check.Checked,
            "new_construction_only": self.new_construction_only_check.Checked,
            "exclude_exterior_walls": self.exclude_exterior_walls_check.Checked,
            "only_scan_qc_target_yes": self.only_scan_qc_target_yes_check.Checked,
            "point_cloud_index": self.point_cloud_combo.SelectedIndex,
            "ok_max_text": format_mm_value(self._last_valid_ok_max),
            "review_max_text": format_mm_value(
                self._last_valid_review_max
            ),
            "create_plan_view": self.create_plan_check.Checked,
            "create_3d_view": self.create_3d_check.Checked,
            "create_pdf_report": self.create_pdf_check.Checked,
            "pdf_auto_enabled_plan_view": self.pdf_auto_enabled_plan_view,
            "preview_callouts": self.preview_callouts_check.Checked,
            "report_sheet_mode_index": self.report_sheet_mode_combo.SelectedIndex,
            "existing_report_sheet_index": (
                self.existing_report_sheet_combo.SelectedIndex
            ),
            "top_n_callouts_value": self.top_n_callouts_slider.Value,
            "top_n_callouts_text": u"{0}".format(
                self.top_n_callouts_slider.Value
            ),
            "paper_size_index": self.paper_size_combo.SelectedIndex
        }

    def _restore_combo_index(self, combo, value):
        try:
            index = int(value)
        except Exception:
            return
        if 0 <= index < combo.Items.Count:
            combo.SelectedIndex = index

    def _restore_ui_state(self):
        state = self.initial_state
        if not state:
            self._update_source_plan_view(None, None)
            self._update_selected_point_cloud(None, None)
            return

        self._restore_combo_index(
            self.analysis_scope_combo,
            state.get("analysis_scope_index", 0)
        )
        self._restore_combo_index(
            self.source_plan_combo,
            state.get("source_plan_index", 0)
        )
        self.interior_walls_only_check.Checked = bool(
            state.get("interior_walls_only", False)
        )
        self.new_construction_only_check.Checked = bool(
            state.get("new_construction_only", False)
        )
        self.exclude_exterior_walls_check.Checked = bool(
            state.get("exclude_exterior_walls", False)
        )
        self.only_scan_qc_target_yes_check.Checked = bool(
            state.get("only_scan_qc_target_yes", False)
        )
        self._restore_combo_index(
            self.point_cloud_combo,
            state.get("point_cloud_index", 0)
        )
        self.ok_max_text.Text = state.get(
            "ok_max_text",
            self.ok_max_text.Text
        )
        self.review_max_text.Text = state.get(
            "review_max_text",
            self.review_max_text.Text
        )
        self._commit_tolerance_inputs()
        self.create_plan_check.Checked = bool(
            state.get("create_plan_view", self.create_plan_check.Checked)
        )
        self.create_3d_check.Checked = bool(
            state.get("create_3d_view", self.create_3d_check.Checked)
        )
        self.preview_callouts_check.Checked = bool(
            state.get("preview_callouts", self.preview_callouts_check.Checked)
        )
        self.pdf_auto_enabled_plan_view = bool(
            state.get("pdf_auto_enabled_plan_view", False)
        )
        self._restore_combo_index(
            self.report_sheet_mode_combo,
            state.get("report_sheet_mode_index", 0)
        )
        self._restore_combo_index(
            self.existing_report_sheet_combo,
            state.get("existing_report_sheet_index", 0)
        )
        self.top_n_callouts_slider.Value = state.get(
            "top_n_callouts_value",
            state.get(
                "top_n_callouts_text",
                self.top_n_callouts_slider.Value
            )
        )
        self._restore_combo_index(
            self.paper_size_combo,
            state.get("paper_size_index", self.paper_size_combo.SelectedIndex)
        )
        self.create_pdf_check.Checked = bool(
            state.get("create_pdf_report", self.create_pdf_check.Checked)
        )
        self._update_analysis_scope_ui(None, None)
        self._update_source_plan_view(None, None)
        self._update_selected_point_cloud(None, None)
        self._update_report_sheet_ui(None, None)
        self._update_pdf_dependency_ui(None, None)

    def _try_parse_tolerance(self, text_value):
        try:
            value = float(text_value)
            if value < 0:
                raise ValueError()
            return value
        except Exception:
            return None

    def _set_tolerance_feedback(self, control, is_valid, message=u""):
        if control is None:
            return
        control.BackColor = Color.White
        if control is self.ok_max_text:
            default_tooltip = self._ok_tolerance_tooltip
            border_panel = self.ok_max_border_panel
        else:
            default_tooltip = self._review_tolerance_tooltip
            border_panel = self.review_max_border_panel
        border_panel.BackColor = (
            TOLERANCE_BORDER_COLOR
            if is_valid
            else Color.FromArgb(214, 132, 132)
        )
        self._set_tooltip(control, message or default_tooltip)

    def _get_tolerance_validation(self):
        ok_max = self._try_parse_tolerance(self.ok_max_text.Text)
        review_max = self._try_parse_tolerance(self.review_max_text.Text)
        if ok_max is None:
            return None, None, u"OK Max는 0 이상의 숫자여야 합니다."
        if review_max is None:
            return None, None, u"Review Max는 0 이상의 숫자여야 합니다."
        if review_max <= ok_max:
            return (
                None,
                None,
                u"Review Max는 OK Max보다 커야 합니다. 마지막 정상값을 유지합니다."
            )
        return ok_max, review_max, u""

    def _handle_tolerance_text_changed(self, sender, event_args):
        if self._updating_tolerances:
            return
        ok_max, review_max, message = self._get_tolerance_validation()
        if message:
            self._set_tolerance_feedback(sender, False, message)
            return
        self._last_valid_ok_max = ok_max
        self._last_valid_review_max = review_max
        self._set_tolerance_feedback(self.ok_max_text, True)
        self._set_tolerance_feedback(self.review_max_text, True)
        self._update_critical_value_display()

    def _handle_tolerance_key_down(self, sender, event_args):
        if event_args.KeyCode != Keys.Enter:
            return
        self._commit_tolerance_inputs(sender)
        try:
            event_args.SuppressKeyPress = True
            event_args.Handled = True
        except Exception:
            pass

    def _handle_tolerance_leave(self, sender, event_args):
        self._commit_tolerance_inputs(sender)

    def _commit_tolerance_inputs(self, trigger_control=None):
        if self._updating_tolerances:
            return True
        ok_max, review_max, message = self._get_tolerance_validation()
        if not message:
            self._last_valid_ok_max = ok_max
            self._last_valid_review_max = review_max
            self._set_tolerance_feedback(self.ok_max_text, True)
            self._set_tolerance_feedback(self.review_max_text, True)
            self._update_critical_value_display()
            return True

        self._updating_tolerances = True
        try:
            self.ok_max_text.Text = format_mm_value(
                self._last_valid_ok_max
            )
            self.review_max_text.Text = format_mm_value(
                self._last_valid_review_max
            )
            self._update_critical_value_display()
        finally:
            self._updating_tolerances = False

        if trigger_control is None:
            self._set_tolerance_feedback(self.ok_max_text, False, message)
            self._set_tolerance_feedback(self.review_max_text, False, message)
        else:
            other_control = (
                self.review_max_text
                if trigger_control is self.ok_max_text
                else self.ok_max_text
            )
            self._set_tolerance_feedback(other_control, True)
            self._set_tolerance_feedback(trigger_control, False, message)
        return False

    def _update_critical_value_display(self):
        display_value = format_mm_value(self._last_valid_review_max)
        self.critical_value_text.Text = u"{0} mm+".format(display_value)

    def _get_tolerance_options(self):
        self._commit_tolerance_inputs()
        return {
            "ok_max": self._last_valid_ok_max,
            "review_max": self._last_valid_review_max,
            "critical_min": self._last_valid_review_max
        }, []

    def _get_top_n_callouts_options(self):
        return self.top_n_callouts_value, u""

    def _update_top_n_callouts_value(self, value):
        self.top_n_callouts_value = value

    def _get_report_sheet_options(self):
        if self.report_sheet_mode_combo.SelectedIndex == 1:
            report_sheet_mode = REPORT_SHEET_MODE_EXISTING
            self._ensure_existing_report_sheets_loaded()
        else:
            report_sheet_mode = REPORT_SHEET_MODE_CREATE_NEW

        report_sheet_id = None
        report_sheet_name = u""
        if (
            report_sheet_mode == REPORT_SHEET_MODE_EXISTING
            and self.existing_report_sheets
        ):
            selected_sheet_index = self.existing_report_sheet_combo.SelectedIndex
            if 0 <= selected_sheet_index < len(self.existing_report_sheets):
                selected_sheet = self.existing_report_sheets[selected_sheet_index]
                report_sheet_id = get_element_id_value(selected_sheet.Id)
                report_sheet_name = get_sheet_name(selected_sheet)

        return {
            "report_sheet_mode": report_sheet_mode,
            "report_sheet_mode_label": (
                REPORT_SHEET_MODE_EXISTING_LABEL
                if report_sheet_mode == REPORT_SHEET_MODE_EXISTING
                else REPORT_SHEET_MODE_CREATE_NEW_LABEL
            ),
            "report_sheet_id": report_sheet_id,
            "report_sheet_name": report_sheet_name
        }

    def _get_paper_size_option(self):
        if self.paper_size_combo.SelectedIndex == 1:
            return u"A2 Landscape"
        return u"A3 Landscape"

    def _get_target_wall_filter_options(self):
        return {
            "interior_walls_only": self.interior_walls_only_check.Checked,
            "new_construction_only": self.new_construction_only_check.Checked,
            "exclude_exterior_walls": self.exclude_exterior_walls_check.Checked,
            "only_scan_qc_target_yes": self.only_scan_qc_target_yes_check.Checked
        }

    def _get_default_pdf_folder(self):
        state = load_report_state(self.settings)
        last_folder = state.get("last_pdf_folder", u"")
        if last_folder and os.path.isdir(last_folder):
            return last_folder

        configured_folder = get_report_output_folder(self.settings)
        if os.path.isdir(configured_folder):
            return configured_folder

        try:
            os.makedirs(configured_folder)
            return configured_folder
        except Exception:
            return os.path.expanduser("~")

    def _select_pdf_output_path(self):
        timestamp = DateTime.Now.ToString("yyMMdd_HHmmss")
        default_file_name = u"Scan_QC_Report_{0}.pdf".format(timestamp)
        save_dialog = SaveFileDialog()
        try:
            save_dialog.Title = "Save Scan QC PDF Report"
            save_dialog.Filter = "PDF files (*.pdf)|*.pdf"
            save_dialog.DefaultExt = "pdf"
            save_dialog.AddExtension = True
            save_dialog.OverwritePrompt = True
            save_dialog.FileName = default_file_name
            save_dialog.InitialDirectory = self._get_default_pdf_folder()
            dialog_result = save_dialog.ShowDialog(self)
            if dialog_result != DialogResult.OK:
                return u"", timestamp, True, u""

            selected_path = save_dialog.FileName
            selected_folder = os.path.dirname(selected_path)
            if selected_folder:
                report_state = load_report_state(self.settings)
                report_state["last_pdf_folder"] = selected_folder
                _saved, save_warning = save_report_state(
                    self.settings,
                    report_state
                )
            else:
                save_warning = u""
            return selected_path, timestamp, False, save_warning
        finally:
            try:
                save_dialog.Dispose()
            except Exception:
                pass

    def _update_selected_point_cloud(self, sender, event_args):
        selected_index = self.point_cloud_combo.SelectedIndex
        if 0 <= selected_index < len(self.point_clouds):
            selected_point_cloud = self.point_clouds[selected_index]
            point_cloud_name = get_point_cloud_name(selected_point_cloud)
            self.selected_point_cloud_label.Text = (
                u"Analysis Point Cloud Source: {0}".format(
                    point_cloud_name
                )
            )
            self.tool_tip.SetToolTip(
                self.point_cloud_combo,
                point_cloud_name
            )
            self.tool_tip.SetToolTip(
                self.selected_point_cloud_label,
                point_cloud_name
            )

    def _update_source_plan_view(self, sender, event_args):
        selected_index = self.source_plan_combo.SelectedIndex
        if 0 <= selected_index < len(self.source_plan_views):
            selected_source_plan_view = self.source_plan_views[selected_index]
            self.selected_source_plan_label.Text = u"Selected Source Plan View: {0}".format(
                get_source_plan_view_name(selected_source_plan_view)
            )
            source_plan_label = get_source_plan_view_label(
                selected_source_plan_view
            )
            self.tool_tip.SetToolTip(
                self.source_plan_combo,
                source_plan_label
            )
            self.tool_tip.SetToolTip(
                self.selected_source_plan_label,
                source_plan_label
            )
        self._update_target_status_label()

    def _update_target_status_label(self):
        if not hasattr(self, "target_status_label"):
            return
        installed = self.target_parameter_status.get("available", False)
        installed_text = u"Installed" if installed else u"Not Installed"
        target_count_text = u"—"
        selected_index = self.source_plan_combo.SelectedIndex
        if 0 <= selected_index < len(self.source_plan_views):
            view_id = get_element_id_value(
                self.source_plan_views[selected_index].Id
            )
            if view_id in self.target_counts_by_view_id:
                target_count_text = u"{0}".format(
                    self.target_counts_by_view_id.get(view_id, 0)
                )
        self.target_status_label.Text = (
            u"SCAN_QC_TARGET {0}    |    Targets: {1}".format(
                installed_text,
                target_count_text
            )
        )

    def _update_analysis_scope_ui(self, sender, event_args):
        show_selected_walls = self.analysis_scope_combo.SelectedIndex == 1
        self.selected_walls_group.Visible = show_selected_walls
        if show_selected_walls:
            self.selected_walls_row_style.SizeType = SizeType.AutoSize
        else:
            self.selected_walls_row_style.SizeType = SizeType.Absolute
            self.selected_walls_row_style.Height = 0.0
        self.PerformLayout()
        if not self._is_initializing:
            self._configure_scroll_fallback(None, None)

    def _populate_existing_report_sheet_combo(self):
        self.existing_report_sheet_combo.BeginUpdate()
        try:
            self.existing_report_sheet_combo.Items.Clear()
            for sheet in self.existing_report_sheets:
                self.existing_report_sheet_combo.Items.Add(
                    get_sheet_label(sheet)
                )
            if self.existing_report_sheets:
                self.existing_report_sheet_combo.SelectedIndex = 0
            elif self.existing_report_sheets_loaded:
                self.existing_report_sheet_combo.Items.Add(
                    "No existing Sheets found"
                )
                self.existing_report_sheet_combo.SelectedIndex = 0
            else:
                self.existing_report_sheet_combo.Items.Add(
                    "Sheets load when Use Existing Sheet is selected"
                )
                self.existing_report_sheet_combo.SelectedIndex = 0
        finally:
            self.existing_report_sheet_combo.EndUpdate()

    def _ensure_existing_report_sheets_loaded(self):
        if self.existing_report_sheets_loaded:
            return
        self.existing_report_sheets_loaded = True
        if self.existing_report_sheet_loader is not None:
            try:
                self.existing_report_sheets = list(
                    self.existing_report_sheet_loader() or []
                )
            except Exception:
                self.existing_report_sheets = []
        self._populate_existing_report_sheet_combo()

    def _update_report_sheet_ui(self, sender, event_args):
        use_existing_sheet = self.report_sheet_mode_combo.SelectedIndex == 1
        if (
            use_existing_sheet
            and not self._is_initializing
            and not self.existing_report_sheets_loaded
        ):
            self._ensure_existing_report_sheets_loaded()
        self.existing_report_sheet_combo.Visible = use_existing_sheet
        self.existing_report_sheet_combo.Enabled = (
            use_existing_sheet and bool(self.existing_report_sheets)
        )
        self.report_sheet_mode_layout.SetColumnSpan(
            self.report_sheet_mode_combo,
            1 if use_existing_sheet else 2
        )

    def _update_pdf_dependency_ui(self, sender, event_args):
        if self.create_pdf_check.Checked:
            if not self.create_plan_check.Checked:
                self.pdf_auto_enabled_plan_view = True
            self.create_plan_check.Checked = True
            self.create_plan_check.Enabled = False
        else:
            self.create_plan_check.Enabled = True
            self.pdf_auto_enabled_plan_view = False

    def _confirm(self, sender, event_args):
        selected_index = self.point_cloud_combo.SelectedIndex
        if selected_index < 0 or selected_index >= len(self.point_clouds):
            return

        source_plan_index = self.source_plan_combo.SelectedIndex
        if source_plan_index < 0 or source_plan_index >= len(self.source_plan_views):
            return

        selected_point_cloud = self.point_clouds[selected_index]
        selected_source_plan_view = self.source_plan_views[source_plan_index]
        selected_output_options = []

        if self.create_plan_check.Checked:
            selected_output_options.append(u"Create QC Plan View")
        if self.create_3d_check.Checked:
            selected_output_options.append(u"Create QC 3D View")
        if self.create_pdf_check.Checked:
            selected_output_options.append(u"Create PDF Report")
        if self.export_csv_check.Checked:
            selected_output_options.append(u"Export CSV Data")
        if self.preview_callouts_check.Checked:
            selected_output_options.append(
                u"Create Preview Callouts When No Deviation Data"
            )

        if self.analysis_scope_combo.SelectedIndex == 1:
            analysis_scope = ANALYSIS_SCOPE_SELECTED_WALLS
        else:
            analysis_scope = ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL

        tolerance_mm, tolerance_warnings = self._get_tolerance_options()
        top_n_callouts, top_n_warning = self._get_top_n_callouts_options()
        if top_n_warning:
            tolerance_warnings.append(top_n_warning)
        report_sheet_options = self._get_report_sheet_options()

        pdf_output_path = u""
        report_timestamp = u""
        pdf_export_cancelled = False
        pdf_path_warning = u""
        if self.create_pdf_check.Checked:
            (
                pdf_output_path,
                report_timestamp,
                pdf_export_cancelled,
                pdf_path_warning
            ) = self._select_pdf_output_path()
            if pdf_path_warning:
                tolerance_warnings.append(pdf_path_warning)
            if pdf_export_cancelled:
                self.result = None
                self.DialogResult = DialogResult.Cancel
                self.Close()
                return

        self.result = {
            "point_cloud_name": get_point_cloud_name(selected_point_cloud),
            "point_cloud_id": get_element_id_value(selected_point_cloud.Id),
            "source_plan_view_name": get_source_plan_view_name(selected_source_plan_view),
            "source_plan_view_id": get_element_id_value(selected_source_plan_view.Id),
            "tolerance_mm": tolerance_mm,
            "tolerance_warnings": tolerance_warnings,
            "target_wall_filter": self._get_target_wall_filter_options(),
            "top_n_callouts": top_n_callouts,
            "paper_size": self._get_paper_size_option(),
            "create_plan_view": self.create_plan_check.Checked,
            "create_3d_view": self.create_3d_check.Checked,
            "create_pdf_report": self.create_pdf_check.Checked,
            "pdf_save_dialog_result": (
                u"Selected" if self.create_pdf_check.Checked else u"Not requested"
            ),
            "pdf_required_qc_plan_view": (
                u"Auto-created"
                if self.create_pdf_check.Checked and self.pdf_auto_enabled_plan_view
                else (
                    u"Existing"
                    if self.create_pdf_check.Checked
                    else u"Not requested"
                )
            ),
            "pdf_output_path": pdf_output_path,
            "report_timestamp": report_timestamp,
            "pdf_export_cancelled": pdf_export_cancelled,
            "export_csv": self.export_csv_check.Checked,
            "create_preview_callouts_when_no_deviation_data": (
                self.preview_callouts_check.Checked
            ),
            "analysis_scope": analysis_scope,
            "analysis_scope_label": ANALYSIS_SCOPE_LABELS[analysis_scope],
            "selected_output_options": selected_output_options
        }
        self.result.update(report_sheet_options)
        self.DialogResult = DialogResult.OK
        self.Close()


def request_scan_qc_options(
    selected_wall_count,
    point_clouds,
    source_plan_views,
    existing_report_sheets,
    default_source_plan_view_id,
    settings,
    target_parameter_status=None,
    target_counts_by_view_id=None,
    initial_state=None,
    target_action_handler=None,
    existing_report_sheet_loader=None,
    startup_metrics=None
):
    def _scan_profile_metrics():
        metrics = get_runtime_diagnostics()
        if startup_metrics:
            total_watch = startup_metrics.get("total_watch")
            if total_watch is not None:
                metrics["scan_button_elapsed_ms"] = total_watch.ElapsedMilliseconds
        return metrics

    close_profile = create_ui_close_profile(
        u"Scan QC",
        _scan_profile_metrics
    )
    construction_watch = Stopwatch.StartNew()
    options_form = ScanQcForm(
        selected_wall_count,
        point_clouds,
        source_plan_views,
        existing_report_sheets,
        default_source_plan_view_id,
        settings,
        target_parameter_status,
        target_counts_by_view_id,
        initial_state,
        target_action_handler,
        existing_report_sheet_loader
    )
    construction_watch.Stop()
    close_profile.attach(options_form)
    if startup_metrics:
        logger = startup_metrics.get("logger")
        if logger is not None:
            try:
                logger.info(
                    "[Scan QC Startup] Form/control construction: {0} ms".format(
                        construction_watch.ElapsedMilliseconds
                    )
                )
                logger.info(
                    "[Scan QC Startup] ComboBox population: {0} ms".format(
                        options_form.combo_population_ms
                    )
                )
                total_watch = startup_metrics.get("total_watch")
                if total_watch is not None:
                    logger.info(
                        "[Scan QC Startup] Total before Form display: {0} ms".format(
                            total_watch.ElapsedMilliseconds
                        )
                    )
            except Exception:
                pass
    try:
        dialog_result = close_profile.show_dialog()
        selected_options = options_form.result
    finally:
        close_profile.dispose()

    if dialog_result != DialogResult.OK or selected_options is None:
        return None

    return selected_options
