import { Fraction, roundMoney } from "./money.js";
import { normalizeProfile } from "./profile.js";
import type {
  CalculatedComponent, ComparisonResult, Component, IncomeBand, MunicipalityCatalog,
  Offer, Price, Profile, Registry, Selectors,
} from "./types.js";

type Trace = Record<string, unknown>[];
type SelectedRow = { selectors?: Selectors };

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

export function validOn(record: { valid_from?: string | null; valid_to?: string | null }, asOf: string): boolean {
  return (record.valid_from == null || record.valid_from <= asOf) &&
    (record.valid_to == null || asOf <= record.valid_to);
}

export function familyCount(city: MunicipalityCatalog, profile: Profile): number | null {
  const children = profile.children.filter(child => child.resident);
  switch (city.family_basis) {
    case "resident_children": return children.length;
    case "under_18": return children.filter(child => child.age_months < 216).length;
    case "child_benefit": return children.filter(child => child.child_benefit).length;
    case "under_18_or_child_benefit":
      return children.filter(child => child.age_months < 216 || child.child_benefit).length;
    default: return null;
  }
}

export function incomeValue(profile: Profile, basis: string, period: "year" | "month"): Fraction | null {
  const entries = (profile.incomes ?? []).filter(entry => entry.basis === basis);
  const same = entries.find(entry => entry.period === period);
  if (same) return new Fraction(same.amount_cents);
  // Period conversion is allowed only within the same statutory income definition.
  if (entries.length === 1) {
    const value = new Fraction(entries[0].amount_cents);
    return period === "year" ? value.multiply(12) : value.divide(12);
  }
  return null;
}

export function bandMatches(band: IncomeBand, profile: Profile): boolean {
  if (band.single_parent != null && band.single_parent !== profile.single_parent) return false;
  if (profile.income_mode === "highest_band") return band.is_highest;
  const income = incomeValue(profile, band.basis, band.period);
  if (income === null) return false;
  return (band.lower_cents === null || (band.lower_inclusive
    ? income.compare(band.lower_cents) >= 0 : income.compare(band.lower_cents) > 0)) &&
    (band.upper_cents === null || (band.upper_inclusive
      ? income.compare(band.upper_cents) <= 0 : income.compare(band.upper_cents) < 0));
}

function rowMatches(row: SelectedRow, city: MunicipalityCatalog, profile: Profile, count: number): boolean {
  const selectors = row.selectors;
  if (!selectors) throw new Error("A canonical price row is missing tariff selectors.");
  if (selectors.family_count_is_minimum ? count < selectors.family_count : count !== selectors.family_count) return false;
  if (selectors.care_rank != null && (profile.care_rank == null || (selectors.care_rank_is_minimum
    ? profile.care_rank < selectors.care_rank : profile.care_rank !== selectors.care_rank))) return false;
  if ((selectors.pass_id ?? "none") !== profile.pass_id) return false;
  if (selectors.income_band_id != null) {
    const band = city.income_bands.find(entry => entry.id === selectors.income_band_id);
    if (!band) throw new Error("A canonical price row references an unknown income band.");
    return bandMatches(band, profile);
  }
  return true;
}

function applyRules(city: MunicipalityCatalog, item: Offer, initial: Fraction, profile: Profile,
  trace: Trace, componentKind = "care"): [Fraction | null, string | null] {
  const selected = profile.approved_rules ?? [];
  const rules = city.rules.filter(rule => selected.includes(rule.id));
  if (rules.length !== selected.length) return [null, "unknown_rule"];
  if (rules.filter(rule => !rule.stackable).length > 1) return [null, "discounts_not_stackable"];
  let value = initial;
  for (const rule of rules) {
    if (rule.execution_status !== "supported") return [null, "rule_not_executable"];
    if (!(rule.requires ?? []).every(condition => (profile.eligibility ?? []).includes(condition))) {
      return [null, "eligibility_not_confirmed"];
    }
    const params = rule.parameters;
    if (!params) throw new Error("A supported rule is missing canonical parameters.");
    if (!(params.components ?? ["care"]).includes(componentKind)) continue;
    let percent = params.percent;
    if (["income_discount", "income_ratio"].includes(rule.kind ?? "") || params.income_below_cents !== undefined) {
      const income = incomeValue(profile, params.income_basis!, params.income_period!);
      if (income === null) return [null, "income_definition_missing"];
      if (params.income_below_cents !== undefined && income.compare(params.income_below_cents) >= 0) {
        return [null, "discount_income_limit_not_met"];
      }
      if (rule.kind === "income_discount") {
        if (item.age_group !== "u3" && (item.weekly_minutes === null || item.weekly_minutes <= 2100)) {
          return [null, "discount_not_applicable"];
        }
        percent = params.bands?.find(band => income.compare(band.below_cents) < 0)?.percent;
        if (percent === undefined) return [null, "discount_income_limit_not_met"];
      }
      if (rule.kind === "income_ratio") {
        if (income.compare(params.threshold_cents!) >= 0) return [null, "discount_income_limit_not_met"];
        value = value.multiply(income).divide(params.threshold_cents!);
        trace.push({ operation: "income_ratio", rule_id: rule.id, evidence: rule.evidence });
        continue;
      }
    }
    if (percent === undefined) throw new Error("A supported discount is missing its percentage.");
    value = value.multiply(100 - percent).divide(100);
    if (params.rounding) value = new Fraction(roundMoney(value, params.rounding));
    trace.push({ operation: "discount", rule_id: rule.id, percent, evidence: rule.evidence });
  }
  return [value, null];
}

