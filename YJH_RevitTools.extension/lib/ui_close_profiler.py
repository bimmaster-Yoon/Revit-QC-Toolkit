# -*- coding: utf-8 -*-

"""Development-only WinForms close lifecycle profiler.

Enable with the environment variable ``UI_PERF_DEBUG=1``. The legacy
``REVIT_QC_UI_CLOSE_PROFILE=1`` switch is also accepted.
The profiler never writes to the pyRevit output window. It appends compact
records to the local Revit QC Toolkit log folder instead.
"""

import io
import os
from datetime import datetime

import clr

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")

from System.Diagnostics import Process, Stopwatch
from System.Threading import Thread, ThreadStart
from System.Windows.Forms import Application


UI_PERF_DEBUG = False
PROFILE_ENV_NAME = "UI_PERF_DEBUG"
LEGACY_PROFILE_ENV_NAME = "REVIT_QC_UI_CLOSE_PROFILE"
PROFILE_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Revit_QC_Toolkit",
    "logs",
    "ui_close_profile.log"
)

try:
    TEXT_TYPE = unicode
except NameError:
    TEXT_TYPE = str


def _is_enabled():
    if UI_PERF_DEBUG:
        return True
    values = [
        os.environ.get(PROFILE_ENV_NAME, u""),
        os.environ.get(LEGACY_PROFILE_ENV_NAME, u"")
    ]
    return any(
        TEXT_TYPE(value).strip().lower() in (u"1", u"true", u"yes", u"on")
        for value in values
    )


def is_ui_perf_debug_enabled():
    return _is_enabled()


def _safe_text(value):
    try:
        return TEXT_TYPE(value)
    except Exception:
        try:
            return str(value)
        except Exception:
            return u"N/A"


