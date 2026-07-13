# -*- coding: utf-8 -*-

import io
import os
import sys
import traceback
from datetime import datetime

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Diagnostics import Process, ProcessStartInfo, Stopwatch
from System.Drawing import (
    Color, ContentAlignment, FontStyle, Point, Rectangle, Size, SolidBrush
)
from System.Windows.Forms import (
    AutoScaleMode, AutoSizeMode, BorderStyle, Button, ColumnStyle, DockStyle,
    Control, FlatStyle, FlowDirection, FlowLayoutPanel, Form,
    FormBorderStyle, FormStartPosition, Keys, Label, LinkLabel, MouseButtons,
    Padding, Panel, RowStyle, SizeType, TableLayoutPanel, TextFormatFlags,
    TextRenderer, MessageBox, MessageBoxButtons, MessageBoxIcon
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from qc_ui_style import (
    BORDER_COLOR, HELP_BACKGROUND_COLOR, NAVY_COLOR, ORANGE_COLOR,
    ORANGE_HOVER_COLOR, WARNING_BACKGROUND_COLOR,
    attach_border_hover, detach_border_hover, get_preferred_font
)
from toolkit_version import get_toolkit_version_label
from ui_close_profiler import (
    create_ui_close_profile, is_ui_perf_debug_enabled
)


WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 900
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 820
WINDOW_PADDING = 24
HEADER_BODY_GAP = 22
NAVIGATION_WIDTH = 215
NAVIGATION_DETAIL_GAP = 20
NAVIGATION_BUTTON_HEIGHT = 46
NAVIGATION_BUTTON_GAP = 8
DETAIL_PADDING = 24
CARD_GAP = 12
CARD_PADDING_HORIZONTAL = 18
CARD_PADDING_VERTICAL = 14
SCROLLBAR_WIDTH = 10
SCROLL_TRACK_INSET = 2
SCROLL_THUMB_MIN_HEIGHT = 36
DETAIL_BOTTOM_PADDING = 20
FOOTER_HEIGHT = 64

HOVER_COLOR = Color.FromArgb(247, 249, 251)
CARD_FILL_COLOR = Color.FromArgb(247, 249, 251)
BODY_TEXT_COLOR = Color.FromArgb(51, 71, 91)
SUBTITLE_COLOR = Color.FromArgb(100, 116, 135)
OVERVIEW_ACCENT_COLOR = Color.FromArgb(232, 117, 22)
SCROLL_TRACK_COLOR = Color.FromArgb(238, 241, 244)
SCROLL_THUMB_COLOR = Color.FromArgb(242, 140, 40)
SCROLL_THUMB_HOVER_COLOR = Color.FromArgb(220, 118, 23)
SELECTED_NAVIGATION_COLOR = Color.FromArgb(255, 244, 234)

HELP_PROFILE_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Revit_QC_Toolkit",
    "logs",
    "help_navigation_profile.log"
)
GITHUB_REPOSITORY_URL = (
    u"https://github.com/BIMboy-Yoon/Revit-QC-Toolkit"
)
GITHUB_RELEASES_URL = GITHUB_REPOSITORY_URL + u"/releases"


