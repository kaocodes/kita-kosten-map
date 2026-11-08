import { compareMunicipalities, createPersonalProfile, normalizeProfile } from "../domain/index.js";
import type { ComparisonResult, Income, MunicipalityCatalog, Profile, Registry } from "../domain/index.js";

export interface ChildDraft {
  years: string; months: string; resident: boolean; childBenefit: boolean;
  birthdayMonth: "unknown" | "yes" | "no";
}
export interface LocalDraft {
  passId: string; rules: string[]; eligibility: string[]; incomes: Record<string, string>;
}
export interface PersonalDraft {
  children: ChildDraft[]; targetChild: number; household: "together" | "single" | "separate";
  schoolEntry: boolean; careRank: string; hours: string[]; incomes: Record<string, string>;
  local: Record<string, LocalDraft>;
}
export interface IncomeField { basis: string; period: "year" | "month"; label: string; help: string }
export const INCOME_FIELDS: IncomeField[] = [
  { basis: "taxable_income", period: "year", label: "Ditzingen: örtliches maßgebliches Jahreseinkommen", help: "Vorjahr des Tarifstichtags, Definition nach § 7: positive Einkünfte einschließlich der genannten Ersatz- und Sozialleistungen. Steuerbescheidwert nicht ungeprüft übernehmen." },
  { basis: "esslingen_gross_income", period: "year", label: "Esslingen: jährliches Familienbrutto nach örtlicher Definition", help: "Laufendes Kalenderjahr des Tarifstichtags, ohne Kindergeld. Einen zulässigen Arbeitnehmer-Pauschbetrag nur nach eigener Prüfung abziehen." },
  { basis: "adjusted_taxable_income", period: "year", label: "Korntal-Münchingen: bereinigtes steuerliches Jahreseinkommen", help: "Vorjahr des Tarifstichtags: zu versteuerndes Einkommen zuzüglich Verlusten aus Vermietung und Verpachtung." },
  { basis: "gross_income", period: "year", label: "Haushaltsbrutto pro Jahr", help: "Für die freiwillige Sozialermäßigung in Kornwestheim. Ersetzt keine der anderen Einkommensdefinitionen." },
];

