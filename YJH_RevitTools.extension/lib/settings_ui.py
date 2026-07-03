# -*- coding: utf-8 -*-

import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Diagnostics import Process, ProcessStartInfo
from System.Drawing import Color, Font, FontFamily, FontStyle, Size
from System.Windows.Forms import (
    AutoScaleMode,
    Button,
    ColumnStyle,
    DialogResult,
    DockStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    GroupBox,
    Label,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    OpenFileDialog,
    Padding,
    RowStyle,
    SizeType,
    TableLayoutPanel,
    TextBox,
    ToolTip
)

from config_loader import load_config, save_local_external_python_path
from exporters import (
    get_xlsx_environment_status,
    probe_external_python_path
)
from report_history import open_file
from report_ui import html_escape


NAVY_COLOR = Color.FromArgb(38, 54, 69)
MUTED_COLOR = Color.FromArgb(102, 112, 122)
LIGHT_BACKGROUND_COLOR = Color.FromArgb(246, 247, 248)
WARNING_BACKGROUND_COLOR = Color.FromArgb(255, 241, 230)


def get_preferred_font(size, style=FontStyle.Regular):
    preferred_names = [u"SUIT", u"Pretendard", u"Malgun Gothic", u"Segoe UI"]

    try:
        available_names = [family.Name.lower() for family in FontFamily.Families]
        for font_name in preferred_names:
            if font_name.lower() in available_names:
                return Font(font_name, size, style)
    except Exception:
        pass

    return Font(u"Segoe UI", size, style)


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
        self.output = output
        self.default_config_path = default_config_path
        self.local_config_path = local_config_path
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
        self.path_tooltip = ToolTip()

        self.Text = "Revit QC Settings"
        self.ClientSize = Size(1080, 820)
        self.MinimumSize = Size(960, 760)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(9.0)
        self.AutoScaleMode = AutoScaleMode.Dpi

        main_layout = TableLayoutPanel()
        main_layout.Dock = DockStyle.Fill
        main_layout.Padding = Padding(24, 20, 24, 18)
        main_layout.ColumnCount = 1
        main_layout.RowCount = 5
        main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 46.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 190.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 68.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 112.0))
        self.Controls.Add(main_layout)

        intro_label = Label()
        intro_label.Text = (
            "Configure external Python for Styled XLSX reports. "
            "No JSON editing required."
        )
        intro_label.Dock = DockStyle.Fill
        intro_label.AutoSize = False
        intro_label.AutoEllipsis = True
        intro_label.Font = get_preferred_font(11.0, FontStyle.Bold)
        intro_label.ForeColor = NAVY_COLOR
        intro_label.Padding = Padding(0, 5, 0, 0)
        main_layout.Controls.Add(intro_label, 0, 0)

        config_group = GroupBox()
        config_group.Text = "Config"
        config_group.Dock = DockStyle.Fill
        config_group.ForeColor = NAVY_COLOR
        config_group.Font = get_preferred_font(9.5, FontStyle.Bold)
        config_group.Padding = Padding(12, 12, 12, 10)
        config_group.Margin = Padding(0, 0, 0, 10)
        main_layout.Controls.Add(config_group, 0, 1)

        config_layout = self._create_field_layout(4)
        config_group.Controls.Add(config_layout)
        self.default_path_text = self._add_field(
            config_layout,
            0,
            "Default config path",
            True
        )
        self.local_path_text = self._add_field(
            config_layout,
            1,
            "Local config path",
            True
        )
        self.local_exists_text = self._add_field(
            config_layout,
            2,
            "Local config exists",
            True
        )
        self.applied_path_text = self._add_field(
            config_layout,
            3,
            "Applied external_python_path",
            True
        )

        environment_group = GroupBox()
        environment_group.Text = "Styled XLSX Environment"
        environment_group.Dock = DockStyle.Fill
        environment_group.ForeColor = NAVY_COLOR
        environment_group.Font = get_preferred_font(9.5, FontStyle.Bold)
        environment_group.Padding = Padding(12, 12, 12, 10)
        environment_group.Margin = Padding(0, 0, 0, 10)
        main_layout.Controls.Add(environment_group, 0, 2)

        environment_layout = self._create_field_layout(9)
        environment_group.Controls.Add(environment_layout)
        self.python_path_text = self._add_field(
            environment_layout,
            0,
            "External Python Path",
            False
        )
        self.python_detected_text = self._add_field(
            environment_layout,
            1,
            "External Python detected",
            True
        )
        self.openpyxl_text = self._add_field(
            environment_layout,
            2,
            "openpyxl available",
            True
        )
        self.openpyxl_version_text = self._add_field(
            environment_layout,
            3,
            "openpyxl version",
            True
        )
        self.python_detail_text = self._add_field(
            environment_layout,
            4,
            "Python detail",
            True
        )
        self.helper_script_text = self._add_field(
            environment_layout,
            5,
            "Helper script",
            True
        )
        self.helper_exists_text = self._add_field(
            environment_layout,
            6,
            "Helper exists",
            True
        )
        self.debug_log_text = self._add_field(
            environment_layout,
            7,
            "Last debug log",
            True
        )
        self.probe_error_text = self._add_field(
            environment_layout,
            8,
            "Probe error",
            True
        )

        self.warning_label = Label()
        self.warning_label.Dock = DockStyle.Fill
        self.warning_label.AutoSize = False
        self.warning_label.BackColor = WARNING_BACKGROUND_COLOR
        self.warning_label.ForeColor = NAVY_COLOR
        self.warning_label.Font = get_preferred_font(8.5)
        self.warning_label.Padding = Padding(10, 8, 10, 6)
        self.warning_label.Margin = Padding(0, 0, 0, 8)
        main_layout.Controls.Add(self.warning_label, 0, 3)

        action_layout = TableLayoutPanel()
        action_layout.Dock = DockStyle.Fill
        action_layout.Margin = Padding(0)
        action_layout.Padding = Padding(0, 4, 0, 0)
        action_layout.ColumnCount = 4
        action_layout.RowCount = 2
        for column_index in range(4):
            action_layout.ColumnStyles.Add(
                ColumnStyle(SizeType.Percent, 25.0)
            )
        action_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
        action_layout.RowStyles.Add(RowStyle(SizeType.Percent, 50.0))
        main_layout.Controls.Add(action_layout, 0, 4)

        self._add_action_button(
            action_layout,
            "Browse Python...",
            self._browse_python,
            0,
            0
        )
        self._add_action_button(
            action_layout,
            "Save Python Path",
            self._save_python_path,
            1,
            0
        )
        self._add_action_button(
            action_layout,
            "Test XLSX Environment",
            self._test_environment,
            2,
            0
        )
        self._add_action_button(
            action_layout,
            "Clear Python Path",
            self._clear_python_path,
            3,
            0
        )
        self._add_action_button(
            action_layout,
            "Open Config Folder",
            self._open_config_folder,
            0,
            1
        )
        self._add_action_button(
            action_layout,
            "Open Debug Log",
            self._open_debug_log,
            1,
            1
        )
        close_button = self._add_action_button(
            action_layout,
            "Close",
            self._close_form,
            3,
            1
        )
        self.CancelButton = close_button

        self._refresh_config_and_environment()

    def _create_field_layout(self, row_count):
        layout = TableLayoutPanel()
        layout.Dock = DockStyle.Fill
        layout.ColumnCount = 2
        layout.RowCount = row_count
        layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 250.0))
        layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        for row_index in range(row_count):
            layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0 / row_count))
        return layout

    def _add_field(self, layout, row_index, label_text, read_only):
        label = Label()
        label.Text = label_text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.Font = get_preferred_font(8.8, FontStyle.Bold)
        label.ForeColor = NAVY_COLOR
        label.Padding = Padding(2, 5, 8, 0)
        layout.Controls.Add(label, 0, row_index)

        text_box = TextBox()
        text_box.Dock = DockStyle.Fill
        text_box.ReadOnly = read_only
        text_box.WordWrap = False
        text_box.Margin = Padding(0, 2, 0, 2)
        text_box.Font = get_preferred_font(8.8)
        text_box.BackColor = Color.White
        text_box.TextChanged += self._update_tooltip
        layout.Controls.Add(text_box, 1, row_index)
        return text_box

    def _add_action_button(self, layout, text, handler, column_index, row_index):
        button = Button()
        button.Text = text
        button.Dock = DockStyle.Fill
        button.Margin = Padding(0, 0, 10, 8)
        button.Font = get_preferred_font(8.8)
        button.Click += handler
        layout.Controls.Add(button, column_index, row_index)
        return button

    def _update_tooltip(self, sender, event_args):
        self.path_tooltip.SetToolTip(sender, sender.Text)

    def _show_text_start(self, text_box):
        text_box.SelectionStart = 0
        text_box.SelectionLength = 0
        text_box.ScrollToCaret()

    def _get_current_config(self):
        return load_config(self.default_config_path, self.local_config_path)

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
        status["external_python_path"] = u""
        return status

    def _refresh_config_and_environment(self, selected_path=None):
        try:
            config = self._get_current_config()
        except Exception as ex:
            MessageBox.Show(
                self,
                u"Config could not be loaded: {0}".format(ex),
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return

        applied_path = config.get("export", {}).get(
            "external_python_path",
            u""
        )
        current_path = applied_path if selected_path is None else selected_path
        self.default_path_text.Text = self.default_config_path
        self.local_path_text.Text = self.local_config_path
        self.local_exists_text.Text = (
            u"Yes" if os.path.isfile(self.local_config_path) else u"No"
        )
        self.applied_path_text.Text = applied_path or u"(empty)"
        self.python_path_text.Text = current_path or u""
        for text_box in [
            self.default_path_text,
            self.local_path_text,
            self.applied_path_text,
            self.python_path_text
        ]:
            self._show_text_start(text_box)
        self._update_environment_fields(
            self._get_environment_status(current_path)
        )

    def _update_environment_fields(self, status):
        self.python_detected_text.Text = status.get(
            "external_python_detected",
            u"No"
        )
        self.openpyxl_text.Text = status.get("openpyxl_available", u"No")
        self.openpyxl_version_text.Text = status.get(
            "openpyxl_version",
            u""
        ) or u"(none)"
        self.python_detail_text.Text = status.get(
            "python_detail",
            u""
        ) or u"(none)"
        self.helper_script_text.Text = status.get(
            "helper_path",
            self.helper_path
        )
        self.helper_exists_text.Text = (
            u"Yes" if status.get("helper_exists", False) else u"No"
        )
        self.debug_log_text.Text = status.get(
            "debug_log_path",
            self.debug_log_path
        )
        self.probe_error_text.Text = status.get(
            "probe_error",
            u""
        ) or u"(none)"
        for text_box in [
            self.python_detail_text,
            self.helper_script_text,
            self.debug_log_text,
            self.probe_error_text
        ]:
            self._show_text_start(text_box)
        self._update_warning(self.python_path_text.Text)

    def _update_warning(self, python_path):
        if is_codex_runtime_path(python_path):
            self.warning_label.Text = (
                "Warning: Current Python path appears to be a temporary Codex "
                "runtime path. For long-term use, select a stable local Python "
                "installation."
            )
            self.warning_label.Visible = True
        else:
            self.warning_label.Text = (
                "Personal Python paths are stored only in qc_config_local.json, "
                "which is excluded from Git."
            )
            self.warning_label.Visible = True

    def _browse_python(self, sender, event_args):
        dialog = OpenFileDialog()
        dialog.Title = "Select external Python executable"
        dialog.Filter = (
            "Python executable (python.exe)|python.exe|All files (*.*)|*.*"
        )
        dialog.CheckFileExists = True
        dialog.CheckPathExists = True
        current_path = self.python_path_text.Text.strip()
        if os.path.isfile(current_path):
            dialog.InitialDirectory = os.path.dirname(current_path)
            dialog.FileName = os.path.basename(current_path)

        if dialog.ShowDialog(self) == DialogResult.OK:
            self.python_path_text.Text = dialog.FileName
            self._update_warning(dialog.FileName)

        dialog.Dispose()

    def _save_python_path(self, sender, event_args):
        python_path = self.python_path_text.Text.strip()
        if not python_path or not os.path.isfile(python_path):
            MessageBox.Show(
                self,
                "Select an existing Python executable before saving.",
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        try:
            save_local_external_python_path(
                self.local_config_path,
                python_path
            )
            self._refresh_config_and_environment()
            MessageBox.Show(
                self,
                "Python path was saved to qc_config_local.json.",
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
        except Exception as ex:
            MessageBox.Show(
                self,
                u"Python path could not be saved: {0}".format(ex),
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _test_environment(self, sender, event_args):
        python_path = self.python_path_text.Text.strip()
        status = self._get_environment_status(python_path)
        self._update_environment_fields(status)
        detected = status.get("external_python_detected", u"No")
        openpyxl_available = status.get("openpyxl_available", u"No")
        openpyxl_version = status.get("openpyxl_version", u"") or u"(none)"

        if detected == u"Yes" and openpyxl_available == u"Yes":
            message = (
                u"External Python detected: Yes\n"
                u"openpyxl available: Yes\n"
                u"openpyxl version: {0}".format(openpyxl_version)
            )
            icon = MessageBoxIcon.Information
        else:
            probe_error = status.get("probe_error", u"") or u"Unknown error"
            install_target = python_path or u"python"
            message = (
                u"External Python detected: {0}\n"
                u"openpyxl available: {1}\n\n"
                u"{2}\n\n"
                u"Install:\n\"{3}\" -m pip install openpyxl".format(
                    detected,
                    openpyxl_available,
                    probe_error,
                    install_target
                )
            )
            icon = MessageBoxIcon.Warning

        MessageBox.Show(
            self,
            message,
            "Styled XLSX Environment",
            MessageBoxButtons.OK,
            icon
        )
        self._print_environment_result(status)

    def _print_environment_result(self, status):
        self.output.print_html(
            u"""
            <div style="font-family:Segoe UI,Arial,sans-serif; margin-top:10px;
                padding:10px; border-left:4px solid #E97826;
                background:#F6F7F8; color:#263645;">
                <strong>Styled XLSX Environment Test</strong><br>
                External Python detected: {0}<br>
                openpyxl available: {1}<br>
                openpyxl version: {2}<br>
                Python detail: {3}<br>
                Probe error: {4}
            </div>
            """.format(
                html_escape(status.get("external_python_detected", u"No")),
                html_escape(status.get("openpyxl_available", u"No")),
                html_escape(status.get("openpyxl_version", u"") or u"(none)"),
                html_escape(status.get("python_detail", u"") or u"(none)"),
                html_escape(status.get("probe_error", u"") or u"(none)")
            )
        )

    def _open_config_folder(self, sender, event_args):
        opened, open_error = open_folder(
            os.path.dirname(self.default_config_path)
        )
        if not opened:
            MessageBox.Show(
                self,
                open_error,
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _open_debug_log(self, sender, event_args):
        if not os.path.isfile(self.debug_log_path):
            MessageBox.Show(
                self,
                "No debug log found.",
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return

        opened, open_error = open_file(self.debug_log_path)
        if not opened:
            MessageBox.Show(
                self,
                open_error,
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _clear_python_path(self, sender, event_args):
        if MessageBox.Show(
            self,
            "Clear external_python_path from qc_config_local.json?",
            "Revit QC Settings",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Question
        ) != DialogResult.Yes:
            return

        try:
            save_local_external_python_path(self.local_config_path, u"")
            self._refresh_config_and_environment()
        except Exception as ex:
            MessageBox.Show(
                self,
                u"Python path could not be cleared: {0}".format(ex),
                "Revit QC Settings",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _close_form(self, sender, event_args):
        self.Close()


def show_settings_dialog(
    output,
    default_config_path,
    local_config_path,
    extension_dir,
    reports_dir
):
    settings_form = QCSettingsForm(
        output,
        default_config_path,
        local_config_path,
        extension_dir,
        reports_dir
    )
    settings_form.ShowDialog()
    settings_form.Dispose()
