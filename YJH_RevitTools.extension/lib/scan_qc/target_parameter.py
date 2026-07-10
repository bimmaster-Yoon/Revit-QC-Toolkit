# -*- coding: utf-8 -*-

"""Install and manage the portable SCAN_QC_TARGET Wall parameter."""

import os

from System import Guid
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    BuiltInCategory,
    ElementId,
    FilteredElementCollector,
    GroupTypeId,
    InstanceBinding,
    ParameterElement,
    SharedParameterElement,
    Transaction,
    Wall
)
from Autodesk.Revit.Exceptions import OperationCanceledException
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType


SCAN_QC_TARGET_PARAMETER_NAME = u"SCAN_QC_TARGET"
SCAN_QC_TARGET_GUID_TEXT = u"3fcae74c-9842-4a1a-9f68-9fc5cbce518b"
SCAN_QC_TARGET_GUID = Guid(SCAN_QC_TARGET_GUID_TEXT)
SHARED_PARAMETER_GROUP_NAME = u"Scan QC"
SHARED_PARAMETER_FILE_NAME = u"ScanQC_SharedParameters.txt"


def _to_text(value):
    if value is None:
        return u""
    try:
        return unicode(value)
    except NameError:
        return str(value)


def _id_value(element_id):
    try:
        return element_id.Value
    except Exception:
        try:
            return element_id.IntegerValue
        except Exception:
            return None


def get_shared_parameter_file_path():
    scan_qc_dir = os.path.dirname(os.path.abspath(__file__))
    extension_dir = os.path.abspath(
        os.path.join(scan_qc_dir, os.pardir, os.pardir)
    )
    return os.path.join(
        extension_dir,
        "resources",
        "parameters",
        SHARED_PARAMETER_FILE_NAME
    )


def get_target_parameter(element):
    if element is None:
        return None
    try:
        return element.get_Parameter(SCAN_QC_TARGET_GUID)
    except Exception:
        return None


def target_parameter_is_yes(element):
    parameter = get_target_parameter(element)
    if parameter is None:
        return False
    try:
        return parameter.AsInteger() == 1
    except Exception:
        return False


def _collect_same_name_conflicts(doc):
    conflicts = []
    elements = (
        FilteredElementCollector(doc)
        .OfClass(ParameterElement)
        .ToElements()
    )
    for element in elements:
        try:
            if _to_text(element.Name) != SCAN_QC_TARGET_PARAMETER_NAME:
                continue
            try:
                if element.GuidValue == SCAN_QC_TARGET_GUID:
                    continue
            except Exception:
                pass
            conflicts.append(element)
        except Exception:
            continue
    return conflicts


def _get_binding_state(doc, shared_parameter_element):
    result = {
        "binding_found": False,
        "instance_binding": False,
        "walls_category_bound": False,
        "definition": None,
        "binding": None
    }
    if shared_parameter_element is None:
        return result

    try:
        target_definition = shared_parameter_element.GetDefinition()
    except Exception:
        return result

    target_definition_id = None
    try:
        target_definition_id = _id_value(target_definition.Id)
    except Exception:
        pass

    iterator = doc.ParameterBindings.ForwardIterator()
    iterator.Reset()
    while iterator.MoveNext():
        definition = iterator.Key
        binding = iterator.Current
        same_definition = False
        try:
            same_definition = (
                target_definition_id is not None
                and _id_value(definition.Id) == target_definition_id
            )
        except Exception:
            same_definition = False
        if not same_definition:
            try:
                same_definition = (
                    _to_text(definition.Name) == SCAN_QC_TARGET_PARAMETER_NAME
                )
            except Exception:
                same_definition = False
        if not same_definition:
            continue

        result["binding_found"] = True
        result["definition"] = definition
        result["binding"] = binding
        result["instance_binding"] = isinstance(binding, InstanceBinding)
        if not result["instance_binding"]:
            try:
                result["instance_binding"] = (
                    _to_text(binding.GetType().Name) == u"InstanceBinding"
                )
            except Exception:
                pass
        try:
            for category in binding.Categories:
                if category.BuiltInCategory == BuiltInCategory.OST_Walls:
                    result["walls_category_bound"] = True
                    break
        except Exception:
            try:
                wall_category = doc.Settings.Categories.get_Item(
                    BuiltInCategory.OST_Walls
                )
                result["walls_category_bound"] = binding.Categories.Contains(
                    wall_category
                )
            except Exception:
                pass
        break

    return result


