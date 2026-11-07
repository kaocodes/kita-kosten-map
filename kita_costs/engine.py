"""Deterministic tariff selection, with explicit unknowns and auditable arithmetic."""

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_PASSES = {"none", "family_card", "city_pass", "social_card", "city_pass_a", "city_pass_b", "city_pass_c"}


def load_cities(root=ROOT):
    return [json.loads(path.read_text()) for path in sorted((Path(root) / "data/municipalities").glob("*.json"))]


def load_default_profile(root=ROOT):
    return json.loads((Path(root) / "data/profiles/default.json").read_text())


def valid_on(record, as_of):
    return (record.get("valid_from") is None or record["valid_from"] <= as_of) and (
        record.get("valid_to") is None or as_of <= record["valid_to"])


def round_money(value, rule="cent_half_up"):
    quantum = Decimal(100) if rule == "whole_euro_half_up" else Decimal(1)
    return int((Decimal(value) / quantum).quantize(Decimal(1), rounding=ROUND_HALF_UP) * quantum)


def validate_profile(profile):
    if date.fromisoformat(profile["as_of"]).isoformat() != profile["as_of"]:
        raise ValueError("The reference date must use YYYY-MM-DD.")
    children = profile["children"]
    if not children or type(profile["target_child"]) is not int or not 0 <= profile["target_child"] < len(children):
        raise ValueError("A valid target child is required.")
    for child in children:
        if type(child["age_months"]) is not int or child["age_months"] < 0:
            raise ValueError("Child age must be a non-negative integer number of months.")
        for field in ("resident", "child_benefit"):
            if not isinstance(child.get(field), bool):
                raise ValueError(f"Each child's {field} must be explicitly true or false.")
        if "birthday_in_reference_month" in child and type(child["birthday_in_reference_month"]) is not bool:
            raise ValueError("Birthday-month confirmation must be boolean.")
    minutes = profile["weekday_minutes"]
    if len(minutes) != 5 or any(type(v) is not int or not 0 <= v <= 1440 for v in minutes) or not sum(minutes):
        raise ValueError("Five daily durations in integer minutes are required.")
    if profile["income_mode"] not in {"highest_band", "specified"}:
        raise ValueError("Invalid income mode.")
    if profile["pass_id"] not in KNOWN_PASSES:
        raise ValueError("Unknown pass identifier.")
    if profile.get("care_rank") is not None and (type(profile["care_rank"]) is not int or profile["care_rank"] < 1):
        raise ValueError("Care rank must be positive or explicitly unknown.")
    seen = set()
    for income in profile.get("incomes", []):
        key = (income["basis"], income["period"])
        if key in seen or income["period"] not in {"year", "month"}:
            raise ValueError("Income definitions must be unique and have an explicit period.")
        if type(income["amount_cents"]) is not int or income["amount_cents"] < 0:
            raise ValueError("Income must be a non-negative integer number of cents.")
        seen.add(key)
    for basis in {entry["basis"] for entry in profile.get("incomes", [])}:
        entries = {entry["period"]: entry["amount_cents"] for entry in profile["incomes"] if entry["basis"] == basis}
        if set(entries) == {"month", "year"} and entries["month"] * 12 != entries["year"]:
            raise ValueError("Monthly and annual values for the same income definition disagree.")


def family_count(city, profile):
    children = [child for child in profile["children"] if child["resident"]]
    basis = city["family_basis"]
    if basis == "resident_children":
        return len(children)
    if basis == "under_18":
        return sum(child["age_months"] < 216 for child in children)
    if basis == "child_benefit":
        return sum(child["child_benefit"] for child in children)
    if basis == "under_18_or_child_benefit":
        return sum(child["age_months"] < 216 or child["child_benefit"] for child in children)
    return None


