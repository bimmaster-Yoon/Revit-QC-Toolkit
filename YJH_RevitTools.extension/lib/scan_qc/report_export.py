# -*- coding: utf-8 -*-

import math
import os

try:
    from Autodesk.Revit.DB import (
        BuiltInParameter,
        BuiltInCategory,
        Color as DBColor,
        ElementId,
        ElementTransformUtils,
        ElementTypeGroup,
        FamilySymbol,
        FilteredElementCollector,
        HorizontalTextAlignment,
        Line,
        OverrideGraphicSettings,
        StorageType,
        TextNote,
        TextNoteOptions,
        TextNoteType,
        Transaction,
        TransactionStatus,
        ViewSheet,
        Viewport,
        XYZ
    )
except Exception:
    BuiltInParameter = None
    BuiltInCategory = None
    DBColor = None
    ElementId = None
    ElementTransformUtils = None
    ElementTypeGroup = None
    FamilySymbol = None
    FilteredElementCollector = None
    HorizontalTextAlignment = None
    Line = None
    OverrideGraphicSettings = None
    StorageType = None
    TextNote = None
    TextNoteOptions = None
    TextNoteType = None
    Transaction = None
    TransactionStatus = None
    ViewSheet = None
    Viewport = None
    XYZ = None

try:
    from Autodesk.Revit.DB import PDFExportOptions
except Exception:
    PDFExportOptions = None

try:
    from System import DateTime
    from System.Collections.Generic import List
except Exception:
    DateTime = None
    List = None

try:
    from report_history import write_latest_report_path
except Exception:
    write_latest_report_path = None

from scan_qc.settings import get_extension_dir, get_report_options


FT_TO_MM = 304.8
DEFAULT_A3_LANDSCAPE_WIDTH_MM = 420.0
DEFAULT_A3_LANDSCAPE_HEIGHT_MM = 297.0
DEFAULT_A2_LANDSCAPE_WIDTH_MM = 594.0
DEFAULT_A2_LANDSCAPE_HEIGHT_MM = 420.0
REPORT_SCALE_CANDIDATES = [50, 75, 100, 150, 200]
SCAN_QC_REPORT_TITLEBLOCK_NAME = u"TB_SCAN_QC_A3_LANDSCAPE"


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def _yes_no(value):
    return u"Yes" if value else u"No"


def _format_mm(value):
    if value is None:
        return u"N/A"
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return u"{0}".format(int(numeric_value))
        return u"{0:.1f}".format(numeric_value)
    except Exception:
        return _to_text(value)


def _format_mm_with_unit(value):
    if value is None:
        return u"N/A"
    return u"{0} mm".format(_format_mm(value))


def _mm_to_internal(mm_value):
    try:
        return float(mm_value) / FT_TO_MM
    except Exception:
        return 0.0


def _safe_bool(value):
    return bool(value)


def _get_paper_size(selected_options):
    paper_size = selected_options.get("paper_size", u"A3 Landscape")
    if paper_size not in (u"A3 Landscape", u"A2 Landscape"):
        paper_size = u"A3 Landscape"
    return paper_size


def _get_paper_size_dimensions_mm(selected_options):
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        return (
            paper_size,
            DEFAULT_A2_LANDSCAPE_WIDTH_MM,
            DEFAULT_A2_LANDSCAPE_HEIGHT_MM
        )
    return (
        u"A3 Landscape",
        DEFAULT_A3_LANDSCAPE_WIDTH_MM,
        DEFAULT_A3_LANDSCAPE_HEIGHT_MM
    )


def _get_layout_profile(selected_options):
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        return {
            "paper_size": paper_size,
            "plan_ratio": 0.815,
            "summary_ratio": 0.185,
            "margin_x_mm": 14.0,
            "margin_y_mm": 13.0,
            "gutter_mm": 9.0,
            "summary_min_width_mm": 96.0
        }
    return {
        "paper_size": u"A3 Landscape",
        "plan_ratio": 0.790,
        "summary_ratio": 0.210,
        "margin_x_mm": 10.0,
        "margin_y_mm": 10.0,
        "gutter_mm": 7.0,
        "summary_min_width_mm": 78.0
    }


def _create_result(requested):
    return {
        "requested": requested,
        "attempted": False,
        "report_sheet_mode": u"create_new",
        "report_sheet_mode_label": u"Scan QC Dedicated Sheet",
        "report_sheet_created": False,
        "sheet_name": u"",
        "sheet_number": u"",
        "sheet_id": None,
        "titleblock_found": False,
        "titleblock_name": u"",
        "titleblock_mode": u"N/A",
        "pdf_required_qc_plan_view": u"N/A",
        "paper_size": u"A3 Landscape",
        "summary_panel_width_mm": u"N/A",
        "viewport_created": False,
        "viewport_id": None,
        "viewport_scale": u"N/A",
        "viewport_scale_source": u"N/A",
        "viewport_title_hidden": False,
        "viewport_title_status": u"N/A",
        "summary_textnote_count": 0,
        "summary_separator_count": 0,
        "summary_layout": u"Dashboard right Summary Panel",
        "pdf_requested": requested,
        "pdf_save_dialog_result": u"N/A",
        "pdf_exported": False,
        "pdf_path": u"",
        "requested_pdf_path": u"",
        "export_cancelled": False,
        "image_requested": False,
        "image_exported": False,
        "image_path": u"",
        "image_status": u"Not requested",
        "failure_reason": u"",
        "warnings": [],
        "errors": []
    }


def _get_timestamp():
    if DateTime is not None:
        try:
            return DateTime.Now.ToString("yyMMdd_HHmmss")
        except Exception:
            pass
    import datetime
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")


def _get_report_timestamp_parts(selected_options):
    timestamp = selected_options.get("report_timestamp") or _get_timestamp()
    compact = _to_text(timestamp)
    date_part = compact[:6] if len(compact) >= 6 else u"000000"
    time_part = compact[7:11] if len(compact) >= 11 else u"0000"
    created_text = u"{0}.{1}.{2} {3}:{4}".format(
        date_part[0:2],
        date_part[2:4],
        date_part[4:6],
        time_part[0:2],
        time_part[2:4]
    )
    report_id = u"SQCR_{0}_{1}".format(date_part, time_part)
    return timestamp, created_text, report_id


def _get_project_name(doc):
    try:
        project_info = doc.ProjectInformation
        if project_info is not None:
            project_name = _to_text(project_info.Name).strip()
            if project_name:
                return project_name
    except Exception:
        pass

    try:
        return _to_text(doc.Title).strip() or u"N/A"
    except Exception:
        return u"N/A"


def _resolve_report_folder(settings):
    report_options = get_report_options(settings)
    extension_dir = get_extension_dir()
    output_folder = report_options.get("output_folder") or u"reports/scan_qc"
    resolved_folder = os.path.abspath(os.path.join(extension_dir, output_folder))
    reports_root = os.path.abspath(os.path.join(extension_dir, "reports"))
    return resolved_folder, reports_root, report_options


def _ensure_folder(folder_path):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)


def _get_titleblock_symbols(doc):
    if FilteredElementCollector is None or BuiltInCategory is None:
        return []
    try:
        symbols = (
            FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsElementType()
            .ToElements()
        )
    except Exception:
        return []

    result = []
    for symbol in symbols:
        if symbol is None:
            continue
        if FamilySymbol is not None:
            try:
                if not isinstance(symbol, FamilySymbol):
                    continue
            except Exception:
                pass
        result.append(symbol)

    try:
        result.sort(key=lambda item: _to_text(item.FamilyName) + u" " + _to_text(item.Name))
    except Exception:
        pass
    return result


def _get_titleblock_display_name(titleblock_symbol):
    if titleblock_symbol is None:
        return u""
    family_name = u""
    type_name = u""
    try:
        family_name = _to_text(titleblock_symbol.FamilyName)
    except Exception:
        pass
    try:
        type_name = _to_text(titleblock_symbol.Name)
    except Exception:
        pass
    return u"{0}: {1}".format(family_name, type_name).strip(u": ")


def _titleblock_matches_scan_qc(titleblock_symbol):
    display_name = _get_titleblock_display_name(titleblock_symbol)
    try:
        type_name = _to_text(titleblock_symbol.Name)
    except Exception:
        type_name = u""
    try:
        family_name = _to_text(titleblock_symbol.FamilyName)
    except Exception:
        family_name = u""

    values = [display_name, type_name, family_name]
    for value in values:
        if value and SCAN_QC_REPORT_TITLEBLOCK_NAME in value:
            return True
    return False


def _find_scan_qc_titleblock(titleblocks):
    for titleblock in titleblocks:
        if _titleblock_matches_scan_qc(titleblock):
            return titleblock
    return None


def _activate_titleblock_if_needed(doc, titleblock_symbol, result):
    if titleblock_symbol is None:
        return

    try:
        if hasattr(titleblock_symbol, "IsActive") and not titleblock_symbol.IsActive:
            titleblock_symbol.Activate()
            doc.Regenerate()
    except Exception as ex:
        result["warnings"].append(
            u"Titleblock activation warning: {0}".format(_to_text(ex))
        )


def _create_titleblockless_report_sheet(doc, result):
    if ViewSheet is None or ElementId is None:
        return None, u"ViewSheet or ElementId API was unavailable."

    try:
        invalid_id = ElementId.InvalidElementId
    except Exception:
        try:
            invalid_id = ElementId(-1)
        except Exception as ex:
            return None, u"Invalid titleblock ElementId was unavailable: {0}".format(
                _to_text(ex)
            )

    try:
        sheet = ViewSheet.Create(doc, invalid_id)
        result["titleblock_mode"] = u"None"
        result["titleblock_found"] = False
        result["titleblock_name"] = u"None"
        return sheet, u""
    except Exception as ex:
        return None, u"Titleblock-free Scan QC Sheet creation failed: {0}".format(
            _to_text(ex)
        )


def _create_titleblock_report_sheet(doc, titleblock_symbol, titleblock_mode, result):
    if titleblock_symbol is None:
        return None, u"Titleblock symbol was unavailable."

    _activate_titleblock_if_needed(doc, titleblock_symbol, result)
    try:
        sheet = ViewSheet.Create(doc, titleblock_symbol.Id)
        result["titleblock_mode"] = titleblock_mode
        result["titleblock_found"] = True
        result["titleblock_name"] = _get_titleblock_display_name(titleblock_symbol)
        return sheet, u""
    except Exception as ex:
        return None, u"{0} Sheet creation failed: {1}".format(
            titleblock_mode,
            _to_text(ex)
        )


