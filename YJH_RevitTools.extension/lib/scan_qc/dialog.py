# -*- coding: utf-8 -*-

import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import DateTime
from System.Drawing import Color, ContentAlignment, Font, FontFamily, FontStyle, Size
from System.Windows.Forms import (
    AutoScaleMode,
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
    GroupBox,
    HorizontalAlignment,
    Label,
    Padding,
    RowStyle,
    SaveFileDialog,
    SizeType,
    TableLayoutPanel,
    TextBox,
    ToolTip
)

from scan_qc.collectors import get_element_id_value, get_point_cloud_name
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


NAVY_COLOR = Color.FromArgb(38, 54, 69)
BUTTON_NAVY_COLOR = Color.FromArgb(83, 103, 119)
BUTTON_HOVER_COLOR = Color.FromArgb(70, 88, 103)
MUTED_COLOR = Color.FromArgb(95, 111, 125)
BORDER_COLOR = Color.FromArgb(214, 221, 227)
HELP_BACKGROUND_COLOR = Color.FromArgb(248, 249, 250)
WARNING_BACKGROUND_COLOR = Color.FromArgb(255, 241, 230)
REPORT_SHEET_MODE_CREATE_NEW = u"create_new"
REPORT_SHEET_MODE_EXISTING = u"existing"
REPORT_SHEET_MODE_CREATE_NEW_LABEL = u"Create New Scan QC Report Sheet"
REPORT_SHEET_MODE_EXISTING_LABEL = u"Use Existing Sheet"


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


