import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { compareModelFamily } from "../../build/domain/model-family.js";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url), "utf8"));
const bundle = read("web/public/data/region-stuttgart.json");
const selection = read("data/expansion/activation.json");
const selected = new Set(selection.municipality_ids);
const review = read(selection.review_path);
const compare = model => compareModelFamily(bundle.tariffs, bundle.profiles.default, model, bundle.registry, bundle.models);

test("Only the eight fully supported expansion municipalities join the original twelve", () => {
  const original = Object.keys(read("data/reviews/model_family_review.json").expected);
  const active = bundle.registry.municipalities.filter(item => item.active).map(item => item.id);
  assert.deepEqual([...active].sort(), [...original, ...selected].sort());
  assert.equal(bundle.tariffs.length, 20);
  for (const id of selected) {
    assert.equal(review.municipalities.find(item => item.id === id).status, "supported_for_reviewed_care_models");
  }
});

test("Projected expansion catalogs preserve independently sourced single and sibling fees", () => {
  const cases = read("data/reviews/expansion_calculation_cases.json").cases;
  for (const reference of cases.filter(item => selected.has(item.municipality_id))) {
    const [household, income_id, ...children] = reference.scenario_id.split("|");
    const model = { household, income_id, children: children.map(child => {
      const [category, minutes] = child.split(":");
      return { category, daily_minutes: Number(minutes) };
    }) };
    const result = compare(model).find(item => item.municipality_id === reference.municipality_id);
    for (const [key, expected] of Object.entries(reference.expected)) assert.equal(result[key], expected, `${reference.id}: ${key}`);
    assert.ok(result.evidence.some(item => item.source_id === reference.evidence.source_id), reference.id);
    for (const evidence of result.evidence) assert.ok(bundle.sources[evidence.source_id], evidence.source_id);
  }
});

test("New cities support both households, all incomes and a four-child mixed-care configuration", () => {
  for (const household of ["couple", "single"]) for (const income of bundle.models.income_scenarios) {
    const results = compare({ household, income_id: income.id, children: [
      { category: "nursery", daily_minutes: 480 }, { category: "kindergarten", daily_minutes: 360 },
      { category: "school", daily_minutes: 480 }, { category: "home", daily_minutes: 480 },
    ] });
    for (const row of results.filter(item => selected.has(item.municipality_id))) {
      assert.equal(row.status, "comparable", row.municipality_id);
      assert.equal(row.care_child_count, 2);
      assert.equal(row.children[2].result, null);
      assert.equal(row.children[3].result, null);
    }
  }
});

test("Browser data omit archival rule parameters while retaining explicit unsupported-rule status", () => {
  for (const tariff of bundle.tariffs.filter(item => selected.has(item.id))) {
    assert.equal(tariff.coverage, undefined);
    for (const rule of tariff.rules.filter(item => item.execution_status !== "supported")) {
      assert.equal(rule.parameters, undefined);
      assert.ok(rule.id);
      assert.ok(bundle.sources[rule.evidence.source_id]);
    }
  }
});