def income_value(profile, basis, period):
    # Only change the period of the same statutory income definition.
    entries = [entry for entry in profile.get("incomes", []) if entry["basis"] == basis]
    same = next((entry for entry in entries if entry["period"] == period), None)
    if same:
        return Decimal(same["amount_cents"])
    if len(entries) == 1:
        entry = entries[0]
        return Decimal(entry["amount_cents"]) * (12 if period == "year" else Decimal(1) / 12)
    return None


def band_matches(band, profile):
    if band.get("single_parent") is not None and band["single_parent"] != profile.get("single_parent"):
        return False
    if profile["income_mode"] == "highest_band":
        return band["is_highest"]
    income = income_value(profile, band["basis"], band["period"])
    if income is None:
        return False
    low, high = band["lower_cents"], band["upper_cents"]
    return (low is None or income >= low if band["lower_inclusive"] else low is None or income > low) and (
        high is None or income <= high if band["upper_inclusive"] else high is None or income < high)


def row_matches(row, city, profile, count):
    selectors = row["selectors"]
    expected = selectors["family_count"]
    if count is None or (count < expected if selectors.get("family_count_is_minimum") else count != expected):
        return False
    rank = selectors.get("care_rank")
    if rank is not None and (profile.get("care_rank") is None or (
        profile["care_rank"] < rank if selectors.get("care_rank_is_minimum") else profile["care_rank"] != rank)):
        return False
    pass_id = profile["pass_id"]
    if selectors.get("pass_id", "none") != pass_id:
        return False
    band_id = selectors.get("income_band_id")
    if band_id is not None:
        return band_matches(next(band for band in city["income_bands"] if band["id"] == band_id), profile)
    return True


def apply_rules(city, item, value, profile, trace, component_kind="care"):
    selected = profile.get("approved_rules", [])
    local_selected = [rule for rule in city["rules"] if rule["id"] in selected]
    if len(local_selected) != len(selected):
        return None, "unknown_rule"
    if len([rule for rule in local_selected if not rule.get("stackable", False)]) > 1:
        return None, "discounts_not_stackable"
    for rule in local_selected:
        if rule.get("execution_status") != "supported":
            return None, "rule_not_executable"
        if not set(rule["requires"]).issubset(profile.get("eligibility", [])):
            return None, "eligibility_not_confirmed"
        params = rule["parameters"]
        if component_kind not in params.get("components", ["care"]):
            continue
        percent = params.get("percent")
        if rule["kind"] in {"income_discount", "income_ratio"} or "income_below_cents" in params:
            income = income_value(profile, params["income_basis"], params["income_period"])
            if income is None:
                return None, "income_definition_missing"
            if "income_below_cents" in params and income >= params["income_below_cents"]:
                return None, "discount_income_limit_not_met"
            if rule["kind"] == "income_discount":
                if item["age_group"] != "u3" and (item["weekly_minutes"] is None or item["weekly_minutes"] <= 2100):
                    return None, "discount_not_applicable"
                percent = next((b["percent"] for b in params["bands"] if income < b["below_cents"]), None)
                if percent is None:
                    return None, "discount_income_limit_not_met"
            if rule["kind"] == "income_ratio":
                if income >= params["threshold_cents"]:
                    return None, "discount_income_limit_not_met"
                value *= income / Decimal(params["threshold_cents"])
                trace.append({"operation": "income_ratio", "rule_id": rule["id"], "evidence": rule["evidence"]})
                continue
        value *= Decimal(100 - percent) / 100
        if params.get("rounding"):
            value = Decimal(round_money(value, params["rounding"]))
        trace.append({"operation": "discount", "rule_id": rule["id"], "percent": percent, "evidence": rule["evidence"]})
    return value, None