export function formulaPrice(city: MunicipalityCatalog, item: Offer, profile: Profile, count: number,
  offeredMinutes?: number): [number | null, Trace, string | null] {
  const formula = item.formula;
  if (!formula) throw new Error("The offer has no price formula.");
  const weeklyMinutes = offeredMinutes ?? item.weekly_minutes;
  if (weeklyMinutes === null) return [null, [], "offered_hours_required"];
  const rate = weeklyMinutes <= formula.threshold_minutes ? formula.below_or_equal_rate_cents : formula.above_rate_cents;
  const percent = formula.family_discount_percent[Math.min(count, 4) - 1];
  const initial = new Fraction(rate).multiply(weeklyMinutes).divide(60).multiply(100 - percent).divide(100);
  const trace: Trace = [{ operation: "weekly_hour_rate", rate_cents: rate, weekly_minutes: weeklyMinutes,
    family_discount_percent: percent, evidence: item.evidence }];
  const [value, reason] = applyRules(city, item, initial, profile, trace);
  if (value === null) return [null, trace, reason];
  return [Math.max(formula.minimum_cents, roundMoney(value, formula.rounding)), trace, null];
}

function mealDetails(city: MunicipalityCatalog, item: Offer, profile: Profile): CalculatedComponent[] {
  const details: CalculatedComponent[] = [];
  for (const part of city.components) {
    if (part.kind === "care_extension" || !validOn(part, profile.as_of)) continue;
    if (part.age_group != null && part.age_group !== item.age_group) continue;
    if (part.offer_ids != null && !part.offer_ids.includes(item.id)) continue;
    const mealDays = profile.meal_days_per_week ?? (item.weekday_minutes ?? []).filter(value => value > 0).length;
    if (part.days_per_week !== undefined && part.days_per_week !== mealDays) continue;
    if (part.minimum_daily_minutes_exclusive !== undefined && item.weekday_minutes !== null &&
        Math.max(...item.weekday_minutes) <= part.minimum_daily_minutes_exclusive) continue;
    let passId = profile.pass_id;
    if (city.id === "leinfelden-echterdingen" && passId.startsWith("city_pass_")) passId = "city_pass_abc";
    if (part.pass_id != null && part.pass_id !== passId) continue;
    const result: CalculatedComponent = { ...structuredClone(part), annual_equivalent_cents: null };
    if (result.amount_cents !== null) {
      const trace: Trace = [];
      const [value, reason] = applyRules(city, item, new Fraction(result.amount_cents), profile, trace, result.kind);
      if (value === null) {
        result.value_status = reason!;
        result.amount_cents = null;
      } else {
        result.amount_cents = roundMoney(value);
        if (result.unit === "per_month" && result.payment_months !== null) {
          result.annual_equivalent_cents = roundMoney(new Fraction(result.amount_cents).multiply(result.payment_months).divide(12));
        }
        result.calculation = trace;
      }
    }
    details.push(result);
  }
  return details;
}

interface Candidate {
  item: Offer;
  row: Price;
  amount: number;
  trace: Trace;
  weekly: number;
}

