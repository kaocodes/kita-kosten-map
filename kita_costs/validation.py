"""Validate canonical records and archived evidence without external dependencies."""

from datetime import date
import hashlib
import json
from pathlib import Path

from .engine import ROOT, validate_profile
from .registry import load_registry, validate_registry


def validate_dataset(cities, root=ROOT, registry=None):
    errors = []
    sources = {s["id"]: s for s in json.loads((Path(root) / "data/source_manifest.json").read_text())}
    city_ids = set()

    def fail(location, message):
        errors.append(f"{location}: {message}")

    def visit(value, location):
        if isinstance(value, dict):
            if "source_id" in value:
                source_id = value["source_id"]
                if source_id not in sources or sources[source_id]["http_status"] != 200:
                    fail(location, f"Unavailable evidence source {source_id}")
                if not value.get("locator"):
                    fail(location, "Missing source locator")
            for key, item in value.items():
                if key.endswith("_cents") and item is not None and (type(item) is not int or item < 0):
                    fail(location + "." + key, "Expected non-negative integer cents or null")
                if key in {"valid_from", "valid_to", "reviewed_at", "reference_date"} and item:
                    try:
                        date.fromisoformat(item)
                    except (ValueError, TypeError):
                        fail(location + "." + key, "Invalid ISO date")
                visit(item, location + "." + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{location}[{index}]")

    for city in cities:
        city_id = city.get("id", "<missing-id>")
        if city_id in city_ids:
            fail(city_id, "Duplicate municipality")
        city_ids.add(city_id)
        required = ["schema_version", "id", "name", "reviewed_at", "reference_date", "scope", "family_basis",
                    "offers", "prices", "income_bands", "components", "rules", "issues", "coverage"]
        missing = [key for key in required if key not in city]
        if missing:
            fail(city_id, "Missing required fields: " + ", ".join(missing))
            continue
        if city["schema_version"] != "1.0":
            fail(city_id, "Unsupported schema version")
        offers = {o["id"]: o for o in city["offers"]}
        bands = {b["id"]: b for b in city["income_bands"]}
        if len(offers) != len(city["offers"]) or len(bands) != len(city["income_bands"]):
            fail(city_id, "Duplicate offer or income band")
        selectors_seen = set()
        all_ids = set()
        for group in ["offers", "prices", "components"]:
            for row in city[group]:
                if row["id"] in all_ids:
                    fail(city_id, "Duplicate record id " + row["id"])
                all_ids.add(row["id"])
        for item in city["offers"]:
            schedule = item["weekday_minutes"]
            if schedule is not None:
                if len(schedule) != 5 or any(type(v) is not int or v < 0 or v > 1440 for v in schedule):
                    fail(item["id"], "Invalid daily schedule")
                if sum(schedule) != item["weekly_minutes"]:
                    fail(item["id"], "Weekly total differs from daily schedule")
            if item["payment_months"] is not None and item["payment_months"] not in range(1, 13):
                fail(item["id"], "Invalid annual billing months")
            if item["valid_to"] and item["valid_to"] < item["valid_from"]:
                fail(item["id"], "Invalid validity interval")
        for row in city["prices"]:
            if row["offer_id"] not in offers:
                fail(row["id"], "Unknown offer")
            band_id = row["selectors"]["income_band_id"]
            if band_id is not None and band_id not in bands:
                fail(row["id"], "Unknown income band")
            if row["amount_cents"] is None and row["value_status"] == "known":
                fail(row["id"], "Missing price incorrectly marked known")
            if row["amount_cents"] is not None and row["value_status"] not in {"known", "conflicting"}:
                fail(row["id"], "Amount cannot be marked missing")
            identity = (row["offer_id"], json.dumps(row["selectors"], sort_keys=True))
            if identity in selectors_seen:
                fail(row["id"], "Duplicate tariff selectors")
            selectors_seen.add(identity)
        for part in city["components"]:
            for offer_id in part.get("offer_ids") or []:
                if offer_id not in offers:
                    fail(part["id"], "Unknown component offer")
        visit(city, city_id)
    errors.extend(validate_registry(load_registry(root) if registry is None else registry, cities, root))
    profile_ids = set()
    profile_paths = sorted((Path(root) / "data/profiles").glob("*.json"))
    for name in {"default.json", "highest_band.json"} - {path.name for path in profile_paths}:
        fail(name, "Missing canonical reference profile")
    for path in profile_paths:
        try:
            profile = json.loads(path.read_text())
            validate_profile(profile)
            if not profile.get("id") or profile["id"] in profile_ids:
                fail(path.name, "Missing or duplicate canonical profile identifier")
            profile_ids.add(profile.get("id"))
            visit(profile, path.name)
        except (ValueError, KeyError, TypeError) as error:
            fail(path.name, f"Invalid canonical profile: {error}")
    for source_id, source in sources.items():
        if source.get("local_path"):
            path = Path(root) / source["local_path"]
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                fail(source_id, "Archived response does not match the stored hash")
    return errors
