# -*- coding: utf-8 -*-

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

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
    Label,
    Padding,
    RowStyle,
    SizeType,
    TableLayoutPanel
)

from scan_qc.collectors import get_element_id_value, get_point_cloud_name
from scan_qc.analysis_scope import (
    ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL,
    ANALYSIS_SCOPE_LABELS,
    ANALYSIS_SCOPE_SELECTED_WALLS
)
from scan_qc.settings import get_output_options, get_tolerance_mm


NAVY_COLOR = Color.FromArgb(38, 54, 69)
BUTTON_NAVY_COLOR = Color.FromArgb(83, 103, 119)
BUTTON_HOVER_COLOR = Color.FromArgb(70, 88, 103)
MUTED_COLOR = Color.FromArgb(95, 111, 125)
BORDER_COLOR = Color.FromArgb(214, 221, 227)
HELP_BACKGROUND_COLOR = Color.FromArgb(248, 249, 250)
WARNING_BACKGROUND_COLOR = Color.FromArgb(255, 241, 230)


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


class ScanQcForm(Form):
    def __init__(self, selected_wall_count, point_clouds, settings):
        Form.__init__(self)
        self.result = None
        self.point_clouds = point_clouds
        tolerance_mm = get_tolerance_mm(settings)
        output_defaults = get_output_options(settings)

        self.Text = "Revit QC - Scan QC"
        self.ClientSize = Size(760, 860)
        self.MinimumSize = Size(740, 900)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(9.5)
        self.AutoScaleMode = AutoScaleMode.Font

        main_layout = TableLayoutPanel()
        main_layout.Dock = DockStyle.Fill
        main_layout.Padding = Padding(28, 22, 28, 24)
        main_layout.ColumnCount = 1
        main_layout.RowCount = 9
        main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 50.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 96.0))
        self.selected_walls_row_style = RowStyle(SizeType.Absolute, 0.0)
        main_layout.RowStyles.Add(self.selected_walls_row_style)
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 132.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 126.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 154.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 78.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 54.0))
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

        self.selected_walls_group = self._create_group("Selected Walls")
        self.selected_walls_group.Visible = False
        main_layout.Controls.Add(self.selected_walls_group, 0, 2)

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

        point_cloud_group = self._create_group("Point Cloud Instance")
        main_layout.Controls.Add(point_cloud_group, 0, 3)

        point_cloud_layout = TableLayoutPanel()
        point_cloud_layout.Dock = DockStyle.Fill
        point_cloud_layout.Padding = Padding(12, 10, 12, 10)
        point_cloud_layout.ColumnCount = 1
        point_cloud_layout.RowCount = 2
        point_cloud_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 40.0))
        point_cloud_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        point_cloud_group.Controls.Add(point_cloud_layout)

        self.point_cloud_combo = ComboBox()
        self.point_cloud_combo.Dock = DockStyle.Fill
        self.point_cloud_combo.DropDownStyle = ComboBoxStyle.DropDownList
        self.point_cloud_combo.Margin = Padding(0, 2, 0, 8)
        self.point_cloud_combo.SelectedIndexChanged += self._update_selected_point_cloud
        point_cloud_layout.Controls.Add(self.point_cloud_combo, 0, 0)

        self.selected_point_cloud_label = Label()
        self.selected_point_cloud_label.Dock = DockStyle.Fill
        self.selected_point_cloud_label.AutoSize = False
        self.selected_point_cloud_label.ForeColor = MUTED_COLOR
        point_cloud_layout.Controls.Add(self.selected_point_cloud_label, 0, 1)

        for point_cloud in point_clouds:
            self.point_cloud_combo.Items.Add(
                u"{0}  [ElementId: {1}]".format(
                    get_point_cloud_name(point_cloud),
                    get_element_id_value(point_cloud.Id)
                )
            )

        tolerance_group = self._create_group("Default Tolerances")
        main_layout.Controls.Add(tolerance_group, 0, 4)

        tolerance_layout = TableLayoutPanel()
        tolerance_layout.Dock = DockStyle.Fill
        tolerance_layout.Padding = Padding(12, 8, 12, 8)
        tolerance_layout.ColumnCount = 3
        tolerance_layout.RowCount = 1
        for index in range(3):
            tolerance_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 33.33))
        tolerance_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        tolerance_group.Controls.Add(tolerance_layout)

        tolerance_layout.Controls.Add(
            self._create_tolerance_label(
                "OK",
                u"0-{0} mm".format(format_mm_value(tolerance_mm["ok_max"])),
                Color.FromArgb(232, 245, 233)
            ),
            0,
            0
        )
        tolerance_layout.Controls.Add(
            self._create_tolerance_label(
                "Review",
                u"{0}-{1} mm".format(
                    format_mm_value(tolerance_mm["ok_max"]),
                    format_mm_value(tolerance_mm["review_max"])
                ),
                WARNING_BACKGROUND_COLOR
            ),
            1,
            0
        )
        tolerance_layout.Controls.Add(
            self._create_tolerance_label(
                "Critical",
                u"{0} mm+".format(format_mm_value(tolerance_mm["critical_min"])),
                Color.FromArgb(252, 235, 235)
            ),
            2,
            0
        )

        output_group = self._create_group("Output Options")
        main_layout.Controls.Add(output_group, 0, 5)

        output_layout = TableLayoutPanel()
        output_layout.Dock = DockStyle.Fill
        output_layout.Padding = Padding(12, 10, 12, 8)
        output_layout.ColumnCount = 2
        output_layout.RowCount = 2
        output_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        output_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
        output_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
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
        self.export_csv_check = self._create_check_box(
            "Export CSV Data",
            output_defaults["export_csv"]
        )
        output_layout.Controls.Add(self.create_plan_check, 0, 0)
        output_layout.Controls.Add(self.create_3d_check, 1, 0)
        output_layout.Controls.Add(self.create_pdf_check, 0, 1)
        output_layout.Controls.Add(self.export_csv_check, 1, 1)

        phase_note = Label()
        phase_note.Text = (
            "Selected Plan and 3D working views will be created after standards setup. "
            "No deviation analysis, markers, PDF, or CSV will be created."
        )
        phase_note.Dock = DockStyle.Fill
        phase_note.AutoSize = False
        phase_note.ForeColor = MUTED_COLOR
        phase_note.BackColor = HELP_BACKGROUND_COLOR
        phase_note.BorderStyle = BorderStyle.FixedSingle
        phase_note.TextAlign = ContentAlignment.MiddleLeft
        phase_note.Padding = Padding(12, 8, 12, 8)
        phase_note.Margin = Padding(0, 10, 0, 10)
        main_layout.Controls.Add(phase_note, 0, 7)

        button_layout = FlowLayoutPanel()
        button_layout.Dock = DockStyle.Fill
        button_layout.FlowDirection = FlowDirection.RightToLeft
        button_layout.WrapContents = False
        button_layout.Margin = Padding(0)
        button_layout.Padding = Padding(0, 10, 0, 0)
        main_layout.Controls.Add(button_layout, 0, 8)

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
            self.selected_point_cloud_label.Text = "Selected Point Cloud: Not available"

    def _create_group(self, text):
        group = GroupBox()
        group.Text = text
        group.Dock = DockStyle.Fill
        group.ForeColor = NAVY_COLOR
        group.Font = get_preferred_font(9.5, FontStyle.Bold)
        group.Margin = Padding(0, 7, 0, 7)
        return group

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

    def _create_check_box(self, text, checked):
        check_box = CheckBox()
        check_box.Text = text
        check_box.Dock = DockStyle.Fill
        check_box.AutoSize = True
        check_box.Margin = Padding(6)
        check_box.ForeColor = NAVY_COLOR
        check_box.Font = get_preferred_font(9.5)
        check_box.Checked = checked
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

    def _update_selected_point_cloud(self, sender, event_args):
        selected_index = self.point_cloud_combo.SelectedIndex
        if 0 <= selected_index < len(self.point_clouds):
            selected_point_cloud = self.point_clouds[selected_index]
            self.selected_point_cloud_label.Text = u"Selected Point Cloud: {0}".format(
                get_point_cloud_name(selected_point_cloud)
            )

    def _update_analysis_scope_ui(self, sender, event_args):
        show_selected_walls = self.analysis_scope_combo.SelectedIndex == 1
        self.selected_walls_group.Visible = show_selected_walls
        self.selected_walls_row_style.Height = 108.0 if show_selected_walls else 0.0
        self.PerformLayout()

    def _confirm(self, sender, event_args):
        selected_index = self.point_cloud_combo.SelectedIndex
        if selected_index < 0 or selected_index >= len(self.point_clouds):
            return

        selected_point_cloud = self.point_clouds[selected_index]
        selected_output_options = []

        if self.create_plan_check.Checked:
            selected_output_options.append(u"Create QC Plan View")
        if self.create_3d_check.Checked:
            selected_output_options.append(u"Create QC 3D View")
        if self.create_pdf_check.Checked:
            selected_output_options.append(u"Create PDF Report")
        if self.export_csv_check.Checked:
            selected_output_options.append(u"Export CSV Data")

        if self.analysis_scope_combo.SelectedIndex == 1:
            analysis_scope = ANALYSIS_SCOPE_SELECTED_WALLS
        else:
            analysis_scope = ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL

        self.result = {
            "point_cloud_name": get_point_cloud_name(selected_point_cloud),
            "point_cloud_id": get_element_id_value(selected_point_cloud.Id),
            "create_plan_view": self.create_plan_check.Checked,
            "create_3d_view": self.create_3d_check.Checked,
            "create_pdf_report": self.create_pdf_check.Checked,
            "export_csv": self.export_csv_check.Checked,
            "analysis_scope": analysis_scope,
            "analysis_scope_label": ANALYSIS_SCOPE_LABELS[analysis_scope],
            "selected_output_options": selected_output_options
        }
        self.DialogResult = DialogResult.OK
        self.Close()


def request_scan_qc_options(selected_wall_count, point_clouds, settings):
    options_form = ScanQcForm(selected_wall_count, point_clouds, settings)
    dialog_result = options_form.ShowDialog()
    selected_options = options_form.result
    options_form.Dispose()

    if dialog_result != DialogResult.OK or selected_options is None:
        return None

    return selected_options
