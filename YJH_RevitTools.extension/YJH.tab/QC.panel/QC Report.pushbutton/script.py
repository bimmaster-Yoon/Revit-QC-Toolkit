# -*- coding: utf-8 -*-

# ============================================================
# Revit Sheet + View + Parameter QC Report
# Revit 2026 + pyRevit + IronPython 호환
#
# 읽기 전용:
# - Transaction을 생성하지 않음
# - 모델의 파라미터 및 요소를 수정하지 않음
# ============================================================

from Autodesk.Revit.DB import (
    BuiltInCategory,
    ElementId,
    FilteredElementCollector,
    StorageType,
    View,
    ViewSheet,
    ViewType
)

from pyrevit import revit, script

from System import Environment, DateTime
from System.IO import Directory, Path, StreamWriter
from System.Text import UTF8Encoding


# ============================================================
# 버전
# ============================================================

VERSION = "v1.8 - Sheet + View + Parameter QC"


# ============================================================
# 기본 설정
# ============================================================

doc = revit.doc
output = script.get_output()

output.set_title("Revit QC Report {0}".format(VERSION))


# ============================================================
# View QC 기준
# ============================================================

SUPPORTED_VIEW_TYPES = (
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.Elevation,
    ViewType.Section,
    ViewType.Detail,
    ViewType.DraftingView,
    ViewType.ThreeD
)

# 주요 도면 View Template 검사 대상
TEMPLATE_REQUIRED_VIEW_TYPES = (
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.Elevation,
    ViewType.Section
)

# Sheet 배치 검사 대상
# 3D View는 작업 및 검토용일 수 있으므로 제외
SHEET_REQUIRED_VIEW_TYPES = (
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.Elevation,
    ViewType.Section,
    ViewType.Detail,
    ViewType.DraftingView
)

TEMPORARY_KEYWORDS = (
    u"Copy",
    u"복사",
    u"Temp",
    u"임시",
    u"Working",
    u"TEST"
)

VIEW_TYPE_NAMES = {
    ViewType.FloorPlan: u"Floor Plan",
    ViewType.CeilingPlan: u"Ceiling Plan",
    ViewType.Elevation: u"Elevation",
    ViewType.Section: u"Section",
    ViewType.Detail: u"Detail",
    ViewType.DraftingView: u"Drafting View",
    ViewType.ThreeD: u"3D View"
}


# ============================================================
# Parameter QC 기준
# ============================================================

PARAMETER_RULES = (
    (
        BuiltInCategory.OST_Rooms,
        u"Rooms",
        u"RoomType"
    ),
    (
        BuiltInCategory.OST_LightingFixtures,
        u"Lighting Fixtures",
        u"ITEMGROUP"
    ),
    (
        BuiltInCategory.OST_ElectricalFixtures,
        u"Electrical Fixtures",
        u"ITEMGROUP"
    ),
    (
        BuiltInCategory.OST_PlumbingFixtures,
        u"Plumbing Fixtures",
        u"ITEMGROUP"
    )
)


# ============================================================
# 문자열 처리
# ============================================================

try:
    text_type = unicode
except NameError:
    text_type = str


def to_text(value):
    """값을 안전하게 문자열로 변환한다."""
    if value is None:
        return u""

    try:
        return text_type(value)
    except Exception:
        return text_type(str(value))


def is_empty(value):
    """문자열이 없거나 공백만 있는지 검사한다."""
    return not to_text(value).strip()


def html_escape(value):
    """HTML 출력용 특수문자 처리."""
    text = to_text(value)

    return (
        text.replace(u"&", u"&amp;")
        .replace(u"<", u"&lt;")
        .replace(u">", u"&gt;")
        .replace(u'"', u"&quot;")
    )


def csv_escape(value):
    """CSV 필드 특수문자 처리."""
    text = to_text(value)

    if (
        u"," in text
        or u'"' in text
        or u"\n" in text
        or u"\r" in text
    ):
        text = text.replace(u'"', u'""')
        return u'"{0}"'.format(text)

    return text


def get_element_id_value(element_id):
    """Revit 2026 및 이전 ElementId API를 함께 지원한다."""
    try:
        return element_id.Value
    except Exception:
        return element_id.IntegerValue


def get_view_type_name(view):
    """View Type의 출력용 이름을 반환한다."""
    if view.ViewType in VIEW_TYPE_NAMES:
        return VIEW_TYPE_NAMES[view.ViewType]

    return to_text(view.ViewType)


