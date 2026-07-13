# -*- coding: utf-8 -*-

"""Shared 96-DPI WinForms design tokens for Revit QC Toolkit dialogs."""

from System.Drawing import Color, Font, FontFamily, FontStyle, Point, Size
from System.Windows.Forms import (
    AutoSizeMode, DockStyle, FlatStyle, Label, Padding, Panel, Screen
)


NAVY_COLOR = Color.FromArgb(38, 54, 69)
SOFT_NAVY_COLOR = Color.FromArgb(74, 91, 106)
BUTTON_NAVY_COLOR = Color.FromArgb(83, 103, 119)
BUTTON_HOVER_COLOR = Color.FromArgb(70, 88, 103)
MUTED_COLOR = Color.FromArgb(95, 111, 125)
BORDER_COLOR = Color.FromArgb(214, 221, 227)
SECONDARY_BORDER_COLOR = Color.FromArgb(199, 208, 216)
LIGHT_FILL_COLOR = Color.FromArgb(244, 246, 248)
HELP_BACKGROUND_COLOR = Color.FromArgb(248, 249, 250)
WARNING_BACKGROUND_COLOR = Color.FromArgb(255, 241, 230)
ORANGE_COLOR = Color.FromArgb(222, 113, 47)
ORANGE_HOVER_COLOR = Color.FromArgb(242, 140, 40)

OUTER_MARGIN = 24
HEADER_TOP_PADDING = 22
HEADER_BOTTOM_MARGIN = 16
SECTION_GAP = 14
GROUP_INNER_PADDING = 12
ROW_GAP = 8
LABEL_CONTROL_GAP = 12
CARD_GAP = 8
CONTROL_HEIGHT = 32
SMALL_ACTION_BUTTON_WIDTH = 108
SMALL_ACTION_BUTTON_HEIGHT = 38
FOOTER_BUTTON_WIDTH = 112
FOOTER_BUTTON_HEIGHT = 40
FOOTER_HEIGHT = 64
BUTTON_GAP = 12
FOOTER_RIGHT_MARGIN = 24
FOOTER_BOTTOM_MARGIN = 24
FOOTER_TOP_MARGIN = 18
SETTINGS_FOOTER_BUTTON_WIDTH = 144
SETTINGS_FOOTER_BUTTON_HEIGHT = 42
SECTION_TITLE_VISIBLE_GAP = 6
SECTION_TITLE_PREFIX = u"   "

# Backward-compatible names used by existing dialogs.
WINDOW_PADDING = OUTER_MARGIN
BUTTON_WIDTH = FOOTER_BUTTON_WIDTH
BUTTON_HEIGHT = FOOTER_BUTTON_HEIGHT
WIDE_BUTTON_WIDTH = 175


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


def align_section_title_accent(
    title_label,
    accent_bar,
    visible_gap=SECTION_TITLE_VISIBLE_GAP
):
    """Align one section accent against its title in logical pixels."""
    title_label.Padding = Padding(0)
    title_label.Margin = Padding(0)
    title_label.Left = accent_bar.Right + int(visible_gap)
    accent_y = title_label.Top + int(
        round((title_label.Height - accent_bar.Height) / 2.0)
    )
    accent_bar.Top = max(1, accent_y)


def apply_scan_reference_section_style(
    group,
    title,
    title_font=None,
    margin_bottom=SECTION_GAP
):
    """Apply the established Scan QC GroupBox legend treatment.

    This intentionally keeps the native GroupBox border and caption masking.
    The hidden label is only a font-metric reference used to center the accent
    bar against the caption text; it does not introduce a header panel or a
    second border.
    """
    group.Text = u"{0}{1}".format(SECTION_TITLE_PREFIX, title)
    group.Dock = DockStyle.Fill
    group.AutoSize = True
    group.AutoSizeMode = AutoSizeMode.GrowAndShrink
    group.FlatStyle = FlatStyle.Flat
    group.ForeColor = NAVY_COLOR
    if title_font is not None:
        group.Font = title_font
    group.Padding = Padding(3)
    group.Margin = Padding(0, 0, 0, int(margin_bottom))

    title_metric = Label()
    title_metric.Text = title
    title_metric.AutoSize = False
    title_metric.Font = group.Font
    title_metric.Location = Point(0, 0)
    preferred_title_size = title_metric.GetPreferredSize(Size(0, 0))
    title_metric.Size = Size(
        max(1, preferred_title_size.Width),
        group.Font.Height
    )
    title_metric.Visible = False
    title_metric.TabStop = False
    group.Controls.Add(title_metric)

    accent = Panel()
    accent.BackColor = ORANGE_HOVER_COLOR
    accent.Size = Size(4, 16)
    accent.Location = Point(12, 1)
    accent.Enabled = False
    accent.Margin = Padding(0)
    group.Controls.Add(accent)
    align_section_title_accent(title_metric, accent)
    accent.BringToFront()
    group.Tag = {
        "section_title_metric": title_metric,
        "section_accent_bar": accent
    }
    return group.Tag


