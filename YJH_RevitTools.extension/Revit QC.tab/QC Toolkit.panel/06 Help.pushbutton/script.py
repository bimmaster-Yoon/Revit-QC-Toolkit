# -*- coding: utf-8 -*-

import os
import sys
import io
from datetime import datetime

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Color, ContentAlignment, FontStyle, Size
from System.Windows.Forms import (
    AutoScaleMode, AutoSizeMode, BorderStyle, Button, ColumnStyle, DockStyle, FlatStyle,
    FlowDirection, FlowLayoutPanel, Form, FormBorderStyle, FormStartPosition,
    Label, Padding, Panel, RowStyle, SizeType, TableLayoutPanel
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir)
)
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from qc_ui_style import (
    BORDER_COLOR, BUTTON_NAVY_COLOR, HELP_BACKGROUND_COLOR, LIGHT_FILL_COLOR,
    MUTED_COLOR, NAVY_COLOR, ORANGE_COLOR, WARNING_BACKGROUND_COLOR,
    BUTTON_GAP, FOOTER_BUTTON_HEIGHT, FOOTER_BUTTON_WIDTH, FOOTER_HEIGHT,
    HEADER_BOTTOM_MARGIN, HEADER_TOP_PADDING, OUTER_MARGIN, SECTION_GAP,
    apply_primary_button_style, configure_content_scroll, get_preferred_font
)
from ui_close_profiler import create_ui_close_profile
from toolkit_version import get_toolkit_version_label


