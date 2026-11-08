import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { compareMunicipalities, passRequirements } from "../../build/domain/index.js";
import { buildPersonalProfile, createPersonalDraft, emptyLocal, parseEuro, parseHours, personalResults, selectTargetChild } from "../../build/site/personal-profile.js";

const bundle = JSON.parse(readFileSync(new URL("../public/data/region-stuttgart.json", import.meta.url), "utf8"));
const reference = bundle.profiles.default;
const build = draft => buildPersonalProfile(reference, draft, bundle.tariffs, bundle.registry);
const evaluate = draft => personalResults(reference, draft, bundle.tariffs, bundle.registry);
const city = (result, id) => result.results.find(item => item.municipality_id === id);
function confirmedDraft() {
  const draft = createPersonalDraft(reference);
  draft.careRank = "1";
  draft.incomes = { gross_income: "80.000", taxable_income: "60.000", esslingen_gross_income: "80.000", adjusted_taxable_income: "60.000" };
  return draft;
}

test("German euro input preserves zero, cents and missing values without floating point rounding", () => {
  assert.equal(parseEuro(""), null);
  assert.equal(parseEuro(" 0 "), 0);
  assert.equal(parseEuro("80.000,01"), 8000001);
  assert.equal(parseEuro("80000,1"), 8000010);
  assert.equal(parseEuro("90071992547409,91"), Number.MAX_SAFE_INTEGER);
  for (const value of ["80,000.00", "1.00", "1e5", "-1", "1,001", "NaN", "90071992547409,92"]) assert.throws(() => parseEuro(value));
});

test("Daily input preserves weekday precision and rejects fractional minutes and oversized days", () => {
  assert.equal(parseHours("7,5"), 450);
  assert.equal(parseHours("8.25"), 495);
  assert.equal(parseHours(""), 0);
  assert.equal(parseHours("24"), 1440);
  for (const value of ["7,01", "-1", "24,5", "abc", "1e1"]) assert.throws(() => parseHours(value));
});

test("Entering personal mode never imports model incomes, local benefits, rank or financial assumptions", () => {
  const input = structuredClone(reference);
  input.municipality_overrides = { ditzingen: { incomes: reference.incomes, approved_rules: ["family_pass"], eligibility: ["family_pass"] } };
  input.pass_id = "family_card";
  input.eligibility = ["valid_family_card"];
  const draft = createPersonalDraft(input);
  const { profile } = build(draft);
  assert.deepEqual(profile.incomes, []);
  assert.deepEqual(profile.municipality_overrides, {});
  assert.equal(profile.care_rank, null);
  assert.equal(profile.pass_id, "none");
  assert.deepEqual(profile.eligibility, []);
  assert.equal(profile.model_income_snapshot, undefined);
  assert.equal(profile.assumptions, undefined);
  assert.deepEqual(input.municipality_overrides.ditzingen.incomes, reference.incomes);
});

test("Missing personal incomes leave flat tariffs usable and income-dependent cities unavailable", () => {
  const results = evaluate(createPersonalDraft(reference));
  assert.equal(city(results, "stuttgart").monthly_equivalent_cents, 22275);
  assert.equal(city(results, "gerlingen").monthly_equivalent_cents, 64000);
  for (const id of ["ditzingen", "esslingen", "korntal-muenchingen", "sindelfingen"]) assert.equal(city(results, id).monthly_equivalent_cents, null, id);
});

test("Explicit independent personal definitions reproduce all twelve reviewed model fees", () => {
  const actual = evaluate(confirmedDraft()).results;
  const expected = compareMunicipalities(bundle.tariffs, reference, bundle.registry);
  assert.equal(actual.length, 12);
  for (const row of actual) {
    const comparison = expected.find(item => item.municipality_id === row.municipality_id);
    assert.equal(row.monthly_equivalent_cents, comparison.monthly_equivalent_cents, row.municipality_id);
    assert.equal(row.offer_id, comparison.offer_id, row.municipality_id);
    assert.deepEqual(row.evidence, comparison.evidence, row.municipality_id);
  }
});

test("A changed gross amount cannot fill separate statutory income definitions", () => {
  const draft = createPersonalDraft(reference);
  draft.incomes.gross_income = "80.000";
  const results = evaluate(draft);
  for (const id of ["ditzingen", "esslingen", "korntal-muenchingen"]) assert.equal(city(results, id).monthly_equivalent_cents, null);
  draft.incomes.taxable_income = "60.000";
  assert.equal(city(evaluate(draft), "ditzingen").monthly_equivalent_cents, 57800);
  assert.equal(city(evaluate(draft), "esslingen").monthly_equivalent_cents, null);
});

