# -*- coding: utf-8 -*-

import os

from Autodesk.Revit.DB import (
    CopyPasteOptions,
    DuplicateTypeAction,
    ElementId,
    ElementTransformUtils,
    FilteredElementCollector,
    IDuplicateTypeNamesHandler,
    SubTransaction,
    Transaction,
    TransactionStatus,
    Transform,
    View,
    View3D
)
from System.Collections.Generic import List

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


def find_view_template(doc, template_name):
    """Find an exact-name View Template in a document."""
    try:
        views = (
            FilteredElementCollector(doc)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        for view in views:
            if view.IsTemplate and view.Name == template_name:
                return view
    except Exception:
        return None

    return None


def has_view_template(doc, template_name):
    """Check for an exact-name View Template in a document."""
    return find_view_template(doc, template_name) is not None


def find_3d_view(doc, view_name):
    """Find an exact-name, non-template 3D View in a document."""
    try:
        views = (
            FilteredElementCollector(doc)
            .OfClass(View3D)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        for view in views:
            if not view.IsTemplate and view.Name == view_name:
                return view
    except Exception:
        return None

    return None


def has_3d_view(doc, view_name):
    """Check for an exact-name, non-template 3D View in a document."""
    return find_3d_view(doc, view_name) is not None


class UseDestinationDuplicateTypeNamesHandler(IDuplicateTypeNamesHandler):
    """Keep destination types when copied standards bring duplicate type names."""

    def OnDuplicateTypeNamesFound(self, duplicate_type_names_handler_args):
        return DuplicateTypeAction.UseDestinationTypes


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


def _create_source_result(settings, template_names, base_view_names):
    standards_path = resolve_standards_rvt_path(settings)
    return {
        "standards_rvt_path": standards_path,
        "standards_rvt_exists": standards_rvt_exists(settings),
        "standards_document_inspected": False,
        "inspection_skipped_reason": u"",
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


def _update_source_result(source_result, standards_doc, template_names, base_view_names):
    source_result["standards_document_inspected"] = True
    source_result.update(
        _check_document_standards(
            standards_doc,
            template_names,
            base_view_names
        )
    )


def inspect_standards_source(application, settings):
    """Open, inspect, and safely close the configured standards RVT."""
    template_names = get_view_template_names(settings)
    base_view_names = get_base_view_names(settings)
    result = _create_source_result(settings, template_names, base_view_names)

    if not result["standards_rvt_exists"]:
        return result

    standards_doc = None
    opened_by_script = False

    try:
        standards_doc, opened_by_script = open_standards_document(
            application,
            result["standards_rvt_path"]
        )
        result["standards_opened_by_script"] = opened_by_script
        _update_source_result(
            result,
            standards_doc,
            template_names,
            base_view_names
        )
    except Exception as ex:
        result["standards_open_error"] = _to_text(ex)
    finally:
        result["standards_close_error"] = close_standards_document(
            standards_doc,
            opened_by_script
        )

    return result


def _get_standard_specs(template_names, base_view_names):
    return [
        {
            "name": template_names["plan"],
            "found_key": "plan_template_found",
            "finder": find_view_template
        },
        {
            "name": template_names["view3d"],
            "found_key": "view3d_template_found",
            "finder": find_view_template
        },
        {
            "name": base_view_names["view3d"],
            "found_key": "base_3d_view_found",
            "finder": find_3d_view
        }
    ]


def _create_installation_result(before_result):
    already_present = []
    for name_key, found_key in (
        ("plan_template_name", "plan_template_found"),
        ("view3d_template_name", "view3d_template_found"),
        ("base_3d_view_name", "base_3d_view_found")
    ):
        if before_result[found_key]:
            already_present.append(before_result[name_key])

    return {
        "required": len(already_present) < 3,
        "attempted": False,
        "transaction_started": False,
        "transaction_committed": False,
        "already_present": already_present,
        "installed": [],
        "missing_in_source": [],
        "copy_failures": [],
        "transaction_error": u"",
        "blocked_reason": u""
    }


def _copy_standard_element(source_doc, target_doc, source_element, copy_options):
    element_ids = List[ElementId]()
    element_ids.Add(source_element.Id)
    return ElementTransformUtils.CopyElements(
        source_doc,
        element_ids,
        target_doc,
        Transform.Identity,
        copy_options
    )


def _install_copy_candidates(target_doc, source_doc, copy_candidates, installation):
    transaction = Transaction(target_doc, "Install Scan QC Standards")
    transaction_started = False

    try:
        transaction.Start()
        transaction_started = True
        installation["transaction_started"] = True

        copy_options = CopyPasteOptions()
        try:
            copy_options.SetDuplicateTypeNamesHandler(
                UseDestinationDuplicateTypeNamesHandler()
            )

            for standard_spec, source_element in copy_candidates:
                standard_name = standard_spec["name"]
                destination_finder = standard_spec["finder"]

                if destination_finder(target_doc, standard_name) is not None:
                    if standard_name not in installation["already_present"]:
                        installation["already_present"].append(standard_name)
                    continue

                subtransaction = SubTransaction(target_doc)
                subtransaction_started = False

                try:
                    subtransaction.Start()
                    subtransaction_started = True
                    _copy_standard_element(
                        source_doc,
                        target_doc,
                        source_element,
                        copy_options
                    )
                    subtransaction_status = subtransaction.Commit()
                    subtransaction_started = False

                    if subtransaction_status != TransactionStatus.Committed:
                        raise Exception(
                            u"Copy sub-transaction ended with status: {0}".format(
                                subtransaction_status
                            )
                        )

                    if destination_finder(target_doc, standard_name) is not None:
                        installation["installed"].append(standard_name)
                    else:
                        installation["copy_failures"].append([
                            standard_name,
                            u"Copy completed but the required name was not found."
                        ])
                except Exception as ex:
                    if subtransaction_started:
                        try:
                            subtransaction.RollBack()
                        except Exception:
                            pass
                    installation["copy_failures"].append([
                        standard_name,
                        _to_text(ex)
                    ])
        finally:
            copy_options.Dispose()

        transaction_status = transaction.Commit()
        transaction_started = False
        if transaction_status == TransactionStatus.Committed:
            installation["transaction_committed"] = True
        else:
            installation["installed"] = []
            installation["transaction_error"] = (
                u"Transaction ended with status: {0}".format(transaction_status)
            )
    except Exception as ex:
        installation["transaction_error"] = _to_text(ex)
        installation["installed"] = []
        if transaction_started:
            try:
                transaction.RollBack()
            except Exception:
                pass


def _reconcile_installation_result(before_result, after_result, installation):
    for name_key, found_key in (
        ("plan_template_name", "plan_template_found"),
        ("view3d_template_name", "view3d_template_found"),
        ("base_3d_view_name", "base_3d_view_found")
    ):
        standard_name = before_result[name_key]
        was_missing = not before_result[found_key]
        is_found_after = after_result[found_key]

        if was_missing and is_found_after:
            if standard_name not in installation["installed"]:
                installation["installed"].append(standard_name)
            installation["missing_in_source"] = [
                name for name in installation["missing_in_source"]
                if name != standard_name
            ]
            installation["copy_failures"] = [
                failure for failure in installation["copy_failures"]
                if failure[0] != standard_name
            ]
        elif standard_name in installation["installed"] and not is_found_after:
            installation["installed"].remove(standard_name)
            if not any(
                failure[0] == standard_name
                for failure in installation["copy_failures"]
            ):
                installation["copy_failures"].append([
                    standard_name,
                    u"The required name was missing after the transaction."
                ])


def install_missing_standards(target_doc, settings):
    """Install only missing named Scan QC standards from the configured RVT."""
    template_names = get_view_template_names(settings)
    base_view_names = get_base_view_names(settings)
    standard_specs = _get_standard_specs(template_names, base_view_names)
    before_result = _check_document_standards(
        target_doc,
        template_names,
        base_view_names
    )
    source_result = _create_source_result(settings, template_names, base_view_names)
    installation = _create_installation_result(before_result)
    result = {
        "before": before_result,
        "standards_source": source_result,
        "installation": installation,
        "after": before_result
    }

    if not installation["required"]:
        source_result["inspection_skipped_reason"] = (
            u"All required standards already exist in the current project."
        )
        return result

    standards_doc = None
    opened_by_script = False

    try:
        if not source_result["standards_rvt_exists"]:
            if installation["required"]:
                installation["blocked_reason"] = (
                    u"The configured standards source file was not found."
                )
            return result

        standards_doc, opened_by_script = open_standards_document(
            target_doc.Application,
            source_result["standards_rvt_path"]
        )
        source_result["standards_opened_by_script"] = opened_by_script
        _update_source_result(
            source_result,
            standards_doc,
            template_names,
            base_view_names
        )

        copy_candidates = []
        for standard_spec in standard_specs:
            if before_result[standard_spec["found_key"]]:
                continue

            source_element = standard_spec["finder"](
                standards_doc,
                standard_spec["name"]
            )
            if source_element is None:
                installation["missing_in_source"].append(standard_spec["name"])
            else:
                copy_candidates.append((standard_spec, source_element))

        if copy_candidates:
            installation["attempted"] = True
            _install_copy_candidates(
                target_doc,
                standards_doc,
                copy_candidates,
                installation
            )
    except Exception as ex:
        source_result["standards_open_error"] = _to_text(ex)
        if installation["required"]:
            installation["blocked_reason"] = (
                u"The standards source file could not be opened: {0}".format(
                    _to_text(ex)
                )
            )
    finally:
        source_result["standards_close_error"] = close_standards_document(
            standards_doc,
            opened_by_script
        )
        result["after"] = _check_document_standards(
            target_doc,
            template_names,
            base_view_names
        )
        _reconcile_installation_result(
            before_result,
            result["after"],
            installation
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