def _create_dedicated_scan_qc_sheet(doc, result):
    sheet, warning = _create_titleblockless_report_sheet(doc, result)
    if sheet is not None:
        return sheet
    if warning:
        result["warnings"].append(warning)

    titleblocks = _get_titleblock_symbols(doc)
    scan_qc_titleblock = _find_scan_qc_titleblock(titleblocks)
    if scan_qc_titleblock is not None:
        sheet, warning = _create_titleblock_report_sheet(
            doc,
            scan_qc_titleblock,
            u"ScanQC Titleblock",
            result
        )
        if sheet is not None:
            return sheet
        if warning:
            result["warnings"].append(warning)

    if titleblocks:
        fallback_titleblock = titleblocks[0]
        sheet, warning = _create_titleblock_report_sheet(
            doc,
            fallback_titleblock,
            u"Fallback Existing",
            result
        )
        if sheet is not None:
            result["warnings"].append(
                u"Scan QC dedicated Sheet fallback used an existing project "
                u"Titleblock because titleblock-free Sheet creation and "
                u"{0} were unavailable.".format(SCAN_QC_REPORT_TITLEBLOCK_NAME)
            )
            return sheet
        if warning:
            result["warnings"].append(warning)

    result["failure_reason"] = (
        u"Report Sheet creation failed. Titleblock-free Sheet creation was "
        u"unavailable and no usable fallback Titleblock was found."
    )
    result["warnings"].append(result["failure_reason"])
    return None


