import { z } from "zod";
import { compareMunicipalities, normalizeProfile } from "./index.js";
import { Fraction, roundMoney } from "./money.js";
import type { ComparisonResult, Income, MunicipalityCatalog, Profile, Registry } from "./types.js";

const category = z.enum(["nursery", "kindergarten", "school", "home"]);
const childSchema = z.strictObject({ category, daily_minutes: z.union([z.literal(360), z.literal(480)]) });
const selectionSchema = z.strictObject({ household: z.enum(["couple", "single"]), income_id: z.string(), children: z.array(childSchema).min(1).max(12) });
export type ModelSelection = z.infer<typeof selectionSchema>;
export type ModelCategory = z.infer<typeof category>;
export interface ModelCatalog {
  schema_version: string; default: ModelSelection; max_children: number;
  categories: { id: ModelCategory; label: string; description: string; age_months: number; care_enabled: boolean }[];
  care_options: { minutes: number; label: string }[];
  income_scenarios: { id: string; gross_annual_cents: number; incomes: Income[]; assumption: string }[];
  assumptions: string[];
}
export interface FamilyChildResult {
  index: number; category: ModelCategory; daily_minutes: number; in_care: boolean;
  result: ComparisonResult | null;
  possible_monthly_cents?: [number, number];
}
export interface FamilyResult extends ComparisonResult {
  children: FamilyChildResult[]; care_child_count: number;
}

export function validateModelCatalog(input: unknown): ModelCatalog {
  const parsed = z.object({ schema_version: z.literal("1.0"), default: selectionSchema, max_children: z.number().int().min(1).max(12),
    categories: z.array(z.object({ id: category, label: z.string().min(1), description: z.string(), age_months: z.number().int().nonnegative(), care_enabled: z.boolean() })).length(4),
    care_options: z.array(z.object({ minutes: z.union([z.literal(360), z.literal(480)]), label: z.string() })).length(2),
    income_scenarios: z.array(z.object({ id: z.string(), gross_annual_cents: z.number().int().nonnegative(), assumption: z.string(),
      incomes: z.array(z.object({ basis: z.string(), period: z.enum(["year", "month"]), amount_cents: z.number().int().nonnegative() })) })).length(6),
    assumptions: z.array(z.string()),
  }).parse(input);
  if (new Set(parsed.categories.map(item => item.id)).size !== 4 || new Set(parsed.care_options.map(item => item.minutes)).size !== 2 ||
      new Set(parsed.income_scenarios.map(item => item.id)).size !== 6 || new Set(parsed.income_scenarios.map(item => item.gross_annual_cents)).size !== 6) throw new Error("Duplicate model definitions");
  normalizeSelection(parsed.default, parsed);
  const required = ["gross_income", "taxable_income", "esslingen_gross_income", "adjusted_taxable_income"];
  for (const scenario of parsed.income_scenarios) {
    if (scenario.incomes.length !== required.length || required.some(basis => scenario.incomes.filter(item => item.basis === basis && item.period === "year").length !== 1) ||
        scenario.incomes.some(item => !Number.isSafeInteger(item.amount_cents)) ||
        scenario.incomes.find(item => item.basis === "gross_income")!.amount_cents !== scenario.gross_annual_cents) throw new Error("Incomplete model income definitions");
  }
  return structuredClone(parsed);
}

export function normalizeSelection(input: unknown, catalog: ModelCatalog): ModelSelection {
  const selection = selectionSchema.parse(input);
  if (!catalog.income_scenarios.some(item => item.id === selection.income_id) || selection.children.length > catalog.max_children) throw new Error("Unknown model scenario");
  return selection;
}

export function modelProfile(reference: Profile, selection: ModelSelection, catalog: ModelCatalog): Profile {
  const scenario = catalog.income_scenarios.find(item => item.id === selection.income_id)!;
  const profile = structuredClone(reference);
  profile.id = "configured-model-family"; delete profile.label;
  profile.children = selection.children.map(child => ({ age_months: catalog.categories.find(item => item.id === child.category)!.age_months, resident: true, child_benefit: true }));
  profile.incomes = structuredClone(scenario.incomes); profile.income_mode = "specified";
  profile.single_parent = selection.household === "single";
  profile.household = { parent_count: profile.single_parent ? 1 : 2, parents_living_together: !profile.single_parent };
  profile.pass_id = "none"; profile.approved_rules = []; profile.eligibility = [];
  delete profile.municipality_overrides;
  profile.assumptions = { ...profile.assumptions, income_scenario: scenario.id, income_values_are_model_assumptions: true };
  profile.model_income_snapshot = { incomes: structuredClone(profile.incomes), assumptions: structuredClone(profile.assumptions) };
  return normalizeProfile(profile);
}

function sum(values: number[]): number { return values.reduce((total, value) => total + value, 0); }

