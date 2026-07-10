# -*- coding: utf-8 -*-

"""Small in-memory cache for Scan QC setup data in a persistent pyRevit engine."""


_CACHE = {}
_REGISTERED_APPLICATION_IDS = set()
_REGISTERED_SUBSCRIPTION_COUNTS = {}


def _document_key(doc):
    try:
        return int(doc.GetHashCode())
    except Exception:
        return id(doc)


def _application_key(application):
    try:
        return int(application.GetHashCode())
    except Exception:
        return id(application)


def _value_is_valid(value):
    values = value if isinstance(value, (list, tuple)) else [value]
    for item in values:
        if item is None:
            continue
        try:
            if hasattr(item, "IsValidObject") and not item.IsValidObject:
                return False
        except Exception:
            return False
    return True


def get_or_collect(doc, cache_name, collector):
    doc_key = _document_key(doc)
    document_cache = _CACHE.setdefault(doc_key, {})
    if document_cache.get("__document__") is not doc:
        document_cache.clear()
        document_cache["__document__"] = doc
    cached_value = document_cache.get(cache_name)
    if cached_value is not None and _value_is_valid(cached_value):
        return cached_value, True

    value = collector()
    document_cache[cache_name] = value
    return value, False


def set_cached_value(doc, cache_name, value):
    document_cache = _CACHE.setdefault(_document_key(doc), {})
    document_cache["__document__"] = doc
    document_cache[cache_name] = value


def invalidate_document(doc):
    if doc is None:
        return
    _CACHE.pop(_document_key(doc), None)


def _on_document_changed(sender, event_args):
    try:
        invalidate_document(event_args.GetDocument())
    except Exception:
        pass


def _on_document_closing(sender, event_args):
    try:
        invalidate_document(event_args.Document)
    except Exception:
        pass


def register_document_invalidation(application):
    """Register best-effort invalidation once per Revit Application object."""
    application_key = _application_key(application)
    if application_key in _REGISTERED_APPLICATION_IDS:
        return
    subscription_count = 0
    try:
        application.DocumentChanged += _on_document_changed
        subscription_count += 1
    except Exception:
        pass
    try:
        application.DocumentClosing += _on_document_closing
        subscription_count += 1
    except Exception:
        pass
    _REGISTERED_APPLICATION_IDS.add(application_key)
    _REGISTERED_SUBSCRIPTION_COUNTS[application_key] = subscription_count


def get_runtime_diagnostics():
    """Return lightweight cache/event counts for development profiling."""
    application_count = len(_REGISTERED_APPLICATION_IDS)
    return {
        "scan_cache_document_count": len(_CACHE),
        "scan_registered_application_count": application_count,
        "scan_external_event_subscription_count": sum(
            _REGISTERED_SUBSCRIPTION_COUNTS.values()
        )
    }
