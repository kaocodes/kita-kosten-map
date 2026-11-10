import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { compareModelFamily, modelProfile, normalizeSelection, validateModelCatalog } from "../../build/domain/model-family.js";
import { compareMunicipalities } from "../../build/domain/index.js";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url), "utf8"));
const bundle = read("web/public/data/region-stuttgart.json");
const models = validateModelCatalog(read("data/models/configuration.json"));
const base = () => structuredClone(models.default);
const child = (category, daily_minutes = 480) => ({ category, daily_minutes });
const compare = (selection, tariffs = bundle.tariffs, registry = bundle.registry) => compareModelFamily(tariffs, bundle.profiles.default, selection, registry, models);
const city = (rows, id) => rows.find(row => row.municipality_id === id);

test("Default model preserves every reviewed municipal fee, package and source", () => {
  const original = compareMunicipalities(bundle.tariffs, bundle.profiles.default, bundle.registry);
  const configured = compare(base());
  for (const row of configured) {
    const expected = city(original, row.municipality_id);
    for (const key of ["monthly_care_cents", "annual_care_cents", "monthly_equivalent_cents", "booked_weekly_minutes", "offer_id", "status"]) assert.equal(row[key], expected[key], key);
    assert.deepEqual(row.evidence, [...new Map(expected.evidence.map(item => [item.source_id + ":" + item.locator, item])).values()]);
  }
});

test("Six explicit income scenarios cover six Esslingen, four Ditzingen and five Korntal bands", () => {
  const selected = { esslingen: new Set(), ditzingen: new Set(), "korntal-muenchingen": new Set() };
  for (const scenario of models.income_scenarios) {
    const results = compare({ ...base(), income_id: scenario.id });
    for (const id of Object.keys(selected)) {
      const result = city(results, id).children[0].result;
      assert.equal(result.status, "comparable");
      const tariff = bundle.tariffs.find(item => item.id === id);
      selected[id].add(tariff.prices.find(item => item.id === result.selected_price_id).selectors.income_band_id);
    }
  }
  assert.equal(selected.esslingen.size, 6);
  assert.equal(selected.ditzingen.size, 4);
  assert.equal(selected["korntal-muenchingen"].size, 5);
});

test("Both household choices, all scenarios and both care durations calculate without stale assumptions", () => {
  for (const household of ["couple", "single"]) for (const scenario of models.income_scenarios) for (const minutes of [360, 480]) {
    const selection = { household, income_id: scenario.id, children: [child("nursery", minutes)] };
    assert.equal(compare(selection).filter(item => item.status === "comparable").length,
      bundle.registry.municipalities.filter(item => item.active).length);
    const profile = modelProfile(bundle.profiles.default, selection, models);
    assert.equal(profile.single_parent, household === "single");
    assert.deepEqual(profile.model_income_snapshot.incomes, scenario.incomes);
    assert.deepEqual(profile.approved_rules, []);
    assert.equal(profile.pass_id, "none");
  }
});

test("Two children match independently transcribed published table cells", () => {
  const rows = compare({ ...base(), children: [child("nursery"), child("kindergarten")] });
  // Published 2-child, no-pass cells: Stuttgart PDF pp. 1–2; Korntal Anlagen 1/2;
  // Esslingen GT table; Ditzingen GT45 table. Amounts are original monthly cents.
  for (const [id, first, second, months] of [["stuttgart", 20200, 12000, 11], ["korntal-muenchingen", 23920, 16790, 11],
    ["esslingen", 41300, 24300, 12], ["ditzingen", 44500, 30600, 12]]) {
    const row = city(rows, id);
    assert.equal(row.children[0].result.monthly_care_cents, first, id);
    assert.equal(row.children[1].result.monthly_care_cents, second, id);
    assert.equal(row.annual_care_cents, (first + second) * months, id);
    assert.equal(row.monthly_equivalent_cents, Math.round((first + second) * months / 12), id);
    assert.ok(row.evidence.length);
  }
});

