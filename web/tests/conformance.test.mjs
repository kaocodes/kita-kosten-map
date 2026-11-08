import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";
import {
  compareMunicipalities, createPersonalProfile, evaluateCity, formulaPrice,
  normalizeProfile, ProfileValidationError,
} from "../../build/domain/index.js";
import { Fraction, roundMoney } from "../../build/domain/money.js";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url), "utf8"));
const catalog = readdirSync(new URL("../../data/municipalities/", import.meta.url)).sort()
  .filter(name => name.endsWith(".json")).map(name => read("data/municipalities/" + name));
const registry = read("data/municipality_registry.json");
const cases = read("tests/fixtures/comparison_cases.json").cases;
const python = read("build/python-reference-results.json");
const expectedById = new Map(python.map(record => [record.id, record]));

function evaluateCase(scenario) {
  let profile = read(`data/profiles/${scenario.profile ?? "highest_band"}.json`);
  const cities = structuredClone(catalog);
  if (scenario.personal) profile = createPersonalProfile(profile);
  Object.assign(profile, structuredClone(scenario.profile_updates ?? {}));
  for (const field of scenario.remove_fields ?? []) delete profile[field];
  if (scenario.child_updates) Object.assign(profile.children[profile.target_child], scenario.child_updates);
  const city = cities.find(city => city.id === scenario.municipality_id);
  for (const update of scenario.catalog_updates ?? []) {
    const matches = city[update.collection].filter(record => update.id === "*" || record.id === update.id);
    assert.ok(matches.length > 0, `Unknown fixture target: ${update.id}`);
    for (const record of matches) Object.assign(record, structuredClone(update.values));
  }
  for (const duplicate of scenario.duplicates ?? []) {
    const record = city[duplicate.collection].find(record => record.id === duplicate.id);
    assert.ok(record, `Unknown fixture target: ${duplicate.id}`);
    city[duplicate.collection].push({ ...structuredClone(record), id: duplicate.new_id });
  }
  switch (scenario.operation ?? "compare") {
    case "round_money": return roundMoney(new Fraction(scenario.numerator, scenario.denominator), scenario.rounding);
    case "normalize": return normalizeProfile(profile);
    case "personalize": return createPersonalProfile(profile);
    case "formula_price": {
      const offer = city.offers.find(offer => offer.age_group === "u3" && offer.formula);
      return formulaPrice(city, offer, normalizeProfile(profile), scenario.family_count, scenario.offered_minutes);
    }
    case "city": return evaluateCity(city, profile);
    default: return compareMunicipalities(cities, profile, registry, scenario.municipality_id);
  }
}

for (const scenario of cases) {
  test(`Python/TypeScript parity: ${scenario.id}`, () => {
    let actual;
    try {
      actual = { id: scenario.id, result: evaluateCase(scenario) };
    } catch (error) {
      if (!(error instanceof ProfileValidationError)) throw error;
      actual = { id: scenario.id, error: error.code };
    }
    assert.deepEqual(actual, expectedById.get(scenario.id));
    if (scenario.expected_error) {
      assert.equal(actual.error, scenario.expected_error);
      return;
    }
    assert.ok("result" in actual);
    if ("expected_value" in scenario) assert.equal(actual.result, scenario.expected_value);
    if ("expected_amount" in scenario) assert.equal(actual.result[0], scenario.expected_amount);
    if (scenario.expected) {
      const row = (scenario.operation ?? "compare") === "compare" ? actual.result[0] : actual.result;
      for (const [key, value] of Object.entries(scenario.expected)) {
        if (key === "reasons_include") for (const reason of value) assert.ok(row.reasons.includes(reason));
        else assert.deepEqual(row[key], value, key);
      }
    }
  });
}