HELP_SECTIONS = [
    (
        u"Getting Started",
        u"Toolkit Overview",
        u"Revit QC Toolkit은 Sheet, View, Parameter 및 Point Cloud 기반 모델 "
        u"정합성을 검토하는 pyRevit 도구입니다.",
        [
            (u"사용 순서", u"1. QC Settings에서 Rule Set과 Excel 환경을 확인합니다.\r\n"
             u"2. 빠른 상태 확인은 QC Lite, 전체 문서 검토는 DOC QC를 실행합니다.\r\n"
             u"3. Point Cloud 검토는 Scan QC에서 Source Plan View와 Point Cloud를 선택합니다.\r\n"
             u"4. 저장 결과는 Report 버튼으로 다시 열 수 있습니다."),
            (u"Model Safety", u"DOC QC와 QC Lite는 read-only입니다. Scan QC는 선택한 "
             u"옵션에 따라 SCAN_QC_* 작업 View, Revision Cloud와 Report Sheet를 생성할 수 있습니다."),
            (u"Toolkit Info", u"Version: {0}\r\nRevit 2026 + pyRevit Extension\r\n"
             u"버전 표시는 공통 toolkit_version 모듈을 기준으로 합니다.".format(
                 get_toolkit_version_label()
             ))
        ]
    ),
    (
        u"DOC QC",
        u"DOC QC",
        u"Sheet / View / Parameter 전체 도면 패키지를 현재 Rule Set으로 검토합니다.",
        [
            (u"Review Scope", u"Current Project를 기본으로 검토합니다. Current Sheet Set, Selected Sheets, "
             u"Active View Only 항목은 UI에서 실행 가능 상태를 확인한 뒤 사용합니다."),
            (u"QC Categories", u"Sheet QC / View QC / Parameter QC를 선택합니다. Naming QC와 "
             u"View Placement QC는 기존 Sheet·View 검사에 포함됩니다."),
            (u"Rule / Report", u"Rule Set, Report Folder, Report Style을 확인합니다. XLSX Report와 "
             u"pyRevit Output Summary 출력은 기존 보고서 엔진을 사용합니다."),
            (u"실행 후", u"Open Report After Run을 선택하면 정상 생성된 보고서를 실행 후 엽니다. "
             u"저장 위치 선택을 취소하면 파일을 변경하지 않고 조용히 종료합니다.")
        ]
    ),
    (
        u"QC Lite",
        u"QC Lite",
        u"Sheet와 View의 주요 Issue를 빠르게 확인하는 프로젝트 상태 Dashboard입니다.",
        [
            (u"Dashboard", u"Sheet / View Issue Count, Severity Count와 Top Issues를 카드형으로 표시합니다."),
            (u"다음 작업", u"Parameter까지 검토하려면 DOC QC를 실행하고, 저장된 결과는 Report로 엽니다."),
            (u"주의사항", u"QC Lite의 Parameter QC와 Scan QC 카드는 상태 안내용이며 N/A로 표시됩니다.")
        ]
    ),
    (
        u"Scan QC",
        u"Scan QC",
        u"Point Cloud를 기준으로 Wall Deviation을 샘플링하고 QC View, Revision Cloud ID와 PDF Report를 생성합니다.",
        [
            (u"검토 기준", u"Analysis Scope, Source Plan View, Analysis Point Cloud Source를 선택합니다. "
             u"선택한 Point Cloud가 Wall Deviation Sampling 기준입니다."),
            (u"Target Wall Filter", u"Interior / Exterior는 도면상 위치가 아니라 Wall Type Function 기준입니다.\r\n"
             u"New Construction은 Phase Created 기준입니다.\r\nSCAN_QC_TARGET은 사용자 Parameter 기준입니다.\r\n"
             u"여러 필터는 AND 조건으로 적용됩니다."),
            (u"Target 지정", u"SCAN_QC_TARGET Shared Parameter를 Walls에 설치할 수 있습니다. Pick & Mark / "
             u"Pick & Clear로 값을 지정하고 Show Targets로 현재 대상을 선택 표시합니다."),
            (u"Tolerance / Top N", u"Default Tolerances는 mm 기준입니다. Top N Callouts는 오렌지 Slider 또는 "
             u"직접 숫자 입력으로 1~20 범위에서 설정합니다."),
            (u"View / Report", u"QC Plan / 3D View, Revision Cloud ID, A3/A2 PDF Report를 생성할 수 있습니다. "
             u"CSV Export는 Planned 상태이며 비활성입니다."),
            (u"Model Safety", u"원본 Source Plan View와 Point Cloud 그래픽은 수정하지 않습니다. "
             u"생성 요소는 SCAN_QC_* 작업 View와 Report Sheet에 한정됩니다.")
        ]
    ),
    (
        u"QC Settings",
        u"QC Settings",
        u"Excel Report 환경과 프로젝트별 QC Rule Set을 관리합니다.",
        [
            (u"Python / Excel", u"Python 경로를 지정하고 Python / Excel Library / Excel Report 상태를 "
             u"확인합니다. Test와 Clear는 현재 외부 실행 환경을 점검·해제합니다."),
            (u"QC Rules", u"Rule Set을 선택하고 적용합니다. Copy로 새 JSON preset을 만들고 "
             u"Open Rule Folder에서 수정한 뒤 Reload로 다시 읽습니다."),
            (u"Rule Count", u"Sheet / View / Parameter 규칙과 Required Parameter 개수를 동일한 카드에서 확인합니다."),
            (u"진단", u"Details에서 환경 상세를 확인하고 Open Log에서 XLSX helper 실행 로그를 엽니다.")
        ]
    ),
    (
        u"Report",
        u"Report",
        u"DOC QC와 QC Lite는 CSV / Styled XLSX를 유지하며, QC Lite는 Compact Summary HTML과 선택형 PDF도 생성합니다. Scan QC는 전용 PDF Report를 생성합니다.",
        [
            (u"DOC QC", u"Full CSV는 개별 항목, Summary CSV는 그룹 결과, Styled XLSX는 공유용 보고서입니다."),
            (u"Scan QC", u"A3/A2 전용 Report Sheet에 QC Plan View와 Revision Cloud ID Mapping을 배치합니다."),
            (u"Report 버튼", u"가장 최근에 정상 생성된 QC 보고서를 기본 프로그램으로 엽니다."),
            (u"저장 취소", u"파일 또는 폴더 선택을 취소하면 설정과 파일을 변경하지 않고 조용히 돌아갑니다.")
        ]
    ),
    (
        u"Help",
        u"Help",
        u"Toolkit의 기능별 사용 방법, 모델 안전 기준과 문제 확인 순서를 안내합니다.",
        [
            (u"기능 안내", u"DOC QC → QC Lite → Scan QC → QC Settings → Report 순서로 각 기능을 확인합니다."),
            (u"실무 기준", u"검사 범위, 출력 형식, 모델 변경 여부와 현재 제한사항을 실행 전에 확인합니다.")
        ]
    ),
    (
        u"Troubleshooting",
        u"Troubleshooting",
        u"실행 전 환경과 모델 기준을 순서대로 확인하면 대부분의 문제를 빠르게 분리할 수 있습니다.",
        [
            (u"XLSX가 생성되지 않음", u"QC Settings에서 Python / Excel Library / Excel Report가 Ready인지 확인합니다."),
            (u"Scan QC 결과가 없음", u"Source Plan View, Analysis Point Cloud Source, Target Wall Filter, Wall Type Function과 Phase를 확인합니다."),
            (u"PDF가 생성되지 않음", u"저장 경로 권한, QC Plan View 생성 여부와 Report Sheet 생성 경고를 확인합니다."),
            (u"UI가 잘림", u"창을 확대하거나 내부 Scroll을 사용합니다. Windows 배율이 높은 경우 pyRevit Reload 후 다시 확인합니다.")
        ]
    )
]