def collect_report_sheets(doc):
    if FilteredElementCollector is None or ViewSheet is None:
        return []

    sheets = []
    try:
        collected_sheets = (
            FilteredElementCollector(doc)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for sheet in collected_sheets:
            if sheet is None:
                continue
            try:
                if sheet.IsPlaceholder:
                    continue
            except Exception:
                pass
            sheets.append(sheet)
    except Exception:
        return []

    try:
        sheets.sort(
            key=lambda item: (
                _to_text(getattr(item, "SheetNumber", u"")),
                _to_text(getattr(item, "Name", u""))
            )
        )
    except Exception:
        pass
    return sheets


def _collect_existing_sheet_values(doc):
    sheet_names = set()
    sheet_numbers = set()
    if FilteredElementCollector is None or ViewSheet is None:
        return sheet_names, sheet_numbers

    try:
        sheets = (
            FilteredElementCollector(doc)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for sheet in sheets:
            try:
                sheet_names.add(_to_text(sheet.Name))
            except Exception:
                pass
            try:
                sheet_numbers.add(_to_text(sheet.SheetNumber))
            except Exception:
                pass
    except Exception:
        pass

    return sheet_names, sheet_numbers


def _get_unique_sheet_values(doc, timestamp):
    sheet_names, sheet_numbers = _collect_existing_sheet_values(doc)
    base_name = u"SCAN_QC_REPORT_{0}".format(timestamp)
    base_number = u"SQC_{0}".format(timestamp)

    sheet_name = base_name
    sheet_number = base_number
    suffix = 2
    while sheet_name in sheet_names or sheet_number in sheet_numbers:
        sheet_name = u"{0}_{1}".format(base_name, suffix)
        sheet_number = u"{0}_{1}".format(base_number, suffix)
        suffix += 1

    return sheet_name, sheet_number


def _get_sheet_outline(sheet, selected_options=None):
    if not hasattr(selected_options, "get"):
        selected_options = {}

    try:
        if selected_options.get("report_sheet_mode") != u"existing":
            _paper_size, width_mm, height_mm = _get_paper_size_dimensions_mm(
                selected_options
            )
            width = _mm_to_internal(width_mm)
            height = _mm_to_internal(height_mm)
            return -width / 2.0, -height / 2.0, width / 2.0, height / 2.0
    except Exception:
        pass

    try:
        outline = sheet.Outline
        min_u = float(outline.Min.U)
        min_v = float(outline.Min.V)
        max_u = float(outline.Max.U)
        max_v = float(outline.Max.V)
        if max_u > min_u and max_v > min_v:
            return min_u, min_v, max_u, max_v
    except Exception:
        pass

    _paper_size, width_mm, height_mm = _get_paper_size_dimensions_mm(selected_options)
    width = _mm_to_internal(width_mm)
    height = _mm_to_internal(height_mm)
    return -width / 2.0, -height / 2.0, width / 2.0, height / 2.0


def _create_xyz(x, y, z=0.0):
    if XYZ is None:
        return None
    return XYZ(float(x), float(y), float(z))


def _get_text_type_id(doc):
    if ElementTypeGroup is None:
        return None
    try:
        return doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)
    except Exception:
        return None


def _get_existing_text_type_by_name(doc, type_name):
    if FilteredElementCollector is None or TextNoteType is None:
        return None

    try:
        text_types = (
            FilteredElementCollector(doc)
            .OfClass(TextNoteType)
            .WhereElementIsElementType()
            .ToElements()
        )
        for text_type in text_types:
            try:
                if _to_text(text_type.Name) == type_name:
                    return text_type
            except Exception:
                pass
    except Exception:
        pass
    return None


def _set_text_type_size(text_type, text_size_mm):
    if text_type is None or text_size_mm is None:
        return False

    size_value = _mm_to_internal(text_size_mm)
    parameters = []
    try:
        if BuiltInParameter is not None:
            parameters.append(text_type.get_Parameter(BuiltInParameter.TEXT_SIZE))
    except Exception:
        pass
    try:
        parameters.append(text_type.LookupParameter(u"Text Size"))
    except Exception:
        pass

    for parameter in parameters:
        if parameter is None:
            continue
        try:
            if parameter.IsReadOnly:
                continue
            parameter.Set(size_value)
            return True
        except Exception:
            pass
    return False


def _set_text_type_bold(text_type, is_bold):
    if text_type is None:
        return False

    value = 1 if is_bold else 0
    parameters = []
    try:
        if BuiltInParameter is not None:
            parameters.append(text_type.get_Parameter(BuiltInParameter.TEXT_STYLE_BOLD))
    except Exception:
        pass
    for parameter_name in (u"Bold", u"굵게"):
        try:
            parameters.append(text_type.LookupParameter(parameter_name))
        except Exception:
            pass

    for parameter in parameters:
        if parameter is None:
            continue
        try:
            if parameter.IsReadOnly:
                continue
            parameter.Set(value)
            return True
        except Exception:
            pass
    return False


def _get_report_text_style(suffix, text_size_mm):
    style_key = _to_text(suffix).lower()
    if style_key in (u"title", u"report_title"):
        return u"SQCR_TITLE", text_size_mm, True
    if style_key in (u"subtitle", u"report_subtitle"):
        return u"SQCR_SUBTITLE", text_size_mm, False
    if style_key in (u"meta", u"report_meta"):
        return u"SQCR_META", text_size_mm, False
    if style_key in (u"section", u"section_header"):
        return u"SQCR_SECTION_HEADER", text_size_mm, True
    if style_key in (u"table_header",):
        return u"SQCR_TABLE_HEADER", text_size_mm, True
    if style_key in (u"table_body", u"chip"):
        return u"SQCR_TABLE_BODY", text_size_mm, False
    return u"SQCR_BODY", text_size_mm, False


def _get_or_create_report_text_type(doc, suffix, text_size_mm):
    default_text_type_id = _get_text_type_id(doc)
    type_name, style_size_mm, is_bold = _get_report_text_style(
        suffix,
        text_size_mm
    )

    existing_type = _get_existing_text_type_by_name(doc, type_name)
    if existing_type is not None:
        try:
            _set_text_type_size(existing_type, style_size_mm)
            _set_text_type_bold(existing_type, is_bold)
            return existing_type.Id
        except Exception:
            return default_text_type_id

    if default_text_type_id is None:
        return None

    try:
        default_text_type = doc.GetElement(default_text_type_id)
        if default_text_type is None:
            return default_text_type_id
        new_text_type = default_text_type.Duplicate(type_name)
        _set_text_type_size(new_text_type, style_size_mm)
        _set_text_type_bold(new_text_type, is_bold)
        return new_text_type.Id
    except Exception:
        return default_text_type_id


def _create_wrapped_text_note(
    doc,
    sheet,
    position,
    width,
    text,
    horizontal_alignment=None,
    text_type_id=None
):
    if TextNote is None:
        return None

    if text_type_id is None:
        text_type_id = _get_text_type_id(doc)
    options = None
    try:
        if text_type_id is not None and TextNoteOptions is not None:
            options = TextNoteOptions(text_type_id)
            try:
                if horizontal_alignment is None:
                    horizontal_alignment = HorizontalTextAlignment.Left
                options.HorizontalAlignment = horizontal_alignment
            except Exception:
                pass
            try:
                return TextNote.Create(
                    doc,
                    sheet.Id,
                    position,
                    width,
                    text,
                    options
                )
            except Exception:
                return TextNote.Create(
                    doc,
                    sheet.Id,
                    position,
                    text,
                    options
                )

        if text_type_id is not None:
            try:
                return TextNote.Create(
                    doc,
                    sheet.Id,
                    position,
                    width,
                    text,
                    text_type_id
                )
            except Exception:
                return TextNote.Create(
                    doc,
                    sheet.Id,
                    position,
                    text,
                    text_type_id
                )
    finally:
        try:
            if options is not None:
                options.Dispose()
        except Exception:
            pass

    return None


def _create_report_text_note(
    doc,
    sheet,
    position,
    width,
    text,
    size_key=u"body",
    text_size_mm=2.4,
    horizontal_alignment=None
):
    text_type_id = _get_or_create_report_text_type(doc, size_key, text_size_mm)
    return _create_wrapped_text_note(
        doc,
        sheet,
        position,
        width,
        text,
        horizontal_alignment,
        text_type_id
    )


def _get_marker_preview(view_creation_result):
    marker_preview = view_creation_result.get("marker_preview", {})
    if not hasattr(marker_preview, "get"):
        marker_preview = {}
    return marker_preview


def _get_plan_preview(view_creation_result):
    marker_preview = _get_marker_preview(view_creation_result)
    plan_preview = marker_preview.get("plan", {})
    if not hasattr(plan_preview, "get"):
        plan_preview = {}
    return plan_preview


def _get_preview_id_mappings(view_creation_result):
    plan_preview = _get_plan_preview(view_creation_result)
    mappings = plan_preview.get("preview_id_mappings", [])
    if isinstance(mappings, (list, tuple)):
        return [mapping for mapping in mappings if hasattr(mapping, "get")]
    return []


def _build_tolerance_text(selected_options):
    tolerance_mm = selected_options.get("tolerance_mm") or {}
    ok_max = tolerance_mm.get("ok_max", 30)
    review_max = tolerance_mm.get("review_max", 80)
    return u"OK 0-{0} mm / Review {0}-{1} mm / Critical {1} mm+".format(
        _format_mm(ok_max),
        _format_mm(review_max)
    )


def _build_result_count_text(plan_preview):
    return u"OK {0} / Review {1} / Critical {2}".format(
        plan_preview.get("ok_count", 0),
        plan_preview.get("review_count", 0),
        plan_preview.get("critical_count", 0)
    )


def _mapping_metric_text(mapping):
    metric_value = mapping.get("p75_deviation_mm")
    if metric_value is None:
        metric_value = mapping.get("classification_deviation_mm")
    return _format_mm_with_unit(metric_value)


def _get_top_n_callouts(selected_options):
    try:
        top_n = int(selected_options.get("top_n_callouts", 7))
        if top_n <= 0:
            return 7
        return top_n
    except Exception:
        return 7


def _build_id_mapping_lines(mappings, selected_options, plan_preview=None):
    if not mappings:
        return [u"No Review/Critical Revision Cloud ID callouts were created."]
    if not hasattr(plan_preview, "get"):
        plan_preview = {}

    lines = []
    top_n = _get_top_n_callouts(selected_options)
    visible_mappings = list(mappings[:top_n])
    for mapping in visible_mappings:
        metric_value = mapping.get("p75_deviation_mm")
        metric_label = u"P75"
        if metric_value is None:
            metric_value = mapping.get("p90_deviation_mm")
            metric_label = u"P90"
        if metric_value is None:
            metric_value = mapping.get("classification_deviation_mm")
            metric_label = mapping.get("classification_metric", u"P75")
        lines.append(
            u"{0} | Wall {1} | {2} {3} | {4}".format(
                mapping.get("id", u"N/A"),
                mapping.get("wall_id", u"N/A"),
                metric_label,
                _format_mm_with_unit(metric_value),
                mapping.get("status", mapping.get("severity", u"N/A"))
            )
        )
    total_candidate_count = plan_preview.get("candidate_callout_count", len(mappings))
    try:
        total_candidate_count = int(total_candidate_count)
    except Exception:
        total_candidate_count = len(mappings)
    total_display_basis = max(total_candidate_count, len(mappings))
    remaining_count = max(0, total_display_basis - len(visible_mappings))
    if remaining_count:
        lines.append(u"+ {0} more Review/Critical callout results".format(
            remaining_count
        ))
    return lines


def _build_summary_text(doc, source_plan_view, selected_options, view_creation_result):
    plan_preview = _get_plan_preview(view_creation_result)
    mappings = _get_preview_id_mappings(view_creation_result)
    source_plan_name = selected_options.get("source_plan_view_name", u"N/A")
    if not source_plan_name and source_plan_view is not None:
        try:
            source_plan_name = _to_text(source_plan_view.Name)
        except Exception:
            source_plan_name = u"N/A"

    lines = [
        u"SCAN QC SUMMARY",
        u"",
        u"Project: {0}".format(_get_project_name(doc)),
        u"Source Plan View: {0}".format(source_plan_name),
        u"Point Cloud: {0}".format(
            selected_options.get("point_cloud_name", u"N/A")
        ),
        u"Scope: {0}".format(
            selected_options.get("analysis_scope_label", u"N/A")
        ),
        u"Tolerance: {0}".format(_build_tolerance_text(selected_options)),
        u"Result Count: {0}".format(_build_result_count_text(plan_preview)),
        u"",
        u"ID Mapping:"
    ]
    lines.extend(_build_id_mapping_lines(mappings, selected_options, plan_preview))
    return u"\r\n".join(lines)


def _build_summary_sections(doc, source_plan_view, selected_options, view_creation_result):
    plan_preview = _get_plan_preview(view_creation_result)
    source_plan_name = selected_options.get("source_plan_view_name", u"N/A")
    if not source_plan_name and source_plan_view is not None:
        try:
            source_plan_name = _to_text(source_plan_view.Name)
        except Exception:
            source_plan_name = u"N/A"

    point_cloud_name = selected_options.get("point_cloud_name", u"N/A")
    scope_label = selected_options.get("analysis_scope_label", u"N/A")
    top_n = _get_top_n_callouts(selected_options)
    _timestamp, created_text, report_id = _get_report_timestamp_parts(
        selected_options
    )

    return [
        {
            "title": u"SCAN QC REPORT",
            "lines": [
                u"Created: {0}".format(created_text),
                u"Report ID: {0}".format(report_id)
            ]
        },
        {
            "title": u"REPORT INFO",
            "lines": [
                u"Report Sheet: {0}".format(
                    selected_options.get("report_sheet_mode_label", u"Scan QC Dedicated Sheet")
                ),
                u"Top N Callouts: {0}".format(top_n)
            ]
        },
        {
            "title": u"PROJECT / SOURCE",
            "lines": [
                u"Project: {0}".format(_get_project_name(doc)),
                u"Source Plan: {0}".format(source_plan_name),
                u"Point Cloud: {0}".format(point_cloud_name),
                u"Scope: {0}".format(scope_label)
            ]
        },
        {
            "title": u"TOLERANCE",
            "lines": [
                _build_tolerance_text(selected_options)
            ]
        },
        {
            "title": u"RESULT COUNT",
            "lines": [
                _build_result_count_text(plan_preview)
            ]
        }
    ]


def _build_id_mapping_rows(view_creation_result, selected_options):
    plan_preview = _get_plan_preview(view_creation_result)
    mappings = _get_preview_id_mappings(view_creation_result)
    top_n = _get_top_n_callouts(selected_options)
    # preview_id_mappings is the displayed callout list produced by markers.py.
    # Keep the report table on the same display basis as the Plan View IDs.
    visible_mappings = list(mappings[:top_n])
    rows = []

    for mapping in visible_mappings:
        metric_value = mapping.get("p75_deviation_mm")
        if metric_value is None:
            metric_value = mapping.get("p90_deviation_mm")
        if metric_value is None:
            metric_value = mapping.get("classification_deviation_mm")
        status = mapping.get("status", mapping.get("severity", u"N/A"))
        status_text = _to_text(status).upper()
        if status_text == u"CRITICAL":
            status_text = u"CRIT"
        elif status_text == u"REVIEW":
            status_text = u"REV"
        rows.append([
            mapping.get("id", u"N/A"),
            _to_text(mapping.get("wall_id", u"N/A")),
            _format_mm(metric_value),
            status_text
        ])

    total_candidate_count = plan_preview.get("candidate_callout_count", len(mappings))
    try:
        total_candidate_count = int(total_candidate_count)
    except Exception:
        total_candidate_count = len(mappings)
    total_display_basis = max(total_candidate_count, len(mappings))
    remaining_count = max(0, total_display_basis - len(visible_mappings))
    return rows, remaining_count


def _build_tolerance_chip_data(selected_options):
    tolerance_mm = selected_options.get("tolerance_mm") or {}
    ok_max = tolerance_mm.get("ok_max", 30)
    review_max = tolerance_mm.get("review_max", 80)
    return [
        [u"OK", u"0-{0}mm".format(_format_mm(ok_max))],
        [u"Review", u"{0}-{1}mm".format(_format_mm(ok_max), _format_mm(review_max))],
        [u"Critical", u"{0}mm+".format(_format_mm(review_max))]
    ]


def _apply_sheet_line_weight(sheet, element, line_weight):
    if sheet is None or element is None or line_weight is None:
        return False
    if OverrideGraphicSettings is None:
        return False

    try:
        graphics = OverrideGraphicSettings()
        try:
            graphics.SetProjectionLineWeight(int(line_weight))
        except Exception:
            return False
        sheet.SetElementOverrides(element.Id, graphics)
        return True
    except Exception:
        return False


def _create_sheet_separator_line(doc, sheet, start_point, end_point, line_weight=None):
    if Line is None or start_point is None or end_point is None:
        return None

    try:
        line = Line.CreateBound(start_point, end_point)
        detail_curve = doc.Create.NewDetailCurve(sheet, line)
        _apply_sheet_line_weight(sheet, detail_curve, line_weight)
        return detail_curve
    except Exception:
        return None


def _add_rectangle_lines(doc, sheet, min_x, min_y, max_x, max_y, line_weight=None):
    points = [
        (_create_xyz(min_x, min_y, 0.0), _create_xyz(max_x, min_y, 0.0)),
        (_create_xyz(max_x, min_y, 0.0), _create_xyz(max_x, max_y, 0.0)),
        (_create_xyz(max_x, max_y, 0.0), _create_xyz(min_x, max_y, 0.0)),
        (_create_xyz(min_x, max_y, 0.0), _create_xyz(min_x, min_y, 0.0))
    ]
    created_count = 0
    for start_point, end_point in points:
        line = _create_sheet_separator_line(
            doc,
            sheet,
            start_point,
            end_point,
            line_weight
        )
        if line is not None:
            created_count += 1
    return created_count


def _add_summary_table_to_sheet(
    doc,
    sheet,
    source_plan_view,
    selected_options,
    view_creation_result,
    summary_min_x,
    summary_min_y,
    summary_max_x,
    summary_max_y,
    result
):
    sections = _build_summary_sections(
        doc,
        source_plan_view,
        selected_options,
        view_creation_result
    )
    id_rows, remaining_id_count = _build_id_mapping_rows(
        view_creation_result,
        selected_options
    )
    summary_width = max(_mm_to_internal(70.0), summary_max_x - summary_min_x)
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        title_size = 4.5
        section_size = 2.7
        body_size = 2.25
        table_size = 2.05
        title_gap = _mm_to_internal(7.2)
        body_line_height = _mm_to_internal(5.8)
        section_gap = _mm_to_internal(5.2)
    else:
        title_size = 3.9
        section_size = 2.45
        body_size = 2.05
        table_size = 1.85
        title_gap = _mm_to_internal(6.4)
        body_line_height = _mm_to_internal(5.3)
        section_gap = _mm_to_internal(4.3)

    panel_padding = _mm_to_internal(4.0)
    top_padding = _mm_to_internal(5.0)
    underline_gap = _mm_to_internal(3.4)
    text_after_line_gap = _mm_to_internal(3.0)
    x = summary_min_x + panel_padding
    y = summary_max_y - top_padding
    content_max_x = summary_max_x - panel_padding
    text_width = max(_mm_to_internal(60.0), summary_width - (panel_padding * 2.0))
    created_notes = 0
    created_lines = 0

    def add_note(x_pos, y_pos, width, text, size_key, text_size_mm, alignment=None):
        note = _create_report_text_note(
            doc,
            sheet,
            _create_xyz(x_pos, y_pos, 0.0),
            width,
            text,
            size_key,
            text_size_mm,
            alignment
        )
        return 1 if note is not None else 0

    def add_rule(y_pos):
        rule = _create_sheet_separator_line(
            doc,
            sheet,
            _create_xyz(x, y_pos, 0.0),
            _create_xyz(content_max_x, y_pos, 0.0)
        )
        return 1 if rule is not None else 0

    def has_space(required_height):
        return (y - required_height) > (summary_min_y + _mm_to_internal(6.0))

    for section in sections:
        title = section.get("title", u"")
        lines = section.get("lines", [])
        if title == u"SCAN QC REPORT":
            required_height = (
                title_gap
                + (body_line_height * max(1, len(lines)))
                + section_gap
            )
        elif title == u"TOLERANCE":
            required_height = _mm_to_internal(23.0) + section_gap
        else:
            required_height = (
                body_line_height
                + underline_gap
                + text_after_line_gap
                + (body_line_height * max(1, len(lines)))
                + section_gap
            )

        if not has_space(required_height):
            result["warnings"].append(
                u"Report Summary area was too small; remaining rows were omitted."
            )
            break

        if title == u"SCAN QC REPORT":
            created_notes += add_note(
                x,
                y,
                text_width,
                title,
                u"title",
                title_size
            )
            y -= title_gap
            for line_text in lines:
                created_notes += add_note(
                    x,
                    y,
                    text_width,
                    line_text,
                    u"small",
                    body_size
                )
                y -= body_line_height
        else:
            created_notes += add_note(
                x,
                y,
                text_width,
                title,
                u"section",
                section_size
            )
            y -= underline_gap
            created_lines += add_rule(y)
            y -= text_after_line_gap
            if title == u"TOLERANCE":
                chip_data = _build_tolerance_chip_data(selected_options)
                chip_gap = _mm_to_internal(2.0)
                chip_width = (text_width - (chip_gap * 2.0)) / 3.0
                chip_height = _mm_to_internal(10.5)
                chip_top = y
                for index, chip in enumerate(chip_data):
                    chip_min_x = x + ((chip_width + chip_gap) * index)
                    chip_max_x = chip_min_x + chip_width
                    chip_bottom = chip_top - chip_height
                    created_lines += _add_rectangle_lines(
                        doc,
                        sheet,
                        chip_min_x,
                        chip_bottom,
                        chip_max_x,
                        chip_top
                    )
                    created_notes += add_note(
                        chip_min_x + _mm_to_internal(1.0),
                        chip_top - _mm_to_internal(2.0),
                        chip_width - _mm_to_internal(2.0),
                        u"{0}\r\n{1}".format(chip[0], chip[1]),
                        u"chip",
                        1.65 if paper_size == u"A3 Landscape" else 1.85,
                        HorizontalTextAlignment.Center
                    )
                y = chip_top - chip_height
            else:
                for line_text in lines:
                    created_notes += add_note(
                        x,
                        y,
                        text_width,
                        line_text,
                        u"body",
                        body_size
                    )
                    y -= body_line_height

        y -= section_gap

    id_area_bottom = summary_min_y + _mm_to_internal(4.0)
    if y > id_area_bottom + _mm_to_internal(24.0):
        created_notes += add_note(
            x,
            y,
            text_width,
            u"ID MAPPING",
            u"section",
            section_size
        )
        y -= underline_gap
        created_lines += add_rule(y)

        table_top = y - text_after_line_gap
        col_id_x = x
        col_wall_x = x + (text_width * 0.14)
        col_p75_x = x + (text_width * 0.52)
        col_status_x = x + (text_width * 0.70)
        created_notes += add_note(col_id_x, table_top, text_width * 0.11, u"ID", u"table_header", table_size)
        created_notes += add_note(col_wall_x, table_top, text_width * 0.34, u"Wall ID", u"table_header", table_size)
        created_notes += add_note(col_p75_x, table_top, text_width * 0.15, u"P75", u"table_header", table_size)
        created_notes += add_note(col_status_x, table_top, text_width * 0.28, u"Status", u"table_header", table_size)
        table_line = _create_sheet_separator_line(
            doc,
            sheet,
            _create_xyz(x, table_top - _mm_to_internal(3.5), 0.0),
            _create_xyz(content_max_x, table_top - _mm_to_internal(3.5), 0.0)
        )
        if table_line is not None:
            created_lines += 1

        row_y = table_top - _mm_to_internal(7.8)
        row_height = body_line_height
        max_row_count = int(max(0.0, (row_y - id_area_bottom - _mm_to_internal(6.0)) / row_height))
        visible_rows = id_rows[:max_row_count]
        if not visible_rows:
            created_notes += add_note(
                x,
                row_y,
                text_width,
                u"No Review/Critical callouts",
                u"body",
                body_size
            )
        else:
            for row in visible_rows:
                created_notes += add_note(col_id_x, row_y, text_width * 0.11, _to_text(row[0]), u"table_body", table_size)
                created_notes += add_note(col_wall_x, row_y, text_width * 0.34, _to_text(row[1]), u"table_body", table_size)
                created_notes += add_note(col_p75_x, row_y, text_width * 0.15, _to_text(row[2]), u"table_body", table_size)
                created_notes += add_note(col_status_x, row_y, text_width * 0.28, _to_text(row[3]), u"table_body", table_size)
                row_y -= row_height
            hidden_count = remaining_id_count + max(0, len(id_rows) - len(visible_rows))
            if hidden_count:
                created_notes += add_note(
                    x,
                    row_y,
                    text_width,
                    u"+ {0} more".format(hidden_count),
                    u"small",
                    table_size
                )
    else:
        result["warnings"].append(
            u"Report Summary ID Mapping area was too small and was omitted."
        )

    result["summary_textnote_count"] = created_notes
    result["summary_separator_count"] = (
        result.get("summary_separator_count", 0) + created_lines
    )
    if created_notes <= 0:
        result["warnings"].append(
            u"Report Summary table TextNotes could not be created."
        )


def _add_summary_table_to_sheet(
    doc,
    sheet,
    source_plan_view,
    selected_options,
    view_creation_result,
    summary_min_x,
    summary_min_y,
    summary_max_x,
    summary_max_y,
    result
):
    """Create a fixed-zone Summary Panel to avoid text/line overlap in PDF."""
    plan_preview = _get_plan_preview(view_creation_result)
    id_rows, remaining_id_count = _build_id_mapping_rows(
        view_creation_result,
        selected_options
    )
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        title_size = 4.1
        section_size = 2.55
        body_size = 2.15
        table_size = 1.95
        line_height = _mm_to_internal(5.6)
    else:
        title_size = 3.6
        section_size = 2.25
        body_size = 1.9
        table_size = 1.7
        line_height = _mm_to_internal(5.0)

    panel_padding = _mm_to_internal(4.0)
    x = summary_min_x + panel_padding
    content_max_x = summary_max_x - panel_padding
    text_width = max(_mm_to_internal(58.0), content_max_x - x)
    panel_height = summary_max_y - summary_min_y
    created_notes = 0
    created_lines = 0

    _timestamp, created_text, report_id = _get_report_timestamp_parts(
        selected_options
    )
    source_plan_name = selected_options.get("source_plan_view_name", u"N/A")
    point_cloud_name = selected_options.get("point_cloud_name", u"N/A")
    scope_label = selected_options.get("analysis_scope_label", u"N/A")

    def shorten(value, max_chars):
        text = _to_text(value)
        if len(text) <= max_chars:
            return text
        if max_chars <= 3:
            return text[:max_chars]
        return text[:max_chars - 3] + u"..."

    def add_note(x_pos, y_pos, width, text, size_key, text_size_mm, alignment=None):
        note = _create_report_text_note(
            doc,
            sheet,
            _create_xyz(x_pos, y_pos, 0.0),
            width,
            text,
            size_key,
            text_size_mm,
            alignment
        )
        return 1 if note is not None else 0

    def add_rule(y_pos, x_start=None, x_end=None):
        if x_start is None:
            x_start = x
        if x_end is None:
            x_end = content_max_x
        rule = _create_sheet_separator_line(
            doc,
            sheet,
            _create_xyz(x_start, y_pos, 0.0),
            _create_xyz(x_end, y_pos, 0.0)
        )
        return 1 if rule is not None else 0

    def section_bounds(top_ratio, bottom_ratio):
        top = summary_max_y - (panel_height * top_ratio)
        bottom = summary_max_y - (panel_height * bottom_ratio)
        return top, bottom

    def add_section_header(title, top):
        y = top - _mm_to_internal(2.0)
        count_notes = add_note(
            x,
            y,
            text_width,
            title,
            u"section",
            section_size
        )
        line_y = y - _mm_to_internal(3.4)
        count_lines = add_rule(line_y)
        return count_notes, count_lines, line_y - _mm_to_internal(3.0)

    # A. Header / Report Info
    zone_top, zone_bottom = section_bounds(0.00, 0.17)
    y = zone_top - _mm_to_internal(3.0)
    created_notes += add_note(
        x,
        y,
        text_width,
        u"SCAN QC REPORT",
        u"title",
        title_size
    )
    y -= line_height
    created_notes += add_note(
        x,
        y,
        text_width,
        u"Created: {0}".format(created_text),
        u"body",
        body_size
    )
    y -= line_height
    created_notes += add_note(
        x,
        y,
        text_width,
        u"Report ID: {0}".format(report_id),
        u"body",
        body_size
    )
    created_lines += add_rule(zone_bottom + _mm_to_internal(1.0))

    # B. Project / Source
    zone_top, zone_bottom = section_bounds(0.17, 0.38)
    note_count, line_count, y = add_section_header(u"PROJECT / SOURCE", zone_top)
    created_notes += note_count
    created_lines += line_count
    project_lines = [
        u"Project: {0}".format(shorten(_get_project_name(doc), 38)),
        u"Source: {0}".format(shorten(source_plan_name, 38)),
        u"Point Cloud: {0}".format(shorten(point_cloud_name, 34)),
        u"Scope: {0}".format(shorten(scope_label, 34))
    ]
    for line_text in project_lines:
        if y <= zone_bottom + _mm_to_internal(3.0):
            break
        created_notes += add_note(x, y, text_width, line_text, u"body", body_size)
        y -= line_height
    created_lines += add_rule(zone_bottom + _mm_to_internal(1.0))

    # C. Tolerance
    zone_top, zone_bottom = section_bounds(0.38, 0.54)
    note_count, line_count, y = add_section_header(u"TOLERANCE", zone_top)
    created_notes += note_count
    created_lines += line_count
    tolerance_rows = _build_tolerance_chip_data(selected_options)
    label_width = text_width * 0.34
    value_x = x + label_width
    value_width = text_width - label_width
    for row in tolerance_rows:
        if y <= zone_bottom + _mm_to_internal(3.0):
            break
        created_notes += add_note(x, y, label_width, row[0], u"table_body", table_size)
        created_notes += add_note(
            value_x,
            y,
            value_width,
            row[1],
            u"table_body",
            table_size
        )
        y -= line_height
    created_lines += add_rule(zone_bottom + _mm_to_internal(1.0))

    # D. Result Count
    zone_top, zone_bottom = section_bounds(0.54, 0.66)
    note_count, line_count, y = add_section_header(u"RESULT COUNT", zone_top)
    created_notes += note_count
    created_lines += line_count
    count_text = _build_result_count_text(plan_preview)
    top_n_text = u"Top N Callouts: {0}".format(
        selected_options.get("top_n_callouts", u"N/A")
    )
    for line_text in (count_text, top_n_text):
        if y <= zone_bottom + _mm_to_internal(2.0):
            break
        created_notes += add_note(x, y, text_width, line_text, u"body", body_size)
        y -= line_height
    created_lines += add_rule(zone_bottom + _mm_to_internal(1.0))

    # E. ID Mapping
    zone_top, zone_bottom = section_bounds(0.66, 1.00)
    note_count, line_count, y = add_section_header(u"ID MAPPING", zone_top)
    created_notes += note_count
    created_lines += line_count
    table_top = y
    col_id_x = x
    col_wall_x = x + (text_width * 0.14)
    col_p75_x = x + (text_width * 0.54)
    col_status_x = x + (text_width * 0.72)
    created_notes += add_note(col_id_x, table_top, text_width * 0.10, u"ID", u"table_header", table_size)
    created_notes += add_note(col_wall_x, table_top, text_width * 0.36, u"Wall ID", u"table_header", table_size)
    created_notes += add_note(col_p75_x, table_top, text_width * 0.15, u"P75", u"table_header", table_size)
    created_notes += add_note(col_status_x, table_top, text_width * 0.26, u"Status", u"table_header", table_size)
    y = table_top - _mm_to_internal(3.4)
    created_lines += add_rule(y)
    y -= _mm_to_internal(3.6)
    row_height = line_height
    max_rows = int(max(0.0, (y - zone_bottom - _mm_to_internal(5.0)) / row_height))
    visible_rows = id_rows[:max_rows]
    if not visible_rows:
        created_notes += add_note(
            x,
            y,
            text_width,
            u"No Review/Critical callouts",
            u"body",
            body_size
        )
    else:
        for row in visible_rows:
            created_notes += add_note(col_id_x, y, text_width * 0.10, shorten(row[0], 3), u"table_body", table_size)
            created_notes += add_note(col_wall_x, y, text_width * 0.36, shorten(row[1], 14), u"table_body", table_size)
            created_notes += add_note(col_p75_x, y, text_width * 0.15, shorten(row[2], 7), u"table_body", table_size)
            created_notes += add_note(col_status_x, y, text_width * 0.26, shorten(row[3], 6), u"table_body", table_size)
            y -= row_height
        hidden_count = remaining_id_count + max(0, len(id_rows) - len(visible_rows))
        if hidden_count and y > zone_bottom + _mm_to_internal(2.0):
            created_notes += add_note(
                x,
                y,
                text_width,
                u"+ {0} more".format(hidden_count),
                u"small",
                table_size
            )

    result["summary_textnote_count"] = created_notes
    result["summary_separator_count"] = (
        result.get("summary_separator_count", 0) + created_lines
    )
    if created_notes <= 0:
        result["warnings"].append(
            u"Report Summary table TextNotes could not be created."
        )


def _add_summary_table_to_sheet(
    doc,
    sheet,
    source_plan_view,
    selected_options,
    view_creation_result,
    summary_min_x,
    summary_min_y,
    summary_max_x,
    summary_max_y,
    result
):
    """Create a fixed-grid dashboard Summary Panel with SQCR text styles."""
    plan_preview = _get_plan_preview(view_creation_result)
    id_rows, remaining_id_count = _build_id_mapping_rows(
        view_creation_result,
        selected_options
    )
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        title_size = 4.0
        section_size = 2.45
        body_size = 2.05
        table_size = 1.9
        row_height = _mm_to_internal(5.2)
        section_line_gap = _mm_to_internal(2.2)
        body_start_gap = _mm_to_internal(3.1)
    else:
        title_size = 3.65
        section_size = 2.25
        body_size = 1.85
        table_size = 1.72
        row_height = _mm_to_internal(4.65)
        section_line_gap = _mm_to_internal(1.9)
        body_start_gap = _mm_to_internal(2.7)

    panel_padding = _mm_to_internal(4.0)
    card_padding = _mm_to_internal(2.6)
    x = summary_min_x + panel_padding
    content_max_x = summary_max_x - panel_padding
    text_width = max(_mm_to_internal(58.0), content_max_x - x)
    panel_height = summary_max_y - summary_min_y
    created_notes = 0
    created_lines = 0

    _timestamp, created_text, report_id = _get_report_timestamp_parts(
        selected_options
    )
    source_plan_name = selected_options.get("source_plan_view_name", u"N/A")
    point_cloud_name = selected_options.get("point_cloud_name", u"N/A")
    scope_label = selected_options.get("analysis_scope_label", u"N/A")

    def shorten(value, max_chars):
        text = _to_text(value)
        if len(text) <= max_chars:
            return text
        if max_chars <= 3:
            return text[:max_chars]
        return text[:max_chars - 3] + u"..."

    def add_note(x_pos, y_pos, width, text, size_key, text_size_mm, alignment=None):
        note = _create_report_text_note(
            doc,
            sheet,
            _create_xyz(x_pos, y_pos, 0.0),
            width,
            text,
            size_key,
            text_size_mm,
            alignment
        )
        return 1 if note is not None else 0

    def add_rule(y_pos, x_start=None, x_end=None):
        if x_start is None:
            x_start = x
        if x_end is None:
            x_end = content_max_x
        rule = _create_sheet_separator_line(
            doc,
            sheet,
            _create_xyz(x_start, y_pos, 0.0),
            _create_xyz(x_end, y_pos, 0.0)
        )
        return 1 if rule is not None else 0

    def zone(top_ratio, bottom_ratio):
        top = summary_max_y - (panel_height * top_ratio)
        bottom = summary_max_y - (panel_height * bottom_ratio)
        return top, bottom

    def add_block_header(title, top):
        header_y = top - card_padding
        note_count = add_note(
            x,
            header_y,
            text_width,
            title,
            u"section",
            section_size
        )
        rule_y = header_y - section_line_gap
        line_count = add_rule(rule_y)
        body_y = rule_y - body_start_gap
        return note_count, line_count, body_y

    label_width = text_width * 0.34
    value_x = x + label_width + _mm_to_internal(1.5)
    value_width = max(_mm_to_internal(24.0), content_max_x - value_x)

    def add_key_value_rows(rows, top_ratio, bottom_ratio, title):
        created_note_count = 0
        created_line_count = 0
        top, bottom = zone(top_ratio, bottom_ratio)
        notes, lines_created, y_pos = add_block_header(title, top)
        created_note_count += notes
        created_line_count += lines_created
        for row in rows:
            if y_pos <= bottom + _mm_to_internal(2.0):
                break
            created_note_count += add_note(
                x,
                y_pos,
                label_width,
                row[0],
                u"body",
                body_size
            )
            created_note_count += add_note(
                value_x,
                y_pos,
                value_width,
                row[1],
                u"body",
                body_size
            )
            y_pos -= row_height
        return created_note_count, created_line_count

    # Header
    header_top, header_bottom = zone(0.00, 0.18)
    y = header_top - _mm_to_internal(3.0)
    created_notes += add_note(
        x,
        y,
        text_width,
        u"SCAN QC REPORT",
        u"title",
        title_size
    )
    y -= row_height
    created_notes += add_note(
        x,
        y,
        text_width,
        u"Point Cloud Deviation Review",
        u"body",
        body_size
    )
    y -= row_height
    created_notes += add_note(
        x,
        y,
        text_width,
        u"Report ID: {0}".format(report_id),
        u"body",
        body_size
    )
    y -= row_height
    created_notes += add_note(
        x,
        y,
        text_width,
        u"Created: {0}".format(created_text),
        u"body",
        body_size
    )
    created_lines += add_rule(header_bottom + _mm_to_internal(1.2))

    # Project / Source
    notes, lines_created = add_key_value_rows(
        [
            [u"Project", shorten(_get_project_name(doc), 34)],
            [u"Source", shorten(source_plan_name, 34)],
            [u"Point Cloud", shorten(point_cloud_name, 30)],
            [u"Scope", shorten(scope_label, 30)]
        ],
        0.18,
        0.38,
        u"PROJECT / SOURCE"
    )
    created_notes += notes
    created_lines += lines_created

    # Tolerance
    tol_top, tol_bottom = zone(0.38, 0.53)
    notes, lines_created, y = add_block_header(u"TOLERANCE", tol_top)
    created_notes += notes
    created_lines += lines_created
    tolerance_rows = _build_tolerance_chip_data(selected_options)
    for row in tolerance_rows:
        if y <= tol_bottom + _mm_to_internal(2.0):
            break
        created_notes += add_note(x, y, label_width, row[0], u"body", body_size)
        created_notes += add_note(
            value_x,
            y,
            value_width,
            row[1],
            u"body",
            body_size
        )
        y -= row_height

    # Result Count as aligned 2-column rows
    result_top, result_bottom = zone(0.53, 0.68)
    notes, lines_created, y = add_block_header(u"RESULT COUNT", result_top)
    created_notes += notes
    created_lines += lines_created
    status_rows = [
        [u"OK", plan_preview.get("ok_count", 0)],
        [u"REVIEW", plan_preview.get("review_count", 0)],
        [u"CRITICAL", plan_preview.get("critical_count", 0)]
    ]
    for status_row in status_rows:
        if y <= result_bottom + _mm_to_internal(2.0):
            break
        created_notes += add_note(
            x,
            y,
            label_width,
            status_row[0],
            u"body",
            body_size
        )
        created_notes += add_note(
            value_x,
            y,
            value_width,
            _to_text(status_row[1]),
            u"body",
            body_size,
            HorizontalTextAlignment.Right
        )
        y -= row_height

    # ID Mapping table
    id_top, id_bottom = zone(0.68, 0.88)
    notes, lines_created, y = add_block_header(u"ID MAPPING", id_top)
    created_notes += notes
    created_lines += lines_created
    col_id_x = x
    col_wall_x = x + (text_width * 0.14)
    col_p75_x = x + (text_width * 0.55)
    col_status_x = x + (text_width * 0.73)
    created_notes += add_note(col_id_x, y, text_width * 0.10, u"ID", u"table_header", table_size)
    created_notes += add_note(col_wall_x, y, text_width * 0.36, u"WALL ID", u"table_header", table_size)
    created_notes += add_note(col_p75_x, y, text_width * 0.15, u"P75", u"table_header", table_size, HorizontalTextAlignment.Right)
    created_notes += add_note(col_status_x, y, text_width * 0.24, u"STATUS", u"table_header", table_size)
    y -= _mm_to_internal(3.2)
    created_lines += add_rule(y)
    y -= _mm_to_internal(3.2)
    max_rows = int(max(0.0, (y - id_bottom - _mm_to_internal(2.0)) / row_height))
    visible_rows = id_rows[:max_rows]
    if not visible_rows:
        created_notes += add_note(
            x,
            y,
            text_width,
            u"No Review/Critical callouts",
            u"body",
            body_size
        )
    else:
        for row in visible_rows:
            created_notes += add_note(col_id_x, y, text_width * 0.10, shorten(row[0], 3), u"table_body", table_size)
            created_notes += add_note(col_wall_x, y, text_width * 0.36, shorten(row[1], 14), u"table_body", table_size)
            created_notes += add_note(col_p75_x, y, text_width * 0.15, shorten(row[2], 7), u"table_body", table_size, HorizontalTextAlignment.Right)
            created_notes += add_note(col_status_x, y, text_width * 0.24, shorten(row[3], 4), u"table_body", table_size)
            y -= row_height
        hidden_count = remaining_id_count + max(0, len(id_rows) - len(visible_rows))
        if hidden_count and y > id_bottom + _mm_to_internal(1.5):
            created_notes += add_note(
                x,
                y,
                text_width,
                u"+ {0} more".format(hidden_count),
                u"body",
                body_size
            )

    # Method / Note uses the lower panel area instead of leaving empty space
    note_top, note_bottom = zone(0.88, 1.00)
    notes, lines_created, y = add_block_header(u"METHOD / NOTE", note_top)
    created_notes += notes
    created_lines += lines_created
    method_lines = [
        u"Wall-face corrected distance",
        u"P75-based severity classification",
        u"Top N Review/Critical callouts"
    ]
    for line_text in method_lines:
        if y <= note_bottom + _mm_to_internal(1.0):
            break
        created_notes += add_note(x, y, text_width, line_text, u"body", body_size)
        y -= row_height

    result["summary_textnote_count"] = created_notes
    result["summary_separator_count"] = (
        result.get("summary_separator_count", 0) + created_lines
    )
    if created_notes <= 0:
        result["warnings"].append(
            u"Report Summary dashboard TextNotes could not be created."
        )


def _add_summary_table_to_sheet(
    doc,
    sheet,
    source_plan_view,
    selected_options,
    view_creation_result,
    summary_min_x,
    summary_min_y,
    summary_max_x,
    summary_max_y,
    result
):
    """Create a fixed section-grid Summary Panel.

    The panel uses fixed section heights and relative coordinates inside each
    section so section rules never share the same Y position as titles.
    """
    plan_preview = _get_plan_preview(view_creation_result)
    id_rows, remaining_id_count = _build_id_mapping_rows(
        view_creation_result,
        selected_options
    )
    paper_size = _get_paper_size(selected_options)
    if paper_size == u"A2 Landscape":
        title_size = 3.5
        subtitle_size = 1.8
        meta_size = 1.9
        section_size = 2.2
        body_size = 2.0
        table_header_size = 1.95
        table_body_size = 1.85
        body_row_height = _mm_to_internal(5.1)
        table_row_height = _mm_to_internal(4.6)
        section_gap = _mm_to_internal(9.0)
    else:
        title_size = 3.35
        subtitle_size = 1.7
        meta_size = 1.8
        section_size = 2.1
        body_size = 1.9
        table_header_size = 1.85
        table_body_size = 1.78
        body_row_height = _mm_to_internal(4.8)
        table_row_height = _mm_to_internal(4.3)
        section_gap = _mm_to_internal(8.0)

    panel_left_padding = _mm_to_internal(4.0)
    panel_right_padding = _mm_to_internal(4.0)
    section_top_padding = _mm_to_internal(3.0)
    title_to_line_gap = _mm_to_internal(section_size + 2.8)
    line_to_body_gap = _mm_to_internal(3.2)
    section_bottom_padding = max(_mm_to_internal(2.0), section_gap * 0.25)
    column_gap = _mm_to_internal(2.0)
    section_line_weight = 1

    x = summary_min_x + panel_left_padding
    content_max_x = summary_max_x - panel_right_padding
    text_width = max(_mm_to_internal(58.0), content_max_x - x)
    panel_height = summary_max_y - summary_min_y
    created_notes = 0
    created_lines = 0

    _timestamp, created_text, report_id = _get_report_timestamp_parts(
        selected_options
    )
    source_plan_name = selected_options.get("source_plan_view_name", u"N/A")
    point_cloud_name = selected_options.get("point_cloud_name", u"N/A")
    scope_label = selected_options.get("analysis_scope_label", u"N/A")

    def shorten(value, max_chars):
        text = _to_text(value)
        if len(text) <= max_chars:
            return text
        if max_chars <= 3:
            return text[:max_chars]
        return text[:max_chars - 3] + u"..."

    def add_note(x_pos, y_pos, width, text, size_key, text_size_mm, alignment=None):
        note = _create_report_text_note(
            doc,
            sheet,
            _create_xyz(x_pos, y_pos, 0.0),
            width,
            text,
            size_key,
            text_size_mm,
            alignment
        )
        return 1 if note is not None else 0

    def add_rule(y_pos, x_start=None, x_end=None):
        if x_start is None:
            x_start = x
        if x_end is None:
            x_end = content_max_x
        rule = _create_sheet_separator_line(
            doc,
            sheet,
            _create_xyz(x_start, y_pos, 0.0),
            _create_xyz(x_end, y_pos, 0.0),
            section_line_weight
        )
        return 1 if rule is not None else 0

    def next_section(y_cursor, ratio):
        section_height = panel_height * ratio
        section_top = y_cursor
        section_bottom = y_cursor - section_height
        return section_top, section_bottom

    def draw_section_header(title, section_top):
        title_y = section_top - section_top_padding
        note_count = add_note(
            x,
            title_y,
            text_width,
            title,
            u"section",
            section_size
        )
        line_y = title_y - title_to_line_gap
        line_count = add_rule(line_y)
        body_y = line_y - line_to_body_gap
        return note_count, line_count, body_y

    label_width = text_width * 0.34
    value_x = x + label_width + column_gap
    value_width = max(_mm_to_internal(24.0), content_max_x - value_x)

    def draw_key_value_section(title, rows, section_top, section_bottom):
        note_count, line_count, y_pos = draw_section_header(title, section_top)
        min_y = section_bottom + section_bottom_padding
        for row in rows:
            if y_pos <= min_y:
                break
            note_count += add_note(
                x,
                y_pos,
                label_width,
                row[0],
                u"body",
                body_size
            )
            note_count += add_note(
                value_x,
                y_pos,
                value_width,
                row[1],
                u"body",
                body_size
            )
            y_pos -= body_row_height
        return note_count, line_count

    # Fixed section grid ratios. The cursor advances from panel top to bottom.
    section_ratios = [
        (u"HEADER", 0.16),
        (u"PROJECT / SOURCE", 0.22),
        (u"TOLERANCE", 0.13),
        (u"RESULT COUNT", 0.13),
        (u"ID MAPPING", 0.26),
        (u"METHOD / NOTE", 0.10)
    ]
    y_cursor = summary_max_y
    section_bounds = {}
    for title, ratio in section_ratios:
        section_top, section_bottom = next_section(y_cursor, ratio)
        section_bounds[title] = (section_top, section_bottom)
        y_cursor = section_bottom

    # A. Header
    header_top, header_bottom = section_bounds[u"HEADER"]
    header_title_y = header_top - section_top_padding
    created_notes += add_note(
        x,
        header_title_y,
        text_width,
        u"SCAN QC REPORT",
        u"title",
        title_size
    )
    header_line_y = header_title_y - title_to_line_gap
    created_lines += add_rule(header_line_y)
    y = header_line_y - line_to_body_gap
    header_rows = [
        [u"Point Cloud Deviation Review", u"subtitle", subtitle_size],
        [u"Report ID: {0}".format(report_id), u"meta", meta_size],
        [u"Created: {0}".format(created_text), u"meta", meta_size]
    ]
    for row in header_rows:
        if y <= header_bottom + section_bottom_padding:
            break
        created_notes += add_note(x, y, text_width, row[0], row[1], row[2])
        y -= body_row_height

    # B. Project / Source
    notes, lines_created = draw_key_value_section(
        u"PROJECT / SOURCE",
        [
            [u"Project", shorten(_get_project_name(doc), 34)],
            [u"Source", shorten(source_plan_name, 34)],
            [u"Point Cloud", shorten(point_cloud_name, 30)],
            [u"Scope", shorten(scope_label, 30)],
            [
                u"Target Filter",
                shorten(plan_preview.get("target_wall_filter_summary", u"None"), 42)
            ]
        ],
        section_bounds[u"PROJECT / SOURCE"][0],
        section_bounds[u"PROJECT / SOURCE"][1]
    )
    created_notes += notes
    created_lines += lines_created

    # C. Tolerance
    notes, lines_created = draw_key_value_section(
        u"TOLERANCE",
        _build_tolerance_chip_data(selected_options),
        section_bounds[u"TOLERANCE"][0],
        section_bounds[u"TOLERANCE"][1]
    )
    created_notes += notes
    created_lines += lines_created

    # D. Result Count
    notes, lines_created = draw_key_value_section(
        u"RESULT COUNT",
        [
            [u"OK", _to_text(plan_preview.get("ok_count", 0))],
            [u"Review", _to_text(plan_preview.get("review_count", 0))],
            [u"Critical", _to_text(plan_preview.get("critical_count", 0))]
        ],
        section_bounds[u"RESULT COUNT"][0],
        section_bounds[u"RESULT COUNT"][1]
    )
    created_notes += notes
    created_lines += lines_created

    # E. ID Mapping
    id_top, id_bottom = section_bounds[u"ID MAPPING"]
    notes, lines_created, y = draw_section_header(u"ID MAPPING", id_top)
    created_notes += notes
    created_lines += lines_created
    min_id_y = id_bottom + section_bottom_padding
    col_id_x = x
    col_wall_x = x + (text_width * 0.14)
    col_p75_x = x + (text_width * 0.56)
    col_status_x = x + (text_width * 0.75)
    col_id_w = text_width * 0.10
    col_wall_w = text_width * 0.36
    col_p75_w = text_width * 0.15
    col_status_w = text_width * 0.23

    if y > min_id_y:
        created_notes += add_note(
            col_id_x,
            y,
            col_id_w,
            u"ID",
            u"table_header",
            table_header_size
        )
        created_notes += add_note(
            col_wall_x,
            y,
            col_wall_w,
            u"WALL ID",
            u"table_header",
            table_header_size
        )
        created_notes += add_note(
            col_p75_x,
            y,
            col_p75_w,
            u"P75",
            u"table_header",
            table_header_size,
            HorizontalTextAlignment.Right
        )
        created_notes += add_note(
            col_status_x,
            y,
            col_status_w,
            u"STATUS",
            u"table_header",
            table_header_size
        )
        y -= table_row_height

    available_rows = int(max(0.0, (y - min_id_y) / table_row_height))
    max_visible_rows = min(len(id_rows), available_rows)
    visible_rows = id_rows[:max_visible_rows]

    if not visible_rows and y > min_id_y:
        created_notes += add_note(
            x,
            y,
            text_width,
            u"No Review/Critical callouts",
            u"body",
            body_size
        )
    else:
        for row in visible_rows:
            if y <= min_id_y:
                break
            created_notes += add_note(
                col_id_x,
                y,
                col_id_w,
                shorten(row[0], 3),
                u"table_body",
                table_body_size
            )
            created_notes += add_note(
                col_wall_x,
                y,
                col_wall_w,
                shorten(row[1], 14),
                u"table_body",
                table_body_size
            )
            created_notes += add_note(
                col_p75_x,
                y,
                col_p75_w,
                shorten(row[2], 7),
                u"table_body",
                table_body_size,
                HorizontalTextAlignment.Right
            )
            created_notes += add_note(
                col_status_x,
                y,
                col_status_w,
                shorten(row[3], 4),
                u"table_body",
                table_body_size
            )
            y -= table_row_height

    hidden_count = (
        remaining_id_count
        + max(0, len(id_rows) - len(visible_rows))
    )
    if hidden_count and y > min_id_y:
        created_notes += add_note(
            x,
            y,
            text_width,
            u"+ {0} more".format(hidden_count),
            u"body",
            body_size
        )

    # F. Method / Note pinned to the bottom section.
    note_top, note_bottom = section_bounds[u"METHOD / NOTE"]
    notes, lines_created, y = draw_section_header(u"METHOD / NOTE", note_top)
    created_notes += notes
    created_lines += lines_created
    min_note_y = note_bottom + section_bottom_padding
    method_lines = [
        u"Wall-face corrected distance",
        u"P75-based severity classification",
        u"Top N Review/Critical callouts"
    ]
    for line_text in method_lines:
        if y <= min_note_y:
            break
        created_notes += add_note(
            x,
            y,
            text_width,
            line_text,
            u"body",
            body_size
        )
        y -= body_row_height

    result["summary_textnote_count"] = created_notes
    result["summary_separator_count"] = (
        result.get("summary_separator_count", 0) + created_lines
    )
    if created_notes <= 0:
        result["warnings"].append(
            u"Report Summary fixed-grid TextNotes could not be created."
        )


def _create_viewport(doc, sheet, plan_view, center):
    if Viewport is None or plan_view is None:
        return None, u"Viewport API or QC Plan View was unavailable."

    try:
        if hasattr(Viewport, "CanAddViewToSheet"):
            can_add = Viewport.CanAddViewToSheet(doc, sheet.Id, plan_view.Id)
            if not can_add:
                return None, u"QC Plan View could not be added to the Report Sheet."
    except Exception:
        pass

    try:
        return Viewport.Create(doc, sheet.Id, plan_view.Id, center), u""
    except Exception as ex:
        return None, u"QC Plan Viewport creation failed: {0}".format(_to_text(ex))


def _get_viewport_box_outline(viewport):
    if viewport is None:
        return None
    try:
        return viewport.GetBoxOutline()
    except Exception:
        return None


def _outline_min_max(outline):
    if outline is None:
        return None

    try:
        minimum = outline.MinimumPoint
        maximum = outline.MaximumPoint
        return minimum.X, minimum.Y, maximum.X, maximum.Y
    except Exception:
        pass

    try:
        return outline.Min.U, outline.Min.V, outline.Max.U, outline.Max.V
    except Exception:
        pass

    return None


def _get_viewport_box_size(viewport):
    values = _outline_min_max(_get_viewport_box_outline(viewport))
    if not values:
        return None, None
    min_x, min_y, max_x, max_y = values
    return max_x - min_x, max_y - min_y


def _get_viewport_box_center(viewport):
    values = _outline_min_max(_get_viewport_box_outline(viewport))
    if not values:
        return None
    min_x, min_y, max_x, max_y = values
    return _create_xyz(
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        0.0
    )


def _move_viewport_center(doc, viewport, target_center):
    if viewport is None or target_center is None:
        return

    try:
        viewport.SetBoxCenter(target_center)
        return
    except Exception:
        pass

    if ElementTransformUtils is None:
        return

    current_center = _get_viewport_box_center(viewport)
    if current_center is None:
        return

    try:
        translation = target_center.Subtract(current_center)
        ElementTransformUtils.MoveElement(doc, viewport.Id, translation)
    except Exception:
        pass


def _is_generated_scan_qc_plan_view(plan_view):
    if plan_view is None:
        return False
    try:
        return _to_text(plan_view.Name).startswith(u"SCAN_QC_PLAN_")
    except Exception:
        return False


def _get_plan_view_model_size(plan_view):
    if plan_view is None:
        return None, None

    crop_box = None
    try:
        crop_box = plan_view.CropBox
    except Exception:
        crop_box = None

    if crop_box is not None:
        try:
            min_point = crop_box.Min
            max_point = crop_box.Max
            width = abs(float(max_point.X) - float(min_point.X))
            height = abs(float(max_point.Y) - float(min_point.Y))
            if width > 0.0 and height > 0.0:
                return width, height
        except Exception:
            pass

    try:
        bounding_box = plan_view.get_BoundingBox(plan_view)
        if bounding_box is not None:
            min_point = bounding_box.Min
            max_point = bounding_box.Max
            width = abs(float(max_point.X) - float(min_point.X))
            height = abs(float(max_point.Y) - float(min_point.Y))
            if width > 0.0 and height > 0.0:
                return width, height
    except Exception:
        pass

    return None, None


def _choose_report_view_scale(plan_view, target_width, target_height):
    model_width, model_height = _get_plan_view_model_size(plan_view)
    if (
        model_width is None
        or model_height is None
        or model_width <= 0.0
        or model_height <= 0.0
        or target_width <= 0.0
        or target_height <= 0.0
    ):
        return None, u"View crop/model size unavailable"

    for candidate in REPORT_SCALE_CANDIDATES:
        sheet_width = model_width / float(candidate)
        sheet_height = model_height / float(candidate)
        if sheet_width <= target_width and sheet_height <= target_height:
            return candidate, u"Crop/model extent fit"

    required_scale = max(model_width / target_width, model_height / target_height)
    fallback_scale = int(math.ceil(required_scale / 25.0) * 25)
    fallback_scale = max(REPORT_SCALE_CANDIDATES[-1], fallback_scale)
    return fallback_scale, u"Computed fallback; candidate scales exceeded area"


def _fit_viewport_to_area(doc, plan_view, viewport, target_width, target_height, result):
    try:
        current_scale = int(plan_view.Scale)
    except Exception:
        current_scale = 0

    if current_scale > 0:
        result["viewport_scale"] = current_scale

    if not _is_generated_scan_qc_plan_view(plan_view):
        result["viewport_scale_source"] = u"Skipped; not a generated SCAN_QC_PLAN_* view"
        return

    selected_scale, scale_source = _choose_report_view_scale(
        plan_view,
        target_width,
        target_height
    )
    if selected_scale is None:
        result["viewport_scale_source"] = scale_source
        result["warnings"].append(
            u"Viewport scale could not be selected automatically: {0}".format(
                scale_source
            )
        )
        return

    try:
        if current_scale != selected_scale:
            plan_view.Scale = selected_scale
        result["viewport_scale"] = selected_scale
        result["viewport_scale_source"] = scale_source
        doc.Regenerate()
    except Exception as ex:
        result["warnings"].append(
            u"Viewport scale could not be adjusted automatically: {0}".format(
                _to_text(ex)
            )
        )


def _set_integer_parameter_to_zero(element, parameter_names):
    if element is None:
        return False

    for parameter_name in parameter_names:
        try:
            parameter = element.LookupParameter(parameter_name)
            if parameter is None or parameter.IsReadOnly:
                continue
            try:
                storage_type = parameter.StorageType
                if StorageType is not None and storage_type != StorageType.Integer:
                    continue
            except Exception:
                pass
            parameter.Set(0)
            return True
        except Exception:
            pass

    return False


def _try_hide_viewport_title(doc, viewport, result):
    if viewport is None:
        return

    result["viewport_title_status"] = u"Attempted"
    try:
        viewport_type = doc.GetElement(viewport.GetTypeId())
    except Exception:
        viewport_type = None

    target_type = viewport_type
    try:
        if viewport_type is not None:
            base_name = u"SCAN_QC_NO_TITLE"
            current_name = _to_text(viewport_type.Name)
            if base_name not in current_name:
                new_name = base_name
                suffix = 2
                while True:
                    try:
                        target_type = viewport_type.Duplicate(new_name)
                        break
                    except Exception:
                        new_name = u"{0}_{1}".format(base_name, suffix)
                        suffix += 1
                        if suffix > 30:
                            target_type = viewport_type
                            break
                try:
                    if target_type is not None and target_type.Id != viewport.GetTypeId():
                        viewport.ChangeTypeId(target_type.Id)
                except Exception:
                    pass
    except Exception:
        target_type = viewport_type

    parameter_names = [
        u"Show Title",
        u"Show View Title",
        u"View Title",
        u"Show Label"
    ]
    if _set_integer_parameter_to_zero(target_type, parameter_names):
        result["viewport_title_hidden"] = True
        result["viewport_title_status"] = u"Hidden by viewport type parameter"
        return

    try:
        if BuiltInParameter is not None:
            parameter = viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_SHOW_LABEL)
            if parameter is not None and not parameter.IsReadOnly:
                parameter.Set(0)
                result["viewport_title_hidden"] = True
                result["viewport_title_status"] = u"Hidden by viewport parameter"
                return
    except Exception:
        pass

    result["viewport_title_status"] = u"Could not hide automatically"
    result["warnings"].append(
        u"Viewport title could not be hidden automatically. "
        u"If the title is still visible, use a no-title Viewport Type manually."
    )