def inspect_target_parameter(doc):
    try:
        exact_element = SharedParameterElement.Lookup(
            doc,
            SCAN_QC_TARGET_GUID
        )
    except Exception:
        exact_element = None

    conflicts = _collect_same_name_conflicts(doc)
    binding_state = _get_binding_state(doc, exact_element)
    available = bool(
        exact_element is not None
        and binding_state["instance_binding"]
        and binding_state["walls_category_bound"]
    )
    return {
        "parameter_name": SCAN_QC_TARGET_PARAMETER_NAME,
        "parameter_guid": SCAN_QC_TARGET_GUID_TEXT,
        "shared_parameter_element": exact_element,
        "same_guid_found": exact_element is not None,
        "same_name_different_guid": bool(conflicts),
        "conflicting_element_ids": [
            _id_value(element.Id) for element in conflicts
        ],
        "binding_found": binding_state["binding_found"],
        "instance_binding": binding_state["instance_binding"],
        "walls_category_bound": binding_state["walls_category_bound"],
        "available": available,
        "warning": u"",
        "error": u""
    }


def _get_external_definition(application, shared_parameter_path):
    previous_path = u""
    try:
        previous_path = application.SharedParametersFilename or u""
    except Exception:
        previous_path = u""

    try:
        application.SharedParametersFilename = shared_parameter_path
        definition_file = application.OpenSharedParameterFile()
        if definition_file is None:
            return None, u"Shared parameter file could not be opened."
        group = definition_file.Groups.get_Item(SHARED_PARAMETER_GROUP_NAME)
        if group is None:
            return None, u"Shared parameter group was not found."
        definition = group.Definitions.get_Item(SCAN_QC_TARGET_PARAMETER_NAME)
        if definition is None:
            return None, u"SCAN_QC_TARGET definition was not found."
        try:
            if definition.GUID != SCAN_QC_TARGET_GUID:
                return None, u"SCAN_QC_TARGET GUID does not match the configured GUID."
        except Exception:
            return None, u"SCAN_QC_TARGET GUID could not be verified."
        return definition, u""
    finally:
        try:
            application.SharedParametersFilename = previous_path
        except Exception:
            pass


def install_target_parameter(doc, application):
    status = inspect_target_parameter(doc)
    if status["available"]:
        status["installed"] = False
        return status
    if status["same_name_different_guid"] and not status["same_guid_found"]:
        status["installed"] = False
        status["error"] = (
            u"A parameter named SCAN_QC_TARGET already exists with a different GUID."
        )
        return status
    if doc.IsFamilyDocument:
        status["installed"] = False
        status["error"] = u"SCAN_QC_TARGET can only be installed in a project document."
        return status

    shared_parameter_path = get_shared_parameter_file_path()
    if not os.path.isfile(shared_parameter_path):
        status["installed"] = False
        status["error"] = u"Shared parameter file was not found: {0}".format(
            shared_parameter_path
        )
        return status

    external_definition, definition_error = _get_external_definition(
        application,
        shared_parameter_path
    )
    if external_definition is None:
        status["installed"] = False
        status["error"] = definition_error
        return status

    transaction = Transaction(doc, "Install SCAN_QC_TARGET")
    try:
        transaction.Start()
        categories = application.Create.NewCategorySet()
        wall_category = doc.Settings.Categories.get_Item(
            BuiltInCategory.OST_Walls
        )
        categories.Insert(wall_category)
        binding = application.Create.NewInstanceBinding(categories)

        inserted = doc.ParameterBindings.Insert(
            external_definition,
            binding,
            GroupTypeId.IdentityData
        )
        if not inserted and status["same_guid_found"]:
            internal_definition = status[
                "shared_parameter_element"
            ].GetDefinition()
            inserted = doc.ParameterBindings.ReInsert(
                internal_definition,
                binding,
                GroupTypeId.IdentityData
            )
        if not inserted:
            raise Exception("Revit did not accept the parameter binding.")
        transaction.Commit()
    except Exception as ex:
        try:
            transaction.RollBack()
        except Exception:
            pass
        status["installed"] = False
        status["error"] = _to_text(ex)
        return status

    result = inspect_target_parameter(doc)
    result["installed"] = result["available"]
    if not result["available"] and not result["error"]:
        result["error"] = u"Parameter binding could not be verified after installation."
    return result


