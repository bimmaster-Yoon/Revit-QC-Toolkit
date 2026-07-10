# -*- coding: utf-8 -*-

"""Lightweight WinForms controls used by the Scan QC setup dialog."""

from System.Drawing import (
    Color,
    Point,
    Rectangle,
    Size,
    SolidBrush,
    Pen
)
from System.Drawing.Drawing2D import SmoothingMode
from System.Windows.Forms import (
    BorderStyle,
    HorizontalAlignment,
    Keys,
    TextBox,
    UserControl
)


SLIDER_MINIMUM = 1
SLIDER_MAXIMUM = 20
SLIDER_DEFAULT = 7
SLIDER_ROW_HEIGHT = 40
SLIDER_BADGE_COLUMN_WIDTH = 44
SLIDER_BADGE_WIDTH = 42
SLIDER_BADGE_HEIGHT = 28
SLIDER_BADGE_GAP = 12
SLIDER_THUMB_SIZE = 16
SLIDER_TRACK_HEIGHT = 6

TRACK_COLOR = Color.FromArgb(225, 229, 233)
ACTIVE_COLOR = Color.FromArgb(242, 140, 40)
BADGE_BACKGROUND_COLOR = Color.FromArgb(255, 247, 239)
LABEL_COLOR = Color.FromArgb(38, 54, 69)


def clamp_slider_value(value, minimum=SLIDER_MINIMUM, maximum=SLIDER_MAXIMUM):
    """Return an integer value constrained to the slider range."""
    try:
        numeric_value = int(float(value))
    except Exception:
        numeric_value = SLIDER_DEFAULT
    return max(minimum, min(maximum, numeric_value))


def value_from_slider_x(
    mouse_x,
    track_left,
    track_width,
    minimum=SLIDER_MINIMUM,
    maximum=SLIDER_MAXIMUM
):
    """Map a track X coordinate to the nearest integer slider value."""
    if track_width <= 0 or maximum <= minimum:
        return minimum
    ratio = float(mouse_x - track_left) / float(track_width)
    ratio = max(0.0, min(1.0, ratio))
    return clamp_slider_value(
        minimum + int(round(ratio * (maximum - minimum))),
        minimum,
        maximum
    )


def parse_slider_text_value(text_value):
    """Parse an integer entry, returning None for empty or invalid text."""
    try:
        normalized_text = text_value.strip()
    except Exception:
        return None
    if not normalized_text:
        return None
    try:
        return int(normalized_text)
    except Exception:
        return None


