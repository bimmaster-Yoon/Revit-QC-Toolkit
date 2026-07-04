# -*- coding: utf-8 -*-

import clr

clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import (
    Color,
    ColorTranslator,
    ContentAlignment,
    Font,
    FontStyle,
    Size,
)
from System.Windows.Forms import (
    AnchorStyles,
    AutoScaleMode,
    Button,
    DockStyle,
    FlatStyle,
    FlowDirection,
    FlowLayoutPanel,
    Form,
    FormBorderStyle,
    FormStartPosition,
    GroupBox,
    Label,
    Padding,
    Panel,
    RowStyle,
    SizeType,
    TableLayoutPanel,
    TableLayoutPanelCellBorderStyle,
    ColumnStyle,
)

from pyrevit import forms


TEXT_NAVY = ColorTranslator.FromHtml("#263645")
SOFT_NAVY = ColorTranslator.FromHtml("#4A5B6A")
BUTTON_NAVY = ColorTranslator.FromHtml("#536777")
BORDER_GRAY = ColorTranslator.FromHtml("#D6DDE3")
LIGHT_BORDER = ColorTranslator.FromHtml("#E1E5E8")
CARD_FILL = ColorTranslator.FromHtml("#F4F6F8")
MUTED_TEXT = ColorTranslator.FromHtml("#5F6F7D")
READY_GREEN = ColorTranslator.FromHtml("#1E7A3A")
SAFETY_FILL = ColorTranslator.FromHtml("#F2F8F3")
SAFETY_BORDER = ColorTranslator.FromHtml("#CFE3D4")


