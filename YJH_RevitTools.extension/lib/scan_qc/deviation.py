# -*- coding: utf-8 -*-

import math

try:
    from Autodesk.Revit import DB
except Exception:
    DB = None

try:
    from Autodesk.Revit.DB import FilteredElementCollector, Level, Wall, XYZ
except Exception:
    FilteredElementCollector = None
    Level = None
    Wall = None
    XYZ = None

try:
    from Autodesk.Revit.DB.PointClouds import PointCloudFilterFactory
    POINT_CLOUD_FILTER_FACTORY_IMPORT_ERROR = u""
except Exception as ex:
    PointCloudFilterFactory = None
    POINT_CLOUD_FILTER_FACTORY_IMPORT_ERROR = ex

try:
    from System import AppDomain, Array, Object, Type
except Exception:
    AppDomain = None
    Array = None
    Object = None
    Type = None


from scan_qc.analysis_scope import (
    ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL,
    ANALYSIS_SCOPE_SELECTED_WALLS,
    PLAN_VIEW_TYPES
)
from scan_qc.collectors import get_element_id_value, get_point_cloud_name
from scan_qc.settings import get_deviation_options, get_tolerance_mm
from scan_qc.wall_filters import apply_target_wall_filters


STATUS_OK = u"OK"
STATUS_REVIEW = u"REVIEW"
STATUS_CRITICAL = u"CRITICAL"
STATUS_NO_POINT_DATA = u"No Point Data"
STATUS_COORDINATE_MISMATCH = u"Coordinate Mismatch"
STATUS_NO_RELIABLE_WALL_SURFACE_DATA = u"No Reliable Wall Surface Data"
STATUS_SKIPPED = u"Skipped"
POINT_CLOUD_SAMPLING_UNAVAILABLE = (
    u"Point Cloud sampling API unavailable or not implemented"
)
POINT_CLOUD_FILTER_FACTORY_FULL_NAME = (
    u"Autodesk.Revit.DB.PointClouds.PointCloudFilterFactory"
)
FT_TO_MM = 304.8
DEFAULT_MAX_PROCESS_WALLS = 50
DEFAULT_TOP_N_CALLOUTS = 7
MIN_AVERAGE_DISTANCE_FT = 0.05
MAX_AVERAGE_DISTANCE_FT = 0.10
MIN_POINTS_PER_WALL = 500
MAX_POINTS_PER_WALL = 2000
COORDINATE_MISMATCH_THRESHOLD_MM = 5000.0
WALL_FACE_NOISE_MARGIN_MM = 300.0
MIN_WALL_SEGMENT_LENGTH_MM = 300.0
MIN_RELIABLE_CANDIDATE_POINTS = 20
NOISE_OUTLIER_FLOOR_MM = 150.0
CLASSIFICATION_PERCENTILE_LABEL = u"P75"
CLUSTER_THRESHOLD_METRIC_LABEL = u"Cluster P75"
CLUSTER_MAX_GAP_MM = 500.0
MIN_DEVIATION_CLUSTER_POINTS = 8
MIN_DEVIATION_CLUSTER_LENGTH_MM = 300.0
MIN_DEVIATION_CLUSTER_DENSITY_PER_M = 8.0


def _to_text(value):
    if value is None:
        return u""

    try:
        return unicode(value)
    except NameError:
        return str(value)


def _mm_to_internal(mm_value):
    try:
        return float(mm_value) / FT_TO_MM
    except Exception:
        return 0.0


def _internal_to_mm(internal_value):
    try:
        return float(internal_value) * FT_TO_MM
    except Exception:
        return None


def _create_xyz(x, y, z):
    if XYZ is not None:
        return XYZ(float(x), float(y), float(z))
    if DB is not None:
        return DB.XYZ(float(x), float(y), float(z))
    return None


def _type_full_name(api_type):
    if api_type is None:
        return u"N/A"

    try:
        return _to_text(api_type.FullName)
    except Exception:
        pass

    try:
        return _to_text(api_type.__name__)
    except Exception:
        return _to_text(api_type)


def _format_xyz(point):
    if point is None:
        return u"N/A"
    try:
        return u"({0:.6f}, {1:.6f}, {2:.6f}) ft".format(
            point.X,
            point.Y,
            point.Z
        )
    except Exception:
        return _to_text(point)


def _safe_transform(point_cloud, method_name):
    if point_cloud is None:
        return None, u"Point Cloud was unavailable."
    try:
        method = getattr(point_cloud, method_name, None)
        if method is None:
            return None, u"{0} was not available.".format(method_name)
        transform = method()
        if transform is None:
            return None, u"{0} returned None.".format(method_name)
        return transform, u""
    except Exception as ex:
        return None, u"{0} failed: {1}".format(method_name, _to_text(ex))


def _transform_is_identity(transform):
    if transform is None:
        return u"N/A"
    try:
        return u"Yes" if transform.IsIdentity else u"No"
    except Exception:
        return u"Unknown"


def _transform_to_debug(transform, prefix, error):
    return {
        "{0}_available".format(prefix): bool(transform is not None),
        "{0}_error".format(prefix): error or u"",
        "{0}_origin".format(prefix): _format_xyz(
            getattr(transform, "Origin", None) if transform is not None else None
        ),
        "{0}_basis_x".format(prefix): _format_xyz(
            getattr(transform, "BasisX", None) if transform is not None else None
        ),
        "{0}_basis_y".format(prefix): _format_xyz(
            getattr(transform, "BasisY", None) if transform is not None else None
        ),
        "{0}_basis_z".format(prefix): _format_xyz(
            getattr(transform, "BasisZ", None) if transform is not None else None
        ),
        "{0}_is_identity".format(prefix): _transform_is_identity(transform)
    }


def _apply_transform(transform, point):
    if transform is None or point is None:
        return None
    try:
        return transform.OfPoint(point)
    except Exception:
        return None


def _reflect_type(full_type_name):
    if Type is not None:
        try:
            reflected_type = Type.GetType(full_type_name)
            if reflected_type is not None:
                return reflected_type, u"System.Type.GetType"
        except Exception:
            pass

    if AppDomain is not None:
        try:
            assemblies = AppDomain.CurrentDomain.GetAssemblies()
            for assembly in assemblies:
                try:
                    reflected_type = assembly.GetType(full_type_name)
                    if reflected_type is not None:
                        return reflected_type, _to_text(assembly.FullName)
                except Exception:
                    pass
        except Exception:
            pass

    return None, u"Not found by reflection"


def _resolve_point_cloud_filter_factory():
    if PointCloudFilterFactory is not None:
        return PointCloudFilterFactory, u"Direct import", u""

    reflected_type, source = _reflect_type(POINT_CLOUD_FILTER_FACTORY_FULL_NAME)
    if reflected_type is not None:
        return reflected_type, u"Reflection", source

    return (
        None,
        u"Missing",
        _to_text(POINT_CLOUD_FILTER_FACTORY_IMPORT_ERROR)
    )


def _create_result(selected_options):
    return {
        "requested": True,
        "attempted": False,
        "point_cloud_name": selected_options.get("point_cloud_name", u"N/A"),
        "point_cloud_id": selected_options.get("point_cloud_id", u"N/A"),
        "analysis_scope": selected_options.get("analysis_scope", u""),
        "analysis_scope_label": selected_options.get("analysis_scope_label", u""),
        "selected_wall_count": 0,
        "active_plan_level_wall_count": 0,
        "unfiltered_target_wall_count": 0,
        "filtered_target_wall_count": 0,
        "target_wall_count": 0,
        "target_wall_filter": {},
        "target_wall_filter_summary": u"None",
        "excluded_exterior_count": 0,
        "excluded_existing_count": 0,
        "excluded_demolished_count": 0,
        "excluded_by_parameter_count": 0,
        "processed_wall_count": 0,
        "skipped_wall_count": 0,
        "skipped_by_process_limit_count": 0,
        "no_point_data_count": 0,
        "no_reliable_data_count": 0,
        "coordinate_mismatch_count": 0,
        "ok_count": 0,
        "review_count": 0,
        "critical_count": 0,
        "max_process_wall_count": DEFAULT_MAX_PROCESS_WALLS,
        "top_n_callouts": DEFAULT_TOP_N_CALLOUTS,
        "results": [],
        "warnings": [],
        "errors": [],
        "point_cloud_sampling_status": u"Unavailable",
        "sampling_failure_reason": POINT_CLOUD_SAMPLING_UNAVAILABLE,
        "coordinate_debug": {
            "coordinate_mode_used": u"N/A",
            "distance_sanity_check": u"N/A",
            "transform_origin": u"N/A",
            "transform_basis_x": u"N/A",
            "transform_basis_y": u"N/A",
            "transform_basis_z": u"N/A",
            "transform_is_identity": u"N/A",
            "total_transform_origin": u"N/A",
            "total_transform_basis_x": u"N/A",
            "total_transform_basis_y": u"N/A",
            "total_transform_basis_z": u"N/A",
            "total_transform_is_identity": u"N/A",
            "first_wall_endpoints": u"N/A",
            "first_sample_raw_xyz": [],
            "first_sample_transform_xyz": [],
            "first_sample_total_transform_xyz": [],
            "first_sample_used_xyz": [],
            "first_wall_distance_mode_stats": []
        },
        "calculation_note": (
            u"Selected Walls MVP samples PointCloudInstance.GetPoints with a "
            u"MultiPlaneFilter and calculates 2D distance to the Wall "
            u"LocationCurve centerline."
        )
    }