def _add_report_content_to_sheet(
    doc,
    sheet,
    source_plan_view,
    plan_view,
    selected_options,
    view_creation_result,
    result
):
    min_x, min_y, max_x, max_y = _get_sheet_outline(sheet, selected_options)
    width = max_x - min_x
    height = max_y - min_y
    layout_profile = _get_layout_profile(selected_options)
    result["paper_size"] = layout_profile["paper_size"]
    margin_x = _mm_to_internal(layout_profile["margin_x_mm"])
    margin_y = _mm_to_internal(layout_profile["margin_y_mm"])
    gutter = _mm_to_internal(layout_profile["gutter_mm"])

    content_min_x = min_x + margin_x
    content_max_x = max_x - margin_x
    content_min_y = min_y + margin_y
    content_max_y = max_y - margin_y
    content_width = content_max_x - content_min_x
    content_height = content_max_y - content_min_y

    summary_area_width = content_width * layout_profile["summary_ratio"]
    if summary_area_width < _mm_to_internal(layout_profile["summary_min_width_mm"]):
        summary_area_width = _mm_to_internal(layout_profile["summary_min_width_mm"])
        viewport_area_width = max(
            _mm_to_internal(120.0),
            content_width - summary_area_width - gutter
        )
    else:
        viewport_area_width = content_width - summary_area_width - gutter
    result["summary_panel_width_mm"] = _format_mm(summary_area_width * FT_TO_MM)

    viewport_min_x = content_min_x
    viewport_max_x = viewport_min_x + viewport_area_width
    summary_min_x = viewport_max_x + gutter
    summary_max_x = content_max_x
    viewport_area_height = content_height

    border_count = _add_rectangle_lines(
        doc,
        sheet,
        content_min_x,
        content_min_y,
        content_max_x,
        content_max_y,
        line_weight=3
    )
    separator_line = _create_sheet_separator_line(
        doc,
        sheet,
        _create_xyz(summary_min_x - (gutter * 0.50), content_min_y, 0.0),
        _create_xyz(summary_min_x - (gutter * 0.50), content_max_y, 0.0),
        line_weight=2
    )
    if separator_line is not None:
        border_count += 1
    if border_count:
        result["summary_separator_count"] = (
            result.get("summary_separator_count", 0) + border_count
        )
    else:
        result["warnings"].append(
            u"Scan QC Report border/detail lines could not be created."
        )

    viewport_center = _create_xyz(
        viewport_min_x + (viewport_area_width * 0.50),
        content_min_y + (viewport_area_height * 0.50),
        0.0
    )
    viewport, viewport_error = _create_viewport(
        doc,
        sheet,
        plan_view,
        viewport_center
    )
    if viewport is not None:
        result["viewport_created"] = True
        result["viewport_id"] = viewport.Id
        doc.Regenerate()
        _fit_viewport_to_area(
            doc,
            plan_view,
            viewport,
            viewport_area_width * 0.96,
            viewport_area_height * 0.96,
            result
        )
        _move_viewport_center(doc, viewport, viewport_center)
        _try_hide_viewport_title(doc, viewport, result)
    elif viewport_error:
        result["warnings"].append(viewport_error)

    _add_summary_table_to_sheet(
        doc,
        sheet,
        source_plan_view,
        selected_options,
        view_creation_result,
        summary_min_x,
        content_min_y,
        summary_max_x,
        content_max_y,
        result
    )