class TopNCalloutsSlider(UserControl):
    """Painted integer slider with an editable current-value field."""

    def __init__(self, value=SLIDER_DEFAULT):
        UserControl.__init__(self)
        self.DoubleBuffered = True
        self.ResizeRedraw = True
        self.TabStop = True
        self.MinimumSize = Size(0, SLIDER_ROW_HEIGHT)
        self.MaximumSize = Size(0, SLIDER_ROW_HEIGHT)
        self.Height = SLIDER_ROW_HEIGHT
        self.BackColor = Color.White
        self._minimum = SLIDER_MINIMUM
        self._maximum = SLIDER_MAXIMUM
        self._value = clamp_slider_value(value, self._minimum, self._maximum)
        self._dragging = False
        self._updating_top_n = False
        self._value_changed_callback = None

        self._value_text = TextBox()
        self._value_text.AutoSize = False
        self._value_text.BorderStyle = getattr(BorderStyle, "None")
        self._value_text.BackColor = BADGE_BACKGROUND_COLOR
        self._value_text.ForeColor = LABEL_COLOR
        self._value_text.TextAlign = HorizontalAlignment.Center
        self._value_text.Text = u"{0}".format(self._value)
        self._value_text.TabStop = True
        self._value_text.TextChanged += self._on_value_text_changed
        self._value_text.KeyDown += self._on_value_text_key_down
        self._value_text.Leave += self._on_value_text_leave
        self._value_text.Enter += self._on_value_text_enter
        self.Controls.Add(self._value_text)
        self._position_value_text_box()

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, value):
        self._set_value(value)

    @property
    def ValueTextBox(self):
        return self._value_text

    def set_value_changed_callback(self, callback):
        self._value_changed_callback = callback

    def _sync_text_to_value(self):
        text_value = u"{0}".format(self._value)
        if self._value_text.Text == text_value:
            return
        self._updating_top_n = True
        try:
            self._value_text.Text = text_value
            self._value_text.SelectionStart = len(text_value)
        finally:
            self._updating_top_n = False

    def _set_value(self, value, update_text=True):
        next_value = clamp_slider_value(value, self._minimum, self._maximum)
        changed = next_value != self._value
        if changed:
            self._value = next_value
            self._invalidate_slider_region()
        if update_text:
            self._sync_text_to_value()
        if changed and self._value_changed_callback is not None:
            self._value_changed_callback(self._value)
        return changed

    def _parse_value_text(self):
        return parse_slider_text_value(self._value_text.Text)

    def _commit_value_text(self):
        parsed_value = self._parse_value_text()
        if parsed_value is None:
            self._sync_text_to_value()
            return
        self._set_value(parsed_value, update_text=True)

    def _on_value_text_changed(self, sender, event_args):
        if self._updating_top_n:
            return
        parsed_value = self._parse_value_text()
        if parsed_value is None:
            return
        self._set_value(parsed_value, update_text=True)

    def _on_value_text_key_down(self, sender, event_args):
        if event_args.KeyCode == Keys.Enter:
            self._commit_value_text()
            event_args.Handled = True
            event_args.SuppressKeyPress = True

    def _on_value_text_leave(self, sender, event_args):
        self._commit_value_text()

    def _on_value_text_enter(self, sender, event_args):
        self._value_text.SelectAll()

    def _get_badge_bounds(self):
        return Rectangle(
            self.ClientSize.Width
            - SLIDER_BADGE_COLUMN_WIDTH
            + ((SLIDER_BADGE_COLUMN_WIDTH - SLIDER_BADGE_WIDTH) // 2),
            (self.Height - SLIDER_BADGE_HEIGHT) // 2,
            SLIDER_BADGE_WIDTH,
            SLIDER_BADGE_HEIGHT
        )

    def _position_value_text_box(self):
        badge_bounds = self._get_badge_bounds()
        text_height = 20
        self._value_text.Location = Point(
            badge_bounds.X + 3,
            (self.Height - text_height) // 2
        )
        self._value_text.Size = Size(
            max(1, badge_bounds.Width - 6),
            text_height
        )

    def _invalidate_slider_region(self):
        badge_bounds = self._get_badge_bounds()
        self.Invalidate(
            Rectangle(
                0,
                0,
                max(1, badge_bounds.X - SLIDER_BADGE_GAP),
                self.Height
            )
        )

    def _get_track_bounds(self):
        thumb_radius = SLIDER_THUMB_SIZE // 2
        badge_left = (
            self.ClientSize.Width
            - SLIDER_BADGE_COLUMN_WIDTH
            + ((SLIDER_BADGE_COLUMN_WIDTH - SLIDER_BADGE_WIDTH) // 2)
        )
        track_left = thumb_radius
        track_right = badge_left - SLIDER_BADGE_GAP - thumb_radius
        track_width = max(1, track_right - track_left)
        track_top = (self.ClientSize.Height - SLIDER_TRACK_HEIGHT) // 2
        return track_left, track_top, track_width

    def _get_thumb_center_x(self, track_left, track_width):
        ratio = float(self._value - self._minimum) / float(
            self._maximum - self._minimum
        )
        return int(round(track_left + (track_width * ratio)))

    def _set_value_from_mouse(self, mouse_x):
        track_left, _track_top, track_width = self._get_track_bounds()
        next_value = value_from_slider_x(
            mouse_x,
            track_left,
            track_width,
            self._minimum,
            self._maximum
        )
        self._set_value(next_value)

    def OnPaint(self, event_args):
        UserControl.OnPaint(self, event_args)
        graphics = event_args.Graphics
        graphics.SmoothingMode = SmoothingMode.AntiAlias

        track_left, track_top, track_width = self._get_track_bounds()
        thumb_center_x = self._get_thumb_center_x(track_left, track_width)
        track_bounds = Rectangle(
            track_left,
            track_top,
            track_width,
            SLIDER_TRACK_HEIGHT
        )
        active_bounds = Rectangle(
            track_left,
            track_top,
            max(0, thumb_center_x - track_left),
            SLIDER_TRACK_HEIGHT
        )
        track_brush = SolidBrush(TRACK_COLOR)
        try:
            graphics.FillRectangle(track_brush, track_bounds)
        finally:
            track_brush.Dispose()
        if active_bounds.Width > 0:
            active_brush = SolidBrush(ACTIVE_COLOR)
            try:
                graphics.FillRectangle(active_brush, active_bounds)
            finally:
                active_brush.Dispose()

        thumb_bounds = Rectangle(
            thumb_center_x - (SLIDER_THUMB_SIZE // 2),
            (self.Height - SLIDER_THUMB_SIZE) // 2,
            SLIDER_THUMB_SIZE,
            SLIDER_THUMB_SIZE
        )
        thumb_brush = SolidBrush(ACTIVE_COLOR)
        try:
            graphics.FillEllipse(thumb_brush, thumb_bounds)
        finally:
            thumb_brush.Dispose()

        badge_bounds = self._get_badge_bounds()
        if event_args.ClipRectangle.IntersectsWith(badge_bounds):
            badge_brush = SolidBrush(BADGE_BACKGROUND_COLOR)
            try:
                graphics.FillRectangle(badge_brush, badge_bounds)
            finally:
                badge_brush.Dispose()
            badge_pen = Pen(ACTIVE_COLOR, 1.0)
            try:
                graphics.DrawRectangle(badge_pen, badge_bounds)
            finally:
                badge_pen.Dispose()

    def OnResize(self, event_args):
        UserControl.OnResize(self, event_args)
        if hasattr(self, "_value_text"):
            self._position_value_text_box()

    def OnFontChanged(self, event_args):
        UserControl.OnFontChanged(self, event_args)
        if hasattr(self, "_value_text"):
            self._value_text.Font = self.Font

    def OnMouseDown(self, event_args):
        UserControl.OnMouseDown(self, event_args)
        self.Focus()
        track_left, _track_top, track_width = self._get_track_bounds()
        hit_padding = SLIDER_THUMB_SIZE // 2
        if (
            event_args.X < track_left - hit_padding
            or event_args.X > track_left + track_width + hit_padding
        ):
            return
        self._dragging = True
        self.Capture = True
        self._set_value_from_mouse(event_args.X)

    def OnMouseMove(self, event_args):
        UserControl.OnMouseMove(self, event_args)
        if self._dragging:
            self._set_value_from_mouse(event_args.X)

    def OnMouseUp(self, event_args):
        UserControl.OnMouseUp(self, event_args)
        self._dragging = False
        self.Capture = False

    def OnMouseCaptureChanged(self, event_args):
        UserControl.OnMouseCaptureChanged(self, event_args)
        if not self.Capture:
            self._dragging = False

    def IsInputKey(self, key_data):
        key_code = key_data & Keys.KeyCode
        if key_code == Keys.Left or key_code == Keys.Right:
            return True
        return UserControl.IsInputKey(self, key_data)

    def OnKeyDown(self, event_args):
        if event_args.KeyCode == Keys.Left:
            self._set_value(self._value - 1)
            event_args.Handled = True
            return
        if event_args.KeyCode == Keys.Right:
            self._set_value(self._value + 1)
            event_args.Handled = True
            return
        UserControl.OnKeyDown(self, event_args)