HELP_SECTIONS = [
    {
        "nav": u"Getting Started",
        "title": u"Getting Started",
        "subtitle": u"Toolkit Setup and Safe Workflow",
        "overview": (
            u"Revit QC Toolkit은 Sheet, View, Parameter와 Point Cloud 기반 "
            u"모델 정합성을 검토하는 Revit 2026용 pyRevit Extension입니다."
        ),
        "cards": [
            (
                u"Quick Start",
                [
                    u"1. QC Settings에서 Rule Set과 Excel 실행 환경을 확인합니다.",
                    u"2. 빠른 상태 확인은 QC Lite, 전체 문서 검토는 DOC QC를 실행합니다.",
                    u"3. Point Cloud 검토는 Scan QC에서 Source Plan View와 Point Cloud를 선택합니다.",
                    u"4. 최근에 생성된 결과는 Report 버튼으로 다시 열 수 있습니다."
                ]
            ),
            (
                u"Model Safety",
                [
                    u"DOC QC와 QC Lite는 모델을 변경하지 않는 read-only 검사입니다.",
                    u"Scan QC는 선택 옵션에 따라 SCAN_QC_* 작업 View, Revision Cloud와 Report Sheet를 생성할 수 있습니다.",
                    u"원본 View와 Point Cloud 그래픽은 수정하지 않습니다."
                ]
            ),
            (
                u"Supported Environment",
                [
                    u"Revit: 2026",
                    u"Runtime: pyRevit Extension",
                    u"보고서 기능은 QC Settings에 표시되는 Python 및 Excel Library 상태를 따릅니다."
                ]
            ),
            (
                u"Toolkit Information",
                [
                    u"Version: {0}".format(get_toolkit_version_label()),
                    u"Revit: 2026",
                    u"pyRevit: Supported Extension",
                    u"Mode: DOC QC Read-only / Scan QC creates QC result elements"
                ]
            ),
            (
                u"Resources",
                [
                    {
                        "text": u"GitHub Repository · 소스 코드, 설치 파일, 변경 이력",
                        "url": GITHUB_REPOSITORY_URL
                    },
                    {
                        "text": u"GitHub Releases · 최신 설치 ZIP과 Release Notes",
                        "url": GITHUB_RELEASES_URL
                    }
                ]
            )
        ]
    },
    {
        "nav": u"DOC QC",
        "title": u"DOC QC",
        "subtitle": u"Drawing Package Quality Control",
        "overview": (
            u"Sheet / View / Parameter 전체 도면 패키지를 선택한 Rule Set으로 검사하고 "
            u"상세 보고서로 정리합니다."
        ),
        "cards": [
            (
                u"When to Use / 사용 목적",
                [
                    u"제출 전 도면 패키지의 번호, 이름, 필수 Parameter와 View 배치 상태를 한 번에 확인할 때 사용합니다."
                ]
            ),
            (
                u"Workflow / 사용 순서",
                [
                    u"1. Review Scope와 QC Categories를 선택합니다.",
                    u"2. Rule Set, Report Folder와 Report Style을 확인합니다.",
                    u"3. Run을 실행하고 pyRevit Summary 또는 생성된 보고서를 검토합니다."
                ]
            ),
            (
                u"Key Options / 주요 옵션",
                [
                    u"Review Scope: Current Project를 기본으로 하며 지원되는 범위만 실행합니다.",
                    u"QC Categories: Sheet QC / View QC / Parameter QC를 선택합니다.",
                    u"Naming QC와 View Placement QC는 기존 Sheet·View 검사에 포함됩니다.",
                    u"Rule Set: 프로젝트 기준에 맞는 JSON Rule preset을 적용합니다."
                ]
            ),
            (
                u"Output / 결과물",
                [
                    u"pyRevit Output Summary와 상세 XLSX Report를 기존 보고서 엔진으로 생성합니다.",
                    u"Open Report After Run을 선택하면 정상 생성된 보고서를 실행 후 엽니다."
                ]
            ),
            (
                u"Caution / 주의사항",
                [
                    u"저장 위치 선택을 취소하면 설정과 파일을 변경하지 않고 조용히 종료합니다.",
                    u"DOC QC 검사는 Revit 모델 요소를 수정하지 않습니다."
                ]
            )
        ]
    },
    {
        "nav": u"QC Lite",
        "title": u"QC Lite",
        "subtitle": u"Quick Project Health Summary",
        "overview": (
            u"Sheet / View / Parameter의 핵심 Issue를 빠르게 확인하는 요약 검사와 "
            u"프로젝트 상태 Dashboard입니다."
        ),
        "cards": [
            (
                u"When to Use / 사용 목적",
                [
                    u"전체 상세 보고서가 필요하기 전에 현재 프로젝트의 주요 문제 수와 우선순위를 빠르게 파악할 때 사용합니다."
                ]
            ),
            (
                u"DOC QC와 차이",
                [
                    u"QC Lite는 핵심 수치, Severity Count와 Top Issues를 Compact Summary로 보여줍니다.",
                    u"전체 Rule 결과와 상세 XLSX가 필요하면 DOC QC를 실행합니다."
                ]
            ),
            (
                u"Output / 결과 확인",
                [
                    u"Sheet / View / Parameter Issue Count와 대표 Issue를 카드형으로 확인합니다.",
                    u"Compact Summary HTML을 생성하며 설정에 따라 PDF Summary도 생성할 수 있습니다.",
                    u"Scan QC 카드는 별도 Scan QC 실행을 안내하는 상태 정보입니다."
                ]
            ),
            (
                u"다음 작업",
                [
                    u"상세 검토는 DOC QC로 확장하고, 최근 저장 결과는 Report 버튼으로 엽니다."
                ]
            )
        ]
    },
    {
        "nav": u"Scan QC",
        "title": u"Scan QC",
        "subtitle": u"Point Cloud Deviation Review",
        "overview": (
            u"선택한 Point Cloud를 기준으로 Wall Deviation을 샘플링하고 QC View, "
            u"Revision Cloud ID와 PDF Report를 생성합니다."
        ),
        "cards": [
            (
                u"Workflow / 사용 순서",
                [
                    u"1. Analysis Scope와 Source Plan View를 선택합니다.",
                    u"2. Analysis Point Cloud Source와 Target Wall Filter를 확인합니다.",
                    u"3. Tolerance, Top N Callouts와 Output Options를 설정합니다.",
                    u"4. Run 후 QC Plan / 3D View, Revision Cloud ID와 Report 결과를 검토합니다."
                ]
            ),
            (
                u"Analysis Scope / 검토 범위",
                [
                    u"Active Plan Level은 Source Plan View 기준 범위를 사용합니다.",
                    u"Selected Walls는 현재 선택 또는 Revit 다중 선택으로 지정한 Wall만 검토합니다.",
                    u"Analysis Point Cloud Source에서 선택한 Point Cloud가 Wall Deviation Sampling 기준입니다."
                ]
            ),
            (
                u"Target Wall Filter",
                [
                    u"Interior / Exterior는 도면상 위치가 아니라 Wall Type Function 기준입니다.",
                    u"New Construction은 Phase Created 기준입니다.",
                    u"SCAN_QC_TARGET은 Walls에 설치되는 Yes/No 인스턴스 Shared Parameter입니다.",
                    u"여러 필터를 선택하면 모든 조건을 만족하는 Wall만 남는 AND 조건으로 적용됩니다."
                ]
            ),
            (
                u"SCAN_QC_TARGET Workflow",
                [
                    u"파라미터가 없으면 설치 여부를 확인한 뒤 현재 프로젝트 Walls에 자동 바인딩합니다.",
                    u"Pick & Mark: Revit 화면에서 선택한 Wall을 Yes로 지정합니다.",
                    u"Pick & Clear: 선택한 Wall의 대상 값을 No로 해제합니다.",
                    u"Show Targets: 현재 Source Plan View 범위의 대상 Wall을 선택 상태로 표시합니다."
                ]
            ),
            (
                u"Tolerance / Top N Callouts",
                [
                    u"Default Tolerances는 mm 단위이며 이번 실행의 Review / Critical 판정에 사용됩니다.",
                    u"Top N Callouts는 Slider 또는 직접 숫자 입력으로 1~20 범위에서 설정합니다.",
                    u"도면과 Report에는 중복 제거 후 우선순위가 높은 Top N Revision Cloud ID가 표시됩니다."
                ]
            ),
            (
                u"Output / 결과물",
                [
                    u"QC Plan View와 QC 3D View를 생성할 수 있습니다.",
                    u"Review / Critical 위치는 Revision Cloud와 중앙 알파벳 ID로 표시됩니다.",
                    u"A3 / A2 전용 Report Sheet와 PDF Report를 생성할 수 있습니다.",
                    u"CSV Export는 Planned 상태이며 현재 UI에서 비활성입니다."
                ]
            ),
            (
                u"Caution / 모델 안전성",
                [
                    u"원본 Source Plan View와 Point Cloud 그래픽은 수정하지 않습니다.",
                    u"생성 요소는 SCAN_QC_* 작업 View, Revision Cloud와 Report Sheet에 한정됩니다.",
                    u"Point Cloud 데이터가 부족하면 No Point Data 또는 Preview 설정에 따라 결과가 표시됩니다."
                ]
            )
        ]
    },
    {
        "nav": u"QC Settings",
        "title": u"QC Settings",
        "subtitle": u"Rule Set and Report Environment",
        "overview": (
            u"DOC QC 보고서 실행 환경과 프로젝트별 QC Rule Set을 확인하고 관리합니다."
        ),
        "cards": [
            (
                u"Python / Excel Environment",
                [
                    u"Python 경로와 Python / Excel Library / Excel Report 상태를 확인합니다.",
                    u"Test는 현재 외부 실행 환경을 점검하고 Clear는 저장된 경로 설정을 해제합니다."
                ]
            ),
            (
                u"Rule Set",
                [
                    u"프로젝트에 적용할 Rule Set을 선택합니다.",
                    u"Copy로 새 JSON preset을 만들고 Open Rule Folder에서 파일 위치를 엽니다.",
                    u"외부에서 수정한 Rule 파일은 Reload로 다시 읽습니다."
                ]
            ),
            (
                u"Rule Count",
                [
                    u"Sheet / View / Parameter 규칙과 Required Parameter 개수를 카드에서 확인합니다."
                ]
            ),
            (
                u"Details / Open Log",
                [
                    u"Details에서 Python과 Excel 환경의 상세 상태를 확인합니다.",
                    u"Open Log에서 XLSX helper 실행 및 오류 로그를 확인합니다."
                ]
            )
        ]
    },
    {
        "nav": u"Report",
        "title": u"Report",
        "subtitle": u"Open the Latest QC Result",
        "overview": (
            u"가장 최근에 정상 생성된 DOC QC, QC Lite 또는 Scan QC 보고서를 "
            u"기본 연결 프로그램으로 엽니다."
        ),
        "cards": [
            (
                u"Supported Results",
                [
                    u"DOC QC: 상세 XLSX와 기존 CSV 결과",
                    u"QC Lite: Compact Summary HTML과 선택형 PDF",
                    u"Scan QC: A3/A2 전용 PDF Report"
                ]
            ),
            (
                u"저장 경로",
                [
                    u"DOC QC와 QC Lite는 Setup에서 지정한 Report Folder를 사용합니다.",
                    u"Scan QC PDF는 실행 시 선택한 저장 경로를 사용합니다."
                ]
            ),
            (
                u"Report가 없을 때",
                [
                    u"유효한 최근 보고서 경로가 없으면 파일을 열지 않고 안내합니다.",
                    u"저장 선택을 취소한 실행은 최근 보고서 파일과 설정을 변경하지 않습니다."
                ]
            )
        ]
    },
    {
        "nav": u"Help",
        "title": u"Help",
        "subtitle": u"Toolkit Usage Guide",
        "overview": (
            u"Toolkit의 기능별 사용 방법, 모델 안전 기준과 문제 확인 순서를 안내합니다."
        ),
        "cards": [
            (
                u"Navigation",
                [
                    u"왼쪽 메뉴에서 DOC QC → QC Lite → Scan QC → QC Settings → Report 순서로 기능을 확인합니다.",
                    u"Getting Started에는 권장 실행 순서와 모델 변경 범위가 정리되어 있습니다."
                ]
            ),
            (
                u"실행 전 확인",
                [
                    u"검사 범위, 출력 형식, 저장 경로와 모델 변경 여부를 실행 전에 확인합니다.",
                    u"문제가 발생하면 Troubleshooting에서 증상별 원인과 조치 순서를 확인합니다."
                ]
            )
        ]
    },
    {
        "nav": u"Troubleshooting",
        "title": u"Troubleshooting",
        "subtitle": u"Symptoms, Causes and Actions",
        "overview": (
            u"실행 환경, 입력 범위와 저장 조건을 순서대로 확인하면 대부분의 문제를 빠르게 분리할 수 있습니다."
        ),
        "cards": [
            (
                u"XLSX가 생성되지 않음",
                [
                    u"증상 | DOC QC 실행 후 XLSX 파일이 생성되지 않습니다.",
                    u"가능한 원인 | Python 경로 또는 Excel Library 상태가 준비되지 않았습니다.",
                    u"조치 방법 | QC Settings에서 Python / Excel Library / Excel Report가 Ready인지 확인합니다."
                ]
            ),
            (
                u"Scan QC 결과가 없음",
                [
                    u"증상 | 처리된 Wall 또는 Revision Cloud 결과가 없습니다.",
                    u"가능한 원인 | Source Plan View, Point Cloud 또는 Target Filter가 대상과 맞지 않습니다.",
                    u"조치 방법 | Analysis Scope, Analysis Point Cloud Source, Wall Type Function, Phase와 SCAN_QC_TARGET을 확인합니다."
                ]
            ),
            (
                u"PDF가 생성되지 않음",
                [
                    u"증상 | 분석은 완료되지만 PDF 파일이 생성되지 않습니다.",
                    u"가능한 원인 | 저장 경로 권한, QC Plan View 또는 Report Sheet 생성 조건이 충족되지 않았습니다.",
                    u"조치 방법 | 저장 경로와 Output Summary의 Report Sheet / PDF 경고를 확인합니다."
                ]
            ),
            (
                u"UI가 잘림",
                [
                    u"증상 | 높은 Windows 배율 또는 작은 화면에서 카드 하단이 보이지 않습니다.",
                    u"가능한 원인 | WorkingArea보다 Help 콘텐츠의 표시 높이가 큽니다.",
                    u"조치 방법 | 창을 확대하거나 Detail 영역의 fallback Scroll을 사용한 뒤 pyRevit Reload 후 다시 확인합니다."
                ]
            )
        ]
    }
]