# ============================================================
# 공통 Issue 생성
# ============================================================

def add_issue(
    issue_rows,
    category,
    item_type,
    item_name,
    severity,
    qc_item
):
    """공통 Issue List에 QC 항목을 추가한다."""

    issue_rows.append(
        [
            category,
            item_type,
            item_name,
            severity,
            qc_item
        ]
    )


# ============================================================
# Parameter 처리
# ============================================================

def find_shared_parameter(element, parameter_name):
    """
    요소에서 지정된 이름의 Shared Parameter를 찾는다.

    동일한 이름의 일반 Project Parameter가 있어도
    IsShared가 False이면 검사 대상 Shared Parameter로 인정하지 않는다.
    """
    if element is None:
        return None

    try:
        parameters = element.GetParameters(parameter_name)

        for parameter in parameters:
            if parameter.IsShared:
                return parameter

    except Exception:
        return None

    return None


def get_shared_parameter(element, parameter_name):
    """
    인스턴스에서 Shared Parameter를 먼저 찾는다.
    없으면 Type 요소에서 찾는다.

    반환값:
    - parameter
    - Instance 또는 Type
    """

    # 인스턴스 파라미터 확인
    parameter = find_shared_parameter(
        element,
        parameter_name
    )

    if parameter is not None:
        return parameter, u"Instance"

    # Type 파라미터 확인
    try:
        type_id = element.GetTypeId()

        if type_id != ElementId.InvalidElementId:
            type_element = doc.GetElement(type_id)

            parameter = find_shared_parameter(
                type_element,
                parameter_name
            )

            if parameter is not None:
                return parameter, u"Type"

    except Exception:
        pass

    return None, u""


def parameter_has_input_value(parameter):
    """Parameter에 실제 입력값이 있는지 검사한다."""
    if parameter is None:
        return False

    try:
        if not parameter.HasValue:
            return False
    except Exception:
        return False

    try:
        if parameter.StorageType == StorageType.String:
            return not is_empty(parameter.AsString())

        # String 이외의 타입은 HasValue가 True이면 입력된 값으로 판단
        return True

    except Exception:
        return False


def get_parameter_element_name(element, category_name):
    """Parameter QC 결과에 표시할 요소 이름을 만든다."""
    element_id = get_element_id_value(element.Id)

    # Room은 Room Number와 Room Name을 함께 표시
    if category_name == u"Rooms":
        room_number = u""
        room_name = u""

        try:
            room_number = to_text(element.Number)
        except Exception:
            pass

        try:
            room_name = to_text(element.Name)
        except Exception:
            pass

        if is_empty(room_number):
            room_number = u"(번호 없음)"

        if is_empty(room_name):
            room_name = u"(이름 없음)"

        return u"{0} - {1} [Id: {2}]".format(
            room_number,
            room_name,
            element_id
        )

    # Fixture 계열은 Family와 Type 이름을 표시
    try:
        type_id = element.GetTypeId()
        type_element = doc.GetElement(type_id)

        if type_element is not None:
            family_name = u""
            type_name = u""

            try:
                family_name = to_text(type_element.FamilyName)
            except Exception:
                pass

            try:
                type_name = to_text(type_element.Name)
            except Exception:
                pass

            if is_empty(family_name):
                family_name = category_name

            if is_empty(type_name):
                type_name = u"(Type 이름 없음)"

            return u"{0} : {1} [Id: {2}]".format(
                family_name,
                type_name,
                element_id
            )

    except Exception:
        pass

    return u"{0} [Id: {1}]".format(
        category_name,
        element_id
    )


# ============================================================
# CSV 저장 폴더
# ============================================================

def ensure_folder(folder_path):
    """저장 폴더가 없으면 생성한다."""
    if is_empty(folder_path):
        return False

    if not Directory.Exists(folder_path):
        Directory.CreateDirectory(folder_path)

    return Directory.Exists(folder_path)


