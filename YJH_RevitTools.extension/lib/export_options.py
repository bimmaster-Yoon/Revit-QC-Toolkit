# -*- coding: utf-8 -*-

import io
import os

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import Guid
from System.Drawing import Color, Font, FontFamily, FontStyle, Size
from System.Windows.Forms import (
    AutoScaleMode,
    Button,
    CheckBox,
    ColumnStyle,
    DialogResult,
    DockStyle,
    FlowDirection,
    FlowLayoutPanel,
    FlatStyle,
    FolderBrowserDialog,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Label,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    Padding,
    RowStyle,
    SizeType,
    TableLayoutPanel,
    TextBox,
    ToolTip
)

from ui_close_profiler import create_ui_close_profile
from qc_ui_style import configure_tooltip, dispose_tooltip


LATEST_EXPORT_FOLDER_FILE = "latest_export_folder.txt"
NAVY_COLOR = Color.FromArgb(38, 54, 69)
BUTTON_NAVY_COLOR = Color.FromArgb(83, 103, 119)
BUTTON_HOVER_COLOR = Color.FromArgb(70, 88, 103)
MUTED_COLOR = Color.FromArgb(95, 111, 125)
BORDER_COLOR = Color.FromArgb(214, 221, 227)
SECONDARY_BORDER_COLOR = Color.FromArgb(199, 208, 216)
LIGHT_BACKGROUND_COLOR = Color.FromArgb(244, 246, 248)


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
        self.result = None
        self.Text = "Revit QC - Export Options"
        self.ClientSize = Size(820, 470)
        self.MinimumSize = Size(780, 450)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(9.5)
        self.AutoScaleMode = AutoScaleMode.Font

        main_layout = TableLayoutPanel()
        main_layout.Dock = DockStyle.Fill
        main_layout.BackColor = Color.White
        main_layout.Padding = Padding(28, 24, 28, 20)
        main_layout.ColumnCount = 1
        main_layout.RowCount = 6
        main_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 38.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 32.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 88.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 32.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 52.0))
        self.Controls.Add(main_layout)

        intro_label = Label()
        intro_label.Text = "Select an export folder and output formats for the QC report."
        intro_label.Dock = DockStyle.Fill
        intro_label.AutoSize = False
        intro_label.ForeColor = NAVY_COLOR
        intro_label.Font = get_preferred_font(11.0, FontStyle.Bold)
        intro_label.Padding = Padding(0, 3, 0, 0)
        main_layout.Controls.Add(intro_label, 0, 0)

        last_label = Label()
        if last_folder:
            last_label.Text = u"Last export folder: {0}".format(last_folder)
        else:
            last_label.Text = "Last export folder: Not available"
        last_label.Dock = DockStyle.Fill
        last_label.AutoSize = False
        last_label.AutoEllipsis = True
        last_label.ForeColor = MUTED_COLOR
        last_label.Padding = Padding(0, 2, 0, 0)
        main_layout.Controls.Add(last_label, 0, 1)

        self.tool_tip = configure_tooltip(ToolTip())
        self.tool_tip.SetToolTip(last_label, last_label.Text)

        folder_layout = TableLayoutPanel()
        folder_layout.Dock = DockStyle.Fill
        folder_layout.Margin = Padding(0, 4, 0, 8)
        folder_layout.ColumnCount = 1
        folder_layout.RowCount = 2
        folder_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        folder_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        folder_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.Controls.Add(folder_layout, 0, 2)

        folder_label = Label()
        folder_label.Text = "Export folder"
        folder_label.Dock = DockStyle.Fill
        folder_label.AutoSize = False
        folder_label.ForeColor = NAVY_COLOR
        folder_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        folder_layout.Controls.Add(folder_label, 0, 0)

        folder_input_layout = TableLayoutPanel()
        folder_input_layout.Dock = DockStyle.Fill
        folder_input_layout.Margin = Padding(0)
        folder_input_layout.ColumnCount = 2
        folder_input_layout.RowCount = 1
        folder_input_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        folder_input_layout.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 104.0))
        folder_input_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        folder_layout.Controls.Add(folder_input_layout, 0, 1)

        self.folder_text = TextBox()
        self.folder_text.Text = last_folder or u""
        self.folder_text.Dock = DockStyle.Fill
        self.folder_text.Margin = Padding(0, 2, 12, 2)
        self.folder_text.WordWrap = False
        self.folder_text.TextChanged += self._update_folder_tooltip
        folder_input_layout.Controls.Add(self.folder_text, 0, 0)

        self.tool_tip.SetToolTip(self.folder_text, self.folder_text.Text)

        self.browse_button = Button()
        self.browse_button.Text = "Browse..."
        self.browse_button.Dock = DockStyle.Fill
        self.browse_button.Margin = Padding(0)
        self._apply_secondary_button_style(self.browse_button)
        self.browse_button.Click += self._browse_folder
        folder_input_layout.Controls.Add(self.browse_button, 1, 0)

        formats_label = Label()
        formats_label.Text = "Save Options"
        formats_label.Dock = DockStyle.Fill
        formats_label.AutoSize = False
        formats_label.ForeColor = NAVY_COLOR
        formats_label.Font = get_preferred_font(9.5, FontStyle.Bold)
        formats_label.Padding = Padding(0, 4, 0, 0)
        main_layout.Controls.Add(formats_label, 0, 3)

        formats_layout = TableLayoutPanel()
        formats_layout.Dock = DockStyle.Fill
        formats_layout.BackColor = LIGHT_BACKGROUND_COLOR
        formats_layout.Margin = Padding(0, 0, 0, 8)
        formats_layout.Padding = Padding(14, 10, 14, 10)
        formats_layout.ColumnCount = 1
        formats_layout.RowCount = 4
        formats_layout.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        formats_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 36.0))
        formats_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 36.0))
        formats_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 36.0))
        formats_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        main_layout.Controls.Add(formats_layout, 0, 4)

        self.full_csv_check = self._create_check_box(
            "Full CSV",
            not quick_mode
        )
        formats_layout.Controls.Add(self.full_csv_check, 0, 0)
        self.summary_csv_check = self._create_check_box(
            "Summary CSV",
            True
        )
        formats_layout.Controls.Add(self.summary_csv_check, 0, 1)
        self.styled_xlsx_check = self._create_check_box(
            "Styled XLSX Report",
            True
        )
        formats_layout.Controls.Add(self.styled_xlsx_check, 0, 2)

        self.export_note_label = Label()
        self.export_note_label.Dock = DockStyle.Fill
        self.export_note_label.AutoSize = False
        self.export_note_label.ForeColor = MUTED_COLOR
        self.export_note_label.Font = get_preferred_font(8.5)
        self.export_note_label.Padding = Padding(26, 2, 0, 0)
        formats_layout.Controls.Add(self.export_note_label, 0, 3)

        self.full_csv_check.CheckedChanged += self._update_export_state
        self.summary_csv_check.CheckedChanged += self._update_export_state
        self.styled_xlsx_check.CheckedChanged += self._update_export_state
        self._update_export_state(None, None)

        button_layout = FlowLayoutPanel()
        button_layout.Dock = DockStyle.Fill
        button_layout.FlowDirection = FlowDirection.RightToLeft
        button_layout.WrapContents = False
        button_layout.Margin = Padding(0)
        button_layout.Padding = Padding(0, 10, 0, 0)
        main_layout.Controls.Add(button_layout, 0, 5)

        ok_button = Button()
        ok_button.Text = "Run QC"
        ok_button.Size = Size(104, 34)
        ok_button.Margin = Padding(10, 0, 0, 0)
        self._apply_primary_button_style(ok_button)
        ok_button.Click += self._confirm
        self.AcceptButton = ok_button

        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.Size = Size(104, 34)
        cancel_button.Margin = Padding(10, 0, 0, 0)
        self._apply_secondary_button_style(cancel_button)
        cancel_button.DialogResult = DialogResult.Cancel
        button_layout.Controls.Add(cancel_button)
        button_layout.Controls.Add(ok_button)
        self.CancelButton = cancel_button

    def _apply_secondary_button_style(self, button):
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = SECONDARY_BORDER_COLOR
        button.FlatAppearance.MouseOverBackColor = LIGHT_BACKGROUND_COLOR
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

    def _create_check_box(self, text, checked):
        check_box = CheckBox()
        check_box.Text = text
        check_box.Dock = DockStyle.Fill
        check_box.AutoSize = True
        check_box.Margin = Padding(4, 4, 4, 4)
        check_box.ForeColor = NAVY_COLOR
        check_box.Checked = checked
        return check_box

    def _has_selected_export(self):
        return (
            self.full_csv_check.Checked
            or self.summary_csv_check.Checked
            or self.styled_xlsx_check.Checked
        )

    def _update_export_state(self, sender, event_args):
        has_selected_export = self._has_selected_export()
        self.folder_text.Enabled = has_selected_export
        self.browse_button.Enabled = has_selected_export

        if has_selected_export:
            self.export_note_label.Text = (
                "Selected files will be saved to the export folder."
            )
        else:
            self.export_note_label.Text = (
                "No files will be saved. Results will still be shown after QC."
            )

    def _update_folder_tooltip(self, sender, event_args):
        if getattr(self, "tool_tip", None) is not None:
            self.tool_tip.SetToolTip(self.folder_text, self.folder_text.Text)

    def cleanup(self):
        if getattr(self, "_cleanup_done", False):
            return
        self._cleanup_done = True
        dispose_tooltip(getattr(self, "tool_tip", None))
        self.tool_tip = None

    def _browse_folder(self, sender, event_args):
        dialog = FolderBrowserDialog()
        dialog.Description = "Select the Revit QC export folder"
        dialog.ShowNewFolderButton = True

        current_folder = self.folder_text.Text.strip()
        if os.path.isdir(current_folder):
            dialog.SelectedPath = current_folder

        dialog_result = dialog.ShowDialog(self)
        if dialog_result == DialogResult.OK:
            self.folder_text.Text = dialog.SelectedPath
        else:
            self.result = None
            self.DialogResult = DialogResult.Cancel
            self.Close()

        dialog.Dispose()

    def _confirm(self, sender, event_args):
        has_selected_export = self._has_selected_export()
        folder_path = self.folder_text.Text.strip() if has_selected_export else u""

        if has_selected_export:
            is_valid, validation_error = validate_export_folder(folder_path)

            if not is_valid:
                MessageBox.Show(
                    self,
                    validation_error,
                    "Export Options",
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

        self.result = {
            "folder": folder_path,
            "full_csv": self.full_csv_check.Checked,
            "summary_csv": self.summary_csv_check.Checked,
            "styled_xlsx": self.styled_xlsx_check.Checked,
            "selected_formats": selected_formats,
            "folder_history_error": u""
        }
        self.DialogResult = DialogResult.OK
        self.Close()


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
