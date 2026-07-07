# -*- coding: utf-8 -*-


def _yes_no(value):
    return u"Yes" if value else u"No"


def _found_missing(value):
    return u"Found" if value else u"Missing"


def _missing_standard_names(standards_result):
    missing_items = []
    if not standards_result["plan_template_found"]:
        missing_items.append(standards_result["plan_template_name"])
    if not standards_result["view3d_template_found"]:
        missing_items.append(standards_result["view3d_template_name"])
    if not standards_result["base_3d_view_found"]:
        missing_items.append(standards_result["base_3d_view_name"])
    return missing_items


def _standards_rows(standards_result, location_text):
    return [
        [
            u"{0} in {1}".format(
                standards_result["plan_template_name"],
                location_text
            ),
            _found_missing(standards_result["plan_template_found"])
        ],
        [
            u"{0} in {1}".format(
                standards_result["view3d_template_name"],
                location_text
            ),
            _found_missing(standards_result["view3d_template_found"])
        ],
        [
            u"{0} in {1}".format(
                standards_result["base_3d_view_name"],
                location_text
            ),
            _found_missing(standards_result["base_3d_view_found"])
        ]
    ]


def _render_current_project_standards(output, current_project):
    output.print_md("### A. Current Project Standards")
    output.print_table(
        table_data=_standards_rows(current_project, u"current project"),
        columns=[u"Standards Item", u"Status"]
    )

    missing_items = _missing_standard_names(current_project)
    if missing_items:
        output.print_md(
            u"> **Warning:** Current project standards are incomplete. Missing: {0}."
            .format(u", ".join(missing_items))
        )
    else:
        output.print_md("> All required Scan QC standards were found in the project.")


def _render_standards_source(output, standards_source):
    output.print_md("### B. Standards Source File")
    source_rows = [
        [u"Standards RVT Path", standards_source["standards_rvt_path"]],
        [
            u"Standards RVT Exists",
            _yes_no(standards_source["standards_rvt_exists"])
        ]
    ]
    source_rows.extend(_standards_rows(standards_source, u"standards file"))
    output.print_table(
        table_data=source_rows,
        columns=[u"Standards Item", u"Status"]
    )

    if not standards_source["standards_rvt_exists"]:
        output.print_md(
            "> **Warning:** The configured standards RVT file was not found. "
            "The source standards could not be inspected."
        )
        return

    if standards_source["standards_open_error"]:
        output.print_md(
            u"> **Warning:** The standards RVT could not be opened: {0}"
            .format(standards_source["standards_open_error"])
        )
        return

    if standards_source["standards_close_error"]:
        output.print_md(
            u"> **Warning:** The standards RVT was inspected but could not be closed: {0}"
            .format(standards_source["standards_close_error"])
        )

    missing_items = _missing_standard_names(standards_source)
    if missing_items:
        output.print_md(
            u"> **Warning:** Standards source file is incomplete. Missing: {0}. "
            u"No standards were copied or created.".format(u", ".join(missing_items))
        )
    else:
        output.print_md(
            "> All required Scan QC standards were found in the source file."
        )


def _render_standards_check(output, standards_check):
    _render_current_project_standards(
        output,
        standards_check["current_project"]
    )
    _render_standards_source(
        output,
        standards_check["standards_source"]
    )


def render_scan_qc_summary(
    output,
    selected_wall_count,
    selected_options,
    standards_check
):
    """Render the initial Scan QC selection summary in pyRevit output."""
    selected_output_options = selected_options["selected_output_options"]
    output_options_text = (
        u", ".join(selected_output_options)
        if selected_output_options
        else u"None"
    )

    output.set_title("Revit Scan QC")
    output.print_md("## Scan QC Summary")
    output.print_table(
        table_data=[
            [u"Selected Wall Count", selected_wall_count],
            [u"Selected Point Cloud", selected_options["point_cloud_name"]],
            [u"Point Cloud ElementId", selected_options["point_cloud_id"]],
            [u"Selected Output Options", output_options_text]
        ],
        columns=[u"Item", u"Value"]
    )
    _render_standards_check(output, standards_check)
    output.print_md(
        "> Initial UI phase only: no deviation calculation, point recoloring, "
        "view creation, PDF creation, or CSV export was performed."
    )