def get_save_folder():
    """
    DesktopDirectory를 우선 사용한다.
    실패하면 Documents 폴더를 사용한다.
    """

    desktop_error = u""
    documents_error = u""

    try:
        desktop_path = Environment.GetFolderPath(
            Environment.SpecialFolder.DesktopDirectory
        )

        if ensure_folder(desktop_path):
            return desktop_path

    except Exception as ex:
        desktop_error = to_text(ex)

    try:
        documents_path = Environment.GetFolderPath(
            Environment.SpecialFolder.MyDocuments
        )

        if ensure_folder(documents_path):
            return documents_path

    except Exception as ex:
        documents_error = to_text(ex)

    raise Exception(
        u"Desktop 및 Documents 폴더를 사용할 수 없습니다. "
        u"Desktop 오류: {0} / Documents 오류: {1}".format(
            desktop_error,
            documents_error
        )
    )


# ============================================================
# CSV 작성
# ============================================================

def write_csv_row(writer, values):
    """CSV 한 줄을 작성한다."""
    escaped_values = []

    for value in values:
        escaped_values.append(csv_escape(value))

    writer.WriteLine(u",".join(escaped_values))


def save_csv(issue_rows, summary_data, qc_status):
    """전체 QC 결과를 UTF-8 BOM CSV로 저장한다."""

    save_folder = get_save_folder()
    timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss")

    file_name = u"Revit_QC_v1.8_{0}.csv".format(timestamp)
    csv_path = Path.Combine(save_folder, file_name)

    writer = None

    try:
        utf8_bom = UTF8Encoding(True)
        writer = StreamWriter(csv_path, False, utf8_bom)

        write_csv_row(writer, [u"Report Version", VERSION])
        write_csv_row(writer, [u"QC Status", qc_status])
        write_csv_row(
            writer,
            [u"Checked Sheets", summary_data["checked_sheets"]]
        )
        write_csv_row(
            writer,
            [u"Checked Views", summary_data["checked_views"]]
        )
        write_csv_row(
            writer,
            [u"Sheet Issues", summary_data["sheet_issues"]]
        )
        write_csv_row(
            writer,
            [u"View Issues", summary_data["view_issues"]]
        )
        write_csv_row(
            writer,
            [u"Parameter Issues", summary_data["parameter_issues"]]
        )
        write_csv_row(
            writer,
            [u"Total Issues", summary_data["total_issues"]]
        )
        write_csv_row(
            writer,
            [u"High", summary_data["high_count"]]
        )
        write_csv_row(
            writer,
            [u"Medium", summary_data["medium_count"]]
        )
        write_csv_row(
            writer,
            [u"Low", summary_data["low_count"]]
        )

        writer.WriteLine(u"")

        write_csv_row(
            writer,
            [
                u"Category",
                u"Item Type / Number",
                u"Item Name",
                u"Severity",
                u"QC Item"
            ]
        )

        for row in issue_rows:
            write_csv_row(writer, row)

    finally:
        if writer is not None:
            writer.Close()

    return csv_path


# ============================================================
# Sheet 수집
# ============================================================

sheets = list(
    FilteredElementCollector(doc)
    .OfClass(ViewSheet)
    .WhereElementIsNotElementType()
    .ToElements()
)

sheets = sorted(
    sheets,
    key=lambda sheet: to_text(sheet.SheetNumber)
)


# ============================================================
# Sheet에 배치된 View ID 수집
# ============================================================

placed_view_ids = set()

for sheet in sheets:
    sheet_placed_view_ids = sheet.GetAllPlacedViews()

    for placed_view_id in sheet_placed_view_ids:
        placed_view_ids.add(
            get_element_id_value(placed_view_id)
        )


# ============================================================
# 검사 대상 View 수집
# ============================================================

all_views = (
    FilteredElementCollector(doc)
    .OfClass(View)
    .WhereElementIsNotElementType()
    .ToElements()
)

checked_views = []

for view in all_views:
    if view.IsTemplate:
        continue

    if view.ViewType not in SUPPORTED_VIEW_TYPES:
        continue

    checked_views.append(view)


checked_views = sorted(
    checked_views,
    key=lambda view: (
        get_view_type_name(view),
        to_text(view.Name)
    )
)


# ============================================================
# 전체 Issue List
# ============================================================

issue_rows = []


# ============================================================
# Sheet QC
# ============================================================

