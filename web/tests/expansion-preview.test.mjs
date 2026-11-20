import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { weeklyComparison } from "../../build/domain/engine.js";
import { compareModelFamily, validateModelCatalog } from "../../build/domain/model-family.js";
import { feeColor, MISSING_COLOR } from "../../build/site/presentation.js";
import { projectWebTariff } from "../../scripts/project_web_tariff.mjs";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url)));
const firstBatch = read("data/expansion/manifest.json");
const additionalBatch = read("data/expansion/batches/2026-11-20/manifest.json");
const production = read("data/municipality_registry.json");
const bundle = read("build/expansion-preview/region-stuttgart.json");
const geometry = read("build/expansion-preview/municipalities.geojson");
const active = bundle.registry.municipalities.filter(item => item.active);
const models = validateModelCatalog(bundle.models);
const catalogPaths = new Map([...firstBatch.municipalities, ...additionalBatch.municipalities].map(item => [item.id, item.path]));
const productionIDs = new Set(production.municipalities.filter(item => item.active).map(item => item.id));

function compare(selection, tariffs = bundle.tariffs) {
  return compareModelFamily(tariffs, bundle.profiles.default, selection, bundle.registry, models, weeklyComparison);
}

test("Preview matches all original and expansion tariffs to labeled municipal polygons", () => {
  const ids = new Set([...productionIDs, ...catalogPaths.keys()]);
  assert.deepEqual(new Set(active.map(item => item.id)), ids);
  assert.equal(active.length, ids.size);
  assert.deepEqual(new Set(bundle.tariffs.map(item => item.id)), ids);
  for (const entry of active) {
    const matches = geometry.features.filter(feature => feature.properties.municipality_id === entry.id);
    assert.equal(matches.length, 1, entry.id);
    assert.equal(matches[0].properties.ags, entry.ags);
    assert.equal(matches[0].properties.area_id, entry.area_id);
    assert.equal(matches[0].properties.label_point.length, 2);
  }
});

test("Preview projection preserves weekly model-family results from the source catalogs", () => {
  const fullTariffs = active.map(({ id }) => projectWebTariff(read(productionIDs.has(id)
    ? `data/municipalities/${id}.json` : catalogPaths.get(id))));
  const summarize = rows => rows.map(row => ({
    municipality: row.municipality_id, status: row.status, amount: row.monthly_equivalent_cents,
    minutes: row.booked_weekly_minutes, reasons: row.reasons,
    children: row.children.map(({ result }) => result && [
      result.selected_price_id, result.monthly_care_cents, result.booked_weekly_minutes,
      result.components.map(part => [part.id, part.amount_cents, part.value_status]),
    ]),
    evidence: row.evidence.map(({ source_id, locator }) => [source_id, locator]),
  }));
  const nursery = { category: "nursery", daily_minutes: 480 };
  const kindergarten = { category: "kindergarten", daily_minutes: 360 };
  for (const children of [[nursery], [kindergarten], [nursery, kindergarten],
    [{ ...kindergarten, daily_minutes: 480 }, kindergarten]]) {
    const selection = { ...models.default, children };
    const results = compare(selection);
    const expected = summarize(compare(selection, fullTariffs));
    for (const [index, result] of summarize(results).entries()) {
      assert.deepEqual(result, expected[index], result.municipality);
    }
    for (const row of results) {
      for (const evidence of row.evidence) assert.ok(bundle.sources[evidence.source_id], evidence.source_id);
    }
  }
});

test("An unavailable tariff remains on the map and does not become a zero fee", () => {
  const unavailable = compare(models.default).filter(row => row.monthly_equivalent_cents === null);
  assert.deepEqual(unavailable.map(row => row.municipality_id), ["baltmannsweiler"]);
  assert.equal(unavailable[0].status, "unavailable");
  assert.equal(feeColor(unavailable[0]), MISSING_COLOR);
  const kindergarten = { category: "kindergarten", daily_minutes: 480 };
  const results = compare({ ...models.default, children: [kindergarten] });
  const renningen = results.find(row => row.municipality_id === "renningen");
  assert.equal(renningen.status, "unavailable");
  assert.equal(renningen.booked_weekly_minutes, 2400);
  assert.ok(renningen.reasons.includes("tariff_monthly_conversion_not_confirmed"));
  assert.equal(feeColor(renningen), MISSING_COLOR);
});

