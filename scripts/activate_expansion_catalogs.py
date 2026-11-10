"""Promote explicitly selected, fully reviewed catalogs without modifying calculators."""

import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION = "data/expansion/activation.json"


def read(root, path):
    return json.loads((root / path).read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_review(root, selection):
    """Fail closed when the review, input files or complete model coverage change."""
    review = read(root, selection["review_path"])
    if sha256(root / selection["review_path"]) != selection["review_sha256"]:
        raise ValueError("The selected calculation review has changed")
    for path, expected in review["input_sha256"].items():
        if sha256(root / path) != expected:
            raise ValueError("Reviewed input has changed: " + path)
    ids = selection["municipality_ids"]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Selected municipality IDs must be nonempty and unique")
    reviewed = {city["id"]: city for city in review["municipalities"]}
    manifest = {city["id"]: city for city in read(root, "data/expansion/manifest.json")["municipalities"]}
    count = review["configuration_space"]["configurations_per_municipality"]
    for city_id in ids:
        city = reviewed[city_id]
        if city["status"] != "supported_for_reviewed_care_models" or city["unavailable_groups"]:
            raise ValueError("Selected municipality is not fully supported: " + city_id)
        mask = base64.b64decode(city["supported_scenarios_bitset_base64"], validate=True)
        if not all(mask[i // 8] & (1 << (i % 8)) for i in range(count)):
            raise ValueError("Incomplete reviewed configuration space: " + city_id)
        if sha256(root / manifest[city_id]["path"]) != manifest[city_id]["sha256"]:
            raise ValueError("Normalized catalog hash mismatch: " + city_id)

    # The existing site uses 4 November; the audit used 10 November. Prove that
    # every dated record has identical validity, rather than changing either date.
    dates = {read(root, f"data/profiles/{name}.json")["as_of"] for name in ["default", "highest_band"]}
    for as_of in dates:
        if not selection["supported_as_of_from"] <= as_of <= selection["supported_as_of_to"]:
            raise ValueError("The website calculation date is outside the approved interval")
        for city_id in ids:
            catalog = read(root, manifest[city_id]["path"])
            def visit(value):
                if isinstance(value, list):
                    for item in value:
                        visit(item)
                elif isinstance(value, dict):
                    if "valid_from" in value or "valid_to" in value:
                        def valid(day):
                            return (not value.get("valid_from") or value["valid_from"] <= day) and (not value.get("valid_to") or day <= value["valid_to"])
                        if valid(as_of) != valid(review["as_of"]):
                            raise ValueError("Tariff validity differs from reviewed date: " + city_id)
                    for item in value.values():
                        visit(item)
            visit(catalog)
    return manifest


def activate(root=ROOT, check=False):
    """Copy byte-identical catalogs and register only the explicit selection."""
    selection = read(root, SELECTION)
    manifest = check_review(root, selection)
    registry = read(root, "data/municipality_registry.json")
    expected_registry = deepcopy(registry)
    selected = set(selection["municipality_ids"])
    for city_id in selected:
        entry = manifest[city_id]
        area_id = "municipality-" + entry["ags"]
        municipality = {"id": city_id, "name": entry["name"], "ags": entry["ags"], "active": True,
            "region_id": "stuttgart-region", "tariff_id": city_id, "area_id": area_id}
        area = {"id": area_id, "kind": "municipality", "municipality_id": city_id,
            "parent_id": None, "tariff_id": city_id, "geometry_key": entry["ags"]}
        existing = next((m for m in registry["municipalities"] if m["id"] == city_id), None)
        if existing is not None and existing != municipality:
            raise ValueError("Existing municipality differs from approved assignment: " + city_id)
        existing_area = next((a for a in registry["areas"] if a["id"] == area_id), None)
        if existing_area is not None and existing_area != area:
            raise ValueError("Existing area differs from approved assignment: " + city_id)
        if existing is None:
            expected_registry["municipalities"].append(municipality)
        if existing_area is None:
            expected_registry["areas"].append(area)
        original = (root / entry["path"]).read_bytes()
        target = root / f"data/municipalities/{city_id}.json"
        if check:
            if not target.exists() or target.read_bytes() != original:
                raise ValueError("Active catalog differs from reviewed import: " + city_id)
        else:
            target.write_bytes(original)
    for entry in registry["municipalities"]:
        if entry["id"] in manifest and entry["active"] and entry["id"] not in selected:
            raise ValueError("Unapproved expansion municipality is active: " + entry["id"])
    if check:
        if registry != expected_registry:
            raise ValueError("Selected municipalities are not completely registered")
    else:
        expected_registry["municipalities"].sort(key=lambda entry: entry["id"])
        expected_registry["areas"].sort(key=lambda entry: entry["id"])
        (root / "data/municipality_registry.json").write_text(json.dumps(expected_registry, ensure_ascii=False, indent=2) + "\n")
    return len(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the selection without writing files")
    args = parser.parse_args()
    count = activate(check=args.check)
    print(f"{'Verified' if args.check else 'Activated'} {count} fully supported expansion catalogs; calculation engines unchanged.")


if __name__ == "__main__":
    main()