for sheet in sheets:
    sheet_number = to_text(sheet.SheetNumber)
    sheet_name = to_text(sheet.Name)

    display_number = sheet_number
    display_name = sheet_name

    if is_empty(display_number):
        display_number = u"(비어 있음)"

    if is_empty(display_name):
        display_name = u"(비어 있음)"

    if is_empty(sheet_number):
        add_issue(
            issue_rows,
            u"Sheet QC",
            display_number,
            display_name,
            u"High",
            u"Sheet Number 누락"
        )

    if is_empty(sheet_name):
        add_issue(
            issue_rows,
            u"Sheet QC",
            display_number,
            display_name,
            u"High",
            u"Sheet Name 누락"
        )

    sheet_view_ids = sheet.GetAllPlacedViews()

    if sheet_view_ids.Count == 0:
        add_issue(
            issue_rows,
            u"Sheet QC",
            display_number,
            display_name,
            u"Medium",
            u"배치된 View 없음"
        )


# ============================================================
# View QC
# ============================================================

for view in checked_views:
    view_name = to_text(view.Name)
    view_type_name = get_view_type_name(view)

    display_view_name = view_name

    if is_empty(display_view_name):
        display_view_name = u"(비어 있음)"

    # View Name 누락
    if is_empty(view_name):
        add_issue(
            issue_rows,
            u"View QC",
            view_type_name,
            display_view_name,
            u"High",
            u"View Name 누락"
        )

    # 임시 키워드 검사
    if not is_empty(view_name):
        lower_view_name = view_name.lower()
        matched_keywords = []

        for keyword in TEMPORARY_KEYWORDS:
            if keyword.lower() in lower_view_name:
                matched_keywords.append(keyword)

        if matched_keywords:
            add_issue(
                issue_rows,
                u"View QC",
                view_type_name,
                display_view_name,
                u"Low",
                u"임시 키워드 포함: {0}".format(
                    u", ".join(matched_keywords)
                )
            )

    # 투시 3D는 Scale 검사 제외
    should_check_scale = True

    if view.ViewType == ViewType.ThreeD:
        try:
            if view.IsPerspective:
                should_check_scale = False
        except Exception:
            should_check_scale = True

    if should_check_scale:
        try:
            view_scale = view.Scale

            if view_scale <= 0:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"High",
                    u"View Scale 비정상: {0}".format(view_scale)
                )

        except Exception as ex:
            add_issue(
                issue_rows,
                u"View QC",
                view_type_name,
                display_view_name,
                u"High",
                u"View Scale 확인 불가: {0}".format(
                    to_text(ex)
                )
            )

    # 주요 도면 View Template 검사
    if view.ViewType in TEMPLATE_REQUIRED_VIEW_TYPES:
        try:
            if view.ViewTemplateId == ElementId.InvalidElementId:
                add_issue(
                    issue_rows,
                    u"View QC",
                    view_type_name,
                    display_view_name,
                    u"Medium",
                    u"View Template 미적용"
                )

        except Exception as ex:
            add_issue(
                issue_rows,
                u"View QC",
                view_type_name,
                display_view_name,
                u"Medium",
                u"View Template 확인 불가: {0}".format(
                    to_text(ex)
                )
            )

    # 도면용 View Sheet 배치 검사
    if view.ViewType in SHEET_REQUIRED_VIEW_TYPES:
        current_view_id = get_element_id_value(view.Id)

        if current_view_id not in placed_view_ids:
            add_issue(
                issue_rows,
                u"View QC",
                view_type_name,
                display_view_name,
                u"Medium",
                u"Sheet에 배치되지 않은 도면용 View"
            )


# ============================================================
# Parameter QC
# ============================================================

checked_parameter_elements = 0