test("Home and school categories count as siblings without adding care or meal charges", () => {
  for (const category of ["home", "school"]) {
    const row = city(compare({ ...base(), children: [child("nursery"), child(category)] }), "stuttgart");
    assert.equal(row.care_child_count, 1);
    assert.equal(row.monthly_care_cents, 20200);
    assert.equal(row.children[1].result, null);
    assert.equal(row.children[1].in_care, false);
  }
});

test("A family without Kita children has explicitly zero Kita fees and no invented offer", () => {
  for (const row of compare({ ...base(), children: [child("home"), child("school")] })) {
    assert.equal(row.status, "comparable");
    assert.equal(row.monthly_equivalent_cents, 0);
    assert.equal(row.offer_id, null);
    assert.equal(row.care_child_count, 0);
    assert.deepEqual(row.components, []);
  }
});

test("Equal Sindelfingen categories follow input order and retain the reviewed sum", () => {
  const row = city(compare({ ...base(), children: [child("nursery"), child("nursery")] }), "sindelfingen");
  assert.equal(row.status, "comparable");
  assert.equal(row.monthly_equivalent_cents, 28200 + 21150);
  assert.equal(row.children[0].result.monthly_care_cents, 28200);
  assert.equal(row.children[1].result.monthly_care_cents, 21150);
  assert.equal(row.children[0].possible_monthly_cents, undefined);
});

test("Sindelfingen assigns the older Kindergarten child first regardless of input position", () => {
  const selection = { ...base(), children: [child("nursery"), child("kindergarten")] };
  const row = city(compare(selection), "sindelfingen");
  assert.equal(row.status, "comparable");
  assert.equal(row.monthly_equivalent_cents, 35420);
  assert.equal(row.children[0].result.monthly_care_cents, 21150);
  assert.equal(row.children[1].result.monthly_care_cents, 14270);
  assert.deepEqual(row.reasons, []);
  assert.ok(row.children.every(child => child.possible_monthly_cents === undefined));
  const reverse = city(compare({ ...selection, children: [...selection.children].reverse() }), "sindelfingen");
  assert.equal(reverse.monthly_equivalent_cents, 35420);
  assert.equal(reverse.children[0].result.monthly_care_cents, 14270);
  assert.equal(reverse.children[1].result.monthly_care_cents, 21150);
});

test("An unavailable child retains known sibling results but never a partial total", () => {
  const tariffs = structuredClone(bundle.tariffs);
  const cityTariff = tariffs.find(item => item.id === "stuttgart");
  cityTariff.offers = cityTariff.offers.filter(item => item.age_group !== "o3");
  const row = city(compare({ ...base(), children: [child("nursery"), child("kindergarten")] }, tariffs), "stuttgart");
  assert.equal(row.monthly_equivalent_cents, null);
  assert.equal(row.annual_care_cents, null);
  assert.equal(row.children[0].result.monthly_equivalent_cents, 18517);
  assert.equal(row.children[1].result.monthly_equivalent_cents, null);
});

test("A missing assigned rank retains known sibling fees without publishing a partial total", () => {
  const tariffs = structuredClone(bundle.tariffs);
  const tariff = tariffs.find(item => item.id === "sindelfingen");
  tariff.prices = tariff.prices.filter(item => item.selectors.care_rank !== 2);
  const row = city(compare({ ...base(), children: [child("nursery"), child("nursery")] }, tariffs), "sindelfingen");
  assert.equal(row.monthly_equivalent_cents, null);
  assert.equal(row.status, "unavailable");
  assert.equal(row.children[0].result.monthly_equivalent_cents, 28200);
  assert.equal(row.children[1].result.monthly_equivalent_cents, null);
});

test("Sindelfingen ranks only Kita children while home and school children still count for family size", () => {
  const row = city(compare({ ...base(), children: [child("school"), child("nursery"), child("home"), child("kindergarten")] }), "sindelfingen");
  assert.equal(row.status, "comparable");
  assert.equal(row.children[0].result, null);
  assert.equal(row.children[2].result, null);
  assert.equal(row.children[1].result.care_rank, 2);
  assert.equal(row.children[3].result.care_rank, 1);
  assert.equal(row.children[1].result.family_count, 4);
});

