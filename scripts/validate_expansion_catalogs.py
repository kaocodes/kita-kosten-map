"""Validate isolated municipality imports without activating or evaluating them."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kita_costs.engine import load_cities
from kita_costs.registry import load_registry
from kita_costs.validation import validate_dataset


def shape_errors(value, schema, root_schema, location="$:"):
    """Check the JSON Schema vocabulary used by the existing municipality schema."""
    if "$ref" in schema:
        target = root_schema
        for key in schema["$ref"].removeprefix("#/").split("/"):
            target = target[key]
        return shape_errors(value, target, root_schema, location)
    errors = []
    types = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str), "integer": lambda x: type(x) is int,
             "boolean": lambda x: type(x) is bool, "null": lambda x: x is None}
    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(types[t](value) for t in expected):
            return [f"{location}: expected {expected}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: unexpected constant")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value outside enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: errors.append(f"{location}: missing {key}")
        for key, item in value.items():
            if key in schema.get("properties", {}):
                errors.extend(shape_errors(item, schema["properties"][key], root_schema, location+"."+key))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{location}: invalid array length")
        if schema.get("uniqueItems") and len({json.dumps(x,sort_keys=True) for x in value}) != len(value):
            errors.append(f"{location}: duplicate array values")
        for index, item in enumerate(value):
            if "items" in schema:
                errors.extend(shape_errors(item, schema["items"], root_schema, f"{location}[{index}]"))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or ("pattern" in schema and not re.search(schema["pattern"], value)):
            errors.append(f"{location}: invalid string")
        if schema.get("format") == "date":
            try: date.fromisoformat(value)
            except ValueError: errors.append(f"{location}: invalid date")
    if type(value) is int:
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            errors.append(f"{location}: number outside bounds")
    for condition in schema.get("allOf", []):
        errors.extend(shape_errors(value, condition, root_schema, location))
    if "if" in schema and not shape_errors(value, schema["if"], root_schema, location):
        errors.extend(shape_errors(value, schema.get("then", {}), root_schema, location))
    return errors


def validate_imports(catalogs):
    research = json.loads((ROOT / "data/research/neighbor_expansion_2026-11-10.json").read_text())
    schema = json.loads((ROOT / "data/municipality.schema.json").read_text())
    by_id = {item["id"]: item for item in catalogs}
    errors = []
    if len(catalogs) != len(by_id) or set(by_id) != {m["id"] for m in research["municipalities"]}:
        return ["Import must contain exactly the 33 documented municipalities"]
    virtual_registry = deepcopy(load_registry())
    registered = {m["id"]: m for m in virtual_registry["municipalities"]}
    for item in research["municipalities"]:
        city = by_id[item["id"]]
        errors.extend(shape_errors(city, schema, schema, city["id"]))
        if city["coverage"]["publication_status"] != "not_active":
            errors.append(city["id"]+": import must not claim publication")
        if not city["offers"] or (not city["prices"] and not any(o.get("formula") for o in city["offers"])):
            errors.append(city["id"]+": empty tariff import")
        clauses = city["original_research"]["source_clauses"]
        rule_ids = [r["id"] for r in city["rules"]]
        if len(rule_ids) != len(set(rule_ids)):
            errors.append(city["id"]+": duplicate rule identifiers")
        for rule in city["rules"]:
            index = rule.get("parameters", {}).get("original_research_clause_index")
            if index is not None and not 0 <= index < len(clauses):
                errors.append(city["id"]+": missing source-clause text")
        if item["id"] in registered:
            if registered[item["id"]]["active"]:
                errors.append(city["id"]+": import was activated unexpectedly")
            continue
        area = "municipality-"+item["ags"]
        virtual_registry["municipalities"].append({"id":item["id"],"name":item["name"],"ags":item["ags"],
            "active":False,"region_id":"stuttgart-region","tariff_id":item["id"],"area_id":area})
        virtual_registry["areas"].append({"id":area,"kind":"municipality","municipality_id":item["id"],
            "parent_id":None,"tariff_id":item["id"],"geometry_key":item["ags"]})
    errors.extend(validate_dataset(load_cities()+catalogs, registry=virtual_registry))
    return errors


def main():
    catalogs = [json.loads(path.read_text()) for path in sorted((ROOT / "data/expansion/municipalities").glob("*.json"))]
    errors = validate_imports(catalogs)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Valid: {len(catalogs)} isolated catalogs; schema, selectors, source hashes and geographic references verified; no activation or fee evaluation.")


if __name__ == "__main__":
    main()
