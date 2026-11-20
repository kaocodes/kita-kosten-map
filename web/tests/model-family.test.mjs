import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { compareModelFamily, modelProfile, normalizeSelection, validateModelCatalog } from "../../build/domain/model-family.js";
import { weeklyComparison } from "../../build/domain/engine.js";
import { compareMunicipalities } from "../../build/domain/index.js";
import { projectWebTariff } from "../../scripts/project_web_tariff.mjs";

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
    const monthlyNet = scenario.household_net_monthly_cents[household];
    assert.deepEqual(profile.model_income_snapshot.incomes, [
      ...scenario.incomes,
      { basis: "ostfildern_assessable_income", period: "year", amount_cents: scenario.gross_annual_cents },
      { basis: "household_net", period: "month", amount_cents: monthlyNet },
      { basis: "freiberg_household_net", period: "month", amount_cents: monthlyNet + 25900 },
    ]);
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

test("Model families reject five children before evaluating tariffs", () => {
  const children = Array.from({ length: 5 }, () => child("nursery"));
  assert.doesNotThrow(() => compare({ ...base(), children: children.slice(0, 4) }));
  assert.throws(() => compare({ ...base(), children }));
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

const fridayRule = { allowShorterFriday: true };

test("The map's weekly rule matches the 13-municipality release samples", () => {
  const scenarios = [
    [child("nursery", 360)], [child("nursery")], [child("kindergarten", 360)], [child("kindergarten")],
    [child("nursery"), child("kindergarten", 360)], [child("kindergarten", 360), child("school")],
    [child("nursery", 360), child("kindergarten"), child("school"), child("home")], [child("kindergarten")],
  ];
  // Source-backed weekly minutes and monthly equivalents from the release review.
  const expected = {
    affalterbach: [[2400,50300],[2400,50300],[1800,15500],[2400,34000],[4200,61900],[1800,11600],[4800,0],[2400,34000]],
    aichwald: [[2100,54100],[2550,63700],[1800,16600],[2550,27350],[4350,60300],[1800,12900],[4650,15500],[2550,27350]],
    altbach: [[1800,49225],[2400,65633],[1800,20808],[2400,33917],[4200,64992],[1800,16225],[4200,21267],[2400,33917]],
    baltmannsweiler: [[1800,37483],null,[1800,14927],[2430,29796],null,[1800,11195],[4230,13457],[2430,29796]],
    benningen: [[1950,39783],[2730,76450],[1950,19892],[2730,38225],[4680,75075],[1950,15492],[4680,13658],[2730,38225]],
    denkendorf: [[1800,49225],[2700,71133],[1800,16592],[2700,38408],[4500,65542],[1800,12925],[4500,16592],[2700,38408]],
    filderstadt: [[1800,49225],[2400,68915],[1800,16592],[2400,23228],[4200,64130],[1800,12925],[4200,13823],[2400,23228]],
    grafenau: [[1800,53700],[2430,69700],[1800,18300],[2430,33000],[4230,67700],[1800,14000],[4230,18800],[2430,33000]],
    ostfildern: [[2100,31900],[2400,36400],[1800,16600],[2400,22100],[4200,43500],[1800,13600],[4500,18600],[2400,22100]],
    plochingen: [[1800,37200],[2340,65400],[1800,18600],[2340,30300],[4140,67100],[1800,15000],[4140,15500],[2340,30300]],
    steinenbronn: [[2100,41100],[2460,47600],[1950,24800],[2460,29400],[4410,52900],[1950,19000],[4560,13300],[2460,29400]],
    waldenbuch: [[1800,42600],[2400,65700],[1800,23700],[2400,36500],[4200,69200],[1800,18300],[4200,41200],[2400,36500]],
    weissach: [[1800,41300],[2400,55100],[1800,13900],[2400,35300],[4200,53200],[1800,10800],[4200,12800],[2400,35300]],
  };
  for (const [id, results] of Object.entries(expected)) {
    const tariff = projectWebTariff(read(`data/expansion/municipalities/${id}.json`));
    const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
    for (const [index, children] of scenarios.entries()) {
      const [result] = compareModelFamily([tariff], bundle.profiles.default,
        { ...base(), children, household: index === 7 ? "single" : "couple" }, registry, models, weeklyComparison);
      const reference = results[index];
      assert.deepEqual([result.booked_weekly_minutes, result.monthly_equivalent_cents],
        reference ?? [null, null], `${id}, sample ${index + 1}`);
      assert.equal(result.status, reference ? "comparable" : "unavailable");
      if (!reference) assert.deepEqual(result.reasons, ["no_offer_covers_daily_need"]);
    }
  }
});

test("The live catalog uses Ehningen's confirmed 39-hour combination", () => {
  const results = compareModelFamily(bundle.tariffs, bundle.profiles.default, base(), bundle.registry, models, weeklyComparison);
  const ehningen = city(results, "ehningen");
  assert.deepEqual([ehningen.booked_weekly_minutes, ehningen.monthly_equivalent_cents], [2340, 65817]);
  assert.ok(results.every(row => row.status === "comparable"));
});

test("The weekly rule requires five care days and treats 36 hours as eligible", () => {
  const id = "affalterbach";
  const tariff = read(`data/expansion/municipalities/${id}.json`);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
  const offer = tariff.offers.find(item => item.age_group === "u3");
  for (const [schedule, expected] of [
    [[480, 480, 480, 480, 240], 2160],
    [[480, 480, 480, 480, 239], null],
    [[600, 600, 600, 600, 0], null],
  ]) {
    offer.weekday_minutes = schedule;
    offer.weekly_minutes = schedule.reduce((total, minutes) => total + minutes, 0);
    const [result] = compareModelFamily([tariff], bundle.profiles.default, base(), registry, models, weeklyComparison);
    assert.equal(result.booked_weekly_minutes, expected);
    assert.equal(result.status, expected === null ? "unavailable" : "comparable");
  }
});

test("The model shows real weekday hours and monthly equivalents for verified shorter Fridays", () => {
  for (const [id, schedule, amounts] of [
    ["affalterbach", [510, 510, 510, 510, 360], [50300, 34000, 50300, 15500]],
    ["denkendorf", [570, 570, 570, 570, 420], [71133, 38408, 49225, 16592]],
  ]) {
    const tariff = read(`data/expansion/municipalities/${id}.json`);
    const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
    const selections = [child("nursery"), child("kindergarten"), child("nursery", 360), child("kindergarten", 360)];
    selections.forEach((entry, index) => {
      const selection = { ...base(), children: [entry] };
      const [family] = compareModelFamily([tariff], bundle.profiles.default, selection, registry, models, fridayRule);
      const row = family.children[0].result;
      assert.equal(family.monthly_equivalent_cents, amounts[index], id);
      assert.deepEqual(row.shorter_friday_weekday_minutes, index < 2 ? schedule : undefined, id);
      if (index < 2) {
        assert.equal(row.booked_weekly_minutes, schedule.reduce((total, minutes) => total + minutes, 0));
        assert.ok(row.extra_weekly_minutes >= 0);
        assert.equal(compare(selection, [tariff], registry)[0].monthly_equivalent_cents, null);
      }
    });
  }
});

test("A weekly average cannot substitute for the Friday minimum or for eight hours on an earlier weekday", () => {
  const id = "affalterbach";
  const tariff = read(`data/expansion/municipalities/${id}.json`);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
  const offer = tariff.offers.find(item => item.age_group === "u3");
  for (const schedule of [[540, 540, 540, 540, 359], [479, 540, 540, 540, 420]]) {
    offer.weekday_minutes = schedule;
    offer.weekly_minutes = schedule.reduce((total, minutes) => total + minutes, 0);
    const [result] = compareModelFamily([tariff], bundle.profiles.default, base(), registry, models, fridayRule);
    assert.equal(result.status, "unavailable");
    assert.deepEqual(result.reasons, ["no_offer_covers_daily_need"]);
    assert.equal(result.booked_weekly_minutes, null);
  }
});

test("An offer with four care days loses to a more expensive five-day offer", () => {
  const id = "affalterbach";
  const tariff = read(`data/expansion/municipalities/${id}.json`);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
  const fullWeek = tariff.offers.find(item => item.age_group === "u3");
  const fourDays = { ...fullWeek, id: "four-day-test", weekday_minutes: [600, 600, 600, 600, 0], weekly_minutes: 2400 };
  tariff.offers.push(fourDays);
  const fullWeekPrices = tariff.prices.filter(row => row.offer_id === fullWeek.id);
  tariff.prices.push(...fullWeekPrices.map(row => ({
    ...row, id: row.id + "-four-days", offer_id: fourDays.id, amount_cents: row.amount_cents - 10000,
  })));
  const [fallback] = compareModelFamily([tariff], bundle.profiles.default, base(), registry, models, fridayRule);
  assert.equal(fallback.offer_id, fullWeek.id);
  tariff.offers = [fourDays];
  const [unavailable] = compareModelFamily([tariff], bundle.profiles.default, base(), registry, models, fridayRule);
  assert.equal(unavailable.status, "unavailable");
  assert.deepEqual(unavailable.reasons, ["no_offer_covers_daily_need"]);
});

test("Weekly-hours comparison selects the smaller eligible packages in Deizisau and Fellbach", () => {
  const scenarios = [
    base(),
    { ...base(), children: [child("nursery", 360)] },
    { ...base(), children: [child("kindergarten")] },
    { ...base(), children: [child("kindergarten", 360)] },
    { ...base(), children: [child("nursery"), child("kindergarten", 360)] },
    { ...base(), children: [child("nursery", 360), child("kindergarten"), child("school"), child("home")] },
    { ...base(), household: "single", income_id: models.income_scenarios[0].id, children: [child("nursery"), child("kindergarten")] },
    { ...base(), income_id: models.income_scenarios.at(-1).id, children: [child("kindergarten"), child("kindergarten")] },
  ];
  for (const scenario of scenarios) {
    const results = compareModelFamily(bundle.tariffs, bundle.profiles.default, scenario, bundle.registry, models, fridayRule);
    const previous = compare(scenario);
    const changed = new Map([
      ["deizisau", [600, 600, 600, 600, 360]],
      ["fellbach", [540, 540, 540, 540, 390]],
    ]);
    const other = rows => rows.filter(row => !changed.has(row.municipality_id));
    assert.deepEqual(other(results), other(previous));
    for (const [id, schedule] of changed) {
      const family = city(results, id);
      for (const child of family.children.filter(child => child.in_care && child.daily_minutes === 480)) {
        assert.deepEqual(child.result.shorter_friday_weekday_minutes, schedule);
        assert.equal(child.result.booked_weekly_minutes, schedule.reduce((sum, value) => sum + value, 0));
      }
    }
  }
});

test("A smaller eligible package with a shorter Friday takes priority over a longer full-week package", () => {
  const id = "affalterbach";
  const tariff = read(`data/expansion/municipalities/${id}.json`);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
  const original = tariff.offers.find(item => item.age_group === "u3");
  const fullWeek = { ...original, id: "full-week", weekday_minutes: Array(5).fill(540), weekly_minutes: 2700 };
  tariff.offers.push(fullWeek);
  tariff.prices.push(...tariff.prices.filter(row => row.offer_id === original.id)
    .map(row => ({ ...row, id: `full-week-${row.id}`, offer_id: fullWeek.id })));
  const [family] = compareModelFamily([tariff], bundle.profiles.default, base(), registry, models, fridayRule);
  const result = family.children[0].result;
  assert.equal(result.offer_id, original.id);
  assert.deepEqual(result.shorter_friday_weekday_minutes, [510, 510, 510, 510, 360]);
});

test("Aichwald browser tariffs separate the meal and keep its original published total reproducible", () => {
  const id = "aichwald";
  const catalog = read(`data/expansion/municipalities/${id}.json`);
  const tariff = projectWebTariff(catalog);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
  const cases = [
    [child("nursery", 360), 54100, 5300, 59400],
    [child("nursery"), 70050, 5300, 75350],
    [child("kindergarten", 360), 20750, 7500, 20750],
    [child("kindergarten"), 31750, 7500, 39250],
  ];
  for (const [entry, care, meal, total] of cases) {
    const selection = { ...base(), children: [entry] };
    const [result] = compareModelFamily([tariff], bundle.profiles.default, selection, registry, models, fridayRule);
    const row = result.children[0].result;
    const [mealPart] = row.components;
    const price = catalog.prices.find(item => item.id === row.selected_price_id);
    assert.equal(result.monthly_equivalent_cents, care);
    assert.equal(price.amount_cents, total);
    assert.equal(row.total_mandatory_monthly_equivalent_cents, total);
    assert.equal(row.payment_months, 12);
    assert.equal(row.components.length, 1);
    assert.equal(mealPart.amount_cents, meal);
    assert.equal(mealPart.required, care !== total);
    assert.equal(mealPart.separated_from_care_price, care !== total ? true : undefined);
    assert.equal(row.shorter_friday_weekday_minutes, undefined);
    assert.equal(row.booked_weekly_minutes, entry.daily_minutes === 480 ? 2850 : 2100);
  }

  for (const [selection, expected] of [
    [{ ...base(), children: [child("nursery"), child("kindergarten", 360)] }, 68300],
    [{ ...base(), household: "single", children: [child("nursery"), child("kindergarten"), child("home"), child("school")] }, 19450],
  ]) {
    const [result] = compareModelFamily([tariff], bundle.profiles.default, selection, registry, models, fridayRule);
    assert.equal(result.monthly_equivalent_cents, expected);
  }

  assert.deepEqual(catalog, read(`data/expansion/municipalities/${id}.json`));
});


test("Source tariff samples cover transferred rules for eleven expansion municipalities", () => {
  const scenarios = [
    [child("nursery", 360)],
    [child("nursery")],
    [child("kindergarten", 360)],
    [child("kindergarten")],
    [child("nursery"), child("kindergarten", 360)],
    [child("kindergarten", 360), child("school")],
    [child("nursery", 360), child("kindergarten"), child("school"), child("home")],
    [child("kindergarten")],
  ];
  // Published tariff cells with the documented meal and payment-month adjustments.
  const expected = {
    affalterbach: [50300, 50300, 15500, 34000, 61900, 11600, 0, 34000],
    aichwald: [54100, 70050, 20750, 31750, 68300, 16150, 16300, 31750],
    altbach: [49225, 65633, 20808, 33917, 64992, 16225, 21267, 33917],
    baltmannsweiler: [37483, null, 14927, 34454, null, 11195, 14388, 34454],
    benningen: [39783, 76450, 19892, 38225, 75075, 15492, 13658, 38225],
    denkendorf: [49225, 71133, 16592, 38408, 65542, 12925, 16592, 38408],
    filderstadt: [49225, null, 16592, null, null, 12925, null, null],
    grafenau: [53700, null, 18300, 38100, null, 14000, 20100, 38100],
    plochingen: [37200, 70000, 18600, 34000, 69400, 15000, 15600, 34000],
    steinenbronn: [41100, null, 24800, null, null, 19000, null, null],
    weissach: [41300, 55100, 13900, 35300, 53200, 10800, 12800, 35300],
  };

  for (const [id, amounts] of Object.entries(expected)) {
    const original = read(`data/expansion/municipalities/${id}.json`);
    const tariff = projectWebTariff(original);
    const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
    for (const [index, children] of scenarios.entries()) {
      const selection = { ...base(), household: index === 7 ? "single" : "couple", children };
      const [result] = compareModelFamily([tariff], bundle.profiles.default, selection, registry, models, fridayRule);
      const amount = amounts[index];
      const context = `${id}, sample ${index + 1}`;
      assert.equal(result.status, amount === null ? "unavailable" : "comparable", context);
      assert.equal(result.monthly_equivalent_cents, amount, context);
      if (amount === null) assert.ok(result.reasons.length, context);
      else assert.ok(result.evidence.length, context);
      const row = result.children[0].result;
      if (id === "plochingen") {
        assert.ok(tariff.offers.every(offer => offer.scope === "municipal"), context);
        assert.ok(result.children.every(child => !child.result?.offer_label?.includes("St. Johann")), context);
        assert.equal(row.components.length, index === 1 || index === 4 ? 1 : index === 3 || index === 7 ? 2 : 0, context);
      }
      if (id === "benningen" && index < 4) {
        const fullDay = index % 2 === 1;
        assert.equal(row.booked_weekly_minutes, fullDay ? 2730 : 1950, context);
        assert.deepEqual(row.shorter_friday_weekday_minutes, fullDay ? [570, 570, 570, 570, 450] : undefined, context);
        assert.deepEqual(row.components.filter(part => part.kind === "meal").map(part => part.amount_cents), [6100], context);
      }
      if (id === "weissach" && index < 4) {
        const longDay = index % 2 === 1;
        assert.deepEqual(row.components.map(part => part.amount_cents), longDay ? [700, 6000] : [500], context);
        assert.equal(row.booked_weekly_minutes, longDay ? 2400 : 1800, context);
      }
      if (id === "altbach" && index < 4) {
        assert.equal(row.components[0].amount_cents, 10200, context);
        assert.equal(row.components[0].required, index !== 2, context);
        assert.equal(row.components[0].payment_months, 11, context);
      }
      if ((id === "grafenau" || id === "denkendorf") && (index === 0 || index === 2 || index === 3)) {
        assert.equal(row.components.length, index === 3 ? 1 : 0, context);
      }
    }
  }
});


test("Benningen has its own prices and meal tariff for children aged one", () => {
  const tariff = read("data/expansion/municipalities/benningen.json");
  const registry = { municipalities: [{ id: tariff.id, tariff_id: tariff.id, active: true, name: tariff.name }] };
  for (const [duration, expected] of [[360, 53350], [480, 82042]]) {
    const profile = structuredClone(bundle.profiles.default);
    profile.children[0].age_months = 18;
    profile.weekday_minutes = Array(5).fill(duration);
    const [result] = compareMunicipalities([tariff], profile, registry, undefined, fridayRule);
    assert.equal(result.monthly_equivalent_cents, expected);
    assert.deepEqual(result.components.filter(part => part.kind === "meal").map(part => [part.amount_cents, part.payment_months]), [[3300, 11]]);
  }
});

test("Freiberg uses the verified municipal schedule only with an explicit local net income", () => {
  const tariff = read("data/expansion/municipalities/freiberg.json");
  const registry = { municipalities: [{ id: tariff.id, tariff_id: tariff.id, active: true, name: tariff.name }] };
  const profile = structuredClone(bundle.profiles.default);
  profile.children[0].age_months = 48;
  profile.care_rank = 1;
  assert.equal(compareMunicipalities([tariff], profile, registry)[0].monthly_equivalent_cents, null);
  for (const [net, expected] of [[660100, 32542], [660200, 37400]]) {
    profile.municipality_overrides = { freiberg: { incomes: [
      { basis: "freiberg_household_net", period: "month", amount_cents: net },
    ] } };
    const [result] = compareMunicipalities([tariff], profile, registry);
    assert.equal(result.monthly_equivalent_cents, expected);
    assert.equal(result.booked_weekly_minutes, 2400);
    assert.deepEqual(result.components.map(part => part.amount_cents), [8200]);
  }
});

test("Freiberg model income selects both local fee bands and counts child benefit", () => {
  const tariff = read("data/expansion/municipalities/freiberg.json");
  const registry = { municipalities: [{ id: tariff.id, tariff_id: tariff.id, active: true, name: tariff.name }] };
  for (const [household, income, category, expected] of [
    ["couple", "income-80000", "nursery", 45200],
    ["single", "income-80000", "kindergarten", 32542],
    ["couple", "income-140000", "nursery", 52000],
    ["single", "income-140000", "kindergarten", 37400],
  ]) {
    const [result] = compare({ ...base(), household, income_id: income, children: [child(category)] }, [tariff], registry);
    assert.equal(result.booked_weekly_minutes, 2400);
    assert.equal(result.monthly_equivalent_cents, expected);
  }
  const selection = { ...base(), children: [child("nursery"), child("home"), child("school")] };
  const profile = modelProfile(bundle.profiles.default, selection, models);
  assert.equal(profile.incomes.find(row => row.basis === "freiberg_household_net").amount_cents, 528767);
});

test("Remaining expansion catalog samples match the supported single-child tariff cells", () => {
  const selections = [child("nursery", 360), child("nursery"), child("kindergarten", 360), child("kindergarten")];
  const expected = {
    eberdingen: [36600, null, 15600, null],
    magstadt: [48200, 59500, 16600, 39400],
    remseck: [32633, 74525, 20625, 37217],
    renningen: [49200, 65600, 20800, null],
    rutesheim: [21000, 36500, 16600, 36500],
  };
  for (const [id, amounts] of Object.entries(expected)) {
    const catalog = read(`data/expansion/municipalities/${id}.json`);
    const registry = { municipalities: [{ id, tariff_id: id, active: true, name: catalog.name }] };
    for (const [index, entry] of selections.entries()) {
      const [result] = compareModelFamily([catalog], bundle.profiles.default, { ...base(), children: [entry] },
        registry, models, fridayRule);
      assert.equal(result.monthly_equivalent_cents, amounts[index], `${id}, sample ${index + 1}`);
      assert.equal(result.status, amounts[index] === null ? "unavailable" : "comparable");
      if (id === "remseck" && entry.category === "kindergarten") {
        const [meal] = result.children[0].result.components;
        assert.equal(meal.amount_cents, 9000);
        assert.equal(meal.required, entry.daily_minutes === 480);
      }
    }
  }
});

test("Ostfildern's model uses the selected annual gross income for its prior-year tariff band", () => {
  const id = "ostfildern";
  const catalog = read(`data/expansion/municipalities/${id}.json`);
  const registry = { municipalities: [{ id, tariff_id: id, active: true, name: catalog.name }] };
  const profile = structuredClone(bundle.profiles.default);
  profile.children[0].age_months = 48;
  profile.weekday_minutes = Array(5).fill(360);
  assert.equal(compareMunicipalities([catalog], profile, registry)[0].monthly_equivalent_cents, null);
  profile.municipality_overrides = { [id]: { incomes: [
    { basis: "ostfildern_assessable_income", period: "year", amount_cents: 8000000 },
  ] } };
  const [result] = compareMunicipalities([catalog], profile, registry);
  assert.equal(result.monthly_equivalent_cents, 16600);
  assert.equal(result.booked_weekly_minutes, 1800);
  const model = { ...base(), children: [child("kindergarten", 360)] };
  assert.equal(compare(model, [catalog], registry)[0].monthly_equivalent_cents, 16600);
  assert.notEqual(compare({ ...model, income_id: "income-40000" }, [catalog], registry)[0].monthly_equivalent_cents, 16600);
});

test("Waldenbuch selects the 39-hour Friday package and a missing price preserves the known hours", () => {
  for (const [id, entry, expectedHours, expectedPrice] of [
    ["waldenbuch", child("nursery"), 39, 66600],
    ["waldenbuch", child("kindergarten"), 39, 37000],
    ["renningen", child("kindergarten"), 40, null],
  ]) {
    const tariff = read(`data/expansion/municipalities/${id}.json`);
    const registry = { municipalities: [{ id, tariff_id: id, active: true, name: tariff.name }] };
    const [family] = compareModelFamily([tariff], bundle.profiles.default, { ...base(), children: [entry] },
      registry, models, fridayRule);
    assert.equal(family.booked_weekly_minutes, expectedHours * 60, id);
    assert.equal(family.monthly_equivalent_cents, expectedPrice, id);
  }
});