def _find_sheet_by_id(doc, sheet_id):
    if sheet_id in (None, u"", u"N/A"):
        return None
    try:
        target_text = _to_text(sheet_id)
        for sheet in collect_report_sheets(doc):
            if _to_text(getattr(sheet.Id, "IntegerValue", sheet.Id)) == target_text:
                return sheet
            try:
                if _to_text(sheet.Id.Value) == target_text:
                    return sheet
            except Exception:
                pass
    except Exception:
        pass
    return None


def _create_report_sheet_elements(
    doc,
    source_plan_view,
    plan_view,
    selected_options,
    view_creation_result,
    timestamp,
    result
):
    result["report_sheet_mode"] = selected_options.get(
        "report_sheet_mode",
        u"create_new"
    )
    result["report_sheet_mode_label"] = selected_options.get(
        "report_sheet_mode_label",
        u"Scan QC Dedicated Sheet"
    )
    if result["report_sheet_mode"] != u"existing":
        result["report_sheet_mode_label"] = u"Scan QC Dedicated Sheet"

    if result["report_sheet_mode"] == u"existing":
        sheet = _find_sheet_by_id(doc, selected_options.get("report_sheet_id"))
        if sheet is None:
            result["failure_reason"] = (
                u"Selected existing Report Sheet was not found."
            )
            result["warnings"].append(result["failure_reason"])
            return None

        transaction = Transaction(doc, "Populate Existing Scan QC Report Sheet")
        transaction_started = False
        try:
            transaction.Start()
            transaction_started = True
            _add_report_content_to_sheet(
                doc,
                sheet,
                source_plan_view,
                plan_view,
                selected_options,
                view_creation_result,
                result
            )
            status = transaction.Commit()
            transaction_started = False
            if status != TransactionStatus.Committed:
                result["failure_reason"] = (
                    u"Existing Report Sheet transaction ended with status: {0}"
                    .format(status)
                )
                return None

            result["report_sheet_created"] = True
            result["sheet_name"] = _to_text(getattr(sheet, "Name", u""))
            result["sheet_number"] = _to_text(getattr(sheet, "SheetNumber", u""))
            result["sheet_id"] = sheet.Id
            return sheet
        except Exception as ex:
            result["failure_reason"] = (
                u"Existing Report Sheet update failed: {0}".format(_to_text(ex))
            )
            result["errors"].append(result["failure_reason"])
            if transaction_started:
                try:
                    transaction.RollBack()
                except Exception:
                    pass
            return None

    sheet_name, sheet_number = _get_unique_sheet_values(doc, timestamp)
    transaction = Transaction(doc, "Create Scan QC Report Sheet")
    transaction_started = False
    sheet = None

    try:
        transaction.Start()
        transaction_started = True

        sheet = _create_dedicated_scan_qc_sheet(doc, result)
        if sheet is None:
            if transaction_started:
                try:
                    transaction.RollBack()
                except Exception:
                    pass
            return None

        try:
            sheet.SheetNumber = sheet_number
        except Exception as ex:
            result["warnings"].append(
                u"Report Sheet number could not be set: {0}".format(_to_text(ex))
            )
        try:
            sheet.Name = sheet_name
        except Exception as ex:
            result["warnings"].append(
                u"Report Sheet name could not be set: {0}".format(_to_text(ex))
            )

        _add_report_content_to_sheet(
            doc,
            sheet,
            source_plan_view,
            plan_view,
            selected_options,
            view_creation_result,
            result
        )

        status = transaction.Commit()
        transaction_started = False
        if status != TransactionStatus.Committed:
            result["failure_reason"] = (
                u"Report Sheet transaction ended with status: {0}".format(status)
            )
            return None

        result["report_sheet_created"] = True
        result["sheet_name"] = sheet_name
        result["sheet_number"] = sheet_number
        result["sheet_id"] = sheet.Id
        return sheet
    except Exception as ex:
        result["failure_reason"] = u"Report Sheet creation failed: {0}".format(
            _to_text(ex)
        )
        result["errors"].append(result["failure_reason"])
        if transaction_started:
            try:
                transaction.RollBack()
            except Exception:
                pass
        return None