test("The three additional municipalities use source-checked hours and standard fees", () => {
  const expected = {
    "neuhausen-auf-den-fildern": [[2175, 62084], [2400, 68506], [2400, 35120], [2400, 35120]],
    markgroeningen: [[1800, 50000], [2400, 66500], [1800, 15058], [2400, 20077]],
    "bietigheim-bissingen": [[1800, 25900], [2400, 40400], [1800, 15000], [2400, 28100]],
  };
  const scenarios = [["nursery", 360], ["nursery", 480], ["kindergarten", 360], ["kindergarten", 480]];
  for (const [index, [category, daily_minutes]] of scenarios.entries()) {
    const results = compare({ ...models.default, children: [{ category, daily_minutes }] });
    for (const [id, reference] of Object.entries(expected)) {
      const row = results.find(result => result.municipality_id === id);
      assert.equal(row.status, "comparable", id);
      assert.deepEqual([row.booked_weekly_minutes, row.monthly_equivalent_cents], reference[index], id);
    }
  }
});

test("Bietigheim-Bissingen applies the VÖ exemption to birth rank, including siblings outside Kita", () => {
  const nursery = { category: "nursery", daily_minutes: 360 };
  const kindergarten = { category: "kindergarten", daily_minutes: 480 };
  const school = { category: "school", daily_minutes: 480 };
  const children = [nursery, school, kindergarten];
  for (const entries of [children, [...children].reverse()]) {
    const results = compare({ ...models.default, children: entries });
    const city = results.find(row => row.municipality_id === "bietigheim-bissingen");
    assert.equal(city.status, "comparable");
    assert.equal(city.children.find(child => child.category === "nursery").result.monthly_equivalent_cents, 0);
    assert.equal(city.monthly_equivalent_cents, 14200);
    assert.equal(city.children.find(child => child.category === "kindergarten").result.components[0].amount_cents, 9500);
  }
});

test("Weinstadt uses confirmed five-day offers, the household scale and eleven fee months", () => {
  const nursery = { category: "nursery", daily_minutes: 360 };
  const nurseryFullDay = { ...nursery, daily_minutes: 480 };
  const kindergarten = { category: "kindergarten", daily_minutes: 360 };
  const kindergartenFullDay = { ...kindergarten, daily_minutes: 480 };
  const school = { category: "school", daily_minutes: 480 };
  const home = { category: "home", daily_minutes: 480 };
  const cases = [
    [[nursery], 1800, 39875], [[nurseryFullDay], 2400, 63800],
    [[kindergarten], 1800, 15950], [[kindergartenFullDay], 2400, 31900],
    [[nurseryFullDay, kindergarten], 4200, 67833], [[kindergartenFullDay, school], 2400, 27133],
    [[school, kindergartenFullDay, nursery, home], 4200, 17967],
    [[kindergartenFullDay], 2400, 31900, "single"],
  ];
  for (const [children, minutes, amount, household = "couple"] of cases) {
    const row = compare({ ...models.default, household, children }).find(item => item.municipality_id === "weinstadt");
    assert.equal(row.status, "comparable");
    assert.deepEqual([row.booked_weekly_minutes, row.monthly_equivalent_cents, row.payment_months], [minutes, amount, 11]);
    for (const child of row.children.filter(item => item.in_care && item.daily_minutes === 480)) {
      const meal = child.result.components.find(item => item.kind === "meal");
      assert.deepEqual([meal.amount_cents, meal.required, meal.payment_months], [10500, true, 11]);
    }
  }
});