def formula_price(city, item, profile, count, offered_minutes=None):
    formula = item["formula"]
    weekly_minutes = offered_minutes if offered_minutes is not None else item["weekly_minutes"]
    if weekly_minutes is None:
        return None, [], "offered_hours_required"
    rate = formula["below_or_equal_rate_cents"] if weekly_minutes <= formula["threshold_minutes"] else formula["above_rate_cents"]
    value = Decimal(rate) * Decimal(weekly_minutes) / 60
    percent = formula["family_discount_percent"][min(count, 4) - 1]
    value *= Decimal(100 - percent) / 100
    trace = [{"operation": "weekly_hour_rate", "rate_cents": rate, "weekly_minutes": weekly_minutes,
              "family_discount_percent": percent, "evidence": item["evidence"]}]
    value, reason = apply_rules(city, item, value, profile, trace)
    if reason:
        return None, trace, reason
    value = max(formula["minimum_cents"], round_money(value, formula["rounding"]))
    return value, trace, None


def meal_details(city, item, profile, count):
    details = []
    for part in city["components"]:
        if part["kind"] == "care_extension" or not valid_on(part, profile["as_of"]):
            continue
        if part.get("age_group") not in {None, item["age_group"]}:
            continue
        if part.get("offer_ids") is not None and item["id"] not in part["offer_ids"]:
            continue
        meal_days = profile.get("meal_days_per_week", sum(v > 0 for v in item["weekday_minutes"]))
        if part.get("days_per_week") is not None and part["days_per_week"] != meal_days:
            continue
        if part.get("minimum_daily_minutes_exclusive") is not None and item.get("weekday_minutes") is not None:
            if max(item["weekday_minutes"]) <= part["minimum_daily_minutes_exclusive"]:
                continue
        pass_id = profile["pass_id"]
        if city["id"] == "leinfelden-echterdingen" and pass_id.startswith("city_pass_"):
            pass_id = "city_pass_abc"
        if part.get("pass_id") is not None and part["pass_id"] != pass_id:
            continue
        result = deepcopy(part)
        result["annual_equivalent_cents"] = None
        if result["amount_cents"] is not None:
            trace = []
            value, reason = apply_rules(city, item, Decimal(result["amount_cents"]), profile, trace, result["kind"])
            if reason:
                result["value_status"] = reason
                result["amount_cents"] = None
            else:
                result["amount_cents"] = round_money(value)
                if result["unit"] == "per_month" and result["payment_months"] is not None:
                    result["annual_equivalent_cents"] = round_money(Decimal(result["amount_cents"]) * result["payment_months"] / 12)
                result["calculation"] = trace
        details.append(result)
    return details