def _write_navigation_profile(page_name, metrics):
    if not is_ui_perf_debug_enabled():
        return
    try:
        log_folder = os.path.dirname(HELP_PROFILE_LOG_PATH)
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        ordered_keys = (
            "navigation_click_ms",
            "page_definition_load_ms",
            "page_control_construction_ms",
            "card_creation_ms",
            "text_assignment_ms",
            "layout_pass_ms",
            "panel_switch_ms",
            "total_ms",
            "cache_hit"
        )
        fields = []
        for key in ordered_keys:
            fields.append(u"{0}={1}".format(key, metrics.get(key, 0)))
        with io.open(HELP_PROFILE_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(
                u"[{0}] page={1} {2}\n".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    page_name,
                    u" ".join(fields)
                )
            )
    except Exception:
        pass


def safe_text(value):
    try:
        return unicode(value)
    except Exception:
        try:
            return str(value)
        except Exception:
            return u"알 수 없는 오류"


class HelpVerticalScrollBar(Control):
    def __init__(self):
        Control.__init__(self)
        self.Width = SCROLLBAR_WIDTH
        self.MinimumSize = Size(SCROLLBAR_WIDTH, 0)
        self.MaximumSize = Size(SCROLLBAR_WIDTH, 0)
        self.TabStop = False
        self.DoubleBuffered = True
        self.BackColor = SCROLL_TRACK_COLOR
        self._value_changed = None
        self._maximum = 0
        self._viewport_height = 0
        self._content_height = 0
        self._value = 0
        self._thumb_rect = Rectangle.Empty
        self._dragging = False
        self._drag_offset = 0
        self._thumb_hover = False

    @property
    def Value(self):
        return self._value

    def configure(self, content_height, viewport_height):
        content_height = max(0, int(content_height))
        viewport_height = max(0, int(viewport_height))
        maximum = max(0, content_height - viewport_height)
        changed = (
            content_height != self._content_height
            or viewport_height != self._viewport_height
            or maximum != self._maximum
        )
        self._content_height = content_height
        self._viewport_height = viewport_height
        self._maximum = maximum
        self.Visible = maximum > 0
        if maximum <= 0:
            self.set_value(0)
        elif self._value > maximum:
            self.set_value(maximum)
        if changed:
            self._update_thumb_rect()
            self.Invalidate()

    def set_value(self, value):
        value = max(0, min(int(value), self._maximum))
        if value == self._value:
            return False
        self._value = value
        self._update_thumb_rect()
        self.Invalidate()
        if self._value_changed is not None:
            self._value_changed(self._value)
        return True

    def scroll_by(self, delta):
        return self.set_value(self._value + int(delta))

    def scroll_page(self, direction):
        distance = max(40, self._viewport_height - 40)
        return self.scroll_by(distance * int(direction))

    def scroll_home(self):
        return self.set_value(0)

    def scroll_end(self):
        return self.set_value(self._maximum)

    def _update_thumb_rect(self):
        track_height = max(0, self.ClientSize.Height)
        thumb_width = max(2, self.ClientSize.Width - (SCROLL_TRACK_INSET * 2))
        if track_height <= 0 or self._maximum <= 0 or self._content_height <= 0:
            self._thumb_rect = Rectangle(
                SCROLL_TRACK_INSET,
                0,
                thumb_width,
                0
            )
            return
        thumb_height = max(
            SCROLL_THUMB_MIN_HEIGHT,
            int(
                float(track_height) * float(self._viewport_height)
                / float(self._content_height)
            )
        )
        thumb_height = min(track_height, thumb_height)
        travel = max(0, track_height - thumb_height)
        thumb_top = 0
        if travel > 0 and self._maximum > 0:
            thumb_top = int(
                float(travel) * float(self._value) / float(self._maximum)
            )
        self._thumb_rect = Rectangle(
            SCROLL_TRACK_INSET,
            thumb_top,
            thumb_width,
            thumb_height
        )

    def OnResize(self, event_args):
        Control.OnResize(self, event_args)
        self._update_thumb_rect()
        self.Invalidate()

    def OnPaint(self, event_args):
        Control.OnPaint(self, event_args)
        event_args.Graphics.Clear(SCROLL_TRACK_COLOR)
        if self._thumb_rect.Height <= 0:
            return
        color = (
            SCROLL_THUMB_HOVER_COLOR
            if self._thumb_hover or self._dragging
            else SCROLL_THUMB_COLOR
        )
        brush = SolidBrush(color)
        try:
            event_args.Graphics.FillRectangle(brush, self._thumb_rect)
        finally:
            brush.Dispose()

    def OnMouseDown(self, event_args):
        Control.OnMouseDown(self, event_args)
        if event_args.Button != MouseButtons.Left or self._maximum <= 0:
            return
        if self._thumb_rect.Contains(event_args.Location):
            self._dragging = True
            self._drag_offset = event_args.Y - self._thumb_rect.Top
            self.Capture = True
            self.Invalidate()
            return
        if event_args.Y < self._thumb_rect.Top:
            self.scroll_page(-1)
        else:
            self.scroll_page(1)

    def OnMouseMove(self, event_args):
        Control.OnMouseMove(self, event_args)
        hover = self._thumb_rect.Contains(event_args.Location)
        if hover != self._thumb_hover:
            self._thumb_hover = hover
            self.Invalidate()
        if not self._dragging or self._maximum <= 0:
            return
        travel = max(0, self.ClientSize.Height - self._thumb_rect.Height)
        if travel <= 0:
            return
        thumb_top = max(
            0,
            min(event_args.Y - self._drag_offset, travel)
        )
        value = int(float(thumb_top) * float(self._maximum) / float(travel))
        self.set_value(value)

    def OnMouseUp(self, event_args):
        Control.OnMouseUp(self, event_args)
        if event_args.Button == MouseButtons.Left and self._dragging:
            self._dragging = False
            self.Capture = False
            self.Invalidate()

    def OnMouseLeave(self, event_args):
        Control.OnMouseLeave(self, event_args)
        if self._thumb_hover and not self._dragging:
            self._thumb_hover = False
            self.Invalidate()


