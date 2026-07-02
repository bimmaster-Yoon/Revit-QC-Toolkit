# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import ElementId, StorageType

from collectors import get_element_id_value, is_empty, to_text
from grouping import add_issue


def find_shared_parameter(element, parameter_name):
    if element is None:
        return None

    try:
        for parameter in element.GetParameters(parameter_name):
            if parameter.IsShared:
                return parameter
    except Exception:
        return None

    return None


def get_shared_parameter(doc, element, parameter_name):
    parameter = find_shared_parameter(element, parameter_name)

    if parameter is not None:
        return parameter, u"Instance"

    try:
        type_id = element.GetTypeId()

        if type_id != ElementId.InvalidElementId:
            type_element = doc.GetElement(type_id)
            parameter = find_shared_parameter(type_element, parameter_name)

            if parameter is not None:
                return parameter, u"Type"
    except Exception:
        pass

    return None, u""


def parameter_has_input_value(parameter):
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

        return True
    except Exception:
        return False


def get_parameter_element_name(doc, element, category_name):
    element_id = get_element_id_value(element.Id)

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

    try:
        type_element = doc.GetElement(element.GetTypeId())

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

    return u"{0} [Id: {1}]".format(category_name, element_id)


def run_parameter_checks(doc, parameter_collections, issue_rows):
    checked_parameter_elements = 0

    for collection in parameter_collections:
        category_name = collection["category_name"]
        parameter_name = collection["parameter_name"]

        for element in collection["elements"]:
            checked_parameter_elements += 1
            element_name = get_parameter_element_name(
                doc,
                element,
                category_name
            )
            parameter, parameter_scope = get_shared_parameter(
                doc,
                element,
                parameter_name
            )

            if parameter is None:
                add_issue(
                    issue_rows,
                    u"Parameter QC",
                    category_name,
                    element_name,
                    u"High",
                    u"Shared Parameter 없음: {0}".format(parameter_name)
                )
                continue

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

    return checked_parameter_elements
