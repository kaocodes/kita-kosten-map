"""Load geographic metadata separately from municipal tariff catalogs."""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def load_registry(root=ROOT):
    return json.loads((Path(root) / "data/municipality_registry.json").read_text())


def active_municipalities(registry):
    return [entry for entry in registry["municipalities"] if entry["active"]]


def validate_registry(registry, cities, root=ROOT):
    """Check registry completeness, tariff links and archived AGS assignments."""
    errors = []

    def fail(location, message):
        errors.append(f"registry.{location}: {message}")

    if registry.get("schema_version") != "1.0":
        fail("schema_version", "Unsupported schema version")
    entries = registry.get("municipalities", [])
    areas = registry.get("areas", [])
    if not entries or not isinstance(entries, list) or not isinstance(areas, list):
        return errors + ["registry: Municipality and area lists are required"]
    municipalities = {}
    ags_seen = set()
    for entry in entries:
        city_id = entry.get("id", "<missing-id>")
        required = {"id", "name", "ags", "active", "region_id", "tariff_id", "area_id"}
        if required - entry.keys():
            fail(city_id, "Missing municipality fields: " + ", ".join(sorted(required - entry.keys())))
            continue
        if not isinstance(city_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", city_id):
            fail(str(city_id), "Invalid stable municipality identifier")
            continue
        if city_id in municipalities:
            fail(city_id, "Duplicate municipality identifier")
        municipalities[city_id] = entry
        ags = entry["ags"]
        if not isinstance(ags, str) or not re.fullmatch(r"[0-9]{8}", ags):
            fail(city_id, "AGS must be an eight-digit string")
        elif ags in ags_seen:
            fail(city_id, "Duplicate municipal AGS")
        else:
            ags_seen.add(ags)
        if type(entry["active"]) is not bool:
            fail(city_id, "Active status must be boolean")
        for field in ("name", "region_id", "tariff_id", "area_id"):
            if not isinstance(entry[field], str) or not entry[field]:
                fail(city_id, f"A non-empty {field} is required")
    if errors:
        return errors
    catalogs = {city.get("id", "<missing-id>"): city for city in cities}
    expected = {entry["tariff_id"] for entry in entries if entry["active"]}
    registered = {entry["tariff_id"] for entry in entries}
    for tariff_id in sorted(expected - catalogs.keys()):
        fail(tariff_id, "Missing tariff catalog for an active municipality")
    for tariff_id in sorted(catalogs.keys() - registered):
        fail(tariff_id, "Unregistered tariff catalog")

    geometry = registry.get("geometry_reference", {})
    geometry_fields = {"path", "sha256", "key_property", "name_property", "source_url", "license_url"}
    if not isinstance(geometry, dict) or any(not isinstance(geometry.get(key), str) or not geometry[key]
                                             for key in geometry_fields):
        return errors + ["registry.geometry_reference: Missing geometry provenance or key fields"]
    try:
        path = Path(root) / geometry["path"]
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != geometry["sha256"]:
            fail("geometry_reference", "Archived geometry does not match the stored hash")
        features = json.loads(content)["features"]
        by_key = {}
        for feature in features:
            key = feature["properties"][geometry["key_property"]]
            by_key.setdefault(key, []).append(feature)
    except (KeyError, OSError, ValueError, TypeError):
        return errors + ["registry.geometry_reference: Cannot read the archived geometry reference"]

    area_ids = set()
    by_area_id = {}
    for area in areas:
        area_id = area.get("id", "<missing-id>")
        required = {"id", "kind", "municipality_id", "parent_id", "tariff_id", "geometry_key"}
        if required - area.keys():
            fail(str(area_id), "Missing area fields")
            continue
        if not isinstance(area_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", area_id):
            fail(str(area_id), "A stable area identifier is required")
            continue
        if any(not isinstance(area[key], str) or not area[key]
               for key in ("kind", "municipality_id", "tariff_id", "geometry_key")):
            fail(area_id, "Area references must be non-empty strings")
            continue
        if area_id in area_ids:
            fail(area_id, "Duplicate area identifier")
        area_ids.add(area_id)
        by_area_id[area_id] = area
        municipality = municipalities.get(area["municipality_id"])
        if municipality is None:
            fail(area_id, "Unknown parent municipality")
            continue
        if area["tariff_id"] != municipality["tariff_id"]:
            fail(area_id, "Area tariff differs from its municipality")
        if area["kind"] not in {"municipality", "district"}:
            fail(area_id, "Unknown area kind")
        matches = by_key.get(area["geometry_key"], [])
        if len(matches) != 1:
            fail(area_id, "Geometry key must identify exactly one archived feature")
        if area["kind"] == "municipality":
            if area["geometry_key"] != municipality["ags"] or area["parent_id"] is not None:
                fail(area_id, "Municipal area must use its AGS and have no parent area")
            if len(matches) == 1 and matches[0]["properties"].get(geometry["name_property"]) != municipality["name"]:
                fail(area_id, "Official name differs from the archived AGS assignment")
        elif area["parent_id"] != municipality["area_id"]:
            fail(area_id, "District must reference the municipal parent area")
    for entry in entries:
        area = by_area_id.get(entry["area_id"])
        if area is None or area["municipality_id"] != entry["id"] or area["kind"] != "municipality":
            fail(entry["id"], "Missing or mismatched municipal area")
        catalog = catalogs.get(entry["tariff_id"])
        if catalog and entry["tariff_id"] == entry["id"] and catalog.get("name") != entry["name"]:
            fail(entry["id"], "Catalog name differs from the registry")
    return errors