def _find_selected_point_cloud(point_clouds, selected_options):
    selected_id = selected_options.get("point_cloud_id")
    for point_cloud in point_clouds:
        try:
            point_cloud_id = get_element_id_value(point_cloud.Id)
            if (
                point_cloud_id == selected_id
                or _to_text(point_cloud_id) == _to_text(selected_id)
            ):
                return point_cloud
        except Exception:
            pass
    return None


def _get_active_plan_level(doc, active_view):
    if active_view is None or Level is None:
        return None
    try:
        if active_view.IsTemplate or active_view.ViewType not in PLAN_VIEW_TYPES:
            return None
    except Exception:
        return None

    try:
        level = active_view.GenLevel
        if isinstance(level, Level):
            return level
    except Exception:
        pass

    try:
        level = doc.GetElement(active_view.LevelId)
        if isinstance(level, Level):
            return level
    except Exception:
        pass

    return None


def _element_is_on_level(element, level):
    try:
        return get_element_id_value(element.LevelId) == get_element_id_value(level.Id)
    except Exception:
        return False


def _collect_active_level_walls(doc, active_view, max_wall_count):
    if FilteredElementCollector is None or Wall is None:
        return [], u"Revit Wall collection API was unavailable."

    level = _get_active_plan_level(doc, active_view)
    if level is None:
        return [], (
            u"Active Plan Level wall collection requires a valid plan view with "
            u"an associated Level."
        )

    walls = []
    collection_warning = u""
    try:
        view_walls = (
            FilteredElementCollector(doc, active_view.Id)
            .OfClass(Wall)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for wall in view_walls:
            if not _element_is_on_level(wall, level):
                continue
            try:
                if wall.IsHidden(active_view):
                    continue
            except Exception:
                pass
            walls.append(wall)
    except Exception as view_ex:
        try:
            all_walls = (
                FilteredElementCollector(doc)
                .OfClass(Wall)
                .WhereElementIsNotElementType()
                .ToElements()
            )
            for wall in all_walls:
                if not _element_is_on_level(wall, level):
                    continue
                try:
                    bounding_box = wall.get_BoundingBox(active_view)
                    if bounding_box is None:
                        continue
                except Exception:
                    pass
                walls.append(wall)
            if walls:
                collection_warning = (
                    u"Source Plan View visible Wall collector failed; "
                    u"fallback used Level + view bounding box filtering. "
                    u"Collector error: {0}"
                ).format(_to_text(view_ex))
        except Exception as fallback_ex:
            return [], (
                u"Source Plan View visible Wall collection failed: {0}; "
                u"fallback failed: {1}"
            ).format(_to_text(view_ex), _to_text(fallback_ex))

    if max_wall_count > 0 and len(walls) > max_wall_count:
        limit_warning = (
            u"Active Plan Level Source Plan View scope found {0} visible Walls; "
            u"processing "
            u"was limited to the first {1} Walls."
        ).format(len(walls), max_wall_count)
        if collection_warning:
            limit_warning = u"{0} {1}".format(collection_warning, limit_warning)
        return walls[:max_wall_count], (
            limit_warning
        )

    return walls, collection_warning


def collect_target_walls(doc, active_view, selected_walls, selected_options, settings):
    options = get_deviation_options(settings)
    analysis_scope = selected_options.get("analysis_scope")

    if analysis_scope == ANALYSIS_SCOPE_SELECTED_WALLS:
        return list(selected_walls or []), u""

    if analysis_scope == ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL:
        return _collect_active_level_walls(
            doc,
            active_view,
            options["max_active_level_walls"]
        )

    return [], u"Unsupported Analysis Scope for deviation calculation: {0}".format(
        analysis_scope
    )


def _get_wall_location_segment(wall):
    try:
        location_curve = wall.Location.Curve
        if location_curve is None:
            return None, None
        return location_curve.GetEndPoint(0), location_curve.GetEndPoint(1)
    except Exception:
        return None, None


def _is_line_curve(curve):
    if curve is None:
        return False
    if DB is not None:
        try:
            line_class = getattr(DB, "Line", None)
            if line_class is not None and isinstance(curve, line_class):
                return True
        except Exception:
            pass
    try:
        return _to_text(curve.GetType().Name) == u"Line"
    except Exception:
        return False


def _get_wall_line_segment_for_calculation(wall):
    try:
        location = wall.Location
        location_curve = location.Curve
    except Exception:
        return None, None, u"Wall LocationCurve was unavailable."

    if location_curve is None:
        return None, None, u"Wall LocationCurve was unavailable."

    if not _is_line_curve(location_curve):
        return None, None, (
            u"Arc/Curve Wall skipped. Selected Walls MVP calculates only Line "
            u"LocationCurve Walls."
        )

    try:
        return location_curve.GetEndPoint(0), location_curve.GetEndPoint(1), u""
    except Exception as ex:
        return None, None, u"Wall Line endpoints could not be read: {0}".format(
            _to_text(ex)
        )


def _wall_segment_length_mm(start, end):
    if start is None or end is None:
        return None
    try:
        length_ft = math.sqrt(
            math.pow(end.X - start.X, 2.0)
            + math.pow(end.Y - start.Y, 2.0)
            + math.pow(end.Z - start.Z, 2.0)
        )
        return _internal_to_mm(length_ft)
    except Exception:
        return None


def _get_wall_type_width_ft(wall):
    try:
        wall_type = wall.WallType
        width = wall_type.Width
        if width is not None and width > 0:
            return float(width), u""
    except Exception as ex:
        return 0.0, u"WallType.Width could not be read: {0}".format(_to_text(ex))
    return 0.0, u"WallType.Width was unavailable or zero."


def _wall_marker_center(wall):
    start, end = _get_wall_location_segment(wall)
    if start is not None and end is not None:
        return _create_xyz(
            (start.X + end.X) / 2.0,
            (start.Y + end.Y) / 2.0,
            (start.Z + end.Z) / 2.0
        )

    try:
        bounding_box = wall.get_BoundingBox(None)
        if bounding_box is not None:
            return _create_xyz(
                (bounding_box.Min.X + bounding_box.Max.X) / 2.0,
                (bounding_box.Min.Y + bounding_box.Max.Y) / 2.0,
                (bounding_box.Min.Z + bounding_box.Max.Z) / 2.0
            )
    except Exception:
        pass

    return None


def _create_no_point_result(wall, message):
    return {
        "wall": wall,
        "wall_id": get_element_id_value(wall.Id),
        "status": STATUS_NO_POINT_DATA,
        "avg_deviation_mm": None,
        "max_deviation_mm": None,
        "p95_deviation_mm": None,
        "classification_deviation_mm": None,
        "classification_metric": CLASSIFICATION_PERCENTILE_LABEL,
        "median_deviation_mm": None,
        "p75_deviation_mm": None,
        "p90_deviation_mm": None,
        "raw_centerline_avg_mm": None,
        "raw_centerline_max_mm": None,
        "raw_centerline_median_mm": None,
        "raw_centerline_p75_mm": None,
        "raw_centerline_p90_mm": None,
        "raw_centerline_p95_mm": None,
        "corrected_avg_mm": None,
        "corrected_max_mm": None,
        "corrected_median_mm": None,
        "corrected_p75_mm": None,
        "corrected_p90_mm": None,
        "corrected_p95_mm": None,
        "wall_type_width_mm": None,
        "wall_half_width_mm": None,
        "candidate_limit_mm": None,
        "point_count": 0,
        "candidate_point_count": 0,
        "candidate_point_count_before_outlier_filter": 0,
        "rejected_outside_segment": 0,
        "rejected_noise": 0,
        "rejected_extreme_noise": 0,
        "cluster_count": 0,
        "deviation_clusters": [],
        "primary_cluster": None,
        "cluster_length_mm": None,
        "cluster_status": u"N/A",
        "marker_center": _wall_marker_center(wall),
        "message": message,
        "skip_reason": message,
        "sampling_status": u"No Point Data",
        "coordinate_mode": u"N/A",
        "distance_sanity_check": u"N/A",
        "coordinate_mode_stats": []
    }


def _create_skipped_result(wall, message):
    result = _create_no_point_result(wall, message)
    result["status"] = STATUS_SKIPPED
    result["sampling_status"] = STATUS_SKIPPED
    return result


def _create_coordinate_mismatch_result(wall, message, coordinate_result):
    if not isinstance(coordinate_result, dict):
        coordinate_result = {}
    selected_stats = coordinate_result.get("selected_stats") or {}
    classification_value = _get_classification_distance_mm(selected_stats)
    clusters = selected_stats.get("deviation_clusters") or []
    return {
        "wall": wall,
        "wall_id": get_element_id_value(wall.Id),
        "status": STATUS_COORDINATE_MISMATCH,
        "avg_deviation_mm": selected_stats.get("avg_mm"),
        "max_deviation_mm": selected_stats.get("max_mm"),
        "p95_deviation_mm": selected_stats.get("p95_mm"),
        "classification_deviation_mm": classification_value,
        "classification_metric": CLASSIFICATION_PERCENTILE_LABEL,
        "median_deviation_mm": selected_stats.get("median_mm"),
        "p75_deviation_mm": selected_stats.get("p75_mm"),
        "p90_deviation_mm": selected_stats.get("p90_mm"),
        "raw_centerline_avg_mm": selected_stats.get("centerline_avg_mm"),
        "raw_centerline_max_mm": selected_stats.get("centerline_max_mm"),
        "raw_centerline_median_mm": selected_stats.get("centerline_median_mm"),
        "raw_centerline_p75_mm": selected_stats.get("centerline_p75_mm"),
        "raw_centerline_p90_mm": selected_stats.get("centerline_p90_mm"),
        "raw_centerline_p95_mm": selected_stats.get("centerline_p95_mm"),
        "corrected_avg_mm": selected_stats.get("avg_mm"),
        "corrected_max_mm": selected_stats.get("max_mm"),
        "corrected_median_mm": selected_stats.get("median_mm"),
        "corrected_p75_mm": selected_stats.get("p75_mm"),
        "corrected_p90_mm": selected_stats.get("p90_mm"),
        "corrected_p95_mm": selected_stats.get("p95_mm"),
        "wall_type_width_mm": coordinate_result.get("wall_type_width_mm"),
        "wall_half_width_mm": coordinate_result.get("wall_half_width_mm"),
        "candidate_limit_mm": coordinate_result.get("candidate_limit_mm"),
        "point_count": selected_stats.get("sampled_point_count", 0),
        "candidate_point_count": selected_stats.get("point_count", 0),
        "candidate_point_count_before_outlier_filter": selected_stats.get(
            "candidate_point_count_before_outlier_filter",
            0
        ),
        "rejected_outside_segment": selected_stats.get(
            "rejected_outside_segment",
            0
        ),
        "rejected_noise": selected_stats.get("rejected_noise", 0),
        "rejected_extreme_noise": selected_stats.get("rejected_extreme_noise", 0),
        "cluster_count": len(clusters),
        "deviation_clusters": clusters,
        "primary_cluster": clusters[0] if clusters else None,
        "cluster_length_mm": clusters[0].get("length_mm") if clusters else None,
        "cluster_status": clusters[0].get("status") if clusters else u"N/A",
        "marker_center": _wall_marker_center(wall),
        "message": message,
        "skip_reason": message,
        "sampling_status": u"Coordinate Mismatch",
        "coordinate_mode": coordinate_result.get("coordinate_mode", u"N/A"),
        "distance_sanity_check": coordinate_result.get(
            "distance_sanity_check",
            u"Coordinate Mismatch"
        ),
        "coordinate_mode_stats": coordinate_result.get("mode_stats", []),
        "sample_debug": coordinate_result.get("sample_debug", {}),
        "wall_endpoints": coordinate_result.get("wall_endpoints", u"N/A")
    }


def _create_no_reliable_result(wall, message, coordinate_result):
    if not isinstance(coordinate_result, dict):
        coordinate_result = {}
    selected_stats = coordinate_result.get("selected_stats") or {}
    clusters = selected_stats.get("deviation_clusters") or []
    return {
        "wall": wall,
        "wall_id": get_element_id_value(wall.Id),
        "status": STATUS_NO_RELIABLE_WALL_SURFACE_DATA,
        "avg_deviation_mm": selected_stats.get("avg_mm"),
        "max_deviation_mm": selected_stats.get("max_mm"),
        "p95_deviation_mm": selected_stats.get("p95_mm"),
        "classification_deviation_mm": _get_classification_distance_mm(
            selected_stats
        ),
        "classification_metric": CLASSIFICATION_PERCENTILE_LABEL,
        "median_deviation_mm": selected_stats.get("median_mm"),
        "p75_deviation_mm": selected_stats.get("p75_mm"),
        "p90_deviation_mm": selected_stats.get("p90_mm"),
        "raw_centerline_avg_mm": selected_stats.get("centerline_avg_mm"),
        "raw_centerline_max_mm": selected_stats.get("centerline_max_mm"),
        "raw_centerline_median_mm": selected_stats.get("centerline_median_mm"),
        "raw_centerline_p75_mm": selected_stats.get("centerline_p75_mm"),
        "raw_centerline_p90_mm": selected_stats.get("centerline_p90_mm"),
        "raw_centerline_p95_mm": selected_stats.get("centerline_p95_mm"),
        "corrected_avg_mm": selected_stats.get("avg_mm"),
        "corrected_max_mm": selected_stats.get("max_mm"),
        "corrected_median_mm": selected_stats.get("median_mm"),
        "corrected_p75_mm": selected_stats.get("p75_mm"),
        "corrected_p90_mm": selected_stats.get("p90_mm"),
        "corrected_p95_mm": selected_stats.get("p95_mm"),
        "wall_type_width_mm": coordinate_result.get("wall_type_width_mm"),
        "wall_half_width_mm": coordinate_result.get("wall_half_width_mm"),
        "candidate_limit_mm": coordinate_result.get("candidate_limit_mm"),
        "point_count": selected_stats.get("sampled_point_count", 0),
        "candidate_point_count": selected_stats.get("point_count", 0),
        "candidate_point_count_before_outlier_filter": selected_stats.get(
            "candidate_point_count_before_outlier_filter",
            0
        ),
        "rejected_outside_segment": selected_stats.get(
            "rejected_outside_segment",
            0
        ),
        "rejected_noise": selected_stats.get("rejected_noise", 0),
        "rejected_extreme_noise": selected_stats.get("rejected_extreme_noise", 0),
        "cluster_count": len(clusters),
        "deviation_clusters": clusters,
        "primary_cluster": clusters[0] if clusters else None,
        "cluster_length_mm": clusters[0].get("length_mm") if clusters else None,
        "cluster_status": clusters[0].get("status") if clusters else u"N/A",
        "marker_center": _wall_marker_center(wall),
        "message": message,
        "skip_reason": message,
        "sampling_status": STATUS_NO_RELIABLE_WALL_SURFACE_DATA,
        "coordinate_mode": coordinate_result.get("coordinate_mode", u"N/A"),
        "distance_sanity_check": coordinate_result.get(
            "distance_sanity_check",
            u"N/A"
        ),
        "coordinate_mode_stats": coordinate_result.get("mode_stats", []),
        "sample_debug": coordinate_result.get("sample_debug", {}),
        "wall_endpoints": coordinate_result.get("wall_endpoints", u"N/A")
    }


def _get_tolerance_options(selected_options, settings):
    fallback = get_tolerance_mm(settings)
    tolerance = selected_options.get("tolerance_mm")
    if not isinstance(tolerance, dict):
        tolerance = {}

    try:
        ok_max = float(tolerance.get("ok_max", fallback["ok_max"]))
    except Exception:
        ok_max = float(fallback["ok_max"])

    try:
        review_max = float(tolerance.get("review_max", fallback["review_max"]))
    except Exception:
        review_max = float(fallback["review_max"])

    if ok_max < 0 or review_max < ok_max:
        ok_max = float(fallback["ok_max"])
        review_max = float(fallback["review_max"])

    return {
        "ok_max": ok_max,
        "review_max": review_max
    }


def _get_average_distance_ft(options):
    average_distance_ft = _mm_to_internal(options.get("point_sample_spacing_mm", 30))
    if average_distance_ft < MIN_AVERAGE_DISTANCE_FT:
        return MIN_AVERAGE_DISTANCE_FT
    if average_distance_ft > MAX_AVERAGE_DISTANCE_FT:
        return MAX_AVERAGE_DISTANCE_FT
    return average_distance_ft


def _get_max_points_per_wall(options):
    try:
        max_points = int(options.get("max_points_per_wall", MAX_POINTS_PER_WALL))
    except Exception:
        max_points = MAX_POINTS_PER_WALL
    if max_points < MIN_POINTS_PER_WALL:
        return MIN_POINTS_PER_WALL
    if max_points > MAX_POINTS_PER_WALL:
        return MAX_POINTS_PER_WALL
    return max_points


def _get_max_process_walls(options):
    try:
        max_process_walls = int(
            options.get("max_process_walls", DEFAULT_MAX_PROCESS_WALLS)
        )
    except Exception:
        max_process_walls = DEFAULT_MAX_PROCESS_WALLS
    if max_process_walls <= 0:
        return DEFAULT_MAX_PROCESS_WALLS
    return max_process_walls


def _get_top_n_callouts(options):
    try:
        top_n_callouts = int(options.get("top_n_callouts", DEFAULT_TOP_N_CALLOUTS))
    except Exception:
        top_n_callouts = DEFAULT_TOP_N_CALLOUTS
    if top_n_callouts <= 0:
        return DEFAULT_TOP_N_CALLOUTS
    return top_n_callouts


def _build_plane_list(minimum, maximum, inverted=False):
    if DB is None:
        raise Exception(u"Autodesk.Revit.DB was unavailable.")

    try:
        from System.Collections.Generic import List
        planes = List[DB.Plane]()
        direction = -1.0 if inverted else 1.0
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(direction, 0.0, 0.0),
                minimum
            )
        )
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(-direction, 0.0, 0.0),
                maximum
            )
        )
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(0.0, direction, 0.0),
                minimum
            )
        )
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(0.0, -direction, 0.0),
                maximum
            )
        )
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(0.0, 0.0, direction),
                minimum
            )
        )
        planes.Add(
            DB.Plane.CreateByNormalAndOrigin(
                _create_xyz(0.0, 0.0, -direction),
                maximum
            )
        )
        return planes
    except Exception as ex:
        raise Exception(u"Plane list setup failed: {0}".format(_to_text(ex)))


