# -*- coding: utf-8 -*-

"""Shared 96-DPI WinForms design tokens for Revit QC Toolkit dialogs."""

from System.Drawing import Color, Font, FontFamily, FontStyle, Size
from System.Windows.Forms import FlatStyle, Screen


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