test("Same-category Sindelfingen children use input order even with different care durations", () => {
  const row = city(compare({ ...base(), children: [child("nursery", 360), child("nursery", 480)] }), "sindelfingen");
  assert.equal(row.children[0].result.monthly_care_cents, 19070);
  assert.equal(row.children[1].result.monthly_care_cents, 21150);
  assert.equal(row.monthly_equivalent_cents, 40220);
  const reverse = city(compare({ ...base(), children: [child("nursery", 480), child("nursery", 360)] }), "sindelfingen");
  assert.equal(reverse.children[0].result.monthly_care_cents, 28200);
  assert.equal(reverse.children[1].result.monthly_care_cents, 14300);
  assert.equal(reverse.monthly_equivalent_cents, 42500);
});

test("Geographic aliases sharing the Sindelfingen tariff use the same age-based ranking", () => {
  const registry = structuredClone(bundle.registry);
  const original = registry.municipalities.find(item => item.tariff_id === "sindelfingen");
  registry.municipalities.push({ ...original, id: "synthetic-sindelfingen", ags: "99999998", area_id: "synthetic-sindelfingen" });
  const rows = compare({ ...base(), children: [child("nursery"), child("kindergarten")] }, bundle.tariffs, registry);
  assert.equal(city(rows, "synthetic-sindelfingen").monthly_equivalent_cents, 35420);
  assert.equal(city(rows, "sindelfingen").monthly_equivalent_cents, 35420);
});

test("Annual totals are rounded once and never reconstructed from rounded monthly child values", () => {
  const selection = { ...base(), children: [child("nursery"), child("nursery"), child("nursery")] };
  const tariffs = structuredClone(bundle.tariffs);
  for (const price of tariffs.find(item => item.id === "stuttgart").prices) if (price.selectors.family_count === 3 && price.selectors.pass_id === "none") price.amount_cents = 100;
  const row = city(compare(selection, tariffs), "stuttgart");
  assert.equal(row.annual_care_cents, 3300);
  assert.equal(row.monthly_equivalent_cents, 275);
  assert.equal(row.children.reduce((sum, item) => sum + item.result.monthly_equivalent_cents, 0), 276);
});

test("Missing five-child columns remain unavailable and do not extrapolate four-child fees", () => {
  const row = city(compare({ ...base(), children: Array.from({ length: 5 }, () => child("nursery")) }), "kornwestheim");
  assert.equal(row.status, "unavailable");
  assert.equal(row.monthly_equivalent_cents, null);
});

test("Models remain geographically extensible and evaluations never mutate inputs", () => {
  const registry = structuredClone(bundle.registry);
  const entry = { ...registry.municipalities[0], id: "synthetic-area", ags: "99999999", area_id: "synthetic-area" };
  registry.municipalities.push(entry);
  const before = JSON.stringify({ bundle, models });
  const results = compare(base(), bundle.tariffs, registry);
  assert.equal(city(results, entry.id).monthly_equivalent_cents, city(results, registry.municipalities[0].id).monthly_equivalent_cents);
  results[0].children[0].result.evidence[0].locator = "Changed";
  assert.equal(JSON.stringify({ bundle, models }), before);
});

test("Catalogs and model selections reject unknown scenarios, malformed children and incomplete definitions", () => {
  for (const selection of [{ ...base(), income_id: "unknown" }, { ...base(), children: [] }, { ...base(), children: [child("adult")] },
    { ...base(), children: [child("nursery", 420)] }, { ...base(), children: Array(13).fill(child("nursery")) }]) assert.throws(() => normalizeSelection(selection, models));
  const wrong = structuredClone(models); wrong.income_scenarios[0].incomes.pop();
  assert.throws(() => validateModelCatalog(wrong));
  const duplicate = structuredClone(models); duplicate.categories[1] = duplicate.categories[0];
  assert.throws(() => validateModelCatalog(duplicate));
});