def apply_secondary_button_style(button):
    button.FlatStyle = FlatStyle.Flat
    button.FlatAppearance.BorderSize = 1
    button.FlatAppearance.BorderColor = SECONDARY_BORDER_COLOR
    button.FlatAppearance.MouseOverBackColor = LIGHT_FILL_COLOR
    button.FlatAppearance.MouseDownBackColor = BORDER_COLOR
    button.BackColor = Color.White
    button.ForeColor = NAVY_COLOR
    button.UseVisualStyleBackColor = False


def apply_primary_button_style(button):
    button.FlatStyle = FlatStyle.Flat
    button.FlatAppearance.BorderSize = 1
    button.FlatAppearance.BorderColor = BUTTON_NAVY_COLOR
    button.FlatAppearance.MouseOverBackColor = BUTTON_HOVER_COLOR
    button.FlatAppearance.MouseDownBackColor = SOFT_NAVY_COLOR
    button.BackColor = BUTTON_NAVY_COLOR
    button.ForeColor = Color.White
    button.UseVisualStyleBackColor = False


def attach_border_hover(
    button,
    restore_callback=None,
    enter_callback=None
):
    """Attach border-only hover handlers and return a cleanup token."""
    base_back_color = button.BackColor
    base_fore_color = button.ForeColor
    base_border_color = button.FlatAppearance.BorderColor
    base_border_size = button.FlatAppearance.BorderSize
    base_mouse_over_color = button.FlatAppearance.MouseOverBackColor

    def mouse_enter(sender, event_args):
        if not sender.Enabled:
            return
        sender.FlatAppearance.BorderColor = ORANGE_HOVER_COLOR
        sender.FlatAppearance.BorderSize = 1
        sender.FlatAppearance.MouseOverBackColor = sender.BackColor
        if enter_callback is not None:
            enter_callback(sender)
        sender.Invalidate()

    def mouse_leave(sender, event_args):
        if restore_callback is not None:
            restore_callback(sender)
        else:
            sender.BackColor = base_back_color
            sender.ForeColor = base_fore_color
            sender.FlatAppearance.BorderColor = base_border_color
            sender.FlatAppearance.BorderSize = base_border_size
            sender.FlatAppearance.MouseOverBackColor = base_mouse_over_color
        sender.Invalidate()

    button.MouseEnter += mouse_enter
    button.MouseLeave += mouse_leave
    return (button, mouse_enter, mouse_leave)


def detach_border_hover(binding):
    if not binding:
        return
    button, mouse_enter, mouse_leave = binding
    try:
        button.MouseEnter -= mouse_enter
        button.MouseLeave -= mouse_leave
    except Exception:
        pass


def configure_tooltip(tool_tip):
    """Apply low-overhead shared WinForms ToolTip behavior."""
    tool_tip.UseAnimation = False
    tool_tip.UseFading = False
    tool_tip.InitialDelay = 350
    tool_tip.ReshowDelay = 100
    tool_tip.AutoPopDelay = 7000
    tool_tip.ShowAlways = False
    return tool_tip


def dispose_tooltip(tool_tip):
    if tool_tip is None:
        return
    try:
        tool_tip.RemoveAll()
    except Exception:
        pass
    try:
        tool_tip.Dispose()
    except Exception:
        pass


def configure_content_scroll(form, content_host, content_panel, maximum_ratio=0.94):
    """Enable AutoScroll only when content cannot fit inside the working area."""
    try:
        content_host.AutoScroll = False
        content_host.AutoScrollMinSize = Size.Empty
        form.PerformLayout()

        host_width = max(0, content_host.ClientSize.Width)
        if host_width > 0:
            content_panel.Width = host_width
        form.PerformLayout()

        preferred_height = content_panel.PreferredSize.Height
        available_height = content_host.ClientSize.Height
        working_area = Screen.FromControl(form).WorkingArea
        maximum_client_height = int(working_area.Height * maximum_ratio)

        if preferred_height > available_height:
            required_extra = preferred_height - available_height
            requested_height = min(
                maximum_client_height,
                form.ClientSize.Height + required_extra
            )
            if requested_height > form.ClientSize.Height:
                form.ClientSize = Size(form.ClientSize.Width, requested_height)
                form.PerformLayout()
                available_height = content_host.ClientSize.Height

        preferred_width = content_panel.PreferredSize.Width
        horizontal_overflow = preferred_width > content_host.ClientSize.Width + 1
        vertical_overflow = preferred_height > available_height + 1
        # Width is clamped to the host so DPI rounding by one or two pixels
        # does not create an unnecessary vertical scrollbar.
        needs_scroll = vertical_overflow

        if needs_scroll:
            content_host.AutoScrollMinSize = Size(
                0,
                preferred_height
            )
        else:
            content_host.AutoScrollMinSize = Size.Empty
        content_host.AutoScroll = needs_scroll
        return {
            "preferred_width": preferred_width,
            "preferred_height": preferred_height,
            "available_width": content_host.ClientSize.Width,
            "available_height": available_height,
            "horizontal_overflow": horizontal_overflow,
            "vertical_overflow": vertical_overflow,
            "auto_scroll": content_host.AutoScroll
        }
    except Exception:
        try:
            content_host.AutoScroll = False
            content_host.AutoScrollMinSize = Size.Empty
        except Exception:
            pass
        return {}