for rule in PARAMETER_RULES:
    built_in_category = rule[0]
    category_name = rule[1]
    parameter_name = rule[2]

    elements = (
        FilteredElementCollector(doc)
        .OfCategory(built_in_category)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    for element in elements:
        checked_parameter_elements += 1

        element_name = get_parameter_element_name(
            element,
            category_name
        )

        parameter, parameter_scope = get_shared_parameter(
            element,
            parameter_name
        )

        # Shared Parameter 자체가 없음
        if parameter is None:
            add_issue(
                issue_rows,
                u"Parameter QC",
                category_name,
                element_name,
                u"High",
                u"Shared Parameter 없음: {0}".format(
                    parameter_name
                )
            )
            continue

        # Shared Parameter는 있지만 값이 비어 있음
        if not parameter_has_input_value(parameter):
            add_issue(
                issue_rows,
                u"Parameter QC",
                category_name,
                element_name,
                u"Medium",
                u"{0} 값 비어 있음 ({1} Parameter)".format(
                    parameter_name,
                    parameter_scope
                )
            )


# ============================================================
# Summary 계산
# ============================================================

sheet_issue_count = 0
view_issue_count = 0
parameter_issue_count = 0

high_count = 0
medium_count = 0
low_count = 0


for row in issue_rows:
    category = row[0]
    severity = row[3]

    if category == u"Sheet QC":
        sheet_issue_count += 1

    elif category == u"View QC":
        view_issue_count += 1

    elif category == u"Parameter QC":
        parameter_issue_count += 1

    if severity == u"High":
        high_count += 1

    elif severity == u"Medium":
        medium_count += 1

    elif severity == u"Low":
        low_count += 1


total_issue_count = len(issue_rows)


summary_data = {
    "checked_sheets": len(sheets),
    "checked_views": len(checked_views),
    "sheet_issues": sheet_issue_count,
    "view_issues": view_issue_count,
    "parameter_issues": parameter_issue_count,
    "total_issues": total_issue_count,
    "high_count": high_count,
    "medium_count": medium_count,
    "low_count": low_count
}


# ============================================================
# QC Status
# ============================================================

if high_count > 0:
    qc_status = u"Review Required"
    status_color = u"#c62828"

elif medium_count > 0 or low_count > 0:
    qc_status = u"Check Recommended"
    status_color = u"#ef6c00"

else:
    qc_status = u"No Issues Found"
    status_color = u"#2e7d32"


# ============================================================
# Summary 출력
# ============================================================

summary_rows = [
    [u"Checked Sheets", len(sheets)],
    [u"Checked Views", len(checked_views)],
    [u"Checked Parameter Elements", checked_parameter_elements],
    [u"Sheet Issues", sheet_issue_count],
    [u"View Issues", view_issue_count],
    [u"Parameter Issues", parameter_issue_count],
    [u"Total Issues", total_issue_count],
    [u"High / Medium / Low", u"{0} / {1} / {2}".format(
        high_count,
        medium_count,
        low_count
    )]
]

output.print_html(
    u"""
    <div style="font-family:Segoe UI, Arial, sans-serif;">
        <h2>Revit Sheet + View + Parameter QC Report</h2>
        <p>
            <strong>Version:</strong> {0}<br>
            <strong>QC Status:</strong>
            <span style="color:{1}; font-weight:bold;">{2}</span>
        </p>
    </div>
    """.format(
        html_escape(VERSION),
        status_color,
        html_escape(qc_status)
    )
)

output.print_html_table(
    table_data=summary_rows,
    title="QC Summary",
    columns=[
        "Summary Item",
        "Count"
    ],
    column_widths=[
        "260px",
        "120px"
    ],
    table_width_style="width:420px",
    row_striping=True
)


# ============================================================
# 상세 Issue List 출력
# ============================================================

if issue_rows:
    output.print_html_table(
        table_data=issue_rows,
        title="QC Issue List",
        columns=[
            "Category",
            "Item Type / Number",
            "Item Name",
            "Severity",
            "QC Item"
        ],
        column_widths=[
            "100px",
            "160px",
            "300px",
            "80px",
            "320px"
        ],
        table_width_style="width:100%",
        row_striping=True
    )

else:
    output.print_html(
        u"""
        <div style="
            margin-top:12px;
            padding:10px;
            border:1px solid #81c784;
            background-color:#e8f5e9;
            color:#2e7d32;
            font-weight:bold;">
            QC 항목이 발견되지 않았습니다.
        </div>
        """
    )


# ============================================================
# CSV Export
# ============================================================

try:
    saved_csv_path = save_csv(
        issue_rows,
        summary_data,
        qc_status
    )

    output.print_html(
        u"""
        <div style="
            margin-top:12px;
            padding:8px;
            border-left:4px solid #2e7d32;
            background-color:#f1f8e9;">
            <strong>CSV 저장 완료</strong><br>
            {0}
        </div>
        """.format(html_escape(saved_csv_path))
    )

except Exception as ex:
    output.print_html(
        u"""
        <div style="
            margin-top:12px;
            padding:8px;
            border-left:4px solid #c62828;
            background-color:#ffebee;
            color:#b71c1c;">
            <strong>CSV 저장 경고</strong><br>
            CSV 저장에는 실패했지만 QC 검사는 완료되었습니다.<br>
            오류 내용: {0}
        </div>
        """.format(html_escape(ex))
    )