def evaluate_city(city, profile):
    """Return a comparable price, or a specific reason; never guess missing inputs."""
    profile = deepcopy(profile)
    overrides = profile.get("municipality_overrides", {}).get(city["id"], {})
    allowed = {"incomes", "income_mode", "pass_id", "approved_rules", "eligibility", "care_rank"}
    if set(overrides) - allowed:
        raise ValueError("Municipality overrides may only change local tariff inputs.")
    profile.update(overrides)
    validate_profile(profile)
    result = {"municipality_id": city["id"], "municipality": city["name"],
              "profile_id": profile.get("id"), "as_of": profile["as_of"],
              "reviewed_at": city["reviewed_at"], "status": "unavailable", "reasons": [],
              "monthly_care_cents": None, "annual_care_cents": None,
              "monthly_equivalent_cents": None, "offer_id": None, "offer_label": None,
              "booked_weekly_minutes": None, "extra_weekly_minutes": None,
              "payment_months": None, "components": [], "calculation": [],
              "evidence": [], "issues": city["issues"], "alternatives": []}
    if profile["scope"] != "municipal":
        result["reasons"] = ["scope_not_supported"]
        return result
    if profile["as_of"] > city["reviewed_at"] and not profile.get("allow_published_future", False):
        result["reasons"] = ["date_not_reviewed"]
        return result
    child = profile["children"][profile["target_child"]]
    if not child["resident"] or profile.get("school_entry"):
        result["reasons"] = ["target_outside_scope"]
        return result
    effective_age = child["age_months"]
    if effective_age == 36 and city.get("age_transition") == "following_month":
        if "birthday_in_reference_month" not in child:
            result["reasons"] = ["birthday_month_required_for_age_transition"]
            return result
        if child["birthday_in_reference_month"]:
            effective_age = 35
    count = family_count(city, profile)
    if not count:
        result["reasons"] = ["family_definition_not_satisfied"]
        return result
    if city["id"] == "stuttgart" and profile["pass_id"] == "family_card" and sum(c["age_months"] < 36 for c in profile["children"]) > 1:
        result["reasons"] = ["infant_surcharge_allocation_required"]
        return result
    pass_requirements = {
        ("stuttgart", "family_card"): {"valid_family_card"},
        ("sindelfingen", "social_card"): {"valid_social_card"},
        ("esslingen", "city_pass"): {"valid_city_pass", "priority_benefits_denied"},
    }
    required = pass_requirements.get((city["id"], profile["pass_id"]), set())
    if city["id"] == "leinfelden-echterdingen" and profile["pass_id"].startswith("city_pass_"):
        required = {"valid_city_pass", "no_priority_benefit"}
    if not required.issubset(profile.get("eligibility", [])):
        result["reasons"] = ["pass_eligibility_not_confirmed"]
        return result
    local_passes = {p["selectors"].get("pass_id", "none") for p in city["prices"]} | {"none"}
    if profile["pass_id"] not in local_passes:
        result["reasons"] = ["pass_not_supported_for_municipality"]
        return result
    offers = [o for o in city["offers"] if valid_on(o, profile["as_of"]) and
              effective_age >= o["age_min_months"] and
              (o["age_max_months_exclusive"] is None or effective_age < o["age_max_months_exclusive"])]
    candidates = []
    unresolved = []
    failures = set()
    requested = profile["weekday_minutes"]
    for item in offers:
        schedule = item["weekday_minutes"]
        if schedule is None or item["schedule_status"] not in {"published", "verified"}:
            failures.add("schedule_not_confirmed")
            continue
        if not item["continuous"]:
            continue
        actual = list(schedule)
        extension_rows = []
        price_rows = [row for row in city["prices"] if row["offer_id"] == item["id"] and row_matches(row, city, profile, count)]
        if item.get("formula"):
            amount, trace, reason = formula_price(city, item, profile, count)
            if reason:
                failures.add(reason)
                continue
            price_rows = [{"id": None, "amount_cents": amount, "value_status": "known", "evidence": item["evidence"]}]
        else:
            trace = []
        deficits = [max(0, need - have) for need, have in zip(requested, actual, strict=True)]
        if any(deficits):
            # Esslingen's quoted supplement supplies one 30/60-minute extension on selected weekdays.
            parts = [p for p in city["components"] if p["kind"] == "care_extension" and item["id"] in (p.get("offer_ids") or []) and p.get("execution_status") is None]
            needed_minutes = max(deficits)
            needed_days = sum(v > 0 for v in deficits)
            matches = [p for p in parts if p.get("extension_minutes", 0) >= needed_minutes and p.get("days_per_week") == needed_days and row_matches(p, city, profile, count)]
            if not matches:
                continue
            duration = min(p["extension_minutes"] for p in matches)
            extension_rows = [p for p in matches if p["extension_minutes"] == duration]
            if len(extension_rows) != 1:
                failures.add("ambiguous_extension")
                continue
            for i, deficit in enumerate(deficits):
                if deficit:
                    actual[i] += duration
        if not price_rows:
            failures.add("price_or_income_input_missing")
            unresolved.append((sum(actual), "price_or_income_input_missing"))
        for row in price_rows:
            if row["value_status"] != "known" or row["amount_cents"] is None:
                failures.add("tariff_" + row["value_status"])
                if row["value_status"] != "not_offered":
                    unresolved.append((sum(actual), "tariff_" + row["value_status"]))
                continue
            amount = Decimal(row["amount_cents"]) + sum(Decimal(p["amount_cents"]) for p in extension_rows)
            row_trace = deepcopy(trace)
            row_trace.append({"operation": "table_lookup" if not item.get("formula") else "formula_result",
                              "price_id": row["id"], "amount_cents": row["amount_cents"], "evidence": row["evidence"]})
            row_trace.extend({"operation": "extension", "amount_cents": p["amount_cents"], "evidence": p["evidence"]} for p in extension_rows)
            if not item.get("formula"):
                amount, reason = apply_rules(city, item, amount, profile, row_trace)
                if reason:
                    failures.add(reason)
                    continue
            amount = round_money(amount)
            candidates.append({"item": item, "row": row, "amount": amount,
                               "trace": row_trace, "weekly": sum(actual), "schedule": actual,
                               "extension_rows": extension_rows})
    if not candidates:
        result["reasons"] = sorted(failures) or ["no_offer_covers_daily_need"]
        return result
    minimum_minutes = min(c["weekly"] for c in candidates)
    blocking = [reason for minutes, reason in unresolved if minutes <= minimum_minutes]
    if blocking:
        result["reasons"] = sorted(set(blocking))
        return result
    candidates = [c for c in candidates if c["weekly"] == minimum_minutes]
    minimum_amount = min(c["amount"] for c in candidates)
    winners = [c for c in candidates if c["amount"] == minimum_amount]
    if len({c["row"]["id"] for c in winners}) > 1:
        result["status"] = "ambiguous"
        result["reasons"] = ["multiple_equivalent_tariffs_require_scope_clarification"]
        result["alternatives"] = [{"offer_id": c["item"]["id"], "price_id": c["row"]["id"], "monthly_cents": c["amount"]} for c in winners]
        return result
    winner = winners[0]
    item, amount = winner["item"], winner["amount"]
    months = item["payment_months"]
    if months is None:
        result["reasons"] = ["payment_months_unknown"]
    else:
        result["status"] = "comparable"
        result["annual_care_cents"] = amount * months
        result["monthly_equivalent_cents"] = round_money(Decimal(amount) * months / 12)
    result.update(monthly_care_cents=amount, offer_id=item["id"], offer_label=item["original_label"],
                  booked_weekly_minutes=winner["weekly"], extra_weekly_minutes=winner["weekly"] - sum(requested),
                  payment_months=months, family_count=count, care_rank=profile.get("care_rank"),
                  selected_price_id=winner["row"]["id"], calculation=winner["trace"],
                  components=meal_details(city, item, profile, count),
                  evidence=[item["evidence"], winner["row"]["evidence"], item["payment_evidence"], item["schedule_evidence"]])
    result["evidence"].extend(winner["row"].get("corroborating_evidence", []))
    result["calculation"].append({"operation": "annual_equivalent_divided_by_12", "monthly_cents": amount,
                                  "payment_months": months, "result_cents": result["monthly_equivalent_cents"]})
    # Meals can have site-dependent prices or incomplete billing evidence. Never invent a total.
    parts = result["components"]
    mandatory = [p for p in parts if p["required"] is True]
    incomplete = any(p["required"] is None for p in parts) or not parts or any(
        p["value_status"] != "known" or p["annual_equivalent_cents"] is None for p in mandatory)
    meal_variants = len([p for p in mandatory if p["kind"] == "meal"]) > 1
    result["total_mandatory_monthly_equivalent_cents"] = None
    result["total_status"] = "incomplete_or_variant_costs"
    if not incomplete and not meal_variants and result["annual_care_cents"] is not None:
        total_annual = result["annual_care_cents"] + sum(p["amount_cents"] * p["payment_months"] for p in mandatory)
        result["total_mandatory_monthly_equivalent_cents"] = round_money(Decimal(total_annual) / 12)
        result["total_status"] = "known_for_selected_components"
    return result
