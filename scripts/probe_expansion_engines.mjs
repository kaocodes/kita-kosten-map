/** Exercise the unchanged browser engines against isolated import catalogs. */
import { readFileSync, writeFileSync, mkdirSync, openSync, writeSync, closeSync } from "node:fs";
import { createHash } from "node:crypto";
import { compareModelFamily, modelProfile, validateModelCatalog } from "../build/domain/model-family.js";
import { evaluateCity } from "../build/domain/index.js";

const read = path => JSON.parse(readFileSync(new URL("../" + path, import.meta.url), "utf8"));
const destination = new URL("../build/expansion-review/", import.meta.url);
mkdirSync(destination, { recursive: true });
const models = validateModelCatalog(read("data/models/configuration.json"));
const reference = read("data/profiles/default.json");
const manifest = read("data/expansion/manifest.json");
reference.as_of = manifest.normalized_at;
const limitMatch = readFileSync(new URL("../web/src/site/features.ts", import.meta.url), "utf8").match(/MODEL_UI_MAX_CHILDREN\s*=\s*(\d+)/);
if (!limitMatch) throw new Error("Cannot locate the current model UI limit");
const maxChildren = Math.min(models.max_children, Number(limitMatch[1]));
const states = models.categories.flatMap(category => category.care_enabled
  ? models.care_options.map(option => ({ category: category.id, daily_minutes: option.minutes }))
  : [{ category: category.id, daily_minutes: 480 }]);
const combinations = [];
function appendCombinations(prefix, start) {
  if (prefix.length) combinations.push(prefix);
  if (prefix.length === maxChildren) return;
  for (let index = start; index < states.length; index++) appendCombinations([...prefix, states[index]], index);
}
appendCombinations([], 0);
const cases = [];
for (const household of ["couple", "single"]) for (const income of models.income_scenarios) for (const children of combinations) {
  const selection = { household, income_id: income.id, children };
  cases.push({ index: cases.length, id: [household, income.id, ...children.map(child => `${child.category}:${child.daily_minutes}`)].join("|"),
    selection, profile: modelProfile(reference, selection, models) });
}
writeFileSync(new URL("cases.json", destination), JSON.stringify({ max_children: maxChildren, cases }));

const primitiveProfiles = [];
for (const household of ["couple", "single"]) for (const income of models.income_scenarios) {
  for (let count = 1; count <= maxChildren; count++) for (const category of ["nursery", "kindergarten"]) for (const option of models.care_options) {
    const selection = { household, income_id: income.id, children: [
      { category, daily_minutes: option.minutes },
      ...Array.from({ length: count - 1 }, () => ({ category: "home", daily_minutes: 480 })),
    ] };
    const base = modelProfile(reference, selection, models);
    for (let rank = 1; rank <= count; rank++) primitiveProfiles.push({ ...base, target_child: 0,
      weekday_minutes: Array(5).fill(option.minutes), care_rank: rank, school_entry: false });
  }
}
writeFileSync(new URL("primitive-profiles.json", destination), JSON.stringify(primitiveProfiles));

export function compactResult(row) {
  return Object.fromEntries(["status", "reasons", "monthly_care_cents", "annual_care_cents", "monthly_equivalent_cents", "offer_id", "offer_label",
    "selected_price_id", "booked_weekly_minutes", "extra_weekly_minutes", "payment_months", "care_rank"].map(key => [key, row[key] ?? null]).concat([
    ["components", (row.components ?? []).map(part => Object.fromEntries(["id", "kind", "amount_cents", "unit", "required", "payment_months", "value_status", "annual_equivalent_cents"].map(key => [key, part[key] ?? null])))],
  ]));
}
const familyFile = openSync(new URL("family-probes.jsonl", destination), "w");
const primitiveFile = openSync(new URL("primitive-probes.jsonl", destination), "w");
let reversalChecks = 0;
const mismatches = [];
function familyKey(row) {
  return JSON.stringify([row.status, [...row.reasons].sort(), row.annual_care_cents, row.monthly_equivalent_cents, row.monthly_care_cents, row.care_child_count]);
}
for (const entry of manifest.municipalities) {
  const city = read(entry.path);
  const registry = { schema_version: "1.0", municipalities: [{ id: city.id, name: city.name, ags: entry.ags,
    active: true, region_id: "stuttgart-region", tariff_id: city.id, area_id: "municipality-" + entry.ags }] };
  for (const testCase of cases) {
    let result;
    try {
      const row = compareModelFamily([city], reference, testCase.selection, registry, models)[0];
      result = { ...compactResult(row), care_child_count: row.care_child_count,
        children: row.children.map(child => ({ index: child.index, category: child.category, daily_minutes: child.daily_minutes,
          in_care: child.in_care, result: child.result ? compactResult(child.result) : null })) };
      if (testCase.selection.children.length > 1) {
        const reversed = compareModelFamily([city], reference, { ...testCase.selection, children: [...testCase.selection.children].reverse() }, registry, models)[0];
        reversalChecks++;
        if (familyKey(row) !== familyKey(reversed)) mismatches.push({ municipality_id: city.id, case_index: testCase.index });
      }
    } catch (error) {
      result = { engine_error: error.name, message: error.message };
    }
    writeSync(familyFile, JSON.stringify({ municipality_id: city.id, case_index: testCase.index, result }) + "\n");
  }
  for (const [index, profile] of primitiveProfiles.entries()) {
    let result;
    try { result = compactResult(evaluateCity(city, profile)); }
    catch (error) { result = { engine_error: error.name, message: error.message }; }
    writeSync(primitiveFile, JSON.stringify({ municipality_id: city.id, profile_index: index, result }) + "\n");
  }
  process.stdout.write(`Probed ${city.name}: ${cases.length} family configurations.\n`);
}
closeSync(familyFile);
closeSync(primitiveFile);
const summary = { as_of: reference.as_of, municipalities: manifest.municipalities.length, max_children: maxChildren,
  configurations_per_municipality: cases.length, family_probes: cases.length * manifest.municipalities.length,
  primitive_profiles: primitiveProfiles.length, primitive_probes: primitiveProfiles.length * manifest.municipalities.length,
  order_reversal_checks: reversalChecks, order_reversal_mismatches: mismatches,
  family_probe_sha256: createHash("sha256").update(readFileSync(new URL("family-probes.jsonl", destination))).digest("hex") };
writeFileSync(new URL("probe-summary.json", destination), JSON.stringify(summary, null, 2) + "\n");
if (mismatches.length) throw new Error("Family sums depend on child input order; inspect the probe summary");