def _invoke_create_multiplane_filter(factory_type, planes):
    if factory_type is None:
        return None, u"PointCloudFilterFactory still unavailable."

    try:
        return factory_type.CreateMultiPlaneFilter(planes), u"Direct static call"
    except Exception as direct_ex:
        direct_error = _to_text(direct_ex)

    try:
        method = factory_type.GetMethod("CreateMultiPlaneFilter")
        if method is None:
            return None, (
                u"CreateMultiPlaneFilter method was not found on {0}. Direct call "
                u"error: {1}"
            ).format(_type_full_name(factory_type), direct_error)
        if Array is not None and Object is not None:
            return method.Invoke(None, Array[Object]([planes])), u"Reflection Invoke"
        return method.Invoke(None, [planes]), u"Reflection Invoke"
    except Exception as reflection_ex:
        return None, (
            u"CreateMultiPlaneFilter failed. Direct call error: {0}. Reflection "
            u"error: {1}"
        ).format(direct_error, _to_text(reflection_ex))


def _get_wall_filter_box(wall, margin_ft):
    try:
        bounding_box = wall.get_BoundingBox(None)
    except Exception as ex:
        return None, None, u"Wall BoundingBox read failed: {0}".format(_to_text(ex))

    if bounding_box is None:
        return None, None, u"Wall BoundingBox was unavailable."

    return (
        _create_xyz(
            bounding_box.Min.X - margin_ft,
            bounding_box.Min.Y - margin_ft,
            bounding_box.Min.Z - margin_ft
        ),
        _create_xyz(
            bounding_box.Max.X + margin_ft,
            bounding_box.Max.Y + margin_ft,
            bounding_box.Max.Z + margin_ft
        ),
        u""
    )