/** Parse German euro amounts exactly; empty input is distinct from zero. */
export function parseEuro(value: string): number | null {
  const input = value.trim();
  if (!input) return null;
  if (input.length > 30 || !/^(?:\d+|[1-9]\d{0,2}(?:\.\d{3})+)(?:,\d{1,2})?$/.test(input)) throw new Error("Invalid euro amount");
  const [whole, fraction = ""] = input.replaceAll(".", "").split(",");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  if (cents > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Amount exceeds safe integer range");
  return Number(cents);
}

export function parseHours(value: string): number {
  const input = value.trim() || "0";
  if (!/^\d{1,2}(?:[,.]\d{1,2})?$/.test(input)) throw new Error("Invalid hours");
  const [whole, fraction = ""] = input.replace(",", ".").split(".");
  const hundredths = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  const minutes = hundredths * 60 / 100;
  if (!Number.isInteger(minutes) || minutes > 1440) throw new Error("Hours require whole minutes within a day");
  return minutes;
}

export function newChild(): ChildDraft {
  return { years: "2", months: "0", resident: true, childBenefit: true, birthdayMonth: "unknown" };
}

export function createPersonalDraft(reference: Profile): PersonalDraft {
  const profile = createPersonalProfile(reference);
  return {
    children: profile.children.map(child => ({ years: String(Math.floor(child.age_months / 12)), months: String(child.age_months % 12),
      resident: child.resident, childBenefit: child.child_benefit, birthdayMonth: "unknown" })),
    targetChild: profile.target_child, household: profile.single_parent ? "single" : "together",
    schoolEntry: profile.school_entry ?? false, careRank: "", hours: profile.weekday_minutes.map(value => String(value / 60).replace(".", ",")),
    incomes: {}, local: {},
  };
}

export function emptyLocal(): LocalDraft { return { passId: "none", rules: [], eligibility: [], incomes: {} }; }

export function selectTargetChild(draft: PersonalDraft, targetChild: number): PersonalDraft {
  return { ...draft, targetChild, careRank: "", schoolEntry: false };
}

export function localIncomeFields(city: MunicipalityCatalog, rules: string[]): IncomeField[] {
  const fields = new Map<string, IncomeField>();
  for (const rule of city.rules.filter(rule => rules.includes(rule.id))) {
    const params = rule.parameters;
    if (!params?.income_basis || INCOME_FIELDS.some(field => field.basis === params.income_basis)) continue;
    const basis = params.income_basis;
    fields.set(basis, { basis, period: params.income_period!, label: basis === "fellbach_gross_income"
      ? "Fellbach: örtliches Familienbrutto pro Monat" : "Gerlingen: örtliches Haushaltseinkommen pro Jahr",
    help: "Nur nach der örtlichen Gebührenordnung ermitteltes Einkommen eintragen. Es wird nicht aus anderen Einkommensangaben übernommen." });
  }
  return [...fields.values()];
}

export function buildPersonalProfile(reference: Profile, draft: PersonalDraft, tariffs: MunicipalityCatalog[], registry: Registry): {
  profile: Profile | null; errors: Record<string, string>;
} {
  const errors: Record<string, string> = {};
  const profile = createPersonalProfile(reference);
  profile.pass_id = "none"; profile.approved_rules = []; profile.eligibility = [];
  function integer(value: string, key: string, maximum: number): number {
    if (!/^\d{1,3}$/.test(value) || Number(value) > maximum) { errors[key] = `Bitte eine ganze Zahl zwischen 0 und ${maximum} eingeben.`; return 0; }
    return Number(value);
  }
  profile.children = draft.children.map((child, index) => ({
    age_months: integer(child.years, `child-${index}-years`, 99) * 12 + integer(child.months, `child-${index}-months`, 11),
    resident: child.resident, child_benefit: child.childBenefit,
    ...(child.birthdayMonth === "unknown" ? {} : { birthday_in_reference_month: child.birthdayMonth === "yes" }),
  }));
  profile.target_child = draft.targetChild; profile.school_entry = draft.schoolEntry;
  profile.single_parent = draft.household === "single";
  profile.household = { parent_count: draft.household === "together" ? 2 : 1, parents_living_together: draft.household === "together" };
  profile.care_rank = draft.careRank === "" ? null : integer(draft.careRank, "care-rank", 99);
  if (profile.care_rank === 0) errors["care-rank"] = "Der Betreuungsrang beginnt bei 1.";
  profile.weekday_minutes = draft.hours.map((value, index) => {
    try { return parseHours(value); } catch { errors[`hours-${index}`] = "Bitte 0 bis 24 Stunden mit ganzen Minuten eingeben, z. B. 7,5."; return 0; }
  });
  if (!profile.weekday_minutes.some(Boolean)) errors["hours-0"] = "Bitte für mindestens einen Wochentag einen Betreuungsbedarf angeben.";
  function incomes(fields: IncomeField[], values: Record<string, string>, prefix: string): Income[] {
    return fields.flatMap(field => {
      try {
        const value = parseEuro(values[field.basis] ?? "");
        return value === null ? [] : [{ basis: field.basis, period: field.period, amount_cents: value }];
      } catch { errors[prefix + field.basis] = "Bitte einen Eurobetrag eingeben, z. B. 80.000,00. Leer bedeutet unbekannt."; return []; }
    });
  }
  profile.incomes = incomes(INCOME_FIELDS, draft.incomes, "income-");
  profile.municipality_overrides = {};
  for (const municipality of registry.municipalities.filter(item => item.active)) {
    const local = draft.local[municipality.id];
    const city = tariffs.find(item => item.id === municipality.tariff_id);
    if (!local || !city) continue;
    const additional = incomes(localIncomeFields(city, local.rules), local.incomes, `local-${municipality.id}-`);
    profile.municipality_overrides[municipality.id] = { pass_id: local.passId, approved_rules: [...local.rules], eligibility: [...local.eligibility],
      // Local income lists replace the global list in the engine, so preserve every confirmed basis.
      incomes: [...profile.incomes, ...additional] };
  }
  if (Object.keys(errors).length) return { profile: null, errors };
  try { return { profile: normalizeProfile(profile), errors }; }
  catch { return { profile: null, errors: { ...errors, family: "Bitte die Familienangaben vollständig und widerspruchsfrei eingeben." } }; }
}

/** Invalid drafts must remove previous prices from every comparison surface. */
export function personalResults(reference: Profile, draft: PersonalDraft, tariffs: MunicipalityCatalog[], registry: Registry) {
  const built = buildPersonalProfile(reference, draft, tariffs, registry);
  const results: ComparisonResult[] = built.profile ? compareMunicipalities(tariffs, built.profile, registry)
    : registry.municipalities.filter(item => item.active).map(item => ({
      municipality_id: item.id, municipality: item.name, tariff_id: item.tariff_id, ags: item.ags, area_id: item.area_id,
      profile_id: "personal", as_of: reference.as_of, reviewed_at: tariffs.find(city => city.id === item.tariff_id)!.reviewed_at,
      status: "unavailable", reasons: ["invalid_profile_input"], monthly_care_cents: null, annual_care_cents: null,
      monthly_equivalent_cents: null, offer_id: null, offer_label: null, booked_weekly_minutes: null,
      extra_weekly_minutes: null, payment_months: null, components: [], calculation: [], evidence: [], issues: [], alternatives: [],
    }));
  return { ...built, results };
}