test("Both reference profiles match the independent official-source reviews", () => {
  for (const [profileName, reviewName] of [["default", "model_family"], ["highest_band", "highest_band"]]) {
    const review = read(`data/reviews/${reviewName}_review.json`);
    const results = compareMunicipalities(catalog, read(`data/profiles/${profileName}.json`), registry);
    assert.deepEqual(results.map(row => row.municipality_id).sort(), Object.keys(review.expected).sort());
    for (const row of results) {
      const expected = review.expected[row.municipality_id];
      assert.equal(row.status, "comparable");
      assert.equal(row.monthly_care_cents, expected.monthly_cents);
      assert.equal(row.payment_months, expected.payment_months);
      assert.equal(row.booked_weekly_minutes, expected.weekly_minutes);
      assert.equal(row.monthly_equivalent_cents, expected.equivalent_cents);
    }
  }
});

test("Repeated calculation does not share mutable data with inputs or previous results", () => {
  const profile = read("data/profiles/default.json");
  const before = structuredClone({ catalog, profile, registry });
  const first = compareMunicipalities(catalog, profile, registry);
  const second = compareMunicipalities(catalog, profile, registry);
  assert.deepEqual(first, second);
  first[0].evidence[0].locator = "Changed by a caller";
  first[0].components[0].amount_cents = 1;
  assert.deepEqual(compareMunicipalities(catalog, profile, registry), second);
  assert.deepEqual({ catalog, profile, registry }, before);
});

test("Inactive municipalities are omitted and cannot be explicitly selected", () => {
  const inactive = structuredClone(registry);
  inactive.municipalities[0].active = false;
  const results = compareMunicipalities(catalog, read("data/profiles/default.json"), inactive);
  assert.ok(!results.some(row => row.municipality_id === inactive.municipalities[0].id));
  assert.throws(() => compareMunicipalities(catalog, read("data/profiles/default.json"), inactive,
    inactive.municipalities[0].id), /inactive/);
});

test("Additional geographic entries reuse tariffs and retain independent local inputs", () => {
  const expanded = structuredClone(registry);
  expanded.municipalities.push({ id: "test-municipality", name: "Test Municipality", ags: "00000000",
    active: true, tariff_id: "stuttgart", area_id: "test-area", region_id: "test-region" });
  const profile = read("data/profiles/default.json");
  profile.municipality_overrides = { "test-municipality": {
    pass_id: "family_card", eligibility: ["valid_family_card"],
  } };
  const results = compareMunicipalities(catalog, profile, expanded);
  assert.equal(results.at(-1).municipality_id, "test-municipality");
  assert.equal(results.at(-1).monthly_care_cents, 14600);
  assert.equal(results.find(row => row.municipality_id === "stuttgart").monthly_care_cents, 24300);
});

test("Normalization rejects malformed JSON values and supplies only empty optional lists", () => {
  for (const input of [null, [], true, {}, "profile"]) {
    assert.throws(() => normalizeProfile(input), ProfileValidationError);
  }
  const profile = read("data/profiles/highest_band.json");
  delete profile.incomes;
  delete profile.approved_rules;
  delete profile.eligibility;
  const normalized = normalizeProfile(profile);
  assert.deepEqual(normalized.incomes, []);
  assert.deepEqual(normalized.approved_rules, []);
  assert.deepEqual(normalized.eligibility, []);
  assert.ok(!("incomes" in profile));
});

test("Personal inputs discard all model income assumptions without filling tax or local values", () => {
  const model = read("data/profiles/default.json");
  const before = structuredClone(model);
  const personal = createPersonalProfile(model);
  assert.deepEqual(personal.incomes, []);
  assert.ok(!("model_income_snapshot" in personal));
  personal.incomes = [{ basis: "gross_income", period: "year", amount_cents: 9000000 }];
  const results = compareMunicipalities(catalog, personal, registry);
  for (const id of ["ditzingen", "esslingen", "korntal-muenchingen"]) {
    assert.equal(results.find(row => row.municipality_id === id).monthly_equivalent_cents, null);
  }
  assert.deepEqual(model, before);
});

test("Fraction arithmetic keeps repeating periods and safe integer limits exact", () => {
  assert.equal(new Fraction(6000001).divide(12).multiply(12).compare(6000001), 0);
  assert.equal(roundMoney(new Fraction(1, 2)), 1);
  assert.equal(roundMoney(new Fraction(-1, 2)), -1);
  assert.throws(() => roundMoney(new Fraction(9007199254740992n)), RangeError);
});