def _build_wall_multiplane_filters(wall, margin_ft, factory_type):
    minimum, maximum, box_error = _get_wall_filter_box(wall, margin_ft)
    if box_error:
        return [], [box_error]

    filters = []
    attempts = []
    for inverted in (False, True):
        orientation_name = u"inverted normals" if inverted else u"standard normals"
        try:
            planes = _build_plane_list(minimum, maximum, inverted)
            point_filter, creation_method = _invoke_create_multiplane_filter(
                factory_type,
                planes
            )
            if point_filter is not None:
                filters.append((point_filter, orientation_name, creation_method))
                attempts.append(
                    u"MultiPlaneFilter created with {0} / {1}.".format(
                        orientation_name,
                        creation_method
                    )
                )
            else:
                attempts.append(
                    u"MultiPlaneFilter creation failed with {0}: {1}".format(
                        orientation_name,
                        creation_method
                    )
                )
        except Exception as ex:
            attempts.append(
                u"MultiPlaneFilter exception with {0}: {1}".format(
                    orientation_name,
                    _to_text(ex)
                )
            )

    return filters, attempts


def _cloud_point_to_xyz(point):
    if DB is not None:
        try:
            if isinstance(point, DB.XYZ):
                return point
        except Exception:
            pass

    for attribute_name in ("XYZ", "Position", "Point"):
        try:
            value = getattr(point, attribute_name)
            if DB is None:
                return value
            try:
                if isinstance(value, DB.XYZ):
                    return value
            except Exception:
                return value
        except Exception:
            pass

    try:
        return _create_xyz(point.X, point.Y, point.Z)
    except Exception:
        pass

    try:
        return _create_xyz(point[0], point[1], point[2])
    except Exception:
        pass

    return None


def _get_points_with_filter(point_cloud, point_filter, average_distance_ft, max_points):
    get_points = getattr(point_cloud, "GetPoints", None)
    if get_points is None:
        return None, u"PointCloudInstance.GetPoints is not available."

    try:
        point_collection = get_points(
            point_filter,
            average_distance_ft,
            max_points
        )
        if point_collection is None:
            return [], u""
        return list(point_collection), u""
    except Exception as ex:
        return None, _to_text(ex)


def _sample_wall_points(wall, point_cloud, sampling_context):
    if point_cloud is None:
        return [], u"Selected Point Cloud ElementId was not found."

    if sampling_context.get("factory_type") is None:
        return [], sampling_context.get(
            "factory_error",
            POINT_CLOUD_SAMPLING_UNAVAILABLE
        )

    filters, filter_attempts = _build_wall_multiplane_filters(
        wall,
        sampling_context["search_margin_ft"],
        sampling_context["factory_type"]
    )
    if not filters:
        return [], u"; ".join(filter_attempts) or u"Wall MultiPlaneFilter was not created."

    errors = []
    for point_filter, orientation_name, creation_method in filters:
        points, error = _get_points_with_filter(
            point_cloud,
            point_filter,
            sampling_context["average_distance_ft"],
            sampling_context["max_points"]
        )
        if points is not None:
            xyz_points = []
            for point in points:
                xyz = _cloud_point_to_xyz(point)
                if xyz is not None:
                    xyz_points.append(xyz)
            if xyz_points:
                return xyz_points, u""
            errors.append(
                u"GetPoints returned 0 readable XYZ points with {0} / {1}."
                .format(orientation_name, creation_method)
            )
        else:
            errors.append(
                u"GetPoints failed with {0} / {1}: {2}".format(
                    orientation_name,
                    creation_method,
                    error
                )
            )

    return [], u"; ".join(errors) or u"No Point Data in Wall filter box."


def _distance_point_to_segment_2d_detail(point, start, end):
    dx = end.X - start.X
    dy = end.Y - start.Y
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return None, None

    t = (
        ((point.X - start.X) * dx + (point.Y - start.Y) * dy)
        / length_squared
    )

    closest_x = start.X + t * dx
    closest_y = start.Y + t * dy
    distance = math.sqrt(
        (point.X - closest_x) * (point.X - closest_x)
        + (point.Y - closest_y) * (point.Y - closest_y)
    )
    return distance, t


def _distance_point_to_segment_2d(point, start, end):
    distance, t = _distance_point_to_segment_2d_detail(point, start, end)
    if distance is None:
        return None
    if t < 0.0:
        return math.sqrt(
            (point.X - start.X) * (point.X - start.X)
            + (point.Y - start.Y) * (point.Y - start.Y)
        )
    if t > 1.0:
        return math.sqrt(
            (point.X - end.X) * (point.X - end.X)
            + (point.Y - end.Y) * (point.Y - end.Y)
        )
    return distance


def _get_points_for_coordinate_mode(raw_points, mode_name, sampling_context):
    if mode_name == u"raw":
        return list(raw_points or [])

    transform = None
    if mode_name == u"transform":
        transform = sampling_context.get("transform")
    elif mode_name == u"total_transform":
        transform = sampling_context.get("total_transform")

    if transform is None:
        return []

    transformed_points = []
    for point in raw_points or []:
        transformed_point = _apply_transform(transform, point)
        if transformed_point is not None:
            transformed_points.append(transformed_point)
    return transformed_points


def _calculate_wall_face_distance_values_mm(
    points,
    start,
    end,
    wall_half_width_ft,
    candidate_limit_ft
):
    centerline_values_mm = []
    corrected_values_mm = []
    distance_samples = []
    sampled_point_count = 0
    unreadable_distance_count = 0
    rejected_outside_segment = 0
    rejected_noise = 0
    segment_length_ft = math.sqrt(
        ((end.X - start.X) * (end.X - start.X))
        + ((end.Y - start.Y) * (end.Y - start.Y))
    )
    for point in points or []:
        sampled_point_count += 1
        distance_ft, projection_parameter = _distance_point_to_segment_2d_detail(
            point,
            start,
            end
        )
        if distance_ft is None:
            unreadable_distance_count += 1
            continue
        if projection_parameter is None or projection_parameter < 0.0 or projection_parameter > 1.0:
            rejected_outside_segment += 1
            continue
        if distance_ft > candidate_limit_ft:
            rejected_noise += 1
            continue

        centerline_distance_mm = _internal_to_mm(distance_ft)
        corrected_distance_mm = _internal_to_mm(
            max(0.0, distance_ft - wall_half_width_ft)
        )
        if centerline_distance_mm is not None and corrected_distance_mm is not None:
            centerline_values_mm.append(centerline_distance_mm)
            corrected_values_mm.append(corrected_distance_mm)
            projection_distance_ft = projection_parameter * segment_length_ft
            distance_samples.append({
                "projection_parameter": projection_parameter,
                "projection_distance_ft": projection_distance_ft,
                "projection_distance_mm": _internal_to_mm(projection_distance_ft),
                "centerline_distance_mm": centerline_distance_mm,
                "corrected_deviation_mm": corrected_distance_mm
            })

    return {
        "centerline_values_mm": centerline_values_mm,
        "corrected_values_mm": corrected_values_mm,
        "distance_samples": distance_samples,
        "sampled_point_count": sampled_point_count,
        "unreadable_distance_count": unreadable_distance_count,
        "candidate_point_count_before_outlier_filter": len(corrected_values_mm),
        "rejected_outside_segment": rejected_outside_segment,
        "rejected_noise": rejected_noise
    }


def _percentile_mm(values_mm, percentile):
    if not values_mm:
        return None
    sorted_values = sorted(values_mm)
    index = int(math.ceil((percentile / 100.0) * len(sorted_values))) - 1
    if index < 0:
        index = 0
    if index >= len(sorted_values):
        index = len(sorted_values) - 1
    return sorted_values[index]