def safe_text(value):
    try:
        return unicode(value)
    except Exception:
        try:
            return str(value)
        except Exception:
            return u"알 수 없는 오류"


class HelpForm(Form):
    def __init__(self):
        Form.__init__(self)
        self.SuspendLayout()
        self.Text = "Revit QC Toolkit Help"
        self.ClientSize = Size(1240, 1040)
        self.MinimumSize = Size(1140, 920)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.AutoScaleMode = AutoScaleMode.Dpi
        self.BackColor = Color.White
        self.ForeColor = NAVY_COLOR
        self.Font = get_preferred_font(10.0)
        self.nav_font_regular = get_preferred_font(10.0, FontStyle.Regular)
        self.nav_font_bold = get_preferred_font(10.0, FontStyle.Bold)
        self.detail_title_font = get_preferred_font(16.0, FontStyle.Bold)
        self.card_heading_font = get_preferred_font(10.5, FontStyle.Bold)
        self.card_body_font = get_preferred_font(10.0, FontStyle.Regular)
        self.nav_buttons = []
        self.detail_cards = []
        self.detail_labels = []
        self._build_layout()
        self._show_section(0)
        self.Shown += self._configure_scroll_fallback
        self.ResumeLayout(True)
        self.PerformLayout()

    def _build_layout(self):
        root = TableLayoutPanel()
        root.Dock = DockStyle.Fill
        root.Padding = Padding(
            OUTER_MARGIN,
            HEADER_TOP_PADDING,
            OUTER_MARGIN,
            OUTER_MARGIN
        )
        root.ColumnCount = 1
        root.RowCount = 3
        root.RowStyles.Add(RowStyle(SizeType.AutoSize))
        root.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        root.RowStyles.Add(RowStyle(SizeType.Absolute, float(FOOTER_HEIGHT)))
        self.Controls.Add(root)

        header_panel = Panel()
        header_panel.Dock = DockStyle.Fill
        header_panel.AutoSize = True
        header_panel.AutoSizeMode = AutoSizeMode.GrowAndShrink
        root.Controls.Add(header_panel, 0, 0)
        header = Label()
        header.Text = "Revit QC Toolkit Help\r\n기능별 사용 순서와 실무 기준을 확인하세요."
        header.Dock = DockStyle.Top
        header.AutoSize = True
        header.MinimumSize = Size(0, 72)
        header.Font = get_preferred_font(16.0, FontStyle.Bold)
        header.ForeColor = NAVY_COLOR
        header_panel.Controls.Add(header)

        body = TableLayoutPanel()
        body.Dock = DockStyle.Fill
        body.ColumnCount = 2
        body.RowCount = 1
        body.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 250.0))
        body.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        body.Margin = Padding(0, HEADER_BOTTOM_MARGIN, 0, 0)
        root.Controls.Add(body, 0, 1)

        navigation = FlowLayoutPanel()
        navigation.Dock = DockStyle.Fill
        navigation.FlowDirection = FlowDirection.TopDown
        navigation.WrapContents = False
        navigation.AutoScroll = False
        navigation.Padding = Padding(0, 8, 16, 12)
        navigation.BackColor = Color.White
        body.Controls.Add(navigation, 0, 0)
        for index, section in enumerate(HELP_SECTIONS):
            button = Button()
            button.Text = section[0]
            button.Width = 214
            button.Height = 48
            button.Margin = Padding(0, 0, 0, 10)
            button.FlatStyle = FlatStyle.Flat
            button.FlatAppearance.BorderSize = 1
            button.FlatAppearance.BorderColor = BORDER_COLOR
            button.BackColor = Color.White
            button.ForeColor = NAVY_COLOR
            button.Font = self.nav_font_regular
            button.TextAlign = ContentAlignment.MiddleLeft
            button.Padding = Padding(14, 0, 8, 0)
            button.Tag = index
            button.Click += self._navigation_click
            navigation.Controls.Add(button)
            self.nav_buttons.append(button)

        self.detail_host = Panel()
        self.detail_host.Dock = DockStyle.Fill
        self.detail_host.AutoScroll = False
        self.detail_host.BackColor = HELP_BACKGROUND_COLOR
        self.detail_host.BorderStyle = BorderStyle.FixedSingle
        body.Controls.Add(self.detail_host, 1, 0)

        self.detail_panel = FlowLayoutPanel()
        self.detail_panel.Dock = DockStyle.Top
        self.detail_panel.AutoSize = True
        self.detail_panel.FlowDirection = FlowDirection.TopDown
        self.detail_panel.WrapContents = False
        self.detail_panel.AutoScroll = False
        self.detail_panel.Padding = Padding(18, 8, 18, 12)
        self.detail_panel.BackColor = HELP_BACKGROUND_COLOR
        self.detail_panel.SizeChanged += self._resize_cards
        self.detail_host.Controls.Add(self.detail_panel)

        footer_panel = Panel()
        footer_panel.Dock = DockStyle.Bottom
        footer_panel.AutoSize = False
        footer_panel.Height = FOOTER_HEIGHT
        footer_panel.MinimumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.MaximumSize = Size(0, FOOTER_HEIGHT)
        footer_panel.Padding = Padding(0, 10, 0, 14)
        root.Controls.Add(footer_panel, 0, 2)
        footer = FlowLayoutPanel()
        footer.Dock = DockStyle.Right
        footer.AutoSize = False
        footer.Width = FOOTER_BUTTON_WIDTH
        footer.FlowDirection = FlowDirection.LeftToRight
        footer.WrapContents = False
        footer.Padding = Padding(0)
        footer_panel.Controls.Add(footer)
        close = Button()
        close.Text = "Close"
        close.AutoSize = False
        close.Dock = getattr(DockStyle, "None")
        close.Size = Size(FOOTER_BUTTON_WIDTH, FOOTER_BUTTON_HEIGHT)
        close.Margin = Padding(0)
        close.Font = get_preferred_font(9.5)
        apply_primary_button_style(close)
        close.Click += self._close
        footer.Controls.Add(close)
        self.CancelButton = close

    def _navigation_click(self, sender, event_args):
        self._show_section(int(sender.Tag))

    def _show_section(self, index):
        self.detail_panel.SuspendLayout()
        self._dispose_detail_controls()
        self.detail_cards = []
        self.detail_labels = []
        for button_index, button in enumerate(self.nav_buttons):
            selected = button_index == index
            button.BackColor = WARNING_BACKGROUND_COLOR if selected else Color.White
            button.FlatAppearance.BorderColor = ORANGE_COLOR if selected else BORDER_COLOR
            button.Font = self.nav_font_bold if selected else self.nav_font_regular

        section = HELP_SECTIONS[index]
        title = Label()
        title.Text = section[1]
        title.Width = self._detail_width()
        title.Height = 50
        title.Font = self.detail_title_font
        title.ForeColor = NAVY_COLOR
        title.Margin = Padding(0, 0, 0, 6)
        self.detail_panel.Controls.Add(title)
        self.detail_cards.append(title)

        intro = self._make_card(u"Overview", section[2], True)
        self.detail_panel.Controls.Add(intro)
        self.detail_cards.append(intro)
        for card_title, card_text in section[3]:
            card = self._make_card(card_title, card_text, False)
            self.detail_panel.Controls.Add(card)
            self.detail_cards.append(card)
        self.detail_panel.ResumeLayout(True)
        if self.Visible:
            self._configure_scroll_fallback(None, None)

    def _detail_width(self):
        return max(620, self.detail_host.ClientSize.Width - 38)

    def _configure_scroll_fallback(self, sender, event_args):
        configure_content_scroll(
            self,
            self.detail_host,
            self.detail_panel,
            0.94
        )

    def _make_card(self, title, text, accent):
        panel = TableLayoutPanel()
        panel.Width = self._detail_width()
        panel.AutoSize = True
        panel.ColumnCount = 1
        panel.RowCount = 2
        panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        panel.BackColor = Color.White
        panel.Margin = Padding(0, 0, 0, 10)
        panel.Padding = Padding(14, 8, 14, 10)
        heading = Label()
        heading.Text = title
        heading.Dock = DockStyle.Fill
        heading.AutoSize = True
        heading.MinimumSize = Size(0, 28)
        heading.Font = self.card_heading_font
        heading.ForeColor = ORANGE_COLOR if accent else NAVY_COLOR
        panel.Controls.Add(heading, 0, 0)
        body = Label()
        body.Text = text
        body.AutoSize = True
        body.MaximumSize = Size(max(560, self._detail_width() - 32), 0)
        body.Font = self.card_body_font
        body.ForeColor = NAVY_COLOR
        body.Padding = Padding(0, 4, 0, 0)
        body.UseCompatibleTextRendering = True
        panel.Controls.Add(body, 0, 1)
        panel.Tag = body
        self.detail_labels.append(body)
        return panel

    def _resize_cards(self, sender, event_args):
        width = self._detail_width()
        for card in self.detail_cards:
            card.Width = width
        for label in self.detail_labels:
            label.MaximumSize = Size(max(560, width - 32), 0)

    def _dispose_detail_controls(self):
        try:
            controls = [control for control in self.detail_panel.Controls]
            for control in controls:
                self.detail_panel.Controls.Remove(control)
                control.Dispose()
        except Exception:
            try:
                self.detail_panel.Controls.Clear()
            except Exception:
                pass

    def cleanup(self):
        if getattr(self, "_cleanup_done", False):
            return
        self._cleanup_done = True
        try:
            self.detail_panel.SizeChanged -= self._resize_cards
        except Exception:
            pass
        self._dispose_detail_controls()
        for font in (
            self.nav_font_regular,
            self.nav_font_bold,
            self.detail_title_font,
            self.card_heading_font,
            self.card_body_font
        ):
            try:
                font.Dispose()
            except Exception:
                pass

    def _close(self, sender, event_args):
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
                u"[{0}] {1}\n".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    safe_text(error)
                )
            )
    except Exception:
        pass
finally:
    if help_form is not None:
        help_profile.dispose()
