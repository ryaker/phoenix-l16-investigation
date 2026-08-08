import json


_marker_snapshot = None
_marker_site_ids = []


def marker_hit(frame, bp_loc, internal_dict):
    global _marker_snapshot
    target = frame.GetThread().GetProcess().GetTarget()
    _marker_snapshot = {
        str(breakpoint_id): target.FindBreakpointByID(breakpoint_id).GetHitCount()
        for breakpoint_id in _marker_site_ids
    }
    return False


def install_marker(debugger, marker_id, site_ids):
    global _marker_snapshot, _marker_site_ids
    _marker_snapshot = None
    _marker_site_ids = site_ids
    breakpoint = debugger.GetSelectedTarget().FindBreakpointByID(marker_id)
    breakpoint.SetScriptCallbackFunction(__name__ + ".marker_hit")
    breakpoint.SetAutoContinue(True)


def write_report(debugger, path, label, render_type, sites):
    target = debugger.GetSelectedTarget()
    counts = {}
    locations = {}
    for breakpoint_id, name in sites.items():
        breakpoint = target.FindBreakpointByID(int(breakpoint_id))
        counts[name] = breakpoint.GetHitCount()
        locations[name] = breakpoint.GetNumLocations()

    packet = {
        "label": label,
        "render_type": render_type,
        "counts": counts,
        "resolved_locations": locations,
    }
    if _marker_snapshot is not None:
        packet["marker_snapshot"] = {
            name: _marker_snapshot[str(int(breakpoint_id))]
            for breakpoint_id, name in sites.items()
        }
        packet["post_marker_counts"] = {
            name: counts[name] - packet["marker_snapshot"][name]
            for name in counts
        }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("EDITOR_RENDER_TYPE_REPORT " + path)