def _filter_extreme_noise_values(values_mm):
    """Remove high-end outliers without discarding a consistently shifted wall."""
    if not values_mm:
        return [], 0, None
    if len(values_mm) < 8:
        return list(values_mm), 0, None

    q1_mm = _percentile_mm(values_mm, 25.0)
    q3_mm = _percentile_mm(values_mm, 75.0)
    if q1_mm is None or q3_mm is None:
        return list(values_mm), 0, None

    iqr_mm = max(0.0, q3_mm - q1_mm)
    upper_fence_mm = max(
        q3_mm + (1.5 * iqr_mm),
        NOISE_OUTLIER_FLOOR_MM
    )
    filtered_values = [value for value in values_mm if value <= upper_fence_mm]
    if not filtered_values:
        return list(values_mm), 0, upper_fence_mm
    return (
        filtered_values,
        len(values_mm) - len(filtered_values),
        upper_fence_mm
    )


def _filter_extreme_noise_samples(samples):
    if not samples:
        return [], 0, None
    values_mm = [
        sample.get("corrected_deviation_mm")
        for sample in samples
        if hasattr(sample, "get")
        and sample.get("corrected_deviation_mm") is not None
    ]
    _filtered_values, rejected_count, upper_fence_mm = (
        _filter_extreme_noise_values(values_mm)
    )
    if upper_fence_mm is None:
        return list(samples), 0, None

    filtered_samples = [
        sample for sample in samples
        if hasattr(sample, "get")
        and sample.get("corrected_deviation_mm") is not None
        and sample.get("corrected_deviation_mm") <= upper_fence_mm
    ]
    if not filtered_samples:
        return list(samples), 0, upper_fence_mm
    return filtered_samples, rejected_count, upper_fence_mm


def _average_mm(values_mm):
    if not values_mm:
        return None
    return sum(values_mm) / float(len(values_mm))


def _max_mm(values_mm):
    if not values_mm:
        return None
    return max(values_mm)


def _get_classification_distance_mm(stats):
    if not hasattr(stats, "get"):
        return None
    return stats.get("p75_mm")


def _cluster_sort_key(cluster):
    if not hasattr(cluster, "get"):
        return (0.0, 0, 0.0)
    severity_rank = 2 if cluster.get("status") == STATUS_CRITICAL else 1
    return (
        -float(cluster.get("length_mm") or 0.0),
        -severity_rank,
        -int(cluster.get("point_count") or 0)
    )


def _summarize_cluster_samples(samples, tolerance, cluster_index):
    if not samples:
        return None

    sorted_samples = sorted(
        samples,
        key=lambda sample: sample.get("projection_distance_mm") or 0.0
    )
    corrected_values_mm = [
        sample.get("corrected_deviation_mm")
        for sample in sorted_samples
        if sample.get("corrected_deviation_mm") is not None
    ]
    if not corrected_values_mm:
        return None

    start_sample = sorted_samples[0]
    end_sample = sorted_samples[-1]
    start_distance_mm = start_sample.get("projection_distance_mm") or 0.0
    end_distance_mm = end_sample.get("projection_distance_mm") or start_distance_mm
    length_mm = max(0.0, end_distance_mm - start_distance_mm)
    density_per_m = (
        float(len(corrected_values_mm)) / max(length_mm / 1000.0, 0.001)
        if length_mm > 0.0
        else float(len(corrected_values_mm)) * 1000.0
    )
    cluster_p75_mm = _percentile_mm(corrected_values_mm, 75.0)
    cluster_status = _classify_deviation(cluster_p75_mm, tolerance)
    if cluster_status == STATUS_OK:
        return None

    return {
        "cluster_index": cluster_index,
        "status": cluster_status,
        "point_count": len(corrected_values_mm),
        "length_mm": length_mm,
        "density_per_m": density_per_m,
        "start_parameter": start_sample.get("projection_parameter", 0.0),
        "end_parameter": end_sample.get("projection_parameter", 0.0),
        "start_distance_mm": start_distance_mm,
        "end_distance_mm": end_distance_mm,
        "avg_mm": _average_mm(corrected_values_mm),
        "median_mm": _percentile_mm(corrected_values_mm, 50.0),
        "p75_mm": cluster_p75_mm,
        "p90_mm": _percentile_mm(corrected_values_mm, 90.0),
        "p95_mm": _percentile_mm(corrected_values_mm, 95.0),
        "max_mm": _max_mm(corrected_values_mm)
    }


def _build_deviation_clusters(stats, tolerance):
    if not hasattr(stats, "get"):
        return [], u"No distance statistics were available."

    samples = stats.get("distance_samples") or []
    if not samples:
        return [], u"No candidate point samples were available for clustering."

    threshold_mm = tolerance.get("ok_max", 30.0)
    issue_samples = [
        sample for sample in samples
        if hasattr(sample, "get")
        and sample.get("corrected_deviation_mm") is not None
        and sample.get("corrected_deviation_mm") > threshold_mm
    ]
    if not issue_samples:
        return [], u"No corrected deviation samples exceeded OK Max threshold."

    issue_samples = sorted(
        issue_samples,
        key=lambda sample: sample.get("projection_distance_mm") or 0.0
    )
    gap_mm = CLUSTER_MAX_GAP_MM
    raw_clusters = []
    current_cluster = []
    previous_distance_mm = None
    for sample in issue_samples:
        current_distance_mm = sample.get("projection_distance_mm")
        if current_distance_mm is None:
            continue
        if (
            previous_distance_mm is not None
            and current_cluster
            and (current_distance_mm - previous_distance_mm) > gap_mm
        ):
            raw_clusters.append(current_cluster)
            current_cluster = []
        current_cluster.append(sample)
        previous_distance_mm = current_distance_mm
    if current_cluster:
        raw_clusters.append(current_cluster)

    valid_clusters = []
    rejected_reasons = []
    for raw_cluster in raw_clusters:
        cluster = _summarize_cluster_samples(
            raw_cluster,
            tolerance,
            len(valid_clusters) + 1
        )
        if cluster is None:
            rejected_reasons.append(u"cluster status resolved to OK")
            continue
        if cluster["point_count"] < MIN_DEVIATION_CLUSTER_POINTS:
            rejected_reasons.append(
                u"{0} points".format(cluster["point_count"])
            )
            continue
        if cluster["length_mm"] < MIN_DEVIATION_CLUSTER_LENGTH_MM:
            rejected_reasons.append(
                u"{0:.1f} mm length".format(cluster["length_mm"])
            )
            continue
        if cluster["density_per_m"] < MIN_DEVIATION_CLUSTER_DENSITY_PER_M:
            rejected_reasons.append(
                u"{0:.1f} points/m".format(cluster["density_per_m"])
            )
            continue
        cluster["cluster_index"] = len(valid_clusters) + 1
        valid_clusters.append(cluster)

    if valid_clusters:
        return sorted(valid_clusters, key=_cluster_sort_key), u""

    if rejected_reasons:
        return [], (
            u"No deviation cluster met minimum points/length/density thresholds "
            u"({0})."
        ).format(u"; ".join(rejected_reasons[:3]))
    return [], u"No deviation cluster met minimum points/length/density thresholds."


def _get_wall_surface_reliability_warning(stats):
    if not hasattr(stats, "get"):
        return u"No distance statistics were available."

    candidate_count = int(stats.get("point_count") or 0)
    sampled_count = int(stats.get("sampled_point_count") or 0)
    if candidate_count < MIN_RELIABLE_CANDIDATE_POINTS:
        return (
            u"No Reliable Wall Surface Data: only {0} candidate Wall-surface "
            u"points remained after projection, distance, and outlier filters "
            u"({1} sampled points). Minimum required: {2}."
        ).format(candidate_count, sampled_count, MIN_RELIABLE_CANDIDATE_POINTS)

    before_filter_count = int(
        stats.get("candidate_point_count_before_outlier_filter") or 0
    )
    if before_filter_count > 0:
        minimum_stable_count = max(
            MIN_RELIABLE_CANDIDATE_POINTS,
            int(math.ceil(before_filter_count * 0.25))
        )
        if candidate_count < minimum_stable_count:
            return (
                u"No Reliable Wall Surface Data: candidate distribution was "
                u"unstable after extreme-noise filtering ({0}/{1} candidates "
                u"kept)."
            ).format(candidate_count, before_filter_count)

    return u""