def _append_log(line):
    try:
        folder = os.path.dirname(PROFILE_LOG_PATH)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with io.open(PROFILE_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(line + u"\n")
    except Exception:
        pass


def _open_form_snapshot():
    try:
        open_count = int(Application.OpenForms.Count)
        visible_count = 0
        hidden_count = 0
        form_names = []
        for form in Application.OpenForms:
            if form.Visible:
                visible_count += 1
            else:
                hidden_count += 1
            form_names.append(_safe_text(form.Name or form.Text or form.GetType().Name))
        return {
            "open_forms": open_count,
            "visible_forms": visible_count,
            "hidden_forms": hidden_count,
            "form_names": u", ".join(form_names) or u"None"
        }
    except Exception as ex:
        return {
            "open_forms": u"N/A",
            "visible_forms": u"N/A",
            "hidden_forms": u"N/A",
            "form_names": u"Unavailable: {0}".format(_safe_text(ex))
        }


def _component_snapshot(form):
    """Best-effort inventory of non-visual components owned by a Form."""
    timer_count = 0
    worker_count = 0
    component_names = []
    try:
        container = getattr(form, "components", None)
        components = getattr(container, "Components", None)
        if components is not None:
            for component in components:
                type_name = _safe_text(component.GetType().FullName)
                component_names.append(type_name)
                lowered = type_name.lower()
                if "timer" in lowered:
                    timer_count += 1
                if "backgroundworker" in lowered:
                    worker_count += 1
    except Exception:
        pass
    return {
        "owned_timers": timer_count,
        "owned_background_workers": worker_count,
        "owned_components": u", ".join(component_names) or u"None"
    }


class UiCloseProfile(object):
    """Measure one modal WinForms window without changing normal UI behavior."""

    def __init__(self, window_name, extra_metrics_provider=None):
        self.enabled = _is_enabled()
        self.window_name = _safe_text(window_name)
        self.extra_metrics_provider = extra_metrics_provider
        self.total_watch = Stopwatch.StartNew() if self.enabled else None
        self.close_watch = None
        self.form = None
        self._form_closing_handler = None
        self._form_closed_handler = None
        self._post_close_thread = None
        self._last_cpu_ms = None
        self._last_sample_ms = None
        self.dialog_result = u"N/A"
        self.event_counts = {}
        self.event_elapsed_ms = {}
        self._interaction_controls = []
        self._interaction_tooltips = []
        self._interaction_handlers = {}
        self.component_data = {
            "owned_timers": 0,
            "owned_background_workers": 0,
            "owned_components": u"None"
        }
        if self.enabled:
            self._log(u"Profile session started")

    def attach(self, form):
        self.form = form
        if not self.enabled:
            return
        self._form_closing_handler = self._on_form_closing
        self._form_closed_handler = self._on_form_closed
        form.FormClosing += self._form_closing_handler
        form.FormClosed += self._form_closed_handler
        interaction_watch = Stopwatch.StartNew()
        self._attach_interaction_handlers()
        interaction_watch.Stop()
        self.component_data = _component_snapshot(form)
        layout_watch = Stopwatch.StartNew()
        form.PerformLayout()
        layout_watch.Stop()
        self._log(
            u"Form/control construction complete",
            dict(
                self.component_data,
                initial_layout_pass_ms=u"{0:.3f}".format(
                    layout_watch.Elapsed.TotalMilliseconds
                ),
                interaction_probe_attach_ms=u"{0:.3f}".format(
                    interaction_watch.Elapsed.TotalMilliseconds
                ),
                tooltip_instance_count=len(self._interaction_tooltips)
            )
        )

    def show_dialog(self, owner=None):
        if self.form is None:
            raise ValueError("A Form must be attached before ShowDialog.")
        if self.enabled:
            self._log(u"ShowDialog start")
        if owner is None:
            result = self.form.ShowDialog()
        else:
            result = self.form.ShowDialog(owner)
        self.dialog_result = _safe_text(result)
        if self.enabled:
            self._log(u"ShowDialog returned", {
                "dialog_result": self.dialog_result,
                "post_dialog_work_expected": self.dialog_result == u"OK"
            })
        return result

    def dispose(self):
        if self.form is None:
            return
        if self.enabled:
            self._log(u"Dispose start")
        try:
            if self.enabled:
                self._log_interaction_summary()
                self._detach_interaction_handlers()
            cleanup = getattr(self.form, "cleanup", None)
            if callable(cleanup):
                if self.enabled:
                    self._log(u"Custom cleanup start")
                cleanup()
                if self.enabled:
                    self._log(u"Custom cleanup end")
            self.form.Dispose()
        finally:
            if self.enabled:
                self._log(u"Dispose end", {
                    "form_is_disposed": bool(self.form.IsDisposed)
                })
                self._detach_handlers()
                self._start_post_close_samples()
            self.form = None

    def _on_form_closing(self, sender, event_args):
        if self.close_watch is None:
            self.close_watch = Stopwatch.StartNew()
        self._log(u"FormClosing start")
        self._log(u"FormClosing end")

    def _on_form_closed(self, sender, event_args):
        self._log(u"FormClosed start")
        self._log(u"FormClosed end")

    def _detach_handlers(self):
        form = self.form
        if form is None:
            return
        try:
            if self._form_closing_handler is not None:
                form.FormClosing -= self._form_closing_handler
        except Exception:
            pass
        try:
            if self._form_closed_handler is not None:
                form.FormClosed -= self._form_closed_handler
        except Exception:
            pass
        self._form_closing_handler = None
        self._form_closed_handler = None

    def _make_interaction_handler(self, event_name):
        def _handler(sender, event_args):
            watch = Stopwatch.StartNew()
            watch.Stop()
            self.event_counts[event_name] = self.event_counts.get(event_name, 0) + 1
            self.event_elapsed_ms[event_name] = (
                self.event_elapsed_ms.get(event_name, 0.0)
                + watch.Elapsed.TotalMilliseconds
            )
        return _handler

    def _attach_interaction_handlers(self):
        if self.form is None:
            return
        event_names = [
            "MouseEnter", "MouseHover", "MouseMove", "MouseLeave",
            "Layout", "Paint"
        ]
        for event_name in event_names:
            self._interaction_handlers[event_name] = self._make_interaction_handler(
                event_name
            )

        def _attach_control(control):
            try:
                control.MouseEnter += self._interaction_handlers["MouseEnter"]
                control.MouseHover += self._interaction_handlers["MouseHover"]
                control.MouseMove += self._interaction_handlers["MouseMove"]
                control.MouseLeave += self._interaction_handlers["MouseLeave"]
                control.Layout += self._interaction_handlers["Layout"]
                control.Paint += self._interaction_handlers["Paint"]
                self._interaction_controls.append(control)
                for child in control.Controls:
                    _attach_control(child)
            except Exception:
                pass

        _attach_control(self.form)

        popup_handler = self._make_interaction_handler("ToolTipOpening")
        self._interaction_handlers["ToolTipOpening"] = popup_handler
        seen_ids = set()
        for attribute_name in (
            "tool_tip", "folder_tooltip", "last_folder_tooltip"
        ):
            try:
                tooltip = getattr(self.form, attribute_name, None)
                if tooltip is None:
                    continue
                tooltip_id = id(tooltip)
                if tooltip_id in seen_ids:
                    continue
                seen_ids.add(tooltip_id)
                tooltip.Popup += popup_handler
                self._interaction_tooltips.append(tooltip)
            except Exception:
                pass

    def _detach_interaction_handlers(self):
        handlers = self._interaction_handlers
        for control in self._interaction_controls:
            try:
                control.MouseEnter -= handlers.get("MouseEnter")
                control.MouseHover -= handlers.get("MouseHover")
                control.MouseMove -= handlers.get("MouseMove")
                control.MouseLeave -= handlers.get("MouseLeave")
                control.Layout -= handlers.get("Layout")
                control.Paint -= handlers.get("Paint")
            except Exception:
                pass
        popup_handler = handlers.get("ToolTipOpening")
        for tooltip in self._interaction_tooltips:
            try:
                tooltip.Popup -= popup_handler
            except Exception:
                pass
        self._interaction_controls = []
        self._interaction_tooltips = []
        self._interaction_handlers = {}

    def _log_interaction_summary(self):
        summary = {
            "hover_visual_update_count": 0,
            "hover_revit_api_call_count": 0,
            "hover_full_form_layout_call_count": 0
        }
        for event_name in (
            "MouseEnter", "MouseHover", "MouseMove", "MouseLeave",
            "ToolTipOpening", "Layout", "Paint"
        ):
            count = self.event_counts.get(event_name, 0)
            elapsed_ms = self.event_elapsed_ms.get(event_name, 0.0)
            average_ms = elapsed_ms / count if count else 0.0
            summary["{0}_count".format(event_name)] = count
            summary["{0}_avg_ms".format(event_name)] = u"{0:.4f}".format(
                average_ms
            )
        self._log(u"Interaction summary", summary)

    def _start_post_close_samples(self):
        try:
            process = Process.GetCurrentProcess()
            self._last_cpu_ms = process.TotalProcessorTime.TotalMilliseconds
            self._last_sample_ms = self.total_watch.ElapsedMilliseconds
            thread = Thread(ThreadStart(self._sample_post_close))
            thread.IsBackground = True
            thread.Name = "RevitQC UI close profiler"
            self._post_close_thread = thread
            thread.Start()
        except Exception as ex:
            self._log(u"Post-close sampler could not start", {
                "error": _safe_text(ex)
            })

    def _sample_post_close(self):
        cumulative_delays = ((500, u"0.5s"), (500, u"1.0s"), (2000, u"3.0s"))
        for delay_ms, label in cumulative_delays:
            Thread.Sleep(delay_ms)
            self._log_cpu_sample(label)

    def _log_cpu_sample(self, label):
        try:
            process = Process.GetCurrentProcess()
            now_cpu_ms = process.TotalProcessorTime.TotalMilliseconds
            now_ms = self.total_watch.ElapsedMilliseconds
            interval_cpu_ms = now_cpu_ms - self._last_cpu_ms
            interval_wall_ms = max(1.0, now_ms - self._last_sample_ms)
            cpu_ratio = (interval_cpu_ms / interval_wall_ms) * 100.0
            self._last_cpu_ms = now_cpu_ms
            self._last_sample_ms = now_ms
            classification = u"one-time/idle"
            if label == u"3.0s" and cpu_ratio >= 5.0:
                if self.dialog_result == u"OK":
                    classification = u"expected Run workload or sustained activity"
                else:
                    classification = u"sustained activity candidate after Cancel/Close"
            self._log(u"Post-close {0}".format(label), {
                "interval_cpu_ms": u"{0:.1f}".format(interval_cpu_ms),
                "interval_cpu_ratio_pct": u"{0:.1f}".format(cpu_ratio),
                "classification": classification,
                "dialog_result": self.dialog_result,
                "profiler_thread_active": True,
                "thread_count_excluding_profiler": max(
                    0,
                    process.Threads.Count - 1
                )
            })
        except Exception as ex:
            self._log(u"Post-close {0} failed".format(label), {
                "error": _safe_text(ex)
            })

    def _get_extra_metrics(self):
        provider = self.extra_metrics_provider
        if provider is None:
            return {}
        try:
            value = provider()
            return value if hasattr(value, "items") else {}
        except Exception as ex:
            return {"extra_metrics_error": _safe_text(ex)}

    def _log(self, event_name, extra=None):
        if not self.enabled:
            return
        try:
            process = Process.GetCurrentProcess()
            form_data = _open_form_snapshot()
            fields = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "window": self.window_name,
                "event": _safe_text(event_name),
                "dialog_result": self.dialog_result,
                "total_elapsed_ms": self.total_watch.ElapsedMilliseconds,
                "close_elapsed_ms": (
                    self.close_watch.ElapsedMilliseconds if self.close_watch is not None
                    else u"N/A"
                ),
                "process_cpu_total_ms": u"{0:.1f}".format(
                    process.TotalProcessorTime.TotalMilliseconds
                ),
                "thread_count": process.Threads.Count,
                "task_enumeration": u"Not supported; source audit required",
                "profiler_enabled": True
            }
            fields.update(form_data)
            fields.update(self.component_data)
            fields.update(self._get_extra_metrics())
            if extra:
                fields.update(extra)
            ordered = []
            for key in sorted(fields.keys()):
                ordered.append(u"{0}={1}".format(key, _safe_text(fields[key])))
            _append_log(u" | ".join(ordered))
        except Exception:
            pass