def set_selected_wall_targets(doc, walls, target_value):
    result = {"updated_count": 0, "skipped_count": 0, "error": u""}
    target_walls = list(walls or [])
    if not target_walls:
        result["error"] = u"No Wall elements are selected."
        return result

    transaction = Transaction(
        doc,
        "Mark SCAN_QC_TARGET" if target_value else "Clear SCAN_QC_TARGET"
    )
    try:
        transaction.Start()
        for wall in target_walls:
            parameter = get_target_parameter(wall)
            if parameter is None or parameter.IsReadOnly:
                result["skipped_count"] += 1
                continue
            try:
                parameter.Set(1 if target_value else 0)
                result["updated_count"] += 1
            except Exception:
                result["skipped_count"] += 1
        transaction.Commit()
    except Exception as ex:
        try:
            transaction.RollBack()
        except Exception:
            pass
        result["error"] = _to_text(ex)
    return result


class WallSelectionFilter(ISelectionFilter):
    """Allow only Wall elements during an interactive Revit selection."""

    def AllowElement(self, element):
        return isinstance(element, Wall)

    def AllowReference(self, reference, position):
        return False


def pick_walls(uidoc):
    """Pick multiple Walls after the modal setup dialog has been closed."""
    result = {"walls": [], "cancelled": False, "error": u""}
    try:
        references = uidoc.Selection.PickObjects(
            ObjectType.Element,
            WallSelectionFilter(),
            u"Select Walls, then click Finish. Press ESC to cancel."
        )
    except OperationCanceledException:
        result["cancelled"] = True
        return result
    except Exception as ex:
        result["error"] = _to_text(ex)
        return result

    for reference in references:
        try:
            wall = uidoc.Document.GetElement(reference.ElementId)
            if isinstance(wall, Wall):
                result["walls"].append(wall)
        except Exception:
            continue
    return result


def collect_target_walls(doc, source_plan_view=None):
    """Collect marked Walls visible in the requested Source Plan View."""
    try:
        if source_plan_view is not None:
            walls = (
                FilteredElementCollector(doc, source_plan_view.Id)
                .OfClass(Wall)
                .WhereElementIsNotElementType()
                .ToElements()
            )
        else:
            walls = (
                FilteredElementCollector(doc)
                .OfClass(Wall)
                .WhereElementIsNotElementType()
                .ToElements()
            )
    except Exception:
        walls = []

    return [wall for wall in walls if target_parameter_is_yes(wall)]


def build_target_counts_by_view_id(doc, source_plan_views):
    counts = {}
    for source_plan_view in source_plan_views or []:
        view_id = _id_value(source_plan_view.Id)
        if view_id is None:
            continue
        counts[view_id] = len(
            collect_target_walls(doc, source_plan_view)
        )
    return counts


def select_target_walls(doc, uidoc, source_plan_view=None):
    element_ids = List[ElementId]()
    for wall in collect_target_walls(doc, source_plan_view):
        element_ids.Add(wall.Id)

    result = {"selected_count": element_ids.Count, "error": u""}
    try:
        if element_ids.Count:
            uidoc.Selection.SetElementIds(element_ids)
            try:
                uidoc.ShowElements(element_ids)
            except Exception:
                pass
    except Exception as ex:
        result["error"] = _to_text(ex)
    return result