class HelpForm(Form):
    def __init__(self):
        Form.__init__(self)
        self.SuspendLayout()
        self.Text = "Revit QC Toolkit Help"
        self.AutoSize = False
        self.ClientSize = Size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.MinimumSize = Size(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.KeyPreview = True
        self.AutoScaleMode = AutoScaleMode.Dpi
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(10.0)

        self.title_font = get_preferred_font(18.0, FontStyle.Bold)
        self.subtitle_font = get_preferred_font(10.0, FontStyle.Regular)
        self.nav_font_regular = get_preferred_font(10.0, FontStyle.Regular)
        self.nav_font_bold = get_preferred_font(10.0, FontStyle.Bold)
        self.page_title_font = get_preferred_font(16.0, FontStyle.Bold)
        self.page_subtitle_font = get_preferred_font(9.5, FontStyle.Regular)
        self.card_heading_font = get_preferred_font(10.5, FontStyle.Bold)
        self.card_body_font = get_preferred_font(9.5, FontStyle.Regular)
        self.nav_accent_brush = SolidBrush(ORANGE_HOVER_COLOR)

        self.nav_items = []
        self._nav_hover_bindings = []
        self._navigation_hovered = set()
        self._resource_links = []
        self.page_cache = {}
        self.page_metadata = {}
        self.current_page = None
        self.selected_index = -1
        self._last_page_width = -1
        self._perf_enabled = is_ui_perf_debug_enabled()
        self._cleanup_done = False

        self._build_layout()
        self._show_section(0)
        self.Shown += self._on_shown
        self.KeyDown += self._form_key_down
        self.ResumeLayout(True)

    def _build_layout(self):
        root = TableLayoutPanel()
        root.Dock = DockStyle.Fill
        root.Padding = Padding(
            WINDOW_PADDING,
            WINDOW_PADDING,
            WINDOW_PADDING,
            0
        )
        root.ColumnCount = 1
        root.RowCount = 3
        root.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))
        self.Controls.Add(root)

        header = self._build_header()
        root.Controls.Add(header, 0, 0)

        body = TableLayoutPanel()
        body.Dock = DockStyle.Fill
        body.Margin = Padding(0, HEADER_BODY_GAP, 0, 0)
        body.Padding = Padding(0)
        body.ColumnCount = 2
        body.RowCount = 1
        body.ColumnStyles.Add(
            ColumnStyle(
                SizeType.Absolute,
                float(NAVIGATION_WIDTH + NAVIGATION_DETAIL_GAP)
            )
        )
        body.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        body.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        root.Controls.Add(body, 0, 1)

        navigation = self._build_navigation()
        body.Controls.Add(navigation, 0, 0)

        detail_region = TableLayoutPanel()
        detail_region.Dock = DockStyle.Fill
        detail_region.Margin = Padding(0)
        detail_region.Padding = Padding(0)
        detail_region.BackColor = HELP_BACKGROUND_COLOR
        detail_region.ColumnCount = 2
        detail_region.RowCount = 1
        detail_region.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        detail_region.ColumnStyles.Add(
            ColumnStyle(SizeType.Absolute, float(SCROLLBAR_WIDTH))
        )
        detail_region.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        body.Controls.Add(detail_region, 1, 0)

        self.detail_host = Panel()
        self.detail_host.Dock = DockStyle.Fill
        self.detail_host.Margin = Padding(0)
        self.detail_host.Padding = Padding(0)
        self.detail_host.AutoScroll = False
        self.detail_host.TabStop = True
        self.detail_host.BackColor = HELP_BACKGROUND_COLOR
        self.detail_host.BorderStyle = BorderStyle.FixedSingle
        self.detail_host.SizeChanged += self._resize_pages
        self.detail_host.MouseWheel += self._detail_mouse_wheel
        self.detail_host.MouseEnter += self._detail_mouse_enter
        self.detail_host.KeyDown += self._detail_key_down
        detail_region.Controls.Add(self.detail_host, 0, 0)

        self.detail_scrollbar = HelpVerticalScrollBar()
        self.detail_scrollbar._value_changed = (
            self._detail_scroll_value_changed
        )
        self.detail_scrollbar.Dock = DockStyle.Fill
        self.detail_scrollbar.Margin = Padding(0)
        self.detail_scrollbar.Visible = False
        detail_region.Controls.Add(self.detail_scrollbar, 1, 0)

        # Preserve the original Detail viewport height without restoring the
        # removed Close button or its event handler.
        self.footer_spacer = Panel()
        self.footer_spacer.Dock = DockStyle.Fill
        self.footer_spacer.Margin = Padding(0)
        self.footer_spacer.Padding = Padding(0)
        self.footer_spacer.BackColor = Color.White
        root.Controls.Add(self.footer_spacer, 0, 2)


    def _build_header(self):
        header = TableLayoutPanel()
        header.Dock = DockStyle.Top
        header.AutoSize = True
        header.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header.Margin = Padding(0)
        header.Padding = Padding(0)
        header.ColumnCount = 1
        header.RowCount = 2
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))

        title = Label()
        title.Text = u"Revit QC Toolkit Help"
        title.Dock = DockStyle.Fill
        title.AutoSize = True
        title.Font = self.title_font
        title.ForeColor = NAVY_COLOR
        title.Margin = Padding(0)
        header.Controls.Add(title, 0, 0)

        subtitle = Label()
        subtitle.Text = u"기능별 사용 방법과 실무 기준을 확인하세요."
        subtitle.Dock = DockStyle.Fill
        subtitle.AutoSize = True
        subtitle.Font = self.subtitle_font
        subtitle.ForeColor = SUBTITLE_COLOR
        subtitle.Margin = Padding(0, 5, 0, 0)
        header.Controls.Add(subtitle, 0, 1)
        return header

    def _build_navigation(self):
        navigation = FlowLayoutPanel()
        navigation.Dock = DockStyle.Fill
        navigation.FlowDirection = FlowDirection.TopDown
        navigation.WrapContents = False
        navigation.AutoScroll = False
        navigation.Margin = Padding(0, 0, NAVIGATION_DETAIL_GAP, 0)
        navigation.Padding = Padding(0)
        navigation.BackColor = Color.White

        for index, section in enumerate(HELP_SECTIONS):
            item = self._create_navigation_item(index, section["nav"])
            navigation.Controls.Add(item["container"])
            self.nav_items.append(item)
        return navigation

    def _create_navigation_item(self, index, text):
        container = Panel()
        container.Width = NAVIGATION_WIDTH
        container.Height = NAVIGATION_BUTTON_HEIGHT
        container.AutoSize = False
        container.Margin = Padding(0, 0, 0, NAVIGATION_BUTTON_GAP)
        container.Padding = Padding(0)
        container.BackColor = Color.White

        button = Button()
        button.Text = text
        button.AutoSize = False
        button.UseMnemonic = False
        button.Dock = DockStyle.Fill
        button.Margin = Padding(0)
        button.Padding = Padding(20, 0, 8, 0)
        button.Tag = index
        button.FlatStyle = FlatStyle.Flat
        button.FlatAppearance.BorderSize = 1
        button.FlatAppearance.BorderColor = BORDER_COLOR
        button.FlatAppearance.MouseOverBackColor = Color.White
        button.FlatAppearance.MouseDownBackColor = WARNING_BACKGROUND_COLOR
        button.UseVisualStyleBackColor = False
        button.BackColor = Color.White
        button.ForeColor = NAVY_COLOR
        button.Font = self.nav_font_regular
        button.TextAlign = ContentAlignment.MiddleLeft
        button.Click += self._navigation_click
        button.Paint += self._navigation_button_paint
        self._nav_hover_bindings.append(
            attach_border_hover(
                button,
                self._navigation_hover_restore,
                self._navigation_hover_enter
            )
        )
        container.Controls.Add(button)
        return {
            "container": container,
            "button": button,
            "index": index
        }

    def _navigation_click(self, sender, event_args):
        index = int(sender.Tag)
        total_watch = Stopwatch.StartNew() if self._perf_enabled else None
        metrics = {
            "navigation_click_ms": 0.0,
            "page_definition_load_ms": 0.0,
            "page_control_construction_ms": 0.0,
            "card_creation_ms": 0.0,
            "text_assignment_ms": 0.0,
            "layout_pass_ms": 0.0,
            "panel_switch_ms": 0.0,
            "total_ms": 0.0,
            "cache_hit": False
        }
        self._show_section(index, metrics)
        if total_watch is not None:
            total_watch.Stop()
            elapsed = round(total_watch.Elapsed.TotalMilliseconds, 2)
            metrics["navigation_click_ms"] = elapsed
            metrics["total_ms"] = elapsed
            _write_navigation_profile(
                HELP_SECTIONS[index]["nav"],
                metrics
            )

    def _navigation_hover_enter(self, sender):
        index = int(sender.Tag)
        self._navigation_hovered.add(index)
        selected = index == self.selected_index
        sender.BackColor = (
            SELECTED_NAVIGATION_COLOR if selected else Color.White
        )
        sender.ForeColor = NAVY_COLOR
        sender.FlatAppearance.BorderColor = (
            ORANGE_COLOR if selected else ORANGE_HOVER_COLOR
        )
        sender.FlatAppearance.BorderSize = 1

    def _navigation_hover_restore(self, sender):
        index = int(sender.Tag)
        self._navigation_hovered.discard(index)
        selected = index == self.selected_index
        background = SELECTED_NAVIGATION_COLOR if selected else Color.White
        border = ORANGE_HOVER_COLOR if selected else BORDER_COLOR
        sender.BackColor = background
        sender.ForeColor = NAVY_COLOR
        sender.FlatAppearance.BorderColor = border
        sender.FlatAppearance.BorderSize = 1
        sender.FlatAppearance.MouseOverBackColor = background
        sender.Font = self.nav_font_bold if selected else self.nav_font_regular

    def _navigation_button_paint(self, sender, event_args):
        index = int(sender.Tag)
        if index != self.selected_index and index not in self._navigation_hovered:
            return
        accent_height = max(0, sender.ClientSize.Height - 2)
        if accent_height <= 0:
            return
        event_args.Graphics.FillRectangle(
            self.nav_accent_brush,
            1,
            1,
            4,
            accent_height
        )

    def _show_section(self, index, metrics=None):
        if index < 0 or index >= len(HELP_SECTIONS):
            return metrics
        if index == self.selected_index and self.current_page is not None:
            if metrics is not None:
                metrics["cache_hit"] = True
            return metrics

        self.selected_index = index
        self._update_navigation_state(index)

        page = self.page_cache.get(index)
        created = page is None
        if metrics is not None:
            metrics["cache_hit"] = not created

        if created:
            self.SuspendLayout()
            self.detail_host.SuspendLayout()
            page = self._create_page(index, metrics)
            self.page_cache[index] = page

        switch_watch = Stopwatch.StartNew() if self._perf_enabled else None
        if self.current_page is not None:
            self.detail_host.Controls.Remove(self.current_page)
        self.detail_host.Controls.Add(page)
        page.Location = Point(0, 0)
        page.Top = 0
        self.detail_scrollbar.set_value(0)
        self.current_page = page
        self._resize_page(index)
        if switch_watch is not None:
            switch_watch.Stop()
            if metrics is not None:
                metrics["panel_switch_ms"] = round(
                    switch_watch.Elapsed.TotalMilliseconds,
                    2
                )

        layout_watch = Stopwatch.StartNew() if self._perf_enabled else None
        if created:
            self.detail_host.ResumeLayout(False)
            self.ResumeLayout(False)
        self.detail_host.PerformLayout()
        if layout_watch is not None:
            layout_watch.Stop()
            if metrics is not None:
                metrics["layout_pass_ms"] = round(
                    layout_watch.Elapsed.TotalMilliseconds,
                    2
                )
        self._update_scrollbar()
        return metrics

    def _update_navigation_state(self, selected_index):
        for item in self.nav_items:
            selected = item["index"] == selected_index
            background = SELECTED_NAVIGATION_COLOR if selected else Color.White
            item["container"].BackColor = Color.White
            item["button"].BackColor = background
            item["button"].ForeColor = NAVY_COLOR
            item["button"].FlatAppearance.BorderSize = 1
            item["button"].FlatAppearance.BorderColor = (
                ORANGE_HOVER_COLOR if selected else BORDER_COLOR
            )
            item["button"].FlatAppearance.MouseOverBackColor = background
            item["button"].Font = (
                self.nav_font_bold if selected else self.nav_font_regular
            )
            item["button"].Invalidate()

    def _create_page(self, index, metrics=None):
        definition_watch = Stopwatch.StartNew() if self._perf_enabled else None
        section = HELP_SECTIONS[index]
        if definition_watch is not None:
            definition_watch.Stop()
            if metrics is not None:
                metrics["page_definition_load_ms"] = round(
                    definition_watch.Elapsed.TotalMilliseconds,
                    2
                )

        construction_watch = Stopwatch.StartNew() if self._perf_enabled else None
        page = FlowLayoutPanel()
        page.SuspendLayout()
        page.Width = self._page_width()
        page.Dock = getattr(DockStyle, "None")
        page.AutoSize = True
        page.AutoSizeMode = AutoSizeMode.GrowAndShrink
        page.FlowDirection = FlowDirection.TopDown
        page.WrapContents = False
        page.AutoScroll = False
        page.Margin = Padding(0)
        page.Padding = Padding(
            DETAIL_PADDING,
            DETAIL_PADDING - 6,
            DETAIL_PADDING,
            DETAIL_BOTTOM_PADDING
        )
        page.BackColor = HELP_BACKGROUND_COLOR

        metadata = {
            "page": page,
            "cards": [],
            "page_width": self._page_width()
        }

        page_header = self._make_page_header(
            section["title"],
            section["subtitle"]
        )
        page.Controls.Add(page_header)
        metadata["page_header"] = page_header

        overview = self._make_card(
            u"Overview",
            [section["overview"]],
            True,
            metadata,
            metrics
        )
        page.Controls.Add(overview)

        for card_title, card_lines in section["cards"]:
            card = self._make_card(
                card_title,
                card_lines,
                False,
                metadata,
                metrics
            )
            page.Controls.Add(card)

        page.ResumeLayout(False)
        self.page_metadata[index] = metadata
        if construction_watch is not None:
            construction_watch.Stop()
            if metrics is not None:
                metrics["page_control_construction_ms"] = round(
                    construction_watch.Elapsed.TotalMilliseconds,
                    2
                )
        return page

    def _make_page_header(self, title_text, subtitle_text):
        header = TableLayoutPanel()
        header.Width = self._detail_width()
        header.AutoSize = True
        header.AutoSizeMode = AutoSizeMode.GrowAndShrink
        header.Margin = Padding(0, 0, 0, 14)
        header.Padding = Padding(0)
        header.ColumnCount = 1
        header.RowCount = 3
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header.RowStyles.Add(RowStyle(SizeType.AutoSize))
        header.RowStyles.Add(RowStyle(SizeType.Absolute, 1.0))

        title = Label()
        title.Text = title_text
        title.Dock = DockStyle.Fill
        title.AutoSize = True
        title.Font = self.page_title_font
        title.ForeColor = NAVY_COLOR
        title.Margin = Padding(0)
        header.Controls.Add(title, 0, 0)

        subtitle = Label()
        subtitle.Text = subtitle_text
        subtitle.Dock = DockStyle.Fill
        subtitle.AutoSize = True
        subtitle.Font = self.page_subtitle_font
        subtitle.ForeColor = SUBTITLE_COLOR
        subtitle.Margin = Padding(0, 5, 0, 11)
        header.Controls.Add(subtitle, 0, 1)

        divider = Panel()
        divider.Dock = DockStyle.Fill
        divider.Margin = Padding(0)
        divider.BackColor = BORDER_COLOR
        header.Controls.Add(divider, 0, 2)
        return header

    def _make_card(
        self,
        title_text,
        body_lines,
        accent,
        metadata,
        metrics=None
    ):
        card_watch = Stopwatch.StartNew() if self._perf_enabled else None
        width = self._detail_width()
        outer = Panel()
        outer.Width = width
        outer.AutoSize = False
        outer.Margin = Padding(0, 0, 0, CARD_GAP)
        outer.BackColor = BORDER_COLOR

        content = Panel()
        content.AutoSize = False
        content.Margin = Padding(0)
        content.BackColor = CARD_FILL_COLOR
        outer.Controls.Add(content)

        heading = Label()
        heading.Text = title_text
        heading.AutoSize = False
        heading.Font = self.card_heading_font
        heading.ForeColor = OVERVIEW_ACCENT_COLOR if accent else NAVY_COLOR
        heading.TextAlign = ContentAlignment.MiddleLeft
        content.Controls.Add(heading)

        paragraphs = []
        for line in body_lines:
            is_resource_link = isinstance(line, dict) and bool(line.get("url"))
            body = LinkLabel() if is_resource_link else Label()
            text_watch = Stopwatch.StartNew() if self._perf_enabled else None
            body.Text = line.get("text", line.get("url")) if is_resource_link else line
            if text_watch is not None:
                text_watch.Stop()
                if metrics is not None:
                    metrics["text_assignment_ms"] += round(
                        text_watch.Elapsed.TotalMilliseconds,
                        2
                    )
            body.AutoSize = False
            body.Font = self.card_body_font
            body.ForeColor = BODY_TEXT_COLOR
            body.UseCompatibleTextRendering = False
            if is_resource_link:
                body.Tag = line.get("url")
                body.LinkColor = ORANGE_COLOR
                body.ActiveLinkColor = ORANGE_HOVER_COLOR
                body.VisitedLinkColor = ORANGE_COLOR
                body.LinkClicked += self._resource_link_clicked
                self._resource_links.append(body)
            content.Controls.Add(body)
            paragraphs.append(body)

        card_info = {
            "outer": outer,
            "content": content,
            "heading": heading,
            "paragraphs": paragraphs,
            "paragraph_gap": (
                7
                if u"Workflow" in title_text or title_text == u"Quick Start"
                else 10
            ),
            "width": -1
        }
        metadata["cards"].append(card_info)
        self._layout_card(card_info, width, True)
        if card_watch is not None:
            card_watch.Stop()
            if metrics is not None:
                metrics["card_creation_ms"] += round(
                    card_watch.Elapsed.TotalMilliseconds,
                    2
                )
        return outer

    def _resource_link_clicked(self, sender, event_args):
        url = safe_text(getattr(sender, "Tag", u"")).strip()
        if not url:
            return
        try:
            start_info = ProcessStartInfo(url)
            start_info.UseShellExecute = True
            Process.Start(start_info)
        except Exception:
            MessageBox.Show(
                self,
                u"웹 브라우저에서 링크를 열지 못했습니다.\n{0}".format(url),
                u"GitHub Link",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

    def _layout_card(self, card_info, width, force=False):
        if not force and card_info.get("width") == width:
            return
        outer = card_info["outer"]
        content = card_info["content"]
        heading = card_info["heading"]
        paragraphs = card_info["paragraphs"]

        outer.Width = width
        content_width = max(0, width - 2)
        text_width = max(
            420,
            content_width - (CARD_PADDING_HORIZONTAL * 2)
        )
        heading_height = 24
        heading_y = CARD_PADDING_VERTICAL
        paragraph_y = heading_y + heading_height + 10

        heading.Location = Point(CARD_PADDING_HORIZONTAL, heading_y)
        heading.Size = Size(text_width, heading_height)
        measure_flags = TextFormatFlags.WordBreak | TextFormatFlags.NoPadding
        paragraph_gap = card_info["paragraph_gap"]
        for paragraph_index, paragraph in enumerate(paragraphs):
            measured = TextRenderer.MeasureText(
                paragraph.Text,
                paragraph.Font,
                Size(text_width, 0),
                measure_flags
            )
            paragraph_height = max(20, measured.Height)
            paragraph.Location = Point(CARD_PADDING_HORIZONTAL, paragraph_y)
            paragraph.Size = Size(text_width, paragraph_height)
            paragraph_y += paragraph_height
            if paragraph_index < len(paragraphs) - 1:
                paragraph_y += paragraph_gap

        content_height = paragraph_y + CARD_PADDING_VERTICAL
        content.Location = Point(1, 1)
        content.Size = Size(content_width, content_height)
        outer.Height = content_height + 2
        card_info["width"] = width

    def _page_width(self):
        return max(
            620,
            self.detail_host.ClientSize.Width - 2
        )

    def _detail_width(self):
        return max(
            560,
            self._page_width() - (DETAIL_PADDING * 2)
        )

    def _resize_pages(self, sender, event_args):
        if not hasattr(self, "detail_host"):
            return
        page_width = self._page_width()
        if page_width == self._last_page_width:
            self._update_scrollbar()
            return
        self._last_page_width = page_width
        for index in self.page_metadata:
            self._resize_page(index)
        self._update_scrollbar()

    def _resize_page(self, index, force=False):
        metadata = self.page_metadata.get(index)
        if metadata is None:
            return
        page_width = self._page_width()
        if not force and metadata.get("page_width") == page_width:
            return
        width = self._detail_width()
        metadata["page"].Width = page_width
        metadata["page_header"].Width = width
        for card_info in metadata["cards"]:
            self._layout_card(card_info, width, force)
        metadata["page_width"] = page_width

    def _on_shown(self, sender, event_args):
        self._resize_pages(None, None)
        self._update_scrollbar()

    def _update_scrollbar(self):
        if not hasattr(self, "detail_scrollbar"):
            return
        if self.current_page is None:
            self.detail_scrollbar.configure(0, 0)
            return
        content_height = max(
            self.current_page.Height,
            self.current_page.PreferredSize.Height
        )
        self.detail_scrollbar.configure(
            content_height,
            self.detail_host.ClientSize.Height
        )

    def _detail_scroll_value_changed(self, value):
        if self.current_page is None:
            return
        self.current_page.Top = -int(value)

    def _detail_mouse_wheel(self, sender, event_args):
        if event_args.Delta == 0:
            return
        direction = -1 if event_args.Delta > 0 else 1
        self.detail_scrollbar.scroll_by(direction * 72)

    def _detail_mouse_enter(self, sender, event_args):
        try:
            self.detail_host.Focus()
        except Exception:
            pass

    def _detail_key_down(self, sender, event_args):
        handled = True
        if event_args.KeyCode == Keys.Home:
            self.detail_scrollbar.scroll_home()
        elif event_args.KeyCode == Keys.End:
            self.detail_scrollbar.scroll_end()
        elif event_args.KeyCode == Keys.PageUp:
            self.detail_scrollbar.scroll_page(-1)
        elif event_args.KeyCode == Keys.PageDown:
            self.detail_scrollbar.scroll_page(1)
        else:
            handled = False
        if handled:
            event_args.Handled = True

    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        try:
            self.Shown -= self._on_shown
        except Exception:
            pass
        try:
            self.KeyDown -= self._form_key_down
        except Exception:
            pass
        try:
            self.detail_host.SizeChanged -= self._resize_pages
            self.detail_host.MouseWheel -= self._detail_mouse_wheel
            self.detail_host.MouseEnter -= self._detail_mouse_enter
            self.detail_host.KeyDown -= self._detail_key_down
        except Exception:
            pass
        try:
            self.detail_scrollbar._value_changed = None
        except Exception:
            pass
        for item in self.nav_items:
            button = item["button"]
            try:
                button.Click -= self._navigation_click
                button.Paint -= self._navigation_button_paint
            except Exception:
                pass
        for binding in self._nav_hover_bindings:
            detach_border_hover(binding)
        self._nav_hover_bindings = []
        self._navigation_hovered = set()
        for resource_link in self._resource_links:
            try:
                resource_link.LinkClicked -= self._resource_link_clicked
            except Exception:
                pass
        self._resource_links = []
        for page in self.page_cache.values():
            try:
                page.Dispose()
            except Exception:
                pass
        self.page_cache = {}
        self.page_metadata = {}
        for font in (
            self.title_font,
            self.subtitle_font,
            self.nav_font_regular,
            self.nav_font_bold,
            self.page_title_font,
            self.page_subtitle_font,
            self.card_heading_font,
            self.card_body_font
        ):
            try:
                font.Dispose()
            except Exception:
                pass
        try:
            self.nav_accent_brush.Dispose()
        except Exception:
            pass

    def _form_key_down(self, sender, event_args):
        if event_args.KeyCode != Keys.Escape:
            return
        event_args.Handled = True
        event_args.SuppressKeyPress = True
        self.Close()


help_form = None
help_profile = create_ui_close_profile(u"Help")
try:
    help_form = HelpForm()
    help_profile.attach(help_form)
    help_profile.show_dialog()
except Exception as error:
    try:
        log_folder = os.path.join(EXTENSION_DIR, "reports")
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        log_path = os.path.join(log_folder, "help_ui_error.log")
        with io.open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(
                u"[{0}] {1}\n{2}\n".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    safe_text(error),
                    safe_text(traceback.format_exc())
                )
            )
    except Exception:
        pass
finally:
    if help_form is not None:
        help_profile.dispose()