def _summarize_wall_face_distances(distance_values):
    if not isinstance(distance_values, dict):
        distance_values = {}
    samples_before_filter = distance_values.get("distance_samples") or []
    filtered_samples, rejected_extreme_noise, outlier_fence_mm = (
        _filter_extreme_noise_samples(samples_before_filter)
    )
    if filtered_samples:
        corrected_values_before_filter_mm = [
            sample.get("corrected_deviation_mm")
            for sample in samples_before_filter
            if hasattr(sample, "get")
            and sample.get("corrected_deviation_mm") is not None
        ]
        corrected_values_mm = [
            sample.get("corrected_deviation_mm")
            for sample in filtered_samples
            if hasattr(sample, "get")
            and sample.get("corrected_deviation_mm") is not None
        ]
        centerline_values_mm = [
            sample.get("centerline_distance_mm")
            for sample in filtered_samples
            if hasattr(sample, "get")
            and sample.get("centerline_distance_mm") is not None
        ]
    else:
        corrected_values_before_filter_mm = (
            distance_values.get("corrected_values_mm") or []
        )
        corrected_values_mm, rejected_extreme_noise, outlier_fence_mm = (
            _filter_extreme_noise_values(corrected_values_before_filter_mm)
        )
        centerline_values_mm = distance_values.get("centerline_values_mm") or []
    if not corrected_values_mm:
        return {
            "point_count": 0,
            "distance_samples": [],
            "sampled_point_count": distance_values.get("sampled_point_count", 0),
            "candidate_point_count_before_outlier_filter": distance_values.get(
                "candidate_point_count_before_outlier_filter",
                0
            ),
            "avg_mm": None,
            "median_mm": None,
            "p75_mm": None,
            "p90_mm": None,
            "p95_mm": None,
            "max_mm": None,
            "centerline_avg_mm": None,
            "centerline_median_mm": None,
            "centerline_p75_mm": None,
            "centerline_p90_mm": None,
            "centerline_p95_mm": None,
            "centerline_max_mm": None,
            "unreadable_distance_count": distance_values.get(
                "unreadable_distance_count",
                0
            ),
            "rejected_outside_segment": distance_values.get(
                "rejected_outside_segment",
                0
            ),
            "rejected_noise": distance_values.get("rejected_noise", 0),
            "rejected_extreme_noise": rejected_extreme_noise,
            "outlier_fence_mm": outlier_fence_mm
        }
    return {
        "point_count": len(corrected_values_mm),
        "distance_samples": filtered_samples,
        "sampled_point_count": distance_values.get("sampled_point_count", 0),
        "candidate_point_count_before_outlier_filter": distance_values.get(
            "candidate_point_count_before_outlier_filter",
            len(corrected_values_before_filter_mm)
        ),
        "avg_mm": _average_mm(corrected_values_mm),
        "median_mm": _percentile_mm(corrected_values_mm, 50.0),
        "p75_mm": _percentile_mm(corrected_values_mm, 75.0),
        "p90_mm": _percentile_mm(corrected_values_mm, 90.0),
        "p95_mm": _percentile_mm(corrected_values_mm, 95.0),
        "max_mm": _max_mm(corrected_values_mm),
        "centerline_avg_mm": _average_mm(centerline_values_mm),
        "centerline_median_mm": _percentile_mm(centerline_values_mm, 50.0),
        "centerline_p75_mm": _percentile_mm(centerline_values_mm, 75.0),
        "centerline_p90_mm": _percentile_mm(centerline_values_mm, 90.0),
        "centerline_p95_mm": _percentile_mm(centerline_values_mm, 95.0),
        "centerline_max_mm": _max_mm(centerline_values_mm),
        "unreadable_distance_count": distance_values.get(
            "unreadable_distance_count",
            0
        ),
        "rejected_outside_segment": distance_values.get(
            "rejected_outside_segment",
            0
        ),
        "rejected_noise": distance_values.get("rejected_noise", 0),
        "rejected_extreme_noise": rejected_extreme_noise,
        "outlier_fence_mm": outlier_fence_mm
    }


def _format_distance_triplet(stats):
    if not stats or not hasattr(stats, "get") or not stats.get("point_count"):
        return u"N/A"
    corrected_text = (
        u"Face Avg {0:.1f} / P75 {1:.1f} / P90 {2:.1f} / "
        u"P95 {3:.1f} / Max {4:.1f} mm"
    ).format(
        stats.get("avg_mm", 0.0),
        stats.get("p75_mm", 0.0),
        stats.get("p90_mm", 0.0),
        stats.get("p95_mm", 0.0),
        stats.get("max_mm", 0.0)
    )
    centerline_text = (
        u"Centerline Avg {0:.1f} / P90 {1:.1f} / P95 {2:.1f} / "
        u"Max {3:.1f} mm"
    ).format(
        stats.get("centerline_avg_mm", 0.0),
        stats.get("centerline_p90_mm", 0.0),
        stats.get("centerline_p95_mm", 0.0),
        stats.get("centerline_max_mm", 0.0)
    )
    return u"{0} | {1} | Candidates {2}/{3}".format(
        corrected_text,
        centerline_text,
        stats.get("point_count", 0),
        stats.get("sampled_point_count", 0)
    )


def _build_coordinate_mode_stats(
    raw_points,
    start,
    end,
    wall_half_width_ft,
    candidate_limit_ft,
    sampling_context
):
    mode_stats = []
    for mode_name in (u"raw", u"transform", u"total_transform"):
        mode_points = _get_points_for_coordinate_mode(
            raw_points,
            mode_name,
            sampling_context
        )
        distance_values = _calculate_wall_face_distance_values_mm(
            mode_points,
            start,
            end,
            wall_half_width_ft,
            candidate_limit_ft
        )
        stats = _summarize_wall_face_distances(distance_values)
        stats["mode"] = mode_name
        stats["summary"] = _format_distance_triplet(stats)
        mode_stats.append(stats)
    return mode_stats


def _select_coordinate_mode(mode_stats):
    candidates = []
    for stats in mode_stats or []:
        if not hasattr(stats, "get"):
            continue
        classification_mm = _get_classification_distance_mm(stats)
        if classification_mm is None or not stats.get("point_count"):
            continue
        candidates.append(stats)
    if not candidates:
        return None

    reasonable_candidates = [
        stats for stats in candidates
        if _get_classification_distance_mm(stats) < COORDINATE_MISMATCH_THRESHOLD_MM
    ]
    reliable_candidates = [
        stats for stats in reasonable_candidates
        if int(stats.get("point_count") or 0) >= MIN_RELIABLE_CANDIDATE_POINTS
    ]
    sort_key = lambda item: (
        _get_classification_distance_mm(item),
        -int(item.get("point_count") or 0)
    )
    if reliable_candidates:
        return sorted(reliable_candidates, key=sort_key)[0]
    if reasonable_candidates:
        return sorted(reasonable_candidates, key=sort_key)[0]
    return sorted(candidates, key=sort_key)[0]


def _get_sample_debug(raw_points, sampling_context, selected_mode):
    raw_samples = list(raw_points or [])[:3]
    transform_samples = _get_points_for_coordinate_mode(
        raw_samples,
        u"transform",
        sampling_context
    )
    total_transform_samples = _get_points_for_coordinate_mode(
        raw_samples,
        u"total_transform",
        sampling_context
    )
    used_samples = _get_points_for_coordinate_mode(
        raw_samples,
        selected_mode,
        sampling_context
    )
    return {
        "first_sample_raw_xyz": [_format_xyz(point) for point in raw_samples],
        "first_sample_transform_xyz": [
            _format_xyz(point) for point in transform_samples
        ],
        "first_sample_total_transform_xyz": [
            _format_xyz(point) for point in total_transform_samples
        ],
        "first_sample_used_xyz": [_format_xyz(point) for point in used_samples]
    }


def _evaluate_coordinate_modes(
    raw_points,
    start,
    end,
    wall_half_width_ft,
    candidate_limit_ft,
    sampling_context
):
    mode_stats = _build_coordinate_mode_stats(
        raw_points,
        start,
        end,
        wall_half_width_ft,
        candidate_limit_ft,
        sampling_context
    )
    selected_stats = _select_coordinate_mode(mode_stats)
    if selected_stats is None:
        return {
            "coordinate_mode": u"N/A",
            "selected_stats": {},
            "mode_stats": mode_stats,
            "distance_sanity_check": u"No readable distances",
            "sample_debug": _get_sample_debug(raw_points, sampling_context, u"raw")
        }

    selected_mode = selected_stats.get("mode", u"raw")
    classification_mm = _get_classification_distance_mm(selected_stats)
    if (
        classification_mm is not None
        and classification_mm < COORDINATE_MISMATCH_THRESHOLD_MM
    ):
        sanity = u"OK"
    else:
        sanity = (
            u"Coordinate Mismatch: best {0} distance is {1:.1f} mm, above "
            u"{2:.0f} mm sanity threshold."
        ).format(
            CLASSIFICATION_PERCENTILE_LABEL,
            classification_mm or 0.0,
            COORDINATE_MISMATCH_THRESHOLD_MM
        )

    return {
        "coordinate_mode": selected_mode,
        "selected_stats": selected_stats,
        "mode_stats": mode_stats,
        "distance_sanity_check": sanity,
        "sample_debug": _get_sample_debug(
            raw_points,
            sampling_context,
            selected_mode
        )
    }


def _classify_deviation(classification_deviation_mm, tolerance):
    if classification_deviation_mm is None:
        return STATUS_NO_POINT_DATA
    if classification_deviation_mm <= tolerance["ok_max"]:
        return STATUS_OK
    if classification_deviation_mm <= tolerance["review_max"]:
        return STATUS_REVIEW
    return STATUS_CRITICAL


