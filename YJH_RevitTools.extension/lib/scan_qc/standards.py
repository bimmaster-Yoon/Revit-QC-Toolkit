# -*- coding: utf-8 -*-

import os

from Autodesk.Revit.DB import FilteredElementCollector, View, View3D

from scan_qc.settings import (
    get_base_view_names,
    get_standards_path,
    get_view_template_names
)


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def resolve_standards_rvt_path(settings):
    """Resolve the configured portable standards path from the extension root."""
    return get_standards_path(settings)


def standards_rvt_exists(settings):
    """Return whether the configured standards RVT exists without opening it."""
    try:
        return os.path.isfile(resolve_standards_rvt_path(settings))
    except (IOError, OSError, TypeError, ValueError):
        return False


def has_view_template(doc, template_name):
    """Check for an exact-name View Template in the active document."""
    try:
        views = (
            FilteredElementCollector(doc)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        for view in views:
            if view.IsTemplate and view.Name == template_name:
                return True
    except Exception:
        return False

    return False


def has_3d_view(doc, view_name):
    """Check for an exact-name, non-template 3D View in the active document."""
    try:
        views = (
            FilteredElementCollector(doc)
            .OfClass(View3D)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        for view in views:
            if not view.IsTemplate and view.Name == view_name:
                return True
    except Exception:
        return False

    return False


def _same_file_path(first_path, second_path):
    if not first_path or not second_path:
        return False

    try:
        return os.path.normcase(os.path.abspath(first_path)) == os.path.normcase(
            os.path.abspath(second_path)
        )
    except (TypeError, ValueError):
        return False


def _find_open_document(application, standards_path):
    try:
        for open_document in application.Documents:
            if _same_file_path(open_document.PathName, standards_path):
                return open_document
    except Exception:
        pass

    return None


def open_standards_document(application, standards_path):
    """Open the standards RVT without activating it in the Revit UI.

    Returns the document and whether this function opened it. A document that
    was already open is reused and must not be closed by the caller.
    """
    open_document = _find_open_document(application, standards_path)
    if open_document is not None:
        return open_document, False

    return application.OpenDocumentFile(standards_path), True


def close_standards_document(standards_doc, opened_by_script):
    """Close a standards document only when Scan QC opened it."""
    if standards_doc is None or not opened_by_script:
        return u""

    try:
        was_closed = standards_doc.Close(False)
        if was_closed is False:
            return u"Revit reported that the standards document was not closed."
        return u""
    except Exception as ex:
        return _to_text(ex)


def _check_document_standards(doc, template_names, base_view_names):
    return {
        "plan_template_name": template_names["plan"],
        "plan_template_found": has_view_template(doc, template_names["plan"]),
        "view3d_template_name": template_names["view3d"],
        "view3d_template_found": has_view_template(doc, template_names["view3d"]),
        "base_3d_view_name": base_view_names["view3d"],
        "base_3d_view_found": has_3d_view(doc, base_view_names["view3d"])
    }


def inspect_standards_source(application, settings):
    """Open, inspect, and safely close the configured standards RVT."""
    template_names = get_view_template_names(settings)
    base_view_names = get_base_view_names(settings)
    standards_path = resolve_standards_rvt_path(settings)
    file_exists = standards_rvt_exists(settings)
    result = {
        "standards_rvt_path": standards_path,
        "standards_rvt_exists": file_exists,
        "standards_document_inspected": False,
        "standards_opened_by_script": False,
        "standards_open_error": u"",
        "standards_close_error": u"",
        "plan_template_name": template_names["plan"],
        "plan_template_found": False,
        "view3d_template_name": template_names["view3d"],
        "view3d_template_found": False,
        "base_3d_view_name": base_view_names["view3d"],
        "base_3d_view_found": False
    }

    if not file_exists:
        return result

    standards_doc = None
    opened_by_script = False

    try:
        standards_doc, opened_by_script = open_standards_document(
            application,
            standards_path
        )
        result["standards_document_inspected"] = True
        result["standards_opened_by_script"] = opened_by_script
        source_standards = _check_document_standards(
            standards_doc,
            template_names,
            base_view_names
        )
        result.update(source_standards)
    except Exception as ex:
        result["standards_open_error"] = _to_text(ex)
    finally:
        result["standards_close_error"] = close_standards_document(
            standards_doc,
            opened_by_script
        )

    return result


def check_scan_qc_standards(doc, settings):
    """Validate the active project and configured standards source file."""
    template_names = get_view_template_names(settings)
    base_view_names = get_base_view_names(settings)

    return {
        "current_project": _check_document_standards(
            doc,
            template_names,
            base_view_names
        ),
        "standards_source": inspect_standards_source(doc.Application, settings)
    }