/** Evaluate a validated canonical catalog using only local JSON data. */
export function evaluateCity(catalog: MunicipalityCatalog, input: unknown): ComparisonResult {
  const city = structuredClone(catalog);
  let profile = normalizeProfile(input);
  const overrides = profile.municipality_overrides?.[city.id] ?? {};
  if (Object.keys(overrides).length > 0) {
    if ("incomes" in overrides || "income_mode" in overrides) delete profile.model_income_snapshot;
    profile = normalizeProfile({ ...profile, ...overrides });
  }
  const result: ComparisonResult = {
    municipality_id: city.id, municipality: city.name, profile_id: profile.id ?? null,
    as_of: profile.as_of, reviewed_at: city.reviewed_at, status: "unavailable", reasons: [],
    monthly_care_cents: null, annual_care_cents: null, monthly_equivalent_cents: null,
    offer_id: null, offer_label: null, booked_weekly_minutes: null, extra_weekly_minutes: null,
    payment_months: null, components: [], calculation: [], evidence: [], issues: city.issues, alternatives: [],
  };
  const unavailable = (reason: string): ComparisonResult => {
    result.reasons = [reason];
    return result;
  };
  if (profile.scope !== "municipal") return unavailable("scope_not_supported");
  if (profile.as_of > city.reviewed_at && !profile.allow_published_future) return unavailable("date_not_reviewed");
  const child = profile.children[profile.target_child];
  if (!child.resident || profile.school_entry) return unavailable("target_outside_scope");
  let effectiveAge = child.age_months;
  if (effectiveAge === 36 && city.age_transition === "following_month") {
    if (child.birthday_in_reference_month === undefined) return unavailable("birthday_month_required_for_age_transition");
    if (child.birthday_in_reference_month) effectiveAge = 35;
  }
  const count = familyCount(city, profile);
  if (!count) return unavailable("family_definition_not_satisfied");
  if (city.id === "stuttgart" && profile.pass_id === "family_card" &&
      profile.children.filter(entry => entry.age_months < 36).length > 1) return unavailable("infant_surcharge_allocation_required");
  const requirements: Record<string, string[]> = {
    "stuttgart:family_card": ["valid_family_card"],
    "sindelfingen:social_card": ["valid_social_card"],
    "esslingen:city_pass": ["valid_city_pass", "priority_benefits_denied"],
  };
  let required = requirements[`${city.id}:${profile.pass_id}`] ?? [];
  if (city.id === "leinfelden-echterdingen" && profile.pass_id.startsWith("city_pass_")) required = ["valid_city_pass", "no_priority_benefit"];
  if (!required.every(condition => (profile.eligibility ?? []).includes(condition))) return unavailable("pass_eligibility_not_confirmed");
  const localPasses = new Set(["none", ...city.prices.map(row => row.selectors?.pass_id ?? "none")]);
  if (!localPasses.has(profile.pass_id)) return unavailable("pass_not_supported_for_municipality");
  const offers = city.offers.filter(offer => validOn(offer, profile.as_of) && effectiveAge >= offer.age_min_months &&
    (offer.age_max_months_exclusive === null || effectiveAge < offer.age_max_months_exclusive));
  const candidates: Candidate[] = [];
  const unresolved: { minutes: number; reason: string }[] = [];
  const failures = new Set<string>();
  const requested = profile.weekday_minutes;
  for (const item of offers) {
    const schedule = item.weekday_minutes;
    if (schedule === null || !["published", "verified"].includes(item.schedule_status)) {
      failures.add("schedule_not_confirmed");
      continue;
    }
    if (!item.continuous) continue;
    const actual = [...schedule];
    let extensionRows: Component[] = [];
    let priceRows = city.prices.filter(row => row.offer_id === item.id && rowMatches(row, city, profile, count));
    let trace: Trace = [];
    if (item.formula) {
      const [amount, formulaTrace, reason] = formulaPrice(city, item, profile, count);
      if (reason !== null) {
        failures.add(reason);
        continue;
      }
      trace = formulaTrace;
      priceRows = [{ id: null, amount_cents: amount, value_status: "known", evidence: item.evidence }];
    }
    const deficits = requested.map((need, index) => Math.max(0, need - actual[index]));
    if (deficits.some(value => value > 0)) {
      const parts = city.components.filter(part => part.kind === "care_extension" &&
        (part.offer_ids ?? []).includes(item.id) && part.execution_status == null);
      const neededMinutes = Math.max(...deficits);
      const neededDays = deficits.filter(value => value > 0).length;
      const matches = parts.filter(part => (part.extension_minutes ?? 0) >= neededMinutes &&
        part.days_per_week === neededDays && rowMatches(part, city, profile, count));
      if (matches.length === 0) continue;
      const duration = Math.min(...matches.map(part => part.extension_minutes!));
      extensionRows = matches.filter(part => part.extension_minutes === duration);
      if (extensionRows.length !== 1) {
        failures.add("ambiguous_extension");
        continue;
      }
      deficits.forEach((deficit, index) => { if (deficit > 0) actual[index] += duration; });
    }
    if (priceRows.length === 0) {
      failures.add("price_or_income_input_missing");
      unresolved.push({ minutes: sum(actual), reason: "price_or_income_input_missing" });
    }
    for (const row of priceRows) {
      if (row.value_status !== "known" || row.amount_cents === null) {
        const reason = "tariff_" + row.value_status;
        failures.add(reason);
        if (row.value_status !== "not_offered") unresolved.push({ minutes: sum(actual), reason });
        continue;
      }
      let amount = new Fraction(row.amount_cents).add(sum(extensionRows.map(part => part.amount_cents!)));
      const rowTrace = structuredClone(trace);
      rowTrace.push({ operation: item.formula ? "formula_result" : "table_lookup", price_id: row.id,
        amount_cents: row.amount_cents, evidence: row.evidence });
      rowTrace.push(...extensionRows.map(part => ({ operation: "extension", amount_cents: part.amount_cents, evidence: part.evidence })));
      if (!item.formula) {
        const [adjusted, reason] = applyRules(city, item, amount, profile, rowTrace);
        if (adjusted === null) {
          failures.add(reason!);
          continue;
        }
        amount = adjusted;
      }
      candidates.push({ item, row, amount: roundMoney(amount), trace: rowTrace, weekly: sum(actual) });
    }
  }
  if (candidates.length === 0) {
    result.reasons = failures.size ? [...failures].sort() : ["no_offer_covers_daily_need"];
    return result;
  }
  const minimumMinutes = Math.min(...candidates.map(candidate => candidate.weekly));
  const blocking = unresolved.filter(entry => entry.minutes <= minimumMinutes);
  if (blocking.length > 0) {
    result.reasons = [...new Set(blocking.map(entry => entry.reason))].sort();
    return result;
  }
  const smallest = candidates.filter(candidate => candidate.weekly === minimumMinutes);
  const minimumAmount = Math.min(...smallest.map(candidate => candidate.amount));
  const winners = smallest.filter(candidate => candidate.amount === minimumAmount);
  if (new Set(winners.map(candidate => candidate.row.id)).size > 1) {
    result.status = "ambiguous";
    result.reasons = ["multiple_equivalent_tariffs_require_scope_clarification"];
    result.alternatives = winners.map(candidate => ({ offer_id: candidate.item.id,
      price_id: candidate.row.id, monthly_cents: candidate.amount }));
    return result;
  }
  const winner = winners[0];
  const { item, amount } = winner;
  const months = item.payment_months;
  if (months === null) result.reasons = ["payment_months_unknown"];
  else {
    result.status = "comparable";
    result.annual_care_cents = roundMoney(new Fraction(amount).multiply(months));
    result.monthly_equivalent_cents = roundMoney(new Fraction(amount).multiply(months).divide(12));
  }
  Object.assign(result, {
    monthly_care_cents: amount, offer_id: item.id, offer_label: item.original_label,
    booked_weekly_minutes: winner.weekly, extra_weekly_minutes: winner.weekly - sum(requested),
    payment_months: months, family_count: count, care_rank: profile.care_rank ?? null,
    selected_price_id: winner.row.id, calculation: winner.trace, components: mealDetails(city, item, profile),
    evidence: [item.evidence, winner.row.evidence, item.payment_evidence, item.schedule_evidence,
      ...(winner.row.corroborating_evidence ?? [])],
  });
  result.calculation.push({ operation: "annual_equivalent_divided_by_12", monthly_cents: amount,
    payment_months: months, result_cents: result.monthly_equivalent_cents });
  const parts = result.components;
  const mandatory = parts.filter(part => part.required === true);
  const incomplete = parts.some(part => part.required === null) || parts.length === 0 ||
    mandatory.some(part => part.value_status !== "known" || part.annual_equivalent_cents === null);
  const mealVariants = mandatory.filter(part => part.kind === "meal").length > 1;
  result.total_mandatory_monthly_equivalent_cents = null;
  result.total_status = "incomplete_or_variant_costs";
  if (!incomplete && !mealVariants && result.annual_care_cents !== null) {
    let total = new Fraction(result.annual_care_cents);
    for (const part of mandatory) total = total.add(new Fraction(part.amount_cents!).multiply(part.payment_months!));
    result.total_mandatory_monthly_equivalent_cents = roundMoney(total.divide(12));
    result.total_status = "known_for_selected_components";
  }
  return result;
}

/** Resolve active geographic entries independently of the map or user interface. */
export function compareMunicipalities(cities: MunicipalityCatalog[], input: unknown, registry: Registry,
  municipalityId?: string): ComparisonResult[] {
  const profile = normalizeProfile(input);
  const catalogs = new Map(cities.map(city => [city.id, city]));
  let entries = registry.municipalities.filter(entry => entry.active);
  if (municipalityId !== undefined) {
    entries = entries.filter(entry => entry.id === municipalityId);
    if (entries.length === 0) throw new Error("Unknown or inactive municipality.");
  }
  return entries.map(entry => {
    const catalog = catalogs.get(entry.tariff_id);
    if (!catalog) throw new Error(`Missing tariff catalog: ${entry.tariff_id}`);
    const local = { ...profile, municipality_overrides: {
      [entry.tariff_id]: profile.municipality_overrides?.[entry.id] ?? {},
    } };
    return { ...evaluateCity(catalog, local), municipality_id: entry.id, municipality: entry.name,
      ags: entry.ags, area_id: entry.area_id, tariff_id: entry.tariff_id };
  });
}