def get_font(size, bold=False):
    style = FontStyle.Bold if bold else FontStyle.Regular
    try:
        return Font("Malgun Gothic", size, style)
    except Exception:
        return Font("Segoe UI", size, style)


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
        self.Text = "Revit QC Toolkit 도움말"
        self.ClientSize = Size(1200, 900)
        self.MinimumSize = Size(1080, 780)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = True
        self.MinimizeBox = False
        self.ShowInTaskbar = False
        self.AutoScroll = False
        self.AutoScaleMode = AutoScaleMode.Font
        self.BackColor = Color.White
        self.ForeColor = TEXT_NAVY
        self.Font = get_font(10.0)

        self._build_layout()
        self._build_content()
        self.content_panel.SizeChanged += self._resize_content_cards

    def _build_layout(self):
        self.root_layout = TableLayoutPanel()
        self.root_layout.Dock = DockStyle.Fill
        self.root_layout.Padding = Padding(24)
        self.root_layout.ColumnCount = 1
        self.root_layout.RowCount = 3
        self.root_layout.ColumnStyles.Add(
            ColumnStyle(SizeType.Percent, 100.0)
        )
        self.root_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 144.0))
        self.root_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        self.root_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 72.0))
        self.Controls.Add(self.root_layout)

        header = TableLayoutPanel()
        header.Dock = DockStyle.Fill
        header.ColumnCount = 1
        header.RowCount = 2
        header.RowStyles.Add(RowStyle(SizeType.Absolute, 46.0))
        header.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        header.Margin = Padding(0, 0, 0, 20)
        self.root_layout.Controls.Add(header, 0, 0)

        title = Label()
        title.Text = "Revit QC Toolkit 도움말"
        title.Dock = DockStyle.Fill
        title.AutoSize = False
        title.Font = get_font(17.5, True)
        title.ForeColor = TEXT_NAVY
        title.TextAlign = ContentAlignment.MiddleLeft
        header.Controls.Add(title, 0, 0)

        subtitle_area = TableLayoutPanel()
        subtitle_area.Dock = DockStyle.Fill
        subtitle_area.ColumnCount = 1
        subtitle_area.RowCount = 3
        subtitle_area.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        subtitle_area.RowStyles.Add(RowStyle(SizeType.Absolute, 8.0))
        subtitle_area.RowStyles.Add(RowStyle(SizeType.Absolute, 28.0))
        subtitle_area.Margin = Padding(0)
        header.Controls.Add(subtitle_area, 0, 1)

        subtitle_line_1 = Label()
        subtitle_line_1.Text = "Sheet, View, Parameter 검토 기준을 설정하고"
        subtitle_line_1.Dock = DockStyle.Fill
        subtitle_line_1.AutoSize = False
        subtitle_line_1.Font = get_font(11.5)
        subtitle_line_1.ForeColor = MUTED_TEXT
        subtitle_line_1.TextAlign = ContentAlignment.MiddleLeft
        subtitle_line_1.UseCompatibleTextRendering = True
        subtitle_area.Controls.Add(subtitle_line_1, 0, 0)

        subtitle_line_2 = Label()
        subtitle_line_2.Text = (
            "결과를 CSV / Styled Excel Report로 출력하는 pyRevit 기반 QC 도구입니다."
        )
        subtitle_line_2.Dock = DockStyle.Fill
        subtitle_line_2.AutoSize = False
        subtitle_line_2.Font = get_font(11.5)
        subtitle_line_2.ForeColor = MUTED_TEXT
        subtitle_line_2.TextAlign = ContentAlignment.MiddleLeft
        subtitle_line_2.UseCompatibleTextRendering = True
        subtitle_area.Controls.Add(subtitle_line_2, 0, 2)

        self.content_panel = FlowLayoutPanel()
        self.content_panel.Dock = DockStyle.Fill
        self.content_panel.AutoScroll = True
        self.content_panel.FlowDirection = FlowDirection.TopDown
        self.content_panel.WrapContents = False
        self.content_panel.Padding = Padding(0, 0, 8, 0)
        self.content_panel.Margin = Padding(0)
        self.content_panel.BackColor = Color.White
        self.root_layout.Controls.Add(self.content_panel, 0, 1)

        bottom_panel = FlowLayoutPanel()
        bottom_panel.Dock = DockStyle.Fill
        bottom_panel.AutoSize = False
        bottom_panel.FlowDirection = FlowDirection.RightToLeft
        bottom_panel.WrapContents = False
        bottom_panel.Padding = Padding(0, 15, 0, 15)
        bottom_panel.Margin = Padding(0)
        self.root_layout.Controls.Add(bottom_panel, 0, 2)

        close_button = Button()
        close_button.Text = "Close"
        close_button.AutoSize = False
        close_button.Size = Size(150, 42)
        close_button.Font = get_font(10.0)
        close_button.TextAlign = ContentAlignment.MiddleCenter
        close_button.FlatStyle = FlatStyle.Flat
        close_button.FlatAppearance.BorderSize = 1
        close_button.FlatAppearance.BorderColor = BUTTON_NAVY
        close_button.BackColor = BUTTON_NAVY
        close_button.ForeColor = Color.White
        close_button.UseVisualStyleBackColor = False
        close_button.Margin = Padding(0)
        close_button.Click += self._close
        bottom_panel.Controls.Add(close_button)
        self.CancelButton = close_button

    def _card_width(self):
        return max(920, self.content_panel.ClientSize.Width - 36)

    def _estimate_text_lines(self, text, chars_per_line=72):
        line_count = 0
        for line in text.replace(u"\r", u"").split(u"\n"):
            if not line:
                line_count += 1
            else:
                line_count += max(1, (len(line) + chars_per_line - 1) // chars_per_line)
        return line_count

    def _create_card(
        self,
        title,
        text,
        minimum_height,
        safety=False,
        item_gap=12,
        paragraph_gap=12
    ):
        card = GroupBox()
        card.Text = title
        card.Width = self._card_width()
        card.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        card.Margin = Padding(0, 0, 0, 26)
        card.Padding = Padding(24, 18, 24, 28)
        card.Font = get_font(13.0, True)
        card.ForeColor = READY_GREEN if safety else SOFT_NAVY
        card.BackColor = SAFETY_FILL if safety else CARD_FILL

        body = FlowLayoutPanel()
        body.Dock = DockStyle.Fill
        body.AutoSize = False
        body.AutoScroll = False
        body.FlowDirection = FlowDirection.TopDown
        body.WrapContents = False
        body.BackColor = SAFETY_FILL if safety else CARD_FILL
        body.Padding = Padding(14, 12, 14, 18)

        content_height = body.Padding.Top + body.Padding.Bottom
        normalized_text = text.replace(u"\r", u"")
        for line in normalized_text.split(u"\n"):
            if not line:
                spacer = Panel()
                spacer.Width = max(700, card.Width - 96)
                spacer.Height = paragraph_gap
                spacer.Margin = Padding(0)
                spacer.BackColor = body.BackColor
                body.Controls.Add(spacer)
                content_height += paragraph_gap
                continue

            wrapped_lines = self._estimate_text_lines(line)
            line_height = max(30, (wrapped_lines * 24) + 8)
            line_label = Label()
            line_label.Text = line
            line_label.AutoSize = False
            line_label.Width = max(700, card.Width - 96)
            line_label.Height = line_height
            line_label.Font = get_font(10.5)
            line_label.ForeColor = READY_GREEN if safety else TEXT_NAVY
            line_label.BackColor = body.BackColor
            line_label.Margin = Padding(0, 0, 0, item_gap)
            line_label.Padding = Padding(0, 2, 0, 2)
            line_label.TextAlign = ContentAlignment.TopLeft
            line_label.UseCompatibleTextRendering = True
            body.Controls.Add(line_label)
            self.text_labels.append(line_label)
            content_height += line_height + item_gap

        card.Height = max(minimum_height, 70 + content_height)
        card.Controls.Add(body)
        return card

    def _create_table_card(
        self,
        title,
        rows,
        minimum_height,
        headers,
        minimum_row_height
    ):
        card = GroupBox()
        card.Text = title
        card.Width = self._card_width()
        row_heights = []
        for row_data in rows:
            description_length = len(row_data[1])
            row_heights.append(
                78.0 if description_length > 44 else minimum_row_height
            )
        content_height = 50.0 + sum(row_heights)
        card.Height = max(minimum_height, int(90.0 + content_height))
        card.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        card.Margin = Padding(0, 0, 0, 26)
        card.Padding = Padding(24, 18, 24, 28)
        card.Font = get_font(13.0, True)
        card.ForeColor = SOFT_NAVY
        card.BackColor = CARD_FILL

        table = TableLayoutPanel()
        table.Dock = DockStyle.Fill
        table.ColumnCount = 2
        table.RowCount = len(rows) + 1
        table.ColumnStyles.Add(ColumnStyle(SizeType.Absolute, 260.0))
        table.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        table.CellBorderStyle = TableLayoutPanelCellBorderStyle.Single
        table.BackColor = BORDER_GRAY
        table.RowStyles.Add(RowStyle(SizeType.Absolute, 50.0))
        for row_height in row_heights:
            table.RowStyles.Add(RowStyle(SizeType.Absolute, row_height))
        card.Controls.Add(table)

        table.Controls.Add(self._create_table_header(headers[0]), 0, 0)
        table.Controls.Add(self._create_table_header(headers[1]), 1, 0)

        for row_index, row_data in enumerate(rows):
            name_label = self._create_table_label(
                row_data[0],
                True,
                row_index
            )
            value_label = self._create_table_label(
                row_data[1],
                False,
                row_index
            )
            table.Controls.Add(name_label, 0, row_index + 1)
            table.Controls.Add(value_label, 1, row_index + 1)

        return card

    def _create_table_header(self, text):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.Font = get_font(10.5, True)
        label.ForeColor = Color.White
        label.BackColor = BUTTON_NAVY
        label.Padding = Padding(14, 10, 14, 10)
        label.TextAlign = ContentAlignment.MiddleLeft
        label.UseCompatibleTextRendering = True
        return label

    def _create_table_label(self, text, bold, row_index):
        label = Label()
        label.Text = text
        label.Dock = DockStyle.Fill
        label.AutoSize = False
        label.Font = get_font(10.25, bold)
        label.ForeColor = TEXT_NAVY
        label.BackColor = Color.White if row_index % 2 == 0 else CARD_FILL
        label.Padding = Padding(14, 10, 14, 10)
        label.TextAlign = ContentAlignment.MiddleLeft
        label.UseCompatibleTextRendering = True
        return label

    def _build_content(self):
        self.cards = []
        self.text_labels = []

        self._add_card(self._create_card(
            "1. 기본 사용 흐름",
            "1. QC Settings에서 Excel Report 상태를 확인합니다.\r\n"
            "2. 프로젝트에 맞는 Rule Set을 선택하고 Use This를 누릅니다.\r\n"
            "3. Run Full QC 또는 Quick QC를 실행합니다.\r\n"
            "4. Export Options에서 저장 형식을 선택합니다.\r\n"
            "5. 결과를 pyRevit output 또는 CSV / Styled Excel Report로 확인합니다.",
            330
        ))

        self._add_card(self._create_table_card(
            "2. 주요 버튼",
            [
                ("Run Full QC", "Sheet, View, Parameter를 모두 검토합니다."),
                ("Quick QC", "Sheet와 View 중심으로 빠르게 검토합니다."),
                ("QC Settings", "Excel Report 환경과 QC Rule Set을 설정합니다."),
                ("Open Last Report", "마지막으로 저장한 보고서를 엽니다."),
                ("Help", "이 도움말을 표시합니다."),
            ],
            360,
            ("Button", "사용 목적"),
            58.0
        ))

        self._add_card(self._create_table_card(
            "3. QC Settings에서 할 수 있는 것",
            [
                ("Excel Report", "Styled Excel Report 생성을 위한 Python 상태를 확인합니다."),
                ("QC Rules", "프로젝트 또는 회사 기준에 맞는 Rule Set을 선택합니다."),
                ("Rule Count", "현재 Rule Set에 포함된 검사 항목 수를 확인합니다."),
                ("Details", "Python 경로, 설정 파일, Debug Log 등 상세 정보를 확인합니다."),
            ],
            320,
            ("항목", "설명"),
            64.0
        ))

        self._add_card(self._create_card(
            "4. Rule Set 만드는 방법",
            "Rule Set은 Sheet, View, Parameter 검토 기준을 담은 설정 파일입니다. "
            "회사나 프로젝트 기준이 달라지면 기존 Rule Set을 복사해 수정할 수 있습니다.\r\n\r\n"
            "1. QC Settings에서 기준이 될 Rule Set을 선택합니다.\r\n"
            "2. Copy 버튼으로 새 Rule Set 파일을 만듭니다.\r\n"
            "3. Open Rule Folder로 config 폴더를 엽니다.\r\n"
            "4. JSON 파일에서 검사 항목, Severity, Recommendation을 수정합니다.\r\n"
            "5. 새 Rule Set을 선택하고 Use This를 누릅니다.\r\n"
            "6. Run Full QC로 결과가 의도대로 나오는지 확인합니다.\r\n\r\n"
            "Rule Set의 기준은 회사 또는 실무자가 정의하고, JSON은 그 기준을 툴킷이 "
            "읽을 수 있게 정리한 형식입니다.",
            470
        ))

        self._add_card(self._create_table_card(
            "5. Rule Set에서 조정할 수 있는 항목",
            [
                ("Sheet Rules", "배치 View 없는 Sheet, Sheet 이름 규칙, Copy 문구 확인"),
                ("View Rules", "View 이름 규칙, Sheet 배치 여부, 임시 View 확인"),
                ("Parameter Rules", "RoomType, ITEMGROUP 등 필수 Parameter 누락 확인"),
                ("Severity", "High / Medium / Low 중요도 구분"),
                ("Recommendation", "검토자가 확인해야 할 조치 문구"),
            ],
            360,
            ("항목", "예시"),
            64.0
        ))

        self._add_card(self._create_table_card(
            "6. Export Options",
            [
                ("Full CSV", "개별 검토 항목을 모두 포함한 상세 데이터입니다."),
                ("Summary CSV", "반복 항목을 그룹화한 요약 데이터입니다."),
                ("Styled Excel Report", "검토와 공유를 위한 보고서형 XLSX 파일입니다."),
                ("View Only", "저장하지 않고 pyRevit output에서 결과만 확인합니다."),
            ],
            330,
            ("Option", "설명"),
            66.0
        ))

        self._add_card(self._create_card(
            "7. 새 컴퓨터에서 사용할 때",
            "새 PC에서는 pyRevit Extension을 연결한 뒤 QC Settings에서 "
            "Excel Report 상태를 먼저 확인합니다.\r\n\r\n"
            "Excel Report가 Ready가 아니면 Set Python으로 python.exe를 선택하고 "
            "Test를 누릅니다.\r\n\r\n"
            "장기 사용에는 임시 경로가 아닌 안정적인 로컬 Python 또는\r\n"
            "프로젝트 전용 Python 환경을 권장합니다.",
            350,
            False,
            16,
            24
        ))

        self._add_card(self._create_card(
            "8. Model Safety",
            "• 이 툴킷은 read-only 방식으로 동작합니다.\r\n"
            "• Revit 요소를 생성, 삭제, 수정하지 않습니다.\r\n"
            "• 도면 검토, 기준 확인, 협업용 보고서 생성을 지원하기 위한 도구입니다.",
            260,
            True
        ))

        footer = Label()
        footer.Text = "Version: v2.6\r\n\r\npyRevit Extension-based Revit QC Toolkit"
        footer.Width = self._card_width()
        footer.Height = 94
        footer.AutoSize = False
        footer.Font = get_font(10.0)
        footer.ForeColor = SOFT_NAVY
        footer.Margin = Padding(0, 0, 0, 12)
        footer.Padding = Padding(4, 8, 4, 8)
        self.content_panel.Controls.Add(footer)
        self.cards.append(footer)

        contact_label = Label()
        contact_label.Text = (
            "Developed by JeongHo Yoon  |  Contact: yjhbim@gmail.com"
        )
        contact_label.Width = self._card_width()
        contact_label.Height = 38
        contact_label.AutoSize = False
        contact_label.Font = get_font(9.0)
        contact_label.ForeColor = MUTED_TEXT
        contact_label.TextAlign = ContentAlignment.MiddleLeft
        contact_label.Margin = Padding(0, 0, 0, 20)
        contact_label.Padding = Padding(4, 0, 4, 0)
        self.content_panel.Controls.Add(contact_label)
        self.cards.append(contact_label)

    def _add_card(self, card):
        self.content_panel.Controls.Add(card)
        self.cards.append(card)

    def _resize_content_cards(self, sender, args):
        width = self._card_width()
        for card in self.cards:
            card.Width = width
        text_width = max(700, width - 96)
        for line_label in self.text_labels:
            line_label.Width = text_width

    def _close(self, sender, args):
        self.Close()


try:
    HelpForm().ShowDialog()
except Exception as error:
    forms.alert(
        u"Help 창을 표시하는 중 오류가 발생했습니다:\n{0}".format(
            safe_text(error)
        ),
        title="Revit QC Toolkit 도움말",
        warn_icon=True
    )