/** Minimum/maximum assignment cost, without inventing a local sibling-rank order. */
function assignmentRange(matrix: number[][]): [number, number] {
  const states = 1 << matrix.length;
  const min = Array<number>(states).fill(Infinity), max = Array<number>(states).fill(-Infinity);
  min[0] = max[0] = 0;
  for (let mask = 0; mask < states; mask++) {
    let child = 0; for (let bit = mask; bit; bit &= bit - 1) child++;
    for (let rank = 0; rank < matrix.length; rank++) if (!(mask & (1 << rank))) {
      const next = mask | (1 << rank), cost = matrix[child][rank];
      min[next] = Math.min(min[next], min[mask] + cost); max[next] = Math.max(max[next], max[mask] + cost);
    }
  }
  return [min[states - 1], max[states - 1]];
}

export function compareModelFamily(tariffs: MunicipalityCatalog[], reference: Profile, input: unknown, registry: Registry, catalog: ModelCatalog): FamilyResult[] {
  const selection = normalizeSelection(input, catalog);
  const profile = modelProfile(reference, selection, catalog);
  const activeChildren = selection.children.map((child, index) => ({ ...child, index }))
    .filter(child => catalog.categories.find(item => item.id === child.category)!.care_enabled);
  const evaluated = new Map<number, ComparisonResult[]>();
  for (const child of activeChildren) {
    evaluated.set(child.index, compareMunicipalities(tariffs, { ...profile, target_child: child.index,
      weekday_minutes: Array(5).fill(child.daily_minutes), care_rank: 1, school_entry: false }, registry));
  }
  return registry.municipalities.filter(item => item.active).map(municipality => {
    const tariff = tariffs.find(item => item.id === municipality.tariff_id)!;
    const children: FamilyChildResult[] = selection.children.map((child, index) => ({ ...child, index,
      in_care: evaluated.has(index), result: evaluated.get(index)?.find(row => row.municipality_id === municipality.id) ?? null }));
    const rows = children.filter(child => child.in_care).map(child => child.result!);
    let rankAmbiguous = false;
    if (rows.length > 1 && tariff.prices.some(row => row.selectors?.care_rank != null)) {
      const matrix = activeChildren.map(child => Array.from({ length: rows.length }, (_, rank) =>
        compareMunicipalities([tariff], { ...profile, target_child: child.index, weekday_minutes: Array(5).fill(child.daily_minutes),
          care_rank: rank + 1, school_entry: false }, registry, municipality.id)[0]));
      if (matrix.every(row => row.every(value => value.status === "comparable" && value.annual_care_cents !== null))) {
        const [low, high] = assignmentRange(matrix.map(row => row.map(value => value.annual_care_cents!)));
        rankAmbiguous = low !== high;
        activeChildren.forEach((child, index) => {
          const target = children[child.index]; target.result = matrix[index][index];
          const possible = matrix[index].map(row => row.monthly_equivalent_cents!);
          if (Math.min(...possible) !== Math.max(...possible)) target.possible_monthly_cents = [Math.min(...possible), Math.max(...possible)];
        });
      } else {
        rankAmbiguous = true;
        for (const child of children.filter(item => item.in_care)) child.result = { ...child.result!, status: "unavailable",
          monthly_care_cents: null, annual_care_cents: null, monthly_equivalent_cents: null, reasons: ["care_rank_allocation_unresolved"] };
      }
    }
    const careRows = children.filter(child => child.in_care).map(child => child.result!);
    const complete = !rankAmbiguous && careRows.every(row => row.status === "comparable" && row.annual_care_cents !== null);
    const annual = complete ? sum(careRows.map(row => row.annual_care_cents!)) : null;
    const evidence = careRows.flatMap(row => row.evidence);
    if (rankAmbiguous) evidence.push(...tariff.prices.filter(row => row.selectors?.care_rank != null).map(row => row.evidence));
    const first = careRows[0];
    return {
      municipality_id: municipality.id, municipality: municipality.name, ags: municipality.ags, area_id: municipality.area_id, tariff_id: municipality.tariff_id,
      profile_id: profile.id!, as_of: profile.as_of, reviewed_at: tariff.reviewed_at,
      status: complete ? "comparable" : rankAmbiguous || careRows.some(row => row.status === "ambiguous") ? "ambiguous" : "unavailable",
      reasons: rankAmbiguous ? ["care_rank_allocation_unresolved"] : [...new Set(careRows.flatMap(row => row.reasons))],
      annual_care_cents: annual, monthly_equivalent_cents: annual === null ? null : roundMoney(new Fraction(annual).divide(12)),
      monthly_care_cents: complete ? sum(careRows.map(row => row.monthly_care_cents!)) : null,
      payment_months: complete && first && careRows.every(row => row.payment_months === first.payment_months) ? first.payment_months : null,
      offer_id: careRows.length === 1 ? first.offer_id : null, offer_label: careRows.length === 1 ? first.offer_label : null,
      booked_weekly_minutes: complete ? sum(careRows.map(row => row.booked_weekly_minutes!)) : null,
      extra_weekly_minutes: complete ? sum(careRows.map(row => row.extra_weekly_minutes!)) : null,
      components: [], calculation: [{ operation: "family_annual_sum_divided_by_12", complete }],
      evidence: [...new Map(evidence.map(item => [item.source_id + ":" + item.locator, item])).values()],
      issues: tariff.issues, alternatives: [], children, care_child_count: careRows.length,
    };
  });
}