def _make_view_id_list(view_id):
    if List is None or ElementId is None:
        return None
    view_ids = List[ElementId]()
    view_ids.Add(view_id)
    return view_ids


def _safe_set_property(instance, property_name, value):
    try:
        setattr(instance, property_name, value)
        return True
    except Exception:
        return False


def _find_pdf_file(output_folder, base_file_name):
    expected_path = os.path.join(output_folder, base_file_name + u".pdf")
    if os.path.isfile(expected_path):
        return expected_path

    try:
        lower_base = base_file_name.lower()
        for file_name in os.listdir(output_folder):
            lower_name = file_name.lower()
            if lower_name.startswith(lower_base) and lower_name.endswith(u".pdf"):
                return os.path.join(output_folder, file_name)
    except Exception:
        pass

    return expected_path


def _export_pdf(doc, sheet, output_folder, base_file_name):
    if PDFExportOptions is None:
        return False, u"", u"PDFExportOptions API was unavailable."

    _ensure_folder(output_folder)
    view_ids = _make_view_id_list(sheet.Id)
    if view_ids is None:
        return False, u"", u"PDF export view id collection could not be created."

    pdf_options = PDFExportOptions()
    errors = []
    try:
        _safe_set_property(pdf_options, "FileName", base_file_name)
        _safe_set_property(pdf_options, "Combine", True)
        _safe_set_property(pdf_options, "StopOnError", False)

        try:
            exported = doc.Export(output_folder, view_ids, pdf_options)
            pdf_path = _find_pdf_file(output_folder, base_file_name)
            if exported and os.path.isfile(pdf_path):
                return True, pdf_path, u""
            errors.append(
                u"doc.Export(folder, viewIds, options) returned {0}; file={1}"
                .format(exported, pdf_path)
            )
        except Exception as ex:
            errors.append(
                u"doc.Export(folder, viewIds, options) failed: {0}".format(
                    _to_text(ex)
                )
            )

        try:
            exported = doc.Export(
                output_folder,
                base_file_name,
                view_ids,
                pdf_options
            )
            pdf_path = _find_pdf_file(output_folder, base_file_name)
            if exported and os.path.isfile(pdf_path):
                return True, pdf_path, u""
            errors.append(
                u"doc.Export(folder, fileName, viewIds, options) returned {0}; "
                u"file={1}".format(exported, pdf_path)
            )
        except Exception as ex:
            errors.append(
                u"doc.Export(folder, fileName, viewIds, options) failed: {0}"
                .format(_to_text(ex))
            )
    finally:
        try:
            pdf_options.Dispose()
        except Exception:
            pass

    return False, u"", u"PDF export failed. {0}".format(u" | ".join(errors))


