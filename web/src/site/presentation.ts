import type { ComparisonResult } from "../domain/index.js";

export const FEE_BANDS = [
  { upper: 30000, color: "#e5eee1", label: "bis 300 €" },
  { upper: 45000, color: "#b5cbb0", label: "> 300–450 €" },
  { upper: 60000, color: "#7fa785", label: "> 450–600 €" },
  { upper: 90000, color: "#467c62", label: "> 600–900 €" },
  { upper: Infinity, color: "#174c3c", label: "> 900 €" },
];
export const MISSING_COLOR = "#d9dddf";
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