def format_mm_value(value):
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return u"{0}".format(int(numeric_value))
    except (TypeError, ValueError):
        pass

    return u"{0}".format(value)


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
        settings
    ):
        Form.__init__(self)
        self.result = None
        self.point_clouds = point_clouds
        self.source_plan_views = source_plan_views
        self.existing_report_sheets = existing_report_sheets or []
        self.settings = settings
        self.pdf_auto_enabled_plan_view = False
        tolerance_mm = get_tolerance_mm(settings)
        deviation_options = get_deviation_options(settings)
        self.default_tolerance_mm = tolerance_mm
        self.default_top_n_callouts = deviation_options["top_n_callouts"]
        output_defaults = get_output_options(settings)
        report_defaults = get_report_options(settings)
        target_filter_defaults = get_target_wall_filter_defaults(settings)
        self.default_paper_size = report_defaults.get("paper_size", u"A3 Landscape")

        self.Text = "Revit QC - Scan QC"
        self.ClientSize = Size(1220, 1440)
        self.MinimumSize = Size(1100, 1180)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(9.5)
        self.AutoScaleMode = AutoScaleMode.Font
        self.AutoScroll = True
        self.tool_tip = ToolTip()
        self.tool_tip.AutoPopDelay = 12000
        self.tool_tip.InitialDelay = 450
        self.tool_tip.ReshowDelay = 120
        self.tool_tip.ShowAlways = True

        main_layout = TableLayoutPanel()
        main_layout.Dock = DockStyle.Fill
        main_layout.Padding = Padding(34, 24, 34, 30)
        main_layout.ColumnCount = 1
        main_layout.RowCount = 11
        main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 50.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 110.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 150.0))
        self.selected_walls_row_style = RowStyle(SizeType.Absolute, 0.0)
        main_layout.RowStyles.Add(self.selected_walls_row_style)
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 190.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 180.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 164.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 340.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 102.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 64.0))
        self.Controls.Add(main_layout)

        intro_label = Label()
        intro_label.Text = "Scan QC Setup"
        intro_label.Dock = DockStyle.Fill
        intro_label.AutoSize = False
        intro_label.ForeColor = NAVY_COLOR
        intro_label.Font = get_preferred_font(15.0, FontStyle.Bold)
        intro_label.Padding = Padding(0, 5, 0, 0)
        main_layout.Controls.Add(intro_label, 0, 0)

        analysis_scope_group = self._create_group("Analysis Scope")
        main_layout.Controls.Add(analysis_scope_group, 0, 1)
        self._set_tooltip(
            analysis_scope_group,
            u"검토 범위를 선택합니다. Active Plan Level은 선택한 평면도 기준 "
            u"전체 벽을 검토하고, Selected Walls는 사용자가 선택한 벽만 "
            u"검토합니다."
        )

        analysis_scope_layout = TableLayoutPanel()
        analysis_scope_layout.Dock = DockStyle.Fill
        analysis_scope_layout.Padding = Padding(12, 10, 12, 10)
        analysis_scope_layout.ColumnCount = 1
        analysis_scope_layout.RowCount = 1
        analysis_scope_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        analysis_scope_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        analysis_scope_group.Controls.Add(analysis_scope_layout)

        self.analysis_scope_combo = ComboBox()
        self.analysis_scope_combo.Dock = DockStyle.Fill
        self.analysis_scope_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.analysis_scope_combo.Margin = Padding(0, 2, 0, 2)
        self.analysis_scope_combo.Items.Add(
            ANALYSIS_SCOPE_LABELS[ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL]
        )
        self.analysis_scope_combo.Items.Add(
            ANALYSIS_SCOPE_LABELS[ANALYSIS_SCOPE_SELECTED_WALLS]
        )
        self.analysis_scope_combo.SelectedIndex = 0
        analysis_scope_layout.Controls.Add(self.analysis_scope_combo, 0, 0)
        self._set_tooltip(
            self.analysis_scope_combo,
            u"검토 범위를 선택합니다. Active Plan Level은 선택한 Source Plan "
            u"View 기준 벽을 수집하고, Selected Walls는 현재 선택 또는 실행 중 "
            u"선택한 벽만 사용합니다."
        )

        self.selected_walls_group = self._create_group("Selected Walls")
        self.selected_walls_group.Visible = False
        main_layout.Controls.Add(self.selected_walls_group, 0, 3)
        self._set_tooltip(
            self.selected_walls_group,
            u"Selected Walls 모드에서 검토할 Revit Wall 요소를 지정합니다. "
            u"Run 실행 시 선택된 벽이 없으면 Revit 선택 워크플로우로 벽을 "
            u"선택합니다."
        )

        selected_walls_layout = TableLayoutPanel()
        selected_walls_layout.Dock = DockStyle.Fill
        selected_walls_layout.Padding = Padding(12, 6, 12, 8)
        selected_walls_layout.ColumnCount = 1
        selected_walls_layout.RowCount = 2
        selected_walls_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        selected_walls_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 24.0))
        selected_walls_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 32.0))
        self.selected_walls_group.Controls.Add(selected_walls_layout)

        selected_wall_count_label = Label()
        selected_wall_count_label.Text = u"Current selected Wall count: {0}".format(
            selected_wall_count
        )
        selected_wall_count_label.Dock = DockStyle.Fill
        selected_wall_count_label.AutoSize = False
        selected_wall_count_label.ForeColor = NAVY_COLOR
        selected_wall_count_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        selected_walls_layout.Controls.Add(selected_wall_count_label, 0, 0)

        selected_wall_instruction = Label()
        if selected_wall_count > 0:
            selected_wall_instruction.Text = "Run uses the current Revit Wall selection."
        else:
            selected_wall_instruction.Text = "Click Run to pick Walls in Revit."
        selected_wall_instruction.Dock = DockStyle.Fill
        selected_wall_instruction.AutoSize = False
        selected_wall_instruction.ForeColor = MUTED_COLOR
        selected_wall_instruction.TextAlign = ContentAlignment.MiddleLeft
        selected_walls_layout.Controls.Add(selected_wall_instruction, 0, 1)

        self.analysis_scope_combo.SelectedIndexChanged += self._update_analysis_scope_ui
        self._update_analysis_scope_ui(None, None)

        source_plan_group = self._create_group("Source Plan View")
        main_layout.Controls.Add(source_plan_group, 0, 2)
        self._set_tooltip(
            source_plan_group,
            u"QC Plan View와 Active Plan Level 범위의 기준이 되는 평면도입니다. "
            u"원본 View는 수정하지 않고 복제된 Scan QC View만 생성합니다."
        )

        source_plan_layout = TableLayoutPanel()
        source_plan_layout.Dock = DockStyle.Fill
        source_plan_layout.Padding = Padding(12, 10, 12, 10)
        source_plan_layout.ColumnCount = 1
        source_plan_layout.RowCount = 2
        source_plan_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        source_plan_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 40.0))
        source_plan_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        source_plan_group.Controls.Add(source_plan_layout)

        self.source_plan_combo = ComboBox()
        self.source_plan_combo.Dock = DockStyle.Fill
        self.source_plan_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.source_plan_combo.DropDownWidth = 1100
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
        self.selected_source_plan_label.ForeColor = MUTED_COLOR
        self.selected_source_plan_label.AutoEllipsis = True
        source_plan_layout.Controls.Add(self.selected_source_plan_label, 0, 1)

        selected_source_plan_index = 0
        for index, source_plan_view in enumerate(source_plan_views):
            self.source_plan_combo.Items.Add(
                get_source_plan_view_label(source_plan_view)
            )
            if get_element_id_value(source_plan_view.Id) == default_source_plan_view_id:
                selected_source_plan_index = index

        if source_plan_views:
            self.source_plan_combo.SelectedIndex = selected_source_plan_index

        target_filter_group = self._create_group("Target Wall Filter")
        main_layout.Controls.Add(target_filter_group, 0, 4)
        self._set_tooltip(
            target_filter_group,
            u"검토 대상 벽을 제한합니다. Interior/Exterior 기준은 도면상 "
            u"위치가 아니라 Revit Wall Type의 Function 값을 기준으로 합니다. "
            u"여러 필터를 동시에 선택하면 모든 조건을 만족하는 벽만 검토합니다."
        )

        target_filter_layout = TableLayoutPanel()
        target_filter_layout.Dock = DockStyle.Fill
        target_filter_layout.Padding = Padding(12, 10, 12, 16)
        target_filter_layout.ColumnCount = 2
        target_filter_layout.RowCount = 3
        target_filter_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        target_filter_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 42.0))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 42.0))
        target_filter_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
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

        target_filter_help_label = Label()
        target_filter_help_label.Text = (
            "Target filters are optional. When multiple filters are checked, "
            "they are applied together as AND conditions. "
            "여러 필터를 동시에 선택하면 모든 조건을 만족하는 벽만 검토합니다."
        )
        target_filter_help_label.Dock = DockStyle.Fill
        target_filter_help_label.AutoSize = False
        target_filter_help_label.ForeColor = MUTED_COLOR
        target_filter_help_label.TextAlign = ContentAlignment.MiddleLeft
        target_filter_help_label.Padding = Padding(6, 8, 6, 4)
        target_filter_layout.Controls.Add(target_filter_help_label, 0, 2)
        target_filter_layout.SetColumnSpan(target_filter_help_label, 2)
        self._set_tooltip(
            target_filter_help_label,
            u"Target Wall Filter는 선택 사항입니다. 여러 필터를 동시에 "
            u"선택하면 AND 조건으로 적용되어 모든 조건을 만족하는 벽만 "
            u"검토합니다."
        )

        point_cloud_group = self._create_group("Analysis Point Cloud Source")
        main_layout.Controls.Add(point_cloud_group, 0, 5)
        self._set_tooltip(
            point_cloud_group,
            u"오차 계산에 사용할 Point Cloud Instance입니다. 선택한 Point "
            u"Cloud를 기준으로 Wall Deviation Sampling을 수행합니다."
        )

        point_cloud_layout = TableLayoutPanel()
        point_cloud_layout.Dock = DockStyle.Fill
        point_cloud_layout.Padding = Padding(12, 10, 12, 10)
        point_cloud_layout.ColumnCount = 1
        point_cloud_layout.RowCount = 3
        point_cloud_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 40.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        point_cloud_group.Controls.Add(point_cloud_layout)

        self.point_cloud_combo = ComboBox()
        self.point_cloud_combo.Dock = DockStyle.Fill
        self.point_cloud_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.point_cloud_combo.DropDownWidth = 1100
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
        self.selected_point_cloud_label.ForeColor = MUTED_COLOR
        self.selected_point_cloud_label.AutoEllipsis = True
        point_cloud_layout.Controls.Add(self.selected_point_cloud_label, 0, 1)

        point_cloud_help_label = Label()
        point_cloud_help_label.Text = (
            "Selected point cloud is used for wall deviation sampling."
        )
        point_cloud_help_label.Dock = DockStyle.Fill
        point_cloud_help_label.AutoSize = False
        point_cloud_help_label.ForeColor = MUTED_COLOR
        point_cloud_help_label.TextAlign = ContentAlignment.MiddleLeft
        point_cloud_layout.Controls.Add(point_cloud_help_label, 0, 2)

        for point_cloud in point_clouds:
            self.point_cloud_combo.Items.Add(
                u"{0}  [ElementId: {1}]".format(
                    get_point_cloud_name(point_cloud),
                    get_element_id_value(point_cloud.Id)
                )
            )

        tolerance_group = self._create_group("Default Tolerances")
        main_layout.Controls.Add(tolerance_group, 0, 6)
        self._set_tooltip(
            tolerance_group,
            u"Review / Critical 판정 기준입니다. 값은 mm 단위이며, 입력값은 "
            u"이번 실행에 적용됩니다."
        )

        tolerance_layout = TableLayoutPanel()
        tolerance_layout.Dock = DockStyle.Fill
        tolerance_layout.Padding = Padding(12, 10, 12, 10)
        tolerance_layout.ColumnCount = 3
        tolerance_layout.RowCount = 2
        for index in range(3):
            tolerance_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 33.33))
        tolerance_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 46.0))
        tolerance_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        tolerance_group.Controls.Add(tolerance_layout)

        tolerance_layout.Controls.Add(
            self._create_input_label("OK Max (mm)", Color.FromArgb(232, 245, 233)),
            0,
            0
        )
        tolerance_layout.Controls.Add(
            self._create_input_label("Review Max (mm)", WARNING_BACKGROUND_COLOR),
            1,
            0
        )
        tolerance_layout.Controls.Add(
            self._create_input_label("Critical", Color.FromArgb(252, 235, 235)),
            2,
            0
        )

        self.ok_max_text = self._create_tolerance_text_box(tolerance_mm["ok_max"])
        self.review_max_text = self._create_tolerance_text_box(
            tolerance_mm["review_max"]
        )
        self._set_tooltip(
            self.ok_max_text,
            u"OK로 볼 수 있는 최대 오차값입니다. mm 단위이며 이번 실행에만 "
            u"적용됩니다."
        )
        self._set_tooltip(
            self.review_max_text,
            u"Review와 Critical을 나누는 최대 Review 기준값입니다. 이 값을 "
            u"초과하면 Critical로 분류됩니다."
        )
        critical_label = Label()
        critical_label.Text = "Review Max +"
        critical_label.Dock = DockStyle.Fill
        critical_label.AutoSize = False
        critical_label.TextAlign = ContentAlignment.MiddleCenter
        critical_label.BackColor = Color.FromArgb(252, 235, 235)
        critical_label.ForeColor = NAVY_COLOR
        critical_label.Font = get_preferred_font(10.0, FontStyle.Bold)
        critical_label.Margin = Padding(6, 4, 6, 4)
        tolerance_layout.Controls.Add(self.ok_max_text, 0, 1)
        tolerance_layout.Controls.Add(self.review_max_text, 1, 1)
        tolerance_layout.Controls.Add(critical_label, 2, 1)

        output_group = self._create_group("Output Options")
        main_layout.Controls.Add(output_group, 0, 7)
        self._set_tooltip(
            output_group,
            u"Scan QC 실행 후 생성할 결과물을 선택합니다. PDF Report를 선택하면 "
            u"필요한 QC Plan View는 자동으로 생성됩니다."
        )

        output_layout = TableLayoutPanel()
        output_layout.Dock = DockStyle.Fill
        output_layout.Padding = Padding(12, 10, 12, 8)
        output_layout.ColumnCount = 2
        output_layout.RowCount = 6
        output_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        output_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 38.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 38.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 38.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 52.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 60.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 52.0))
        output_group.Controls.Add(output_layout)

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
        output_layout.Controls.Add(self.create_plan_check, 0, 0)
        output_layout.Controls.Add(self.create_3d_check, 1, 0)
        output_layout.Controls.Add(self.create_pdf_check, 0, 1)
        output_layout.Controls.Add(self.export_csv_check, 1, 1)
        output_layout.Controls.Add(self.preview_callouts_check, 0, 2)
        output_layout.SetColumnSpan(self.preview_callouts_check, 2)
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

        self.report_sheet_mode_combo = ComboBox()
        self.report_sheet_mode_combo.Dock = DockStyle.Fill
        self.report_sheet_mode_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.report_sheet_mode_combo.Margin = Padding(6, 6, 6, 6)
        self.report_sheet_mode_combo.Items.Add(REPORT_SHEET_MODE_CREATE_NEW_LABEL)
        self.report_sheet_mode_combo.Items.Add(REPORT_SHEET_MODE_EXISTING_LABEL)
        self.report_sheet_mode_combo.SelectedIndex = 0
        self.report_sheet_mode_combo.SelectedIndexChanged += (
            self._update_report_sheet_ui
        )
        output_layout.Controls.Add(self.report_sheet_mode_combo, 0, 3)
        self._set_tooltip(
            self.report_sheet_mode_combo,
            u"PDF Report Sheet 생성 방식을 선택합니다. 기본값은 Scan QC 전용 "
            u"Clean Report Sheet 생성입니다."
        )

        self.existing_report_sheet_combo = ComboBox()
        self.existing_report_sheet_combo.Dock = DockStyle.Fill
        self.existing_report_sheet_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.existing_report_sheet_combo.DropDownWidth = 900
        self.existing_report_sheet_combo.Margin = Padding(6, 6, 6, 6)
        for sheet in self.existing_report_sheets:
            self.existing_report_sheet_combo.Items.Add(get_sheet_label(sheet))
        if self.existing_report_sheets:
            self.existing_report_sheet_combo.SelectedIndex = 0
        else:
            self.existing_report_sheet_combo.Items.Add("No existing Sheets found")
            self.existing_report_sheet_combo.SelectedIndex = 0
        output_layout.Controls.Add(self.existing_report_sheet_combo, 1, 3)

        top_n_label = Label()
        top_n_label.Text = "Top N Callouts"
        top_n_label.Dock = DockStyle.Fill
        top_n_label.AutoSize = False
        top_n_label.TextAlign = ContentAlignment.MiddleLeft
        top_n_label.ForeColor = NAVY_COLOR
        top_n_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        top_n_label.Margin = Padding(6, 8, 6, 6)
        output_layout.Controls.Add(top_n_label, 0, 4)

        self.top_n_callouts_text = TextBox()
        self.top_n_callouts_text.Text = u"{0}".format(self.default_top_n_callouts)
        self.top_n_callouts_text.Dock = DockStyle.Fill
        self.top_n_callouts_text.Margin = Padding(6, 8, 6, 10)
        self.top_n_callouts_text.Font = get_preferred_font(10.0, FontStyle.Bold)
        self.top_n_callouts_text.TextAlign = HorizontalAlignment.Center
        output_layout.Controls.Add(self.top_n_callouts_text, 1, 4)
        self._set_tooltip(
            self.top_n_callouts_text,
            u"검토 결과 중 심각도가 높은 상위 N개 위치만 Revision Cloud ID로 "
            u"표시합니다."
        )

        paper_size_label = Label()
        paper_size_label.Text = "Paper Size"
        paper_size_label.Dock = DockStyle.Fill
        paper_size_label.AutoSize = False
        paper_size_label.TextAlign = ContentAlignment.MiddleLeft
        paper_size_label.ForeColor = NAVY_COLOR
        paper_size_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        paper_size_label.Margin = Padding(6, 8, 6, 6)
        output_layout.Controls.Add(paper_size_label, 0, 5)

        self.paper_size_combo = ComboBox()
        self.paper_size_combo.Dock = DockStyle.Fill
        self.paper_size_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.paper_size_combo.Margin = Padding(6, 8, 6, 8)
        self.paper_size_combo.Items.Add("A3 Landscape")
        self.paper_size_combo.Items.Add("A2 Landscape")
        self.paper_size_combo.SelectedIndex = (
            1 if self.default_paper_size == u"A2 Landscape" else 0
        )
        output_layout.Controls.Add(self.paper_size_combo, 1, 5)
        self._set_tooltip(
            self.paper_size_combo,
            u"PDF Report Sheet 크기입니다. A3 Landscape가 기본이며, 선택한 "
            u"크기에 맞춰 도면과 Summary 비율을 조정합니다."
        )
        self._update_report_sheet_ui(None, None)
        self._update_pdf_dependency_ui(None, None)

        phase_note = Label()
        phase_note.Text = (
            "Selected Plan and 3D working views will be created after standards setup. "
            "Review/Critical Wall results can be marked in the QC Plan View. "
            "PDF Report requires a QC Plan View and creates it automatically. "
            "CSV export is planned but disabled in this phase."
        )
        phase_note.Dock = DockStyle.Fill
        phase_note.AutoSize = False
        phase_note.ForeColor = MUTED_COLOR
        phase_note.BackColor = HELP_BACKGROUND_COLOR
        phase_note.BorderStyle = BorderStyle.FixedSingle
        phase_note.TextAlign = ContentAlignment.MiddleLeft
        phase_note.Padding = Padding(12, 8, 12, 8)
        phase_note.Margin = Padding(0, 10, 0, 10)
        self.phase_note = phase_note
        main_layout.Controls.Add(phase_note, 0, 9)

        button_layout = FlowLayoutPanel()
        button_layout.Dock = DockStyle.Fill
        button_layout.FlowDirection = FlowDirection.RightToLeft
        button_layout.WrapContents = False
        button_layout.Margin = Padding(0)
        button_layout.Padding = Padding(0, 10, 0, 0)
        main_layout.Controls.Add(button_layout, 0, 10)

        self.run_button = Button()
        self.run_button.Text = "Run"
        self.run_button.Size = Size(104, 34)
        self.run_button.Margin = Padding(10, 0, 0, 0)
        self._apply_primary_button_style(self.run_button)
        self.run_button.Click += self._confirm
        button_layout.Controls.Add(self.run_button)
        self.AcceptButton = self.run_button

        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.Size = Size(104, 34)
        cancel_button.Margin = Padding(10, 0, 0, 0)
        self._apply_secondary_button_style(cancel_button)
        cancel_button.DialogResult = DialogResult.Cancel
        button_layout.Controls.Add(cancel_button)
        self.CancelButton = cancel_button

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

    def _create_group(self, text):
        group = GroupBox()
        group.Text = text
        group.Dock = DockStyle.Fill
        group.ForeColor = NAVY_COLOR
        group.Font = get_preferred_font(9.5, FontStyle.Bold)
        group.Margin = Padding(0, 7, 0, 7)
        return group

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
        label.TextAlign = ContentAlignment.MiddleCenter
        label.BackColor = background_color
        label.ForeColor = NAVY_COLOR
        label.Font = get_preferred_font(9.5, FontStyle.Bold)
        label.Margin = Padding(4)
        return label

    def _create_input_label(self, text, background_color):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.TextAlign = ContentAlignment.MiddleCenter
        label.BackColor = background_color
        label.ForeColor = NAVY_COLOR
        label.Font = get_preferred_font(9.5, FontStyle.Bold)
        label.Margin = Padding(6, 4, 6, 4)
        return label

    def _create_tolerance_text_box(self, value):
        text_box = TextBox()
        text_box.Text = format_mm_value(value)
        text_box.Dock = DockStyle.Fill
        text_box.Margin = Padding(6, 8, 6, 8)
        text_box.Font = get_preferred_font(11.0, FontStyle.Bold)
        text_box.TextAlign = HorizontalAlignment.Center
        return text_box

    def _create_check_box(self, text, checked):
        check_box = CheckBox()
        check_box.Text = text
        check_box.Dock = DockStyle.Fill
        check_box.AutoSize = False
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
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = BORDER_COLOR
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

    def _parse_tolerance_input(self, text_value, fallback, label):
        try:
            value = float(text_value)
            if value < 0:
                raise ValueError()
            return value, u""
        except Exception:
            return fallback, (
                u"{0} tolerance value was invalid and default {1} mm was used."
                .format(label, format_mm_value(fallback))
            )

    def _get_tolerance_options(self):
        warnings = []
        defaults = self.default_tolerance_mm
        ok_max, ok_warning = self._parse_tolerance_input(
            self.ok_max_text.Text,
            defaults["ok_max"],
            u"OK Max"
        )
        review_max, review_warning = self._parse_tolerance_input(
            self.review_max_text.Text,
            defaults["review_max"],
            u"Review Max"
        )
        if ok_warning:
            warnings.append(ok_warning)
        if review_warning:
            warnings.append(review_warning)

        if review_max <= ok_max:
            ok_max = defaults["ok_max"]
            review_max = defaults["review_max"]
            warnings.append(
                u"Review Max must be greater than OK Max. Default tolerance "
                u"values were used."
            )

        return {
            "ok_max": ok_max,
            "review_max": review_max,
            "critical_min": review_max
        }, warnings

    def _parse_positive_int_input(self, text_value, fallback, label):
        try:
            value = int(float(text_value))
            if value <= 0:
                raise ValueError()
            return value, u""
        except Exception:
            return fallback, (
                u"{0} value was invalid and default {1} was used."
                .format(label, fallback)
            )

    def _get_top_n_callouts_options(self):
        return self._parse_positive_int_input(
            self.top_n_callouts_text.Text,
            self.default_top_n_callouts,
            u"Top N Callouts"
        )

    def _get_report_sheet_options(self):
        if self.report_sheet_mode_combo.SelectedIndex == 1:
            report_sheet_mode = REPORT_SHEET_MODE_EXISTING
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
                _saved, save_warning = save_report_state(
                    self.settings,
                    {"last_pdf_folder": selected_folder}
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
            self.selected_point_cloud_label.Text = (
                u"Analysis Point Cloud Source: {0}".format(
                    get_point_cloud_name(selected_point_cloud)
                )
            )

    def _update_source_plan_view(self, sender, event_args):
        selected_index = self.source_plan_combo.SelectedIndex
        if 0 <= selected_index < len(self.source_plan_views):
            selected_source_plan_view = self.source_plan_views[selected_index]
            self.selected_source_plan_label.Text = u"Selected Source Plan View: {0}".format(
                get_source_plan_view_name(selected_source_plan_view)
            )

    def _update_analysis_scope_ui(self, sender, event_args):
        show_selected_walls = self.analysis_scope_combo.SelectedIndex == 1
        self.selected_walls_group.Visible = show_selected_walls
        self.selected_walls_row_style.Height = 108.0 if show_selected_walls else 0.0
        self.PerformLayout()

    def _update_report_sheet_ui(self, sender, event_args):
        use_existing_sheet = self.report_sheet_mode_combo.SelectedIndex == 1
        self.existing_report_sheet_combo.Enabled = (
            use_existing_sheet and bool(self.existing_report_sheets)
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
                self.phase_note.Text = (
                    "PDF export cancelled by user. Scan QC was not started. "
                    "Choose a PDF path, or uncheck Create PDF Report and run again."
                )
                self.phase_note.BackColor = WARNING_BACKGROUND_COLOR
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
    settings
):
    options_form = ScanQcForm(
        selected_wall_count,
        point_clouds,
        source_plan_views,
        existing_report_sheets,
        default_source_plan_view_id,
        settings
    )
    dialog_result = options_form.ShowDialog()
    selected_options = options_form.result
    options_form.Dispose()

    if dialog_result != DialogResult.OK or selected_options is None:
        return None

    return selected_options