def _write_latest_report_pointer(reports_root, pdf_path, result):
    if not pdf_path or write_latest_report_path is None:
        return
    try:
        write_latest_report_path(reports_root, pdf_path)
    except Exception as ex:
        result["warnings"].append(
            u"Last Report pointer could not be updated: {0}".format(_to_text(ex))
        )


def create_scan_qc_report(
    doc,
    source_plan_view,
    plan_view,
    selected_options,
    view_creation_result,
    settings
):
    """Create a Scan QC Report Sheet and export PDF when requested.

    This function is intentionally defensive: report failures are returned in the
    result payload and should not stop Scan QC view, marker, or deviation output.
    """
    requested = _safe_bool(selected_options.get("create_pdf_report", False))
    result = _create_result(requested)
    result["pdf_required_qc_plan_view"] = selected_options.get(
        "pdf_required_qc_plan_view",
        u"N/A"
    )
    result["pdf_save_dialog_result"] = selected_options.get(
        "pdf_save_dialog_result",
        u"N/A"
    )
    result["paper_size"] = _get_paper_size(selected_options)
    report_folder, reports_root, report_options = _resolve_report_folder(settings)
    result["image_requested"] = _safe_bool(report_options.get("export_image", False))

    if not requested:
        result["failure_reason"] = u"Not requested"
        if result["image_requested"]:
            result["image_status"] = u"Image export requires PDF Report request."
        return result

    result["attempted"] = True
    if plan_view is None:
        result["failure_reason"] = (
            u"Generated SCAN_QC_PLAN_* View was unavailable. "
            u"Create QC Plan View must be selected before creating a report."
        )
        result["warnings"].append(result["failure_reason"])
        return result

    if ViewSheet is None or Transaction is None:
        result["failure_reason"] = u"Revit Sheet creation API was unavailable."
        result["errors"].append(result["failure_reason"])
        return result

    timestamp = selected_options.get("report_timestamp") or _get_timestamp()
    sheet = _create_report_sheet_elements(
        doc,
        source_plan_view,
        plan_view,
        selected_options,
        view_creation_result,
        timestamp,
        result
    )
    if sheet is None:
        return result

    selected_pdf_path = selected_options.get("pdf_output_path", u"") or u""
    result["requested_pdf_path"] = selected_pdf_path
    if selected_pdf_path:
        result["pdf_path"] = selected_pdf_path
    if selected_options.get("pdf_export_cancelled", False):
        result["export_cancelled"] = True
        result["failure_reason"] = u"PDF export was cancelled by the user."
        result["warnings"].append(result["failure_reason"])
        result["image_status"] = u"Not requested"
        return result

    if selected_pdf_path:
        report_folder = os.path.dirname(selected_pdf_path)
        base_file_name = os.path.splitext(os.path.basename(selected_pdf_path))[0]
    else:
        base_file_name = u"Scan_QC_Report_{0}".format(timestamp)

    if not report_folder:
        report_folder, reports_root, report_options = _resolve_report_folder(settings)

    pdf_exported, pdf_path, pdf_error = _export_pdf(
        doc,
        sheet,
        report_folder,
        base_file_name
    )
    result["pdf_exported"] = pdf_exported
    if pdf_path:
        result["pdf_path"] = pdf_path
    if pdf_error:
        result["failure_reason"] = pdf_error
        result["warnings"].append(pdf_error)
    if pdf_exported:
        _write_latest_report_pointer(reports_root, pdf_path, result)

    if result["image_requested"]:
        result["image_status"] = (
            u"TODO: PNG/Image export is intentionally left for the next phase. "
            u"PDF export is the stable MVP report output."
        )
    else:
        result["image_status"] = u"Not requested"

    return result
