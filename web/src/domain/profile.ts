import { z } from "zod";
import type { Profile } from "./types.js";

const integer = z.number().int().nonnegative();
const pass = z.enum(["none", "family_card", "city_pass", "social_card", "city_pass_a", "city_pass_b", "city_pass_c"]);
const income = z.looseObject({
  basis: z.string().min(1),
  period: z.enum(["year", "month"]),
  amount_cents: integer,
});
const incomeMode = z.enum(["highest_band", "specified"]);
const localInputs = z.strictObject({
  incomes: z.array(income).optional(),
  income_mode: incomeMode.optional(),
  pass_id: pass.optional(),
  approved_rules: z.array(z.string()).optional(),
  eligibility: z.array(z.string()).optional(),
  care_rank: integer.min(1).nullable().optional(),
});

function isISODate(value: string): boolean {
  if (!/^(?!0000)\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const timestamp = Date.parse(value + "T00:00:00Z");
  return Number.isFinite(timestamp) && new Date(timestamp).toISOString().slice(0, 10) === value;
}

const profileSchema = z.looseObject({
  id: z.string().optional(),
  label: z.string().optional(),
  as_of: z.string().refine(isISODate, "The reference date must use YYYY-MM-DD."),
  children: z.array(z.looseObject({
    age_months: integer,
    resident: z.boolean(),
    child_benefit: z.boolean(),
    birthday_in_reference_month: z.boolean().optional(),
  })).min(1),
  target_child: integer,
  weekday_minutes: z.array(integer.max(1440)).length(5),
  income_mode: incomeMode,
  incomes: z.array(income).default([]),
  care_rank: integer.min(1).nullable().optional(),
  pass_id: pass,
  approved_rules: z.array(z.string()).default([]),
  eligibility: z.array(z.string()).default([]),
  single_parent: z.boolean(),
  scope: z.string(),
  metric: z.string().optional(),
  school_entry: z.boolean().optional(),
  meal_days_per_week: integer.max(5).optional(),
  allow_published_future: z.boolean().optional(),
  municipality_overrides: z.record(z.string().min(1), localInputs).optional(),
  household: z.looseObject({ parent_count: integer.min(1), parents_living_together: z.boolean() }).optional(),
  assumptions: z.record(z.string(), z.unknown()).optional(),
  model_income_snapshot: z.looseObject({
    incomes: z.array(income), assumptions: z.record(z.string(), z.unknown()),
  }).nullable().optional(),
});

export class ProfileValidationError extends Error {
  readonly code = "invalid_profile";
  constructor(message: string) {
    super(message);
    this.name = "ProfileValidationError";
  }
}

function canonicalJSON(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonicalJSON).join(",") + "]";
  if (typeof value === "object" && value !== null) {
    const record = value as Record<string, unknown>;
    return "{" + Object.keys(record).sort().map(key => JSON.stringify(key) + ":" + canonicalJSON(record[key])).join(",") + "}";
  }
  return JSON.stringify(value);
}

function validateIncomeDefinitions(incomes: Profile["incomes"]): void {
  const seen = new Map<string, Map<string, number>>();
  for (const entry of incomes ?? []) {
    const periods = seen.get(entry.basis) ?? new Map<string, number>();
    if (periods.has(entry.period)) throw new ProfileValidationError("Income definitions must be unique and have an explicit period.");
    periods.set(entry.period, entry.amount_cents);
    seen.set(entry.basis, periods);
  }
  for (const periods of seen.values()) {
    if (periods.has("month") && periods.has("year") &&
        BigInt(periods.get("month")!) * 12n !== BigInt(periods.get("year")!)) {
      throw new ProfileValidationError("Monthly and annual values for the same income definition disagree.");
    }
  }
}

/** Normalize JSON input without coercing strings, estimating taxes or confirming eligibility. */
export function normalizeProfile(input: unknown): Profile {
  const parsed = profileSchema.safeParse(input);
  if (!parsed.success) {
    throw new ProfileValidationError(parsed.error.issues.map(issue => `${issue.path.join(".")}: ${issue.message}`).join("; "));
  }
  const profile: Profile = parsed.data;
  if (profile.target_child >= profile.children.length) throw new ProfileValidationError("A valid target child is required.");
  if (!profile.weekday_minutes.some(value => value > 0)) throw new ProfileValidationError("Five daily durations in integer minutes are required.");
  validateIncomeDefinitions(profile.incomes);
  for (const local of Object.values(profile.municipality_overrides ?? {})) validateIncomeDefinitions(local.incomes);
  if (profile.model_income_snapshot != null && canonicalJSON(profile.model_income_snapshot) !==
      canonicalJSON({ incomes: profile.incomes ?? [], assumptions: profile.assumptions ?? {} })) {
    throw new ProfileValidationError("Model income assumptions have changed. Use a personal profile with independently confirmed income definitions.");
  }
  const household = profile.household;
  if (household?.parents_living_together && (household.parent_count < 2 || profile.single_parent)) {
    throw new ProfileValidationError("Cohabiting parents conflict with the stated household composition.");
  }
  // Unknown source metadata is retained, but callers never share mutable state with the calculator.
  return structuredClone(profile);
}

/** Keep family and schedule choices while requiring new, explicit personal income inputs. */
export function createPersonalProfile(input: unknown): Profile {
  const profile = normalizeProfile(input);
  profile.id = "personal";
  delete profile.label;
  profile.income_mode = "specified";
  profile.incomes = [];
  delete profile.model_income_snapshot;
  delete profile.assumptions;
  delete profile.income_assumption_evidence;
  delete profile.municipality_overrides;
  return profile;
}