def _calculate_wall_deviation(wall, point_cloud, sampling_context, tolerance):
    start, end, line_error = _get_wall_line_segment_for_calculation(wall)
    if start is None or end is None:
        return _create_skipped_result(
            wall,
            line_error or u"Wall LocationCurve was unavailable for 2D deviation calculation."
        )

    wall_length_mm = _wall_segment_length_mm(start, end)
    if wall_length_mm is not None and wall_length_mm < MIN_WALL_SEGMENT_LENGTH_MM:
        return _create_skipped_result(
            wall,
            u"Wall skipped: LocationCurve length {0:.1f} mm is shorter than "
            u"the {1:.0f} mm minimum for Scan QC deviation sampling.".format(
                wall_length_mm,
                MIN_WALL_SEGMENT_LENGTH_MM
            )
        )

    raw_points, sampling_error = _sample_wall_points(
        wall,
        point_cloud,
        sampling_context
    )
    if not raw_points:
        return _create_no_point_result(
            wall,
            sampling_error or u"No Point Data in Wall filter box."
        )

    wall_type_width_ft, width_warning = _get_wall_type_width_ft(wall)
    wall_half_width_ft = wall_type_width_ft / 2.0 if wall_type_width_ft > 0 else 0.0
    candidate_limit_ft = wall_half_width_ft + _mm_to_internal(
        WALL_FACE_NOISE_MARGIN_MM
    )

    coordinate_result = _evaluate_coordinate_modes(
        raw_points,
        start,
        end,
        wall_half_width_ft,
        candidate_limit_ft,
        sampling_context
    )
    coordinate_result["wall_endpoints"] = u"{0} -> {1}".format(
        _format_xyz(start),
        _format_xyz(end)
    )
    coordinate_result["wall_type_width_mm"] = _internal_to_mm(wall_type_width_ft)
    coordinate_result["wall_half_width_mm"] = _internal_to_mm(wall_half_width_ft)
    coordinate_result["candidate_limit_mm"] = _internal_to_mm(candidate_limit_ft)
    coordinate_result["wall_width_warning"] = width_warning
    selected_stats = coordinate_result.get("selected_stats") or {}
    if not selected_stats.get("point_count"):
        return _create_no_reliable_result(
            wall,
            u"Point Cloud samples were returned, but no readable 2D distances "
            u"remained after Wall projection and candidate filters.",
            coordinate_result
        )

    reliability_warning = _get_wall_surface_reliability_warning(selected_stats)
    if reliability_warning:
        return _create_no_reliable_result(
            wall,
            reliability_warning,
            coordinate_result
        )

    classification_deviation_mm = _get_classification_distance_mm(selected_stats)
    if (
        classification_deviation_mm is None
        or classification_deviation_mm >= COORDINATE_MISMATCH_THRESHOLD_MM
    ):
        return _create_coordinate_mismatch_result(
            wall,
            coordinate_result.get(
                "distance_sanity_check",
                u"Coordinate Mismatch"
            ),
            coordinate_result
        )

    deviation_clusters, cluster_warning = _build_deviation_clusters(
        selected_stats,
        tolerance
    )
    selected_stats["deviation_clusters"] = deviation_clusters
    selected_stats["cluster_count"] = len(deviation_clusters)
    selected_stats["cluster_warning"] = cluster_warning

    avg_deviation_mm = selected_stats.get("avg_mm")
    max_deviation_mm = selected_stats.get("max_mm")
    primary_cluster = deviation_clusters[0] if deviation_clusters else None
    if primary_cluster:
        status = primary_cluster.get("status", STATUS_REVIEW)
        classification_deviation_mm = primary_cluster.get("p75_mm")
        classification_metric = CLUSTER_THRESHOLD_METRIC_LABEL
        skip_reason = u""
    else:
        status = STATUS_OK
        classification_metric = CLASSIFICATION_PERCENTILE_LABEL
        skip_reason = (
            cluster_warning
            or u"No contiguous deviation cluster met Review/Critical thresholds."
        )

    return {
        "wall": wall,
        "wall_id": get_element_id_value(wall.Id),
        "status": status,
        "avg_deviation_mm": avg_deviation_mm,
        "max_deviation_mm": max_deviation_mm,
        "p95_deviation_mm": selected_stats.get("p95_mm"),
        "classification_deviation_mm": classification_deviation_mm,
        "classification_metric": classification_metric,
        "median_deviation_mm": selected_stats.get("median_mm"),
        "p75_deviation_mm": selected_stats.get("p75_mm"),
        "p90_deviation_mm": selected_stats.get("p90_mm"),
        "raw_centerline_avg_mm": selected_stats.get("centerline_avg_mm"),
        "raw_centerline_max_mm": selected_stats.get("centerline_max_mm"),
        "raw_centerline_median_mm": selected_stats.get("centerline_median_mm"),
        "raw_centerline_p75_mm": selected_stats.get("centerline_p75_mm"),
        "raw_centerline_p90_mm": selected_stats.get("centerline_p90_mm"),
        "raw_centerline_p95_mm": selected_stats.get("centerline_p95_mm"),
        "corrected_avg_mm": selected_stats.get("avg_mm"),
        "corrected_max_mm": selected_stats.get("max_mm"),
        "corrected_median_mm": selected_stats.get("median_mm"),
        "corrected_p75_mm": selected_stats.get("p75_mm"),
        "corrected_p90_mm": selected_stats.get("p90_mm"),
        "corrected_p95_mm": selected_stats.get("p95_mm"),
        "wall_type_width_mm": coordinate_result.get("wall_type_width_mm"),
        "wall_half_width_mm": coordinate_result.get("wall_half_width_mm"),
        "candidate_limit_mm": coordinate_result.get("candidate_limit_mm"),
        "point_count": selected_stats.get("sampled_point_count", 0),
        "candidate_point_count": selected_stats.get("point_count", 0),
        "candidate_point_count_before_outlier_filter": selected_stats.get(
            "candidate_point_count_before_outlier_filter",
            0
        ),
        "rejected_outside_segment": selected_stats.get(
            "rejected_outside_segment",
            0
        ),
        "rejected_noise": selected_stats.get("rejected_noise", 0),
        "rejected_extreme_noise": selected_stats.get("rejected_extreme_noise", 0),
        "cluster_count": len(deviation_clusters),
        "deviation_clusters": deviation_clusters,
        "primary_cluster": primary_cluster,
        "cluster_length_mm": (
            primary_cluster.get("length_mm")
            if primary_cluster
            else None
        ),
        "cluster_status": (
            primary_cluster.get("status")
            if primary_cluster
            else u"N/A"
        ),
        "marker_center": _wall_marker_center(wall),
        "message": u"",
        "skip_reason": skip_reason,
        "sampling_status": u"Sampled",
        "coordinate_mode": coordinate_result.get("coordinate_mode", u"N/A"),
        "distance_sanity_check": coordinate_result.get(
            "distance_sanity_check",
            u"N/A"
        ),
        "coordinate_mode_stats": coordinate_result.get("mode_stats", []),
        "sample_debug": coordinate_result.get("sample_debug", {}),
        "wall_endpoints": coordinate_result.get("wall_endpoints", u"N/A"),
        "wall_width_warning": coordinate_result.get("wall_width_warning", u"")
    }


def _create_sampling_context(options, point_cloud):
    factory_type, resolution_method, factory_detail = (
        _resolve_point_cloud_filter_factory()
    )
    factory_error = u""
    if factory_type is None:
        factory_error = (
            u"PointCloudFilterFactory still unavailable from "
            u"Autodesk.Revit.DB.PointClouds. Import/reflection detail: {0}"
        ).format(factory_detail)

    transform, transform_error = _safe_transform(point_cloud, "GetTransform")
    total_transform, total_transform_error = _safe_transform(
        point_cloud,
        "GetTotalTransform"
    )
    coordinate_debug = {}
    coordinate_debug.update(
        _transform_to_debug(transform, "transform", transform_error)
    )
    coordinate_debug.update(
        _transform_to_debug(
            total_transform,
            "total_transform",
            total_transform_error
        )
    )
    coordinate_debug.update({
        "coordinate_mode_used": u"N/A",
        "distance_sanity_check": u"N/A",
        "first_wall_endpoints": u"N/A",
        "first_sample_raw_xyz": [],
        "first_sample_transform_xyz": [],
        "first_sample_total_transform_xyz": [],
        "first_sample_used_xyz": [],
        "first_wall_distance_mode_stats": []
    })

    return {
        "factory_type": factory_type,
        "factory_resolution": resolution_method,
        "factory_type_name": _type_full_name(factory_type),
        "factory_error": factory_error,
        "transform": transform,
        "total_transform": total_transform,
        "coordinate_debug": coordinate_debug,
        "search_margin_ft": _mm_to_internal(options["point_search_margin_mm"]),
        "average_distance_ft": _get_average_distance_ft(options),
        "max_points": _get_max_points_per_wall(options)
    }


def _append_count(result, wall_result):
    status = wall_result.get("status")
    if status == STATUS_OK:
        result["ok_count"] += 1
    elif status == STATUS_REVIEW:
        result["review_count"] += 1
    elif status == STATUS_CRITICAL:
        result["critical_count"] += 1
    elif status == STATUS_NO_POINT_DATA:
        result["no_point_data_count"] += 1
    elif status == STATUS_NO_RELIABLE_WALL_SURFACE_DATA:
        result["no_reliable_data_count"] += 1
    elif status == STATUS_COORDINATE_MISMATCH:
        result["coordinate_mismatch_count"] += 1
    elif status == STATUS_SKIPPED:
        pass

    if status not in (STATUS_OK, STATUS_REVIEW, STATUS_CRITICAL):
        result["skipped_wall_count"] += 1


