import type { ComparisonResult } from "../domain/index.js";

export const FEE_BANDS = [
  { upper: 30000, color: "#6785c1", label: "bis 300 €" },
  { upper: 40000, color: "#9185cb", label: "> 300–400 €" },
  { upper: 50000, color: "#b08bca", label: "> 400–500 €" },
  { upper: 60000, color: "#dc987a", label: "> 500–600 €" },
  { upper: Infinity, color: "#ea742a", label: "> 600 €" },
];
export const MISSING_COLOR = "#cbd1dc";

/** Keep unknown fees after every known amount, including a documented zero. */
export function compareMonthlyFeesDescending(first: Pick<ComparisonResult, "monthly_equivalent_cents" | "municipality">,
  second: Pick<ComparisonResult, "monthly_equivalent_cents" | "municipality">): number {
  const firstAmount = first.monthly_equivalent_cents;
  const secondAmount = second.monthly_equivalent_cents;
  if (firstAmount === null && secondAmount !== null) return 1;
  if (secondAmount === null && firstAmount !== null) return -1;
  return (secondAmount ?? 0) - (firstAmount ?? 0) || first.municipality.localeCompare(second.municipality, "de");
}

/** The visible collection date comes from fee-source retrievals, never from the calculation date. */
export function sourceCollectionDate(sources: { retrieved_at: string }[]): string | null {
  const dates = sources.map(source => source.retrieved_at.slice(0, 10)).filter(value => /^\d{4}-\d{2}-\d{2}$/.test(value));
  return dates.sort().at(-1) ?? null;
}
const money = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
const number = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 2 });
const date = new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" });

export function formatMoney(cents: number | null): string {
  return cents === null ? "Nicht berechenbar" : money.format(cents / 100);
}

export function formatHours(minutes: number | null): string {
  return minutes === null ? "Nicht belegt" : number.format(minutes / 60) + " Std.";
}

export function formatDate(value: string): string {
  return date.format(new Date(value + "T12:00:00Z"));
}

export function feeColor(result?: Pick<ComparisonResult, "status" | "monthly_equivalent_cents">): string {
  if (!result || result.status !== "comparable" || result.monthly_equivalent_cents === null) return MISSING_COLOR;
  return FEE_BANDS.find(band => result.monthly_equivalent_cents! <= band.upper)!.color;
}

const reasonLabels: Record<string, string> = {
  care_rank_allocation_unresolved: "Die Quelle legt die Zuordnung der Geschwisterränge bei diesen Betreuungsmodellen nicht eindeutig fest. Daher wird keine Familiensumme geschätzt.",
  invalid_profile_input: "Die markierten persönlichen Eingaben müssen korrigiert werden. Vorherige Gebühren werden nicht weiter angezeigt.",
  target_outside_scope: "Das Vergleichskind muss im Haushalt leben und darf noch nicht eingeschult sein.",
  birthday_month_required_for_age_transition: "Bitte angeben, ob der dritte Geburtstag im Monat des Tarifstichtags liegt. Hier wechselt der Tarif erst im Folgemonat.",
  family_definition_not_satisfied: "Die Familie erfüllt die hinterlegte örtliche Definition nicht.",
  pass_eligibility_not_confirmed: "Die Voraussetzungen für den ausgewählten Pass sind noch nicht vollständig bestätigt.",
  eligibility_not_confirmed: "Die Voraussetzungen für die ausgewählte Ermäßigung sind noch nicht vollständig bestätigt.",
  discount_income_limit_not_met: "Das angegebene Einkommen erfüllt die Grenze der ausgewählten Ermäßigung nicht.",
  discount_not_applicable: "Die ausgewählte Ermäßigung gilt nicht für dieses Betreuungsmodell.",
  discounts_not_stackable: "Die ausgewählten Ermäßigungen dürfen nicht kombiniert werden.",
  infant_surcharge_allocation_required: "Bei mehreren Kindern unter drei Jahren mit FamilienCard muss die Zuordnung des Zuschlags geklärt werden.",
  tariff_not_offered: "Für diese Konstellation wird kein entsprechender Tarif angeboten.",
  price_or_income_input_missing: "Eine passende Tarif- oder Einkommensangabe fehlt.",
  income_definition_missing: "Die örtlich erforderliche Einkommensgrundlage fehlt.",
  payment_months_unknown: "Die Zahl der Beitragsmonate ist nicht belegt.",
  schedule_not_confirmed: "Die tägliche Verteilung der Betreuungszeit ist nicht bestätigt.",
  no_offer_covers_daily_need: "Kein belegtes Angebot deckt den Betreuungsbedarf an jedem Tag ab.",
  tariff_not_published: "Für dieses Modell ist kein Preis veröffentlicht.",
  date_not_reviewed: "Der gewählte Tarifstichtag liegt nach dem geprüften Datenstand.",
  multiple_equivalent_tariffs_require_scope_clarification: "Mehrere gleichwertige Tarifvarianten müssen geklärt werden.",
};

export function reasonLabel(reason: string): string {
  return reasonLabels[reason] ?? "Für diesen Vergleich ist eine weitere Klärung erforderlich.";
}