test("Malformed or incomplete edits remove every previous amount, offer, component and trace", () => {
  for (const edit of [draft => { draft.incomes.taxable_income = "60x"; }, draft => { draft.children[0].years = ""; },
    draft => { draft.hours[4] = "7,01"; }, draft => { draft.hours.fill("0"); }, draft => { draft.careRank = "0"; }]) {
    const draft = confirmedDraft(); edit(draft);
    const result = evaluate(draft);
    assert.equal(result.profile, null);
    assert.ok(Object.keys(result.errors).length);
    for (const row of result.results) {
      assert.equal(row.monthly_equivalent_cents, null);
      assert.equal(row.offer_id, null);
      assert.deepEqual(row.components, []);
      assert.deepEqual(row.calculation, []);
      assert.deepEqual(row.reasons, ["invalid_profile_input"]);
    }
  }
});

test("Care rank is independent of sibling count and each weekday constrains the selected package", () => {
  const draft = confirmedDraft();
  draft.children.push({ years: "19", months: "0", resident: true, childBenefit: false, birthdayMonth: "unknown" });
  assert.equal(city(evaluate(draft), "sindelfingen").monthly_equivalent_cents, 33180);
  draft.hours[4] = "7";
  assert.equal(city(evaluate(draft), "fellbach").booked_weekly_minutes, 2700);
  draft.hours[3] = "7";
  const result = city(evaluate(draft), "fellbach");
  assert.equal(result.booked_weekly_minutes, 2400);
  assert.equal(result.monthly_equivalent_cents, 62400);
});

test("Exactly three years requires an explicit birthday month only in affected municipalities", () => {
  const draft = confirmedDraft(); draft.children[0].years = "3";
  let results = evaluate(draft);
  assert.ok(city(results, "fellbach").reasons.includes("birthday_month_required_for_age_transition"));
  assert.equal(city(results, "stuttgart").status, "comparable");
  draft.children[0].birthdayMonth = "yes";
  results = evaluate(draft);
  assert.equal(city(results, "fellbach").monthly_equivalent_cents, 70200);
  draft.children[0].birthdayMonth = "no";
  assert.notEqual(city(evaluate(draft), "fellbach").monthly_equivalent_cents, 70200);
});

test("Local passes require explicit eligibility and never affect neighboring municipalities", () => {
  const draft = confirmedDraft();
  draft.local.stuttgart = { ...emptyLocal(), passId: "family_card" };
  assert.ok(city(evaluate(draft), "stuttgart").reasons.includes("pass_eligibility_not_confirmed"));
  draft.local.stuttgart.eligibility = passRequirements(bundle.tariffs.find(item => item.id === "stuttgart"), "family_card");
  const results = evaluate(draft);
  assert.equal(city(results, "stuttgart").status, "comparable");
  assert.ok(city(results, "stuttgart").monthly_equivalent_cents < 22275);
  assert.equal(city(results, "ditzingen").monthly_equivalent_cents, 57800);
});

test("Local discount income preserves all global bases and remains inactive without confirmation", () => {
  const draft = confirmedDraft();
  draft.local.fellbach = { ...emptyLocal(), rules: ["social_income_ratio"], incomes: { fellbach_gross_income: "485" } };
  assert.ok(city(evaluate(draft), "fellbach").reasons.includes("eligibility_not_confirmed"));
  draft.local.fellbach.eligibility = ["approved_social_reduction", "resident", "no_priority_benefit"];
  assert.equal(city(evaluate(draft), "fellbach").monthly_equivalent_cents, 5900);
  const profile = build(draft).profile;
  assert.equal(profile.municipality_overrides.fellbach.incomes.length, 5);
  assert.equal(city(evaluate(draft), "esslingen").monthly_equivalent_cents, 55100);
  draft.local.fellbach.incomes.fellbach_gross_income = "";
  assert.ok(city(evaluate(draft), "fellbach").reasons.includes("income_definition_missing"));
});

test("School entry and household membership are respected without modifying the reference profile", () => {
  const before = JSON.stringify(reference);
  const draft = confirmedDraft(); draft.schoolEntry = true;
  assert.ok(evaluate(draft).results.every(item => item.monthly_equivalent_cents === null));
  draft.schoolEntry = false; draft.children[0].resident = false;
  assert.ok(evaluate(draft).results.every(item => item.reasons.includes("target_outside_scope")));
  assert.equal(JSON.stringify(reference), before);
});

test("Selecting another child requires its own care rank and school entry confirmation", () => {
  const draft = confirmedDraft(); draft.schoolEntry = true;
  draft.children.push({ years: "1", months: "6", resident: true, childBenefit: true, birthdayMonth: "unknown" });
  const selected = selectTargetChild(draft, 1);
  assert.equal(selected.careRank, "");
  assert.equal(selected.schoolEntry, false);
  assert.equal(selected.targetChild, 1);
  assert.equal(draft.careRank, "1");
  assert.equal(city(evaluate(selected), "sindelfingen").monthly_equivalent_cents, null);
});