def _update_sampling_summary(result):
    sampled_count = 0
    mismatch_count = 0
    no_reliable_count = 0
    skipped_count = 0
    no_point_messages = []
    no_reliable_messages = []
    skipped_messages = []
    for row in result.get("results", []):
        if not hasattr(row, "get"):
            continue
        status = row.get("status")
        if status == STATUS_NO_POINT_DATA:
            message = row.get("message")
            if message:
                no_point_messages.append(message)
        elif status == STATUS_NO_RELIABLE_WALL_SURFACE_DATA:
            no_reliable_count += 1
            message = row.get("message")
            if message:
                no_reliable_messages.append(message)
        elif status == STATUS_COORDINATE_MISMATCH:
            mismatch_count += 1
        elif status == STATUS_SKIPPED:
            skipped_count += 1
            message = row.get("message")
            if message:
                skipped_messages.append(message)
        else:
            sampled_count += 1

    if sampled_count > 0 and (
        result["no_point_data_count"] > 0
        or mismatch_count > 0
        or no_reliable_count > 0
    ):
        result["point_cloud_sampling_status"] = u"Partial"
        result["sampling_failure_reason"] = (
            u"Some Walls had no point data, no reliable wall-surface data, "
            u"or coordinate mismatch."
        )
    elif sampled_count > 0:
        result["point_cloud_sampling_status"] = u"Sampled"
        result["sampling_failure_reason"] = u""
    elif mismatch_count > 0:
        result["point_cloud_sampling_status"] = u"Coordinate Mismatch"
        result["sampling_failure_reason"] = (
            u"Point Cloud samples were returned, but all sampled Walls exceeded "
            u"the coordinate sanity threshold."
        )
    elif no_reliable_count > 0:
        result["point_cloud_sampling_status"] = (
            STATUS_NO_RELIABLE_WALL_SURFACE_DATA
        )
        result["sampling_failure_reason"] = (
            no_reliable_messages[0]
            if no_reliable_messages
            else u"Candidate point distribution was not reliable enough."
        )
    elif no_point_messages:
        first_message = no_point_messages[0]
        if u"PointCloudFilterFactory" in first_message:
            result["point_cloud_sampling_status"] = u"Unavailable"
        elif u"failed" in first_message.lower() or u"exception" in first_message.lower():
            result["point_cloud_sampling_status"] = u"Sampling Error"
        else:
            result["point_cloud_sampling_status"] = u"No Point Data"
        result["sampling_failure_reason"] = first_message
    elif skipped_count > 0:
        result["point_cloud_sampling_status"] = STATUS_SKIPPED
        result["sampling_failure_reason"] = (
            skipped_messages[0]
            if skipped_messages
            else u"All candidate Walls were skipped before Point Cloud sampling."
        )


def _copy_first_wall_debug(result, wall_result):
    coordinate_debug = result.get("coordinate_debug")
    if not isinstance(coordinate_debug, dict) or not hasattr(wall_result, "get"):
        return

    if coordinate_debug.get("coordinate_mode_used") in (None, u"", u"N/A"):
        coordinate_debug["coordinate_mode_used"] = wall_result.get(
            "coordinate_mode",
            u"N/A"
        )
    if coordinate_debug.get("distance_sanity_check") in (None, u"", u"N/A"):
        coordinate_debug["distance_sanity_check"] = wall_result.get(
            "distance_sanity_check",
            u"N/A"
        )
    if coordinate_debug.get("first_wall_endpoints") in (None, u"", u"N/A"):
        coordinate_debug["first_wall_endpoints"] = wall_result.get(
            "wall_endpoints",
            u"N/A"
        )
    if not coordinate_debug.get("first_wall_distance_mode_stats"):
        coordinate_debug["first_wall_distance_mode_stats"] = wall_result.get(
            "coordinate_mode_stats",
            []
        )

    sample_debug = wall_result.get("sample_debug") or {}
    if not isinstance(sample_debug, dict):
        return
    for key in (
        "first_sample_raw_xyz",
        "first_sample_transform_xyz",
        "first_sample_total_transform_xyz",
        "first_sample_used_xyz"
    ):
        if not coordinate_debug.get(key):
            coordinate_debug[key] = sample_debug.get(key, [])


def calculate_wall_deviations(
    doc,
    active_view,
    selected_walls,
    point_clouds,
    selected_options,
    settings
):
    """Calculate Selected Walls MVP deviation without crashing Scan QC."""
    result = _create_result(selected_options)
    result["attempted"] = True

    point_cloud = _find_selected_point_cloud(point_clouds, selected_options)
    if point_cloud is None:
        result["errors"].append(
            u"Selected Point Cloud ElementId was not found in the active document."
        )
    else:
        try:
            result["point_cloud_name"] = get_point_cloud_name(point_cloud)
            result["point_cloud_id"] = get_element_id_value(point_cloud.Id)
        except Exception:
            pass

    target_walls, wall_collection_warning = collect_target_walls(
        doc,
        active_view,
        selected_walls,
        selected_options,
        settings
    )
    if wall_collection_warning:
        result["warnings"].append(wall_collection_warning)

    result["selected_wall_count"] = len(selected_walls or [])
    result["unfiltered_target_wall_count"] = len(target_walls)
    analysis_scope = selected_options.get("analysis_scope")
    if analysis_scope == ANALYSIS_SCOPE_ACTIVE_PLAN_LEVEL:
        result["active_plan_level_wall_count"] = len(target_walls)

    target_walls, filter_result = apply_target_wall_filters(
        target_walls,
        selected_options,
        settings,
        doc
    )
    result["target_wall_filter"] = filter_result
    result["target_wall_filter_summary"] = filter_result.get(
        "target_wall_filter_summary",
        u"None"
    )
    result["filtered_target_wall_count"] = filter_result.get(
        "filtered_target_wall_count",
        len(target_walls)
    )
    result["target_wall_count"] = len(target_walls)
    result["excluded_exterior_count"] = filter_result.get(
        "excluded_exterior_count",
        0
    )
    result["excluded_existing_count"] = filter_result.get(
        "excluded_existing_count",
        0
    )
    result["excluded_demolished_count"] = filter_result.get(
        "excluded_demolished_count",
        0
    )
    result["excluded_by_parameter_count"] = filter_result.get(
        "excluded_by_parameter_count",
        0
    )
    for warning in filter_result.get("warnings", []):
        if warning:
            result["warnings"].append(warning)

    if not target_walls:
        result["warnings"].append(
            u"No target Walls remained after Scan QC target wall filtering."
        )
        return result

    options = get_deviation_options(settings)
    if selected_options.get("top_n_callouts") is not None:
        options["top_n_callouts"] = selected_options.get("top_n_callouts")
    tolerance = _get_tolerance_options(selected_options, settings)
    result["tolerance_mm"] = tolerance
    result["max_process_wall_count"] = _get_max_process_walls(options)
    result["top_n_callouts"] = _get_top_n_callouts(options)

    walls_to_process = target_walls
    max_process_walls = result["max_process_wall_count"]
    if len(walls_to_process) > max_process_walls:
        skipped_by_limit = len(walls_to_process) - max_process_walls
        walls_to_process = walls_to_process[:max_process_walls]
        result["skipped_by_process_limit_count"] = skipped_by_limit
        result["skipped_wall_count"] += skipped_by_limit
        result["warnings"].append(
            u"{0} processing was limited by Max Process Walls: "
            u"processed first {1} of {2} target Walls; {3} Walls were "
            u"skipped by the processing limit.".format(
                selected_options.get("analysis_scope_label", u"Scan QC"),
                max_process_walls,
                len(target_walls),
                skipped_by_limit
            )
        )

    sampling_context = _create_sampling_context(options, point_cloud)
    result["coordinate_debug"] = sampling_context.get(
        "coordinate_debug",
        result.get("coordinate_debug", {})
    )
    if sampling_context.get("factory_type") is None:
        result["warnings"].append(sampling_context.get("factory_error"))

    result["calculation_note"] = (
        u"Scan QC {0} processing used {1} ({2}) and "
        u"PointCloudInstance.GetPoints(filter, averageDistance={3:.3f} ft, "
        u"numPoints={4}). Raw distances are 2D to Wall LocationCurve centerline; "
        u"reported deviations subtract WallType.Width / 2 and use wall-face "
        u"corrected values. Candidate points must project within the Wall line "
        u"segment and be within wall half width + {5:.0f} mm. "
        u"Extreme high-end candidate outliers are filtered before reporting. "
        u"Raw, GetTransform, and GetTotalTransform point coordinates were "
        u"compared; the lowest reliable corrected {6} mode was used. "
        u"Review/Critical callouts are created only when contiguous deviation "
        u"clusters exceed OK Max and meet minimum count, length, and density "
        u"thresholds ({7:.0f} mm max gap, {8:.0f} mm minimum length). "
        u"Only the top {9} Review/Critical callouts should be created in the "
        u"QC Plan View. Wall-level P90/P95/Max are output reference values "
        u"only. Corrected {6} >= {10:.0f} mm is treated as Coordinate Mismatch."
    ).format(
        selected_options.get("analysis_scope_label", u"Analysis Scope"),
        sampling_context.get("factory_type_name"),
        sampling_context.get("factory_resolution"),
        sampling_context.get("average_distance_ft"),
        sampling_context.get("max_points"),
        WALL_FACE_NOISE_MARGIN_MM,
        CLASSIFICATION_PERCENTILE_LABEL,
        CLUSTER_MAX_GAP_MM,
        MIN_DEVIATION_CLUSTER_LENGTH_MM,
        result["top_n_callouts"],
        COORDINATE_MISMATCH_THRESHOLD_MM
    )

    for wall in walls_to_process:
        try:
            wall_result = _calculate_wall_deviation(
                wall,
                point_cloud,
                sampling_context,
                tolerance
            )
        except Exception as ex:
            wall_result = _create_no_point_result(
                wall,
                u"Sampling Error: {0}".format(_to_text(ex))
            )

        result["results"].append(wall_result)
        result["processed_wall_count"] += 1
        _copy_first_wall_debug(result, wall_result)
        _append_count(result, wall_result)

    _update_sampling_summary(result)
    return result