def create_ui_close_profile(window_name, extra_metrics_provider=None):
    return UiCloseProfile(window_name, extra_metrics_provider)


def log_layout_snapshot(window_name, form, content_host, content_panel):
    """Write a development-only WinForms overflow snapshot."""
    if not _is_enabled():
        return
    try:
        top_level_bounds = []
        lowest_bottom = 0
        rightmost_right = 0
        nested_auto_scroll = 0

        def _visit(control):
            count = 0
            try:
                if hasattr(control, "AutoScroll") and control.AutoScroll:
                    count += 1
                for child in control.Controls:
                    count += _visit(child)
            except Exception:
                pass
            return count

        nested_auto_scroll = _visit(content_host)
        for control in content_panel.Controls:
            try:
                bounds = control.Bounds
                type_name = _safe_text(control.GetType().Name)
                control_label = _safe_text(getattr(control, "Text", u""))
                top_level_bounds.append(
                    u"{0}:{1}[L={2},T={3},W={4},H={5}]".format(
                        type_name,
                        control_label,
                        bounds.Left,
                        bounds.Top,
                        bounds.Width,
                        bounds.Height
                    )
                )
                lowest_bottom = max(lowest_bottom, bounds.Bottom)
                rightmost_right = max(rightmost_right, bounds.Right)
            except Exception:
                pass

        footer_panel = getattr(form, "footer_panel", None)
        footer_inside_scroll = False
        footer_bounds = u"N/A"
        if footer_panel is not None:
            try:
                footer_bounds = _safe_text(footer_panel.Bounds)
                current = footer_panel.Parent
                while current is not None:
                    if current == content_host:
                        footer_inside_scroll = True
                        break
                    current = current.Parent
            except Exception:
                pass

        existing_sheet_combo = getattr(form, "existing_report_sheet_combo", None)
        existing_sheet_visible = u"N/A"
        if existing_sheet_combo is not None:
            try:
                existing_sheet_visible = bool(existing_sheet_combo.Visible)
            except Exception:
                pass

        fields = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "window": _safe_text(window_name),
            "event": u"Layout snapshot",
            "form_client_size": _safe_text(form.ClientSize),
            "content_host_client_size": _safe_text(content_host.ClientSize),
            "content_host_display_rectangle": _safe_text(
                content_host.DisplayRectangle
            ),
            "content_panel_preferred_size": _safe_text(
                content_panel.PreferredSize
            ),
            "auto_scroll": bool(content_host.AutoScroll),
            "auto_scroll_min_size": _safe_text(content_host.AutoScrollMinSize),
            "nested_auto_scroll_count": nested_auto_scroll,
            "footer_inside_scroll": footer_inside_scroll,
            "footer_bounds": footer_bounds,
            "existing_sheet_control_visible": existing_sheet_visible,
            "top_level_bounds": u"; ".join(top_level_bounds) or u"None",
            "lowest_control_bottom": lowest_bottom,
            "rightmost_control_right": rightmost_right,
            "device_dpi": getattr(form, "DeviceDpi", u"N/A")
        }
        ordered = []
        for key in sorted(fields.keys()):
            ordered.append(u"{0}={1}".format(key, _safe_text(fields[key])))
        _append_log(u" | ".join(ordered))
    except Exception:
        pass
