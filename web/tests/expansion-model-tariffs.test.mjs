import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { weeklyComparison } from "../../build/domain/engine.js";
import { compareModelFamily, validateModelCatalog } from "../../build/domain/model-family.js";
import { projectWebTariff } from "../../scripts/project_web_tariff.mjs";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url)));
const models = validateModelCatalog(read("data/models/configuration.json"));
const reference = read("data/profiles/default.json");
const nursery = { category: "nursery", daily_minutes: 360 };
const nurseryFullDay = { ...nursery, daily_minutes: 480 };
const kindergarten = { category: "kindergarten", daily_minutes: 360 };
const kindergartenFullDay = { ...kindergarten, daily_minutes: 480 };
const school = { category: "school", daily_minutes: 480 };
const home = { category: "home", daily_minutes: 480 };

const cases = [
  [[nursery]],
  [[nurseryFullDay]],
  [[kindergarten]],
  [[kindergartenFullDay]],
  [[nurseryFullDay, kindergartenFullDay]],
  [[kindergartenFullDay, school]],
  [[school, kindergartenFullDay, nursery, home]],
  [[kindergartenFullDay], "single"],
];

// Expected monthly equivalents from the archived tariffs and the documented model assumptions.
const expected = {
  eberdingen: { prices: [36600, 45700, 15600, 25300, 58300, 25300, 49200, 25300], minutes: [1800, 2250, 1800, 2250] },
  erdmannhausen: { prices: [50060, 60060, 20770, 30770, 63270, 26070, 23590, 26070], minutes: [2050, 2430, 2100, 2460] },
  freiberg: { prices: [34500, 45200, 20992, 32542, 64725, 32542, 54025, 32542], minutes: [1800, 2400, 1800, 2400] },
  hemmingen: { prices: [30680, 59540, 16600, 43160, 94120, 39190, 37050, 34530], minutes: [1800, 2550, 1800, 2550] },
  kernen: { prices: [47100, 49500, 17100, 27500, 61600, 22000, 31300, 24750], minutes: [1800, 2400, 1800, 2400] },
  magstadt: { prices: [48200, 59500, 16600, 39400, 74600, 30500, 32200, 39400], minutes: [1800, 2400, 1800, 2400] },
  remseck: { prices: [32633, 55825, 20625, 27867, 64442, 21450, 10083, 27867], minutes: [1800, 2250, 1800, 2250] },
  renningen: { prices: [49200, 65600, 20800, null, null, null, null, null], minutes: [1800, 2400, 1800, 2400] },
  rutesheim: { prices: [21000, 36500, 16600, 36500, 68000, 36500, 57500, 36500], minutes: [1875, 2400, 1875, 2400] },
  schoenaich: { prices: [51660, 69000, 17568, 53000, 89300, 38000, 25185, 53000], minutes: [1890, 2250, 1905, 3090] },
  schwieberdingen: { prices: [45100, 51242, 16133, 17050, 52525, 13658, 13383, 13658], minutes: [1800, 2400, 1800, 2400] },
  waiblingen: { prices: [24932, 43216, 20777, 34905, 58627, 18105, 26343, 34905], minutes: [1800, 2400, 1800, 2400] },
};

function compare(id, children, household = "couple", income_id = "income-80000") {
  const tariff = projectWebTariff(read(`data/expansion/municipalities/${id}.json`));
  const registry = { municipalities: [{ id, name: tariff.name, active: true, tariff_id: id }] };
  return compareModelFamily([tariff], reference, { household, income_id, children }, registry, models, weeklyComparison)[0];
}

for (const [id, baseline] of Object.entries(expected)) {
  test(`${id}: eight model-family tariff checks`, () => {
    const results = cases.map(([children, household]) => compare(id, children, household));
    assert.deepEqual(results.map(row => row.monthly_equivalent_cents), baseline.prices);
    assert.deepEqual(results.slice(0, 4).map(row => row.booked_weekly_minutes), baseline.minutes);
    assert.ok(results.every((row, index) => row.status === (baseline.prices[index] === null ? "unavailable" : "comparable")));
  });
}

test("special tariff terms are reflected in the model price or the unavailability reason", () => {
  const remseck = compare("remseck", [nurseryFullDay]).children[0].result;
  const meal = remseck.components.find(part => part.kind === "meal");
  assert.deepEqual([meal.amount_cents, meal.payment_months, meal.required], [4500, 10, true]);

  const erdmannhausen = compare("erdmannhausen", [nurseryFullDay, kindergartenFullDay]);
  assert.deepEqual(erdmannhausen.children.map(child => child.result.monthly_care_cents), [42200, 21070]);
  assert.ok(erdmannhausen.children.every(child => child.result.components[0].amount_cents === 3360));

  assert.ok(compare("freiberg", [nurseryFullDay, nursery]).reasons.includes("tariff_sibling_discount_not_confirmed"));
  assert.ok(compare("renningen", [kindergartenFullDay]).reasons.includes("tariff_monthly_conversion_not_confirmed"));
  const rutesheim = compare("rutesheim", [nurseryFullDay, kindergartenFullDay]);
  assert.deepEqual(rutesheim.children.map(child => child.result.monthly_care_cents), [31500, 36500]);
  assert.equal(compare("schwieberdingen", [nurseryFullDay, nursery], "single").monthly_equivalent_cents, 21633);
  assert.ok(compare("schwieberdingen", [kindergartenFullDay, kindergarten]).reasons.includes("tariff_sibling_rank_not_confirmed"));

  const waiblingen = compare("waiblingen", [nurseryFullDay], "couple", "income-180000");
  assert.equal(waiblingen.monthly_equivalent_cents, 62400);
  assert.equal(waiblingen.children[0].result.components[0].value_status, "included");

  const magstadt = compare("magstadt", [school, school, kindergarten, nursery]);
  assert.equal(magstadt.children[3].result.monthly_equivalent_cents, 0);
});
