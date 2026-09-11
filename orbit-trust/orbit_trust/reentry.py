"""Reentry exposure sandbox (handoff doc 08).

Supplied footprint only — never a conjunction report. Point representations, not
a census: the UI says "population represented by included sample points". No
atmospheric breakup, fragment survival or crash-site prediction. Missing asset
value stays unknown, not zero. Reentry inputs never change orbital policy.

Inclusion convention (doc 08): the footprint includes its outer boundary and
excludes the interior of holes; a point on a hole boundary counts as exposed
(documented conservative convention). Overlapping MultiPolygon parts do not
double count (dedup is by point id).
"""

from __future__ import annotations

from decimal import Decimal

from .models import parse_utc
from .money import dec, fmt

_EPS = 1e-12
_MAX_POINTS = 1000  # combined population + asset points (doc 05)
_MAX_ABS_LAT = 85.0  # doc 05/08: latitude within [-85, 85]


def _on_segment(p, a, b) -> bool:
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > _EPS:
        return False
    return (
        min(a[0], b[0]) - _EPS <= p[0] <= max(a[0], b[0]) + _EPS
        and min(a[1], b[1]) - _EPS <= p[1] <= max(a[1], b[1]) + _EPS
    )


def _on_boundary(p, ring) -> bool:
    return any(_on_segment(p, ring[i], ring[i + 1]) for i in range(len(ring) - 1))


def _inside(p, ring) -> bool:
    """Ray casting over the ring's unique vertices. Boundary results are
    undefined here and handled separately by _on_boundary."""
    verts = ring[:-1] if ring[0] == ring[-1] else ring
    x, y = p
    inside = False
    n = len(verts)
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _in_polygon(p, rings) -> bool:
    outer = rings[0]
    if not (_on_boundary(p, outer) or _inside(p, outer)):
        return False
    for hole in rings[1:]:
        if _inside(p, hole) and not _on_boundary(p, hole):  # strict hole interior excluded
            return False
    return True


def point_in_geometry(p, geom: dict) -> bool:
    if geom["type"] == "Polygon":
        return _in_polygon(p, geom["coordinates"])
    return any(_in_polygon(p, poly) for poly in geom["coordinates"])


def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _proper_cross(p1, p2, p3, p4) -> bool:
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


def _self_intersects(ring) -> bool:
    # ponytail: naive O(n^2) edge-pair scan; rings here are small.
    edges = [(ring[i], ring[i + 1]) for i in range(len(ring) - 1)]
    n = len(edges)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                continue  # adjacent edges legitimately share a vertex
            if _proper_cross(*edges[i], *edges[j]):
                return True
    return False


def _validate_geometry(geom: dict) -> str | None:
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for rings in polys:
        for ring in rings:
            if ring[0] != ring[-1]:
                return "domain_ring_not_closed"
            if any(abs(lat) > _MAX_ABS_LAT for _lon, lat in ring):
                return "domain_latitude_out_of_range"
            # an edge spanning >180deg of longitude crosses the antimeridian
            if any(abs(ring[i][0] - ring[i + 1][0]) > 180 for i in range(len(ring) - 1)):
                return "domain_dateline_crossing"
            if _self_intersects(ring):
                return "domain_self_intersecting_ring"
        outer = rings[0]
        for hole in rings[1:]:
            for v in hole[:-1]:
                if not (_on_boundary(v, outer) or _inside(v, outer)):
                    return "domain_hole_not_contained"
    return None


def validate_scenario(scn: dict) -> str | None:
    """Domain geometry checks (docs 05/08). Returns a rejection reason or None.
    These supplement the JSON Schema and never guess a corrected polygon."""
    if parse_utc(scn["window_start"]) >= parse_utc(scn["window_end"]):
        return "domain_window_unordered"
    total = len(scn.get("population_points", [])) + len(scn.get("asset_points", []))
    if total > _MAX_POINTS:
        return "domain_point_budget_exceeded"
    return _validate_geometry(scn["footprint"])


def _dedup(records: list[dict], id_key: str) -> list[dict]:
    """Deduplicate identical ids; reject conflicting duplicate bodies (doc 08)."""
    seen: dict[str, dict] = {}
    for r in records:
        rid = r[id_key]
        if rid in seen:
            if seen[rid] != r:
                raise ValueError(f"conflicting_duplicate_{id_key}:{rid}")
            continue
        seen[rid] = r
    return list(seen.values())


def evaluate(scn: dict) -> dict:
    reason = validate_scenario(scn)
    if reason:
        return {"status": "rejected", "reason": reason}

    footprint = scn["footprint"]
    pop = _dedup(scn.get("population_points", []), "sample_id")
    assets = _dedup(scn.get("asset_points", []), "asset_id")

    included_pop = [pt for pt in pop if point_in_geometry(pt["coordinates"], footprint)]
    represented = sum(pt["represented_population"] for pt in included_pop)

    included_assets = [a for a in assets if point_in_geometry(a["coordinates"], footprint)]

    value_by_currency: dict[str, Decimal] = {}
    unavailable_value = 0
    for a in included_assets:
        rv = a["replacement_value"]
        if rv is None:
            unavailable_value += 1
            continue
        value_by_currency[rv["currency"]] = value_by_currency.get(rv["currency"], Decimal(0)) + dec(rv["amount"])

    # conditional damage only for included assets with both vulnerability inputs
    damage_by_currency: dict[str, Decimal] = {}
    have_vuln = missing_vuln = 0
    for a in included_assets:
        rv = a["replacement_value"]
        pd = a.get("probability_of_damage")
        mlf = a.get("mean_loss_fraction")
        if rv is not None and pd is not None and mlf is not None:
            have_vuln += 1
            expected = dec(pd) * dec(mlf) * dec(rv["amount"])
            damage_by_currency[rv["currency"]] = damage_by_currency.get(rv["currency"], Decimal(0)) + expected
        else:
            missing_vuln += 1

    if have_vuln == 0:
        damage_status = "unavailable_missing_vulnerability"
    elif missing_vuln > 0:
        damage_status = "partial"  # sum only known terms, labelled partial
    else:
        damage_status = "available"

    return {
        "included_population_ids": [pt["sample_id"] for pt in included_pop],
        "represented_population": represented,
        "included_asset_ids": [a["asset_id"] for a in included_assets],
        "asset_count": len(included_assets),
        "exposed_value_by_currency": {c: fmt(v) for c, v in value_by_currency.items()},
        "unavailable_value_count": unavailable_value,
        "damage_status": damage_status,
        "conditional_expected_damage_by_currency": {c: fmt(v) for c, v in damage_by_currency.items()},
    }
