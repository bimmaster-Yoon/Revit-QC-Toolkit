# -*- coding: utf-8 -*-

def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def _yes_no(value):
    return u"Yes" if value else u"No"


def _format_target_wall_filter_options(options):
    if not isinstance(options, dict):
        return u"None"
    enabled = []
    if options.get("interior_walls_only"):
        enabled.append(u"Interior by Wall Type Function")
    if options.get("new_construction_only"):
        enabled.append(u"New Construction by Phase")
    if options.get("exclude_exterior_walls"):
        enabled.append(u"Exclude Exterior by Wall Type Function")
    if options.get("only_scan_qc_target_yes"):
        enabled.append(u"SCAN_QC_TARGET = Yes")
    if not enabled:
        return u"None"
    return u", ".join(enabled)


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


def _render_project_standards(output, title, current_project, warning_prefix):
    output.print_md(title)
    output.print_table(
        table_data=_standards_rows(current_project, u"current project"),
        columns=[u"Standards Item", u"Status"]
    )

    missing_items = _missing_standard_names(current_project)
    if missing_items:
        output.print_md(
            u"> **Warning:** {0} Missing: {1}.".format(
                warning_prefix,
                u", ".join(missing_items)
            )
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


def _format_names(names):
    return u", ".join(names) if names else u"None"


def _format_copy_failures(copy_failures):
    if not copy_failures:
        return u"None"
    return u" | ".join(
        u"{0}: {1}".format(item[0], item[1])
        for item in copy_failures
    )


def _render_installation_result(output, installation):
    output.print_md("### C. Standards Installation")
    output.print_table(
        table_data=[
            [u"Installation Required", _yes_no(installation["required"])],
            [u"Installation Attempted", _yes_no(installation["attempted"])],
            [u"Already Present", _format_names(installation["already_present"])],
            [u"Installed", _format_names(installation["installed"])],
            [
                u"Missing in Standards Source",
                _format_names(installation["missing_in_source"])
            ],
            [u"Copy Failures", _format_copy_failures(installation["copy_failures"])],
            [
                u"Blocked Reason",
                installation["blocked_reason"] or u"None"
            ],
            [
                u"Transaction Status",
                (
                    u"Not required"
                    if not installation["required"]
                    else (
                        u"Not started"
                        if not installation["attempted"]
                        else (
                            u"Committed"
                            if installation["transaction_committed"]
                            else u"Failed"
                        )
                    )
                )
            ]
        ],
        columns=[u"Installation Item", u"Result"]
    )

    if installation["transaction_error"]:
        output.print_md(
            u"> **Warning:** Standards installation transaction failed: {0}"
            .format(installation["transaction_error"])
        )
    if installation["blocked_reason"]:
        output.print_md(
            u"> **Warning:** Standards installation was blocked: {0}"
            .format(installation["blocked_reason"])
        )
    if installation["missing_in_source"]:
        output.print_md(
            u"> **Warning:** Required standards were missing in the source file: {0}."
            .format(u", ".join(installation["missing_in_source"]))
        )
    if installation["copy_failures"]:
        output.print_md(
            u"> **Warning:** One or more standards could not be copied: {0}"
            .format(_format_copy_failures(installation["copy_failures"]))
        )
    if (
        not installation["required"]
        and not installation["attempted"]
    ):
        output.print_md("> No standards installation was required.")


def _render_standards_check(output, standards_result):
    _render_project_standards(
        output,
        "### A. Current Project Standards - Before Installation",
        standards_result["before"],
        u"Current project standards were incomplete before installation."
    )
    _render_standards_source(
        output,
        standards_result["standards_source"]
    )
    _render_installation_result(
        output,
        standards_result["installation"]
    )
    _render_project_standards(
        output,
        "### D. Current Project Standards - After Installation",
        standards_result["after"],
        u"Current project standards remain incomplete after installation."
    )


def _view_name_or_status(view_result):
    if view_result["created"]:
        return view_result["view_name"]
    if not view_result["requested"]:
        return u"Not requested"
    return u"Not created"


def _section_box_status(view_creation_result):
    view3d_result = view_creation_result["view3d"]
    if not view3d_result["requested"]:
        return u"Not requested"
    if not view3d_result["section_box_requested"]:
        return u"Skipped - no selected Walls"
    if view3d_result["section_box_applied"]:
        return u"Applied"
    return u"Failed"


def _format_mm(value):
    if value is None:
        return u"N/A"
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return u"{0}".format(int(numeric_value))
        return u"{0:.1f}".format(numeric_value)
    except (TypeError, ValueError):
        return u"{0}".format(value)


def _format_mm_with_unit(value):
    if value is None:
        return u"N/A"
    return u"{0} mm".format(_format_mm(value))


def _format_xyz_list(values):
    if not values:
        return u"N/A"
    if not isinstance(values, (list, tuple)):
        return _to_text(values)
    return u" | ".join(_to_text(value) for value in values if value) or u"N/A"


def _format_mode_stat(stats):
    if not hasattr(stats, "get"):
        return u"N/A"
    summary = stats.get("summary")
    if summary:
        return summary
    if not stats.get("point_count"):
        return u"N/A"
    return u"Avg {0} / P75 {1} / P90 {2} / P95 {3} / Max {4} mm".format(
        _format_mm(stats.get("avg_mm")),
        _format_mm(stats.get("p75_mm")),
        _format_mm(stats.get("p90_mm")),
        _format_mm(stats.get("p95_mm")),
        _format_mm(stats.get("max_mm"))
    )


def _mode_stats_dict(mode_stats):
    result = {}
    if not isinstance(mode_stats, (list, tuple)):
        return result
    for stats in mode_stats:
        if not hasattr(stats, "get"):
            continue
        result[stats.get("mode", u"N/A")] = stats
    return result


def _render_analysis_scope(output, analysis_scope_result):
    is_selected_walls = (
        analysis_scope_result["analysis_scope"] == u"selected_walls"
    )
    if analysis_scope_result["z_min_mm"] is None:
        z_range_text = u"N/A"
    else:
        z_range_text = u"{0} to {1} mm".format(
            _format_mm(analysis_scope_result["z_min_mm"]),
            _format_mm(analysis_scope_result["z_max_mm"])
        )

    output.print_md("### E. Analysis Scope")
    output.print_table(
        table_data=[
            [u"Analysis Scope", analysis_scope_result["analysis_scope_label"]],
            [
                u"Active Level",
                analysis_scope_result["active_level_name"] or u"N/A"
            ],
            [
                u"Active Level Elevation",
                (
                    u"{0} mm".format(
                        _format_mm(
                            analysis_scope_result["active_level_elevation_mm"]
                        )
                    )
                    if analysis_scope_result["active_level_elevation_mm"] is not None
                    else u"N/A"
                )
            ],
            [
                u"Selected Wall Count",
                (
                    analysis_scope_result["selected_wall_count"]
                    if is_selected_walls
                    else u"N/A"
                )
            ],
            [u"Section Box Z Range", z_range_text],
            [u"Section Box Source", analysis_scope_result["section_box_source"]],
            [
                u"Selected Walls Margin",
                (
                    u"{0} mm".format(
                        _format_mm(analysis_scope_result["section_box_margin_mm"])
                    )
                    if is_selected_walls
                    else u"N/A"
                )
            ]
        ],
        columns=[u"Scope Item", u"Result"]
    )

    for warning in analysis_scope_result["warnings"]:
        output.print_md(u"> **Warning:** {0}".format(warning))
    if analysis_scope_result["error"]:
        output.print_md(
            u"> **Warning:** Analysis Scope could not produce a Section Box: {0}"
            .format(analysis_scope_result["error"])
        )


def _render_view_creation(output, view_creation_result):
    plan_result = view_creation_result["plan"]
    view3d_result = view_creation_result["view3d"]
    analysis_scope_result = view_creation_result["analysis_scope"]
    output.print_md("### F. Scan QC Working Views")
    output.print_table(
        table_data=[
            [u"QC Plan View", _view_name_or_status(plan_result)],
            [u"QC Plan Template Applied", _yes_no(plan_result["template_applied"])],
            [u"QC 3D View", _view_name_or_status(view3d_result)],
            [u"QC 3D Template Applied", _yes_no(view3d_result["template_applied"])],
            [u"3D Section Box", _section_box_status(view_creation_result)]
        ],
        columns=[u"View Setup Item", u"Result"]
    )

    if (
        analysis_scope_result["analysis_scope"] == u"selected_walls"
        and view_creation_result["selected_wall_count"] == 0
    ):
        output.print_md(
            "> **Warning:** No Wall elements were selected. Selected Walls are required "
            "for later Scan QC analysis, and no Wall-based 3D section box was created."
        )
    if plan_result["error"]:
        output.print_md(
            u"> **Warning:** QC Plan View was not created: {0}".format(
                plan_result["error"]
            )
        )
    if plan_result["requested"] and plan_result["template_error"]:
        output.print_md(
            u"> **Warning:** QC Plan View Template was not applied: {0}".format(
                plan_result["template_error"]
            )
        )
    if view3d_result["error"]:
        output.print_md(
            u"> **Warning:** QC 3D View was not created: {0}".format(
                view3d_result["error"]
            )
        )
    if view3d_result["requested"] and view3d_result["template_error"]:
        output.print_md(
            u"> **Warning:** QC 3D View Template was not applied: {0}".format(
                view3d_result["template_error"]
            )
        )
    if view3d_result["section_box_requested"] and view3d_result["section_box_error"]:
        output.print_md(
            u"> **Warning:** QC 3D section box was not applied: {0}".format(
                view3d_result["section_box_error"]
            )
        )


def _render_marker_preview(output, marker_preview_result):
    if not hasattr(marker_preview_result, "get"):
        marker_preview_result = {}
    plan_preview = marker_preview_result.get("plan") or {}
    view3d_preview = marker_preview_result.get("view3d") or {}
    if not hasattr(plan_preview, "get"):
        plan_preview = {}
    if not hasattr(view3d_preview, "get"):
        view3d_preview = {}

    revision_cloud_count = plan_preview.get(
        "revision_cloud_count",
        marker_preview_result.get("revision_cloud_count", 0)
    )
    textnote_label_count = plan_preview.get(
        "text_note_count",
        marker_preview_result.get("textnote_label_count", 0)
    )
    textnote_leader_count = plan_preview.get(
        "leader_count",
        marker_preview_result.get("textnote_leader_count", 0)
    )
    preview_created = plan_preview.get(
        "created",
        marker_preview_result.get("preview_created", False)
    )
    preview_3d_status = marker_preview_result.get(
        "3d_preview_status",
        view3d_preview.get("display_mode", u"Disabled")
    )
    preview_only = marker_preview_result.get(
        "preview_only",
        plan_preview.get("preview_only", True)
    )
    fallback_preview = bool(
        plan_preview.get(
            "preview_callouts_generated_because_no_deviation_data",
            False
        )
    )
    coordinate_debug = plan_preview.get("coordinate_debug") or {}
    if not hasattr(coordinate_debug, "get"):
        coordinate_debug = {}

    if preview_only:
        output.print_md("### G. Scan QC Marker Preview")
        table_rows = [
            [u"2D Plan Preview Requested", _yes_no(plan_preview.get("requested", False))],
            [u"2D Plan Preview Created", _yes_no(preview_created)],
            [
                u"2D Target QC Plan View",
                plan_preview.get("target_view_name", u"") or u"N/A"
            ],
            [u"2D Placement Source", plan_preview.get("placement_source", u"Unavailable")],
            [u"2D Preview Revision", plan_preview.get("revision_description", u"N/A")],
            [u"2D Preview Revision Created", _yes_no(plan_preview.get("revision_created", False))],
            [u"Revision Cloud Count", revision_cloud_count],
            [u"Center ID TextNote Count", textnote_label_count],
            [u"TextNote Leader Count", textnote_leader_count],
            [u"2D Review Count", plan_preview.get("review_count", 0)],
            [u"2D Critical Count", plan_preview.get("critical_count", 0)],
            [
                u"2D Opaque Text Background",
                _yes_no(plan_preview.get("opaque_text_background", False))
            ],
            [u"3D Preview", preview_3d_status or u"Disabled"],
            [
                u"3D Target QC View",
                view3d_preview.get("target_view_name", u"") or u"N/A"
            ]
        ]
        table_columns = [u"Marker Preview Item", u"Result"]
    else:
        output.print_md("### G. Scan QC Wall Deviation Results")
        table_rows = [
            [u"Point Cloud Source", plan_preview.get("point_cloud_name", u"N/A")],
            [u"Point Cloud ElementId", plan_preview.get("point_cloud_id", u"N/A")],
            [
                u"Point Cloud Sampling Status",
                plan_preview.get("point_cloud_sampling_status", u"N/A")
            ],
            [
                u"Sampling Failure Reason",
                plan_preview.get("sampling_failure_reason", u"None") or u"None"
            ],
            [u"Selected Wall Count", plan_preview.get("selected_wall_count", 0)],
            [
                u"Target Wall Filter",
                plan_preview.get("target_wall_filter_summary", u"None")
            ],
            [u"Target Wall Count", plan_preview.get("target_wall_count", 0)],
            [
                u"Filtered Target Wall Count",
                plan_preview.get(
                    "filtered_target_wall_count",
                    plan_preview.get("target_wall_count", 0)
                )
            ],
            [
                u"Excluded Exterior Count",
                plan_preview.get("excluded_exterior_count", 0)
            ],
            [
                u"Excluded Existing Count",
                plan_preview.get("excluded_existing_count", 0)
            ],
            [
                u"Excluded By Parameter Count",
                plan_preview.get("excluded_by_parameter_count", 0)
            ],
            [
                u"Max Process Walls",
                plan_preview.get("max_process_wall_count", u"N/A")
            ],
            [u"Processed Wall Count", plan_preview.get("processed_wall_count", 0)],
            [u"Skipped Wall Count", plan_preview.get("skipped_wall_count", 0)],
            [
                u"Skipped By Process Limit",
                plan_preview.get("skipped_by_process_limit_count", 0)
            ],
            [u"No Point Data Count", plan_preview.get("no_point_data_count", 0)],
            [
                u"Coordinate Mismatch Count",
                plan_preview.get("coordinate_mismatch_count", 0)
            ],
            [
                u"No Reliable Wall Surface Data Count",
                plan_preview.get("no_reliable_data_count", 0)
            ],
            [
                u"Coordinate Mode Used",
                coordinate_debug.get("coordinate_mode_used", u"N/A")
            ],
            [
                u"Distance Sanity Check",
                coordinate_debug.get("distance_sanity_check", u"N/A")
            ],
            [u"OK Count", plan_preview.get("ok_count", 0)],
            [u"Review Count", plan_preview.get("review_count", 0)],
            [u"Critical Count", plan_preview.get("critical_count", 0)],
            [
                u"Top N Callouts",
                plan_preview.get("top_n_callouts", u"N/A")
            ],
            [
                u"Top N Basis",
                plan_preview.get(
                    "top_n_callout_basis",
                    u"Critical first, then Review; P90/P75 descending"
                )
            ],
            [
                u"Callout Candidate Count",
                plan_preview.get("candidate_callout_count", 0)
            ],
            [
                u"Merged Close Cluster Count",
                plan_preview.get("merged_cluster_count", 0)
            ],
            [
                u"Overlap Skipped Callout Count",
                plan_preview.get("overlap_skipped_callout_count", 0)
            ],
            [
                u"Top N Skipped Callout Count",
                plan_preview.get("top_n_skipped_callout_count", 0)
            ],
            [
                u"2D Target QC Plan View",
                plan_preview.get("target_view_name", u"") or u"N/A"
            ],
            [
                u"Created Callout Count",
                plan_preview.get("created_callout_count", revision_cloud_count)
            ],
            [u"Revision Cloud Count", revision_cloud_count],
            [u"Center ID TextNote Count", textnote_label_count],
            [u"TextNote Leader Count", textnote_leader_count],
            [u"Preview Fallback Callouts", _yes_no(fallback_preview)],
            [u"3D Preview", preview_3d_status or u"Disabled"]
        ]
        table_columns = [u"Deviation Item", u"Result"]

    output.print_table(
        table_data=table_rows,
        columns=table_columns
    )

    if not preview_only and plan_preview.get("calculation_note"):
        output.print_md(
            u"> **Calculation:** {0}".format(plan_preview.get("calculation_note"))
        )
    if fallback_preview:
        output.print_md(
            u"> **Preview:** {0}".format(
                plan_preview.get(
                    "preview_callout_reason",
                    u"Preview callouts were generated because no real deviation data was available."
                )
            )
        )

    if not preview_only:
        output.print_md("#### Coordinate Transform Debug")
        output.print_table(
            table_data=[
                [
                    u"Coordinate mode used",
                    coordinate_debug.get("coordinate_mode_used", u"N/A")
                ],
                [
                    u"PointCloud GetTransform Available",
                    _yes_no(coordinate_debug.get("transform_available", False))
                ],
                [
                    u"PointCloud GetTransform Error",
                    coordinate_debug.get("transform_error", u"") or u"None"
                ],
                [
                    u"PointCloud Transform Origin",
                    coordinate_debug.get("transform_origin", u"N/A")
                ],
                [
                    u"PointCloud Transform BasisX",
                    coordinate_debug.get("transform_basis_x", u"N/A")
                ],
                [
                    u"PointCloud Transform BasisY",
                    coordinate_debug.get("transform_basis_y", u"N/A")
                ],
                [
                    u"PointCloud Transform BasisZ",
                    coordinate_debug.get("transform_basis_z", u"N/A")
                ],
                [
                    u"PointCloud Transform IsIdentity",
                    coordinate_debug.get("transform_is_identity", u"N/A")
                ],
                [
                    u"PointCloud GetTotalTransform Available",
                    _yes_no(
                        coordinate_debug.get("total_transform_available", False)
                    )
                ],
                [
                    u"PointCloud GetTotalTransform Error",
                    coordinate_debug.get("total_transform_error", u"") or u"None"
                ],
                [
                    u"PointCloud TotalTransform Origin",
                    coordinate_debug.get("total_transform_origin", u"N/A")
                ],
                [
                    u"PointCloud TotalTransform BasisX",
                    coordinate_debug.get("total_transform_basis_x", u"N/A")
                ],
                [
                    u"PointCloud TotalTransform BasisY",
                    coordinate_debug.get("total_transform_basis_y", u"N/A")
                ],
                [
                    u"PointCloud TotalTransform BasisZ",
                    coordinate_debug.get("total_transform_basis_z", u"N/A")
                ],
                [
                    u"PointCloud TotalTransform IsIdentity",
                    coordinate_debug.get("total_transform_is_identity", u"N/A")
                ],
                [
                    u"First selected Wall curve endpoints",
                    coordinate_debug.get("first_wall_endpoints", u"N/A")
                ],
                [
                    u"First 3 sample point raw XYZ",
                    _format_xyz_list(
                        coordinate_debug.get("first_sample_raw_xyz", [])
                    )
                ],
                [
                    u"First 3 sample point GetTransform XYZ",
                    _format_xyz_list(
                        coordinate_debug.get("first_sample_transform_xyz", [])
                    )
                ],
                [
                    u"First 3 sample point GetTotalTransform XYZ",
                    _format_xyz_list(
                        coordinate_debug.get(
                            "first_sample_total_transform_xyz",
                            []
                        )
                    )
                ],
                [
                    u"First 3 sample point used XYZ",
                    _format_xyz_list(
                        coordinate_debug.get("first_sample_used_xyz", [])
                    )
                ],
                [
                    u"Distance sanity check result",
                    coordinate_debug.get("distance_sanity_check", u"N/A")
                ]
            ],
            columns=[u"Coordinate Debug Item", u"Value"]
        )

        first_mode_stats = _mode_stats_dict(
            coordinate_debug.get("first_wall_distance_mode_stats", [])
        )
        if first_mode_stats:
            output.print_md("#### First Wall Coordinate Mode Distance Check")
            output.print_table(
                table_data=[
                    [
                        u"raw",
                        _format_mode_stat(first_mode_stats.get("raw"))
                    ],
                    [
                        u"transform",
                        _format_mode_stat(first_mode_stats.get("transform"))
                    ],
                    [
                        u"total_transform",
                        _format_mode_stat(
                            first_mode_stats.get("total_transform")
                        )
                    ]
                ],
                columns=[u"Coordinate Mode", u"Avg / P75 / P90 / P95 / Max"]
            )

    preview_id_mappings = plan_preview.get(
        "preview_id_mappings",
        marker_preview_result.get("preview_id_mappings", [])
    ) or []
    if not isinstance(preview_id_mappings, (list, tuple)):
        preview_id_mappings = []
    mapping_rows = []
    for mapping in preview_id_mappings:
        if not hasattr(mapping, "get"):
            continue
        if preview_only or fallback_preview:
            mapping_rows.append([
                mapping.get("id", u"N/A"),
                mapping.get("label", u"N/A"),
                _yes_no(mapping.get("revision_cloud_created", False)),
                _yes_no(mapping.get("id_textnote_created", False))
            ])
        else:
            mapping_rows.append([
                mapping.get("id", u"N/A"),
                u"Wall {0}".format(mapping.get("wall_id", u"N/A")),
                mapping.get("cluster_index", u"N/A"),
                _format_mm_with_unit(mapping.get("cluster_length_mm")),
                mapping.get("cluster_point_count", 0),
                _format_mm_with_unit(mapping.get("avg_deviation_mm")),
                _format_mm_with_unit(mapping.get("classification_deviation_mm")),
                _format_mm_with_unit(mapping.get("p90_deviation_mm")),
                _format_mm_with_unit(mapping.get("p95_deviation_mm")),
                _format_mm_with_unit(mapping.get("max_deviation_mm")),
                mapping.get("classification_metric", u"P75"),
                mapping.get("status", mapping.get("severity", u"N/A")),
                mapping.get("point_count", 0),
                mapping.get("candidate_point_count", 0),
                _yes_no(mapping.get("revision_cloud_created", False)),
                _yes_no(mapping.get("id_textnote_created", False))
            ])
    if mapping_rows:
        if preview_only or fallback_preview:
            output.print_md("#### Preview ID Mapping")
            output.print_table(
                table_data=mapping_rows,
                columns=[
                    u"ID",
                    u"Preview Information",
                    u"Revision Cloud",
                    u"Center ID TextNote"
                ]
            )
        else:
            output.print_md("#### Deviation ID Mapping")
            output.print_table(
                table_data=mapping_rows,
                columns=[
                    u"ID",
                    u"Wall",
                    u"Cluster",
                    u"Cluster Length",
                    u"Cluster Points",
                    u"Face Avg",
                    u"Cluster P75",
                    u"Face P90",
                    u"Face P95",
                    u"Face Max",
                    u"Status Metric",
                    u"Status",
                    u"Sample Points",
                    u"Candidate Points",
                    u"Revision Cloud",
                    u"Center ID TextNote"
                ]
            )

    overlap_skipped_callouts = plan_preview.get("overlap_skipped_callouts") or []
    if not isinstance(overlap_skipped_callouts, (list, tuple)):
        overlap_skipped_callouts = []
    overlap_rows = []
    for skipped_item in overlap_skipped_callouts:
        if not hasattr(skipped_item, "get"):
            continue
        try:
            overlap_percent = u"{0:.0f}%".format(
                float(skipped_item.get("overlap_ratio", 0.0)) * 100.0
            )
        except Exception:
            overlap_percent = u"N/A"
        overlap_rows.append([
            u"Wall {0}".format(skipped_item.get("wall_id", u"N/A")),
            skipped_item.get("cluster_index", u"N/A"),
            skipped_item.get("severity", u"N/A"),
            overlap_percent,
            skipped_item.get("skipped_reason", u"Overlap with selected callout")
        ])
    if overlap_rows:
        output.print_md("#### Overlap-Skipped Callout Candidates")
        output.print_table(
            table_data=overlap_rows,
            columns=[
                u"Wall",
                u"Cluster",
                u"Severity",
                u"Overlap",
                u"Skipped Reason"
            ]
        )

    if not preview_only:
        review_id_by_wall = {}
        for mapping in preview_id_mappings:
            if not hasattr(mapping, "get"):
                continue
            wall_id = mapping.get("wall_id")
            if wall_id not in (None, u"", u"N/A"):
                wall_key = _to_text(wall_id)
                if wall_key not in review_id_by_wall:
                    review_id_by_wall[wall_key] = []
                review_id_by_wall[wall_key].append(mapping.get("id", u""))

        wall_result_rows = []
        wall_deviation_results = plan_preview.get("wall_deviation_results") or []
        if not isinstance(wall_deviation_results, (list, tuple)):
            wall_deviation_results = []
        for item in wall_deviation_results:
            if not hasattr(item, "get"):
                continue
            wall_id = item.get("wall_id", u"N/A")
            wall_result_rows.append([
                u"Wall {0}".format(wall_id),
                item.get("point_count", 0),
                item.get("candidate_point_count", 0),
                _format_mm_with_unit(item.get("wall_half_width_mm")),
                _format_mm_with_unit(item.get("raw_centerline_avg_mm")),
                _format_mm_with_unit(item.get("raw_centerline_p90_mm")),
                _format_mm_with_unit(item.get("raw_centerline_max_mm")),
                _format_mm_with_unit(item.get("corrected_avg_mm")),
                _format_mm_with_unit(item.get("corrected_p75_mm")),
                _format_mm_with_unit(item.get("corrected_p90_mm")),
                _format_mm_with_unit(item.get("corrected_p95_mm")),
                _format_mm_with_unit(item.get("corrected_max_mm")),
                item.get("cluster_count", 0),
                _format_mm_with_unit(item.get("cluster_length_mm")),
                item.get("cluster_status", u"N/A"),
                item.get("status", u"N/A"),
                item.get("classification_metric", u"P75"),
                item.get("coordinate_mode", u"N/A"),
                item.get("distance_sanity_check", u"N/A"),
                u", ".join(review_id_by_wall.get(_to_text(wall_id), [])),
                item.get("skip_reason", item.get("message", u""))
            ])
        if wall_result_rows:
            output.print_md("#### Wall Deviation Results")
            output.print_table(
                table_data=wall_result_rows,
                columns=[
                    u"Wall",
                    u"Point Count",
                    u"Candidate Point Count",
                    u"Wall Half Width",
                    u"Centerline Avg",
                    u"Centerline P90",
                    u"Centerline Max",
                    u"Face Avg",
                    u"Face P75",
                    u"Face P90",
                    u"Face P95",
                    u"Face Max",
                    u"Cluster Count",
                    u"Primary Cluster Length",
                    u"Cluster Status",
                    u"Status",
                    u"Status Metric",
                    u"Coordinate Mode",
                    u"Sanity Check",
                    u"Review ID",
                    u"Skip Reason"
                ]
            )

        coordinate_mode_rows = []
        for item in wall_deviation_results:
            if not hasattr(item, "get"):
                continue
            mode_stats = _mode_stats_dict(item.get("coordinate_mode_stats", []))
            if not mode_stats:
                continue
            coordinate_mode_rows.append([
                u"Wall {0}".format(item.get("wall_id", u"N/A")),
                _format_mode_stat(mode_stats.get("raw")),
                _format_mode_stat(mode_stats.get("transform")),
                _format_mode_stat(mode_stats.get("total_transform")),
                item.get("coordinate_mode", u"N/A"),
                item.get("distance_sanity_check", u"N/A")
            ])
        if coordinate_mode_rows:
            output.print_md("#### Wall Coordinate Mode Distance Check")
            output.print_table(
                table_data=coordinate_mode_rows,
                columns=[
                    u"Wall",
                    u"Raw Avg/P75/P90/P95/Max",
                    u"Transform Avg/P75/P90/P95/Max",
                    u"TotalTransform Avg/P75/P90/P95/Max",
                    u"Used",
                    u"Sanity"
                ]
            )

        no_point_rows = []
        no_point_details = plan_preview.get("no_point_data_details") or []
        if not isinstance(no_point_details, (list, tuple)):
            no_point_details = []
        for item in no_point_details:
            if not hasattr(item, "get"):
                continue
            no_point_rows.append([
                u"Wall {0}".format(item.get("wall_id", u"N/A")),
                item.get("message", u"No Point Data")
            ])
        if no_point_rows:
            output.print_md("#### No Point Data")
            output.print_table(
                table_data=no_point_rows,
                columns=[u"Wall", u"Reason"]
            )

        no_reliable_rows = []
        no_reliable_details = plan_preview.get("no_reliable_data_details") or []
        if not isinstance(no_reliable_details, (list, tuple)):
            no_reliable_details = []
        for item in no_reliable_details:
            if not hasattr(item, "get"):
                continue
            no_reliable_rows.append([
                u"Wall {0}".format(item.get("wall_id", u"N/A")),
                item.get("message", u"No Reliable Wall Surface Data")
            ])
        if no_reliable_rows:
            output.print_md("#### No Reliable Wall Surface Data")
            output.print_table(
                table_data=no_reliable_rows,
                columns=[u"Wall", u"Skip Reason"]
            )

        coordinate_mismatch_rows = []
        coordinate_mismatch_details = (
            plan_preview.get("coordinate_mismatch_details") or []
        )
        if not isinstance(coordinate_mismatch_details, (list, tuple)):
            coordinate_mismatch_details = []
        for item in coordinate_mismatch_details:
            if not hasattr(item, "get"):
                continue
            coordinate_mismatch_rows.append([
                u"Wall {0}".format(item.get("wall_id", u"N/A")),
                item.get("message", u"Coordinate Mismatch")
            ])
        if coordinate_mismatch_rows:
            output.print_md("#### Coordinate Mismatch")
            output.print_table(
                table_data=coordinate_mismatch_rows,
                columns=[u"Wall", u"Reason"]
            )

    plan_warnings = plan_preview.get("warnings") or []
    if not isinstance(plan_warnings, (list, tuple)):
        plan_warnings = [plan_warnings]
    plan_warning_label = u"2D Plan Preview" if preview_only else u"2D Deviation Markers"
    for warning in plan_warnings:
        output.print_md(u"> **Warning:** {0}: {1}".format(
            plan_warning_label,
            warning
        ))
    if plan_preview.get("error"):
        output.print_md(
            u"> **Warning:** {0} was not created: {1}".format(
                plan_warning_label,
                plan_preview.get("error")
            )
        )
    view3d_warnings = view3d_preview.get("warnings") or []
    if not isinstance(view3d_warnings, (list, tuple)):
        view3d_warnings = [view3d_warnings]
    for warning in view3d_warnings:
        output.print_md(u"> **Warning:** 3D Preview: {0}".format(warning))
    if view3d_preview.get("error"):
        output.print_md(
            u"> **Warning:** 3D Preview was not created: {0}".format(
                view3d_preview.get("error")
            )
        )

    preview_warnings = marker_preview_result.get("preview_warnings") or []
    if not isinstance(preview_warnings, (list, tuple)):
        preview_warnings = [preview_warnings]
    for warning in preview_warnings:
        if warning not in plan_warnings and warning not in view3d_warnings:
            warning_label = u"Marker Preview" if preview_only else u"Wall Deviation"
            output.print_md(u"> **Warning:** {0}: {1}".format(
                warning_label,
                warning
            ))

    preview_errors = marker_preview_result.get("preview_errors") or []
    if not isinstance(preview_errors, (list, tuple)):
        preview_errors = [preview_errors]
    for error in preview_errors:
        if error != plan_preview.get("error") and error != view3d_preview.get("error"):
            error_label = u"Marker Preview" if preview_only else u"Wall Deviation"
            output.print_md(u"> **Warning:** {0}: {1}".format(
                error_label,
                error
            ))

    if preview_only:
        output.print_md(
            "> **Preview:** Marker preview only: no deviation calculation was performed."
        )
    else:
        output.print_md(
            "> **MVP:** Selected Walls uses Point Cloud sampling when available. "
            "If sampling fails, the affected Walls are reported as No Point Data, "
            "No Reliable Wall Surface Data, or Sampling Error and Scan QC "
            "continues. Point Cloud colors were not modified."
        )


def _render_report_export(output, report_result):
    if not hasattr(report_result, "get"):
        report_result = {}

    if report_result.get("export_cancelled", False):
        export_status = u"Cancelled"
    elif report_result.get("pdf_exported", False):
        export_status = u"Exported"
    elif report_result.get("requested", False):
        export_status = u"Failed or skipped"
    else:
        export_status = u"Not requested"

    output.print_md("### I. Scan QC Report Export")
    output.print_table(
        table_data=[
            [
                u"Report Requested",
                _yes_no(report_result.get("requested", False))
            ],
            [
                u"Report Sheet Mode",
                report_result.get("report_sheet_mode_label", u"") or u"N/A"
            ],
            [
                u"Paper Size",
                report_result.get("paper_size", u"N/A")
            ],
            [
                u"Titleblock Mode",
                report_result.get("titleblock_mode", u"N/A")
            ],
            [
                u"PDF Required QC Plan View",
                report_result.get("pdf_required_qc_plan_view", u"N/A")
            ],
            [
                u"PDF Save Dialog Result",
                report_result.get("pdf_save_dialog_result", u"N/A")
            ],
            [
                u"Report Sheet Created",
                _yes_no(report_result.get("report_sheet_created", False))
            ],
            [
                u"Report Sheet Name",
                report_result.get("sheet_name", u"") or u"N/A"
            ],
            [
                u"Report Sheet Number",
                report_result.get("sheet_number", u"") or u"N/A"
            ],
            [
                u"Titleblock",
                report_result.get("titleblock_name", u"") or u"N/A"
            ],
            [
                u"QC Plan Viewport",
                _yes_no(report_result.get("viewport_created", False))
            ],
            [
                u"Viewport Scale",
                report_result.get("viewport_scale", u"N/A")
            ],
            [
                u"Viewport Scale Basis",
                report_result.get("viewport_scale_source", u"N/A")
            ],
            [
                u"Viewport Title Hidden",
                _yes_no(report_result.get("viewport_title_hidden", False))
            ],
            [
                u"Viewport Title Status",
                report_result.get("viewport_title_status", u"N/A")
            ],
            [
                u"Summary TextNote/Table",
                report_result.get("summary_textnote_count", 0)
            ],
            [
                u"Summary Layout",
                report_result.get("summary_layout", u"N/A")
            ],
            [
                u"Summary Panel Width",
                u"{0} mm".format(
                    report_result.get("summary_panel_width_mm", u"N/A")
                )
            ],
            [
                u"Summary Separators",
                report_result.get("summary_separator_count", 0)
            ],
            [
                u"Export Cancelled",
                _yes_no(report_result.get("export_cancelled", False))
            ],
            [
                u"PDF Exported",
                _yes_no(report_result.get("pdf_exported", False))
            ],
            [
                u"Export Status",
                export_status
            ],
            [
                u"PDF Path",
                report_result.get("pdf_path", u"") or u"N/A"
            ],
            [
                u"Image Exported",
                _yes_no(report_result.get("image_exported", False))
            ],
            [
                u"Image Path",
                report_result.get("image_path", u"") or u"N/A"
            ],
            [
                u"Image Status",
                report_result.get("image_status", u"") or u"N/A"
            ],
            [
                u"Failure Reason",
                report_result.get("failure_reason", u"") or u"None"
            ]
        ],
        columns=[u"Report Item", u"Result"]
    )

    warnings = report_result.get("warnings") or []
    if not isinstance(warnings, (list, tuple)):
        warnings = [warnings]
    for warning in warnings:
        if warning:
            output.print_md(
                u"> **Warning:** Scan QC Report: {0}".format(warning)
            )

    errors = report_result.get("errors") or []
    if not isinstance(errors, (list, tuple)):
        errors = [errors]
    for error in errors:
        if error and error not in warnings:
            output.print_md(
                u"> **Warning:** Scan QC Report: {0}".format(error)
            )


def render_scan_qc_summary(
    output,
    selected_wall_count,
    selected_options,
    standards_result,
    view_creation_result
):
    """Render the initial Scan QC selection summary in pyRevit output."""
    selected_output_options = selected_options["selected_output_options"]
    output_options_text = (
        u", ".join(selected_output_options)
        if selected_output_options
        else u"None"
    )
    tolerance_mm = selected_options.get("tolerance_mm") or {}
    tolerance_rows = [
        [
            u"OK",
            u"0 to {0} mm".format(_format_mm(tolerance_mm.get("ok_max", 30)))
        ],
        [
            u"Review",
            u"{0} to {1} mm".format(
                _format_mm(tolerance_mm.get("ok_max", 30)),
                _format_mm(tolerance_mm.get("review_max", 80))
            )
        ],
        [
            u"Critical",
            u"> {0} mm".format(_format_mm(tolerance_mm.get("review_max", 80)))
        ]
    ]

    output.set_title("Revit Scan QC")
    output.print_md("## Scan QC Summary")
    output.print_table(
        table_data=[
            [u"Selected Wall Count", selected_wall_count],
            [
                u"Source Plan View",
                selected_options.get("source_plan_view_name", u"N/A")
            ],
            [
                u"Source Plan View ElementId",
                selected_options.get("source_plan_view_id", u"N/A")
            ],
            [
                u"Analysis Point Cloud Source",
                selected_options["point_cloud_name"]
            ],
            [u"Point Cloud ElementId", selected_options["point_cloud_id"]],
            [u"Selected Output Options", output_options_text],
            [
                u"Top N Callouts",
                selected_options.get("top_n_callouts", u"N/A")
            ],
            [
                u"Paper Size",
                selected_options.get("paper_size", u"A3 Landscape")
            ],
            [
                u"Target Wall Filter",
                _format_target_wall_filter_options(
                    selected_options.get("target_wall_filter", {})
                )
            ],
            [
                u"Preview Callouts When No Deviation Data",
                _yes_no(
                    selected_options.get(
                        "create_preview_callouts_when_no_deviation_data",
                        False
                    )
                )
            ]
        ],
        columns=[u"Item", u"Value"]
    )
    output.print_md("### Selected Scan QC Tolerances")
    output.print_table(
        table_data=tolerance_rows,
        columns=[u"Status", u"Tolerance"]
    )
    for warning in selected_options.get("tolerance_warnings", []):
        output.print_md(u"> **Warning:** {0}".format(warning))
    _render_standards_check(output, standards_result)
    _render_analysis_scope(output, view_creation_result["analysis_scope"])
    _render_view_creation(output, view_creation_result)
    _render_marker_preview(output, view_creation_result.get("marker_preview", {}))
    marker_preview = view_creation_result.get("marker_preview", {})
    plan_preview = {}
    if hasattr(marker_preview, "get"):
        plan_preview = marker_preview.get("plan") or {}
    if hasattr(plan_preview, "get"):
        output.print_md("### H. Scan QC Processing Limits")
        output.print_table(
            table_data=[
                [
                    u"Source Plan View",
                    selected_options.get("source_plan_view_name", u"N/A")
                ],
                [
                    u"Top N Callouts",
                    plan_preview.get(
                        "top_n_callouts",
                        selected_options.get("top_n_callouts", u"N/A")
                    )
                ],
                [
                    u"Active Plan Level Wall Count",
                    plan_preview.get("active_plan_level_wall_count", 0)
                ],
                [
                    u"Filtered Target Wall Count",
                    plan_preview.get(
                        "filtered_target_wall_count",
                        plan_preview.get("target_wall_count", 0)
                    )
                ],
                [
                    u"Excluded Exterior Count",
                    plan_preview.get("excluded_exterior_count", 0)
                ],
                [
                    u"Excluded Existing Count",
                    plan_preview.get("excluded_existing_count", 0)
                ],
                [
                    u"Excluded By Parameter Count",
                    plan_preview.get("excluded_by_parameter_count", 0)
                ]
            ],
            columns=[u"Processing Item", u"Result"]
        )
    _render_report_export(output, view_creation_result.get("report", {}))
    report_result = view_creation_result.get("report", {})
    pdf_exported = (
        hasattr(report_result, "get")
        and report_result.get("pdf_exported", False)
    )
    if pdf_exported:
        output.print_md(
            "> No point recoloring or CSV export was performed. "
            "PDF report export was completed from the generated Report Sheet."
        )
    else:
        output.print_md(
            "> No point recoloring or CSV export was performed. "
            "PDF report export was not completed."
        )
