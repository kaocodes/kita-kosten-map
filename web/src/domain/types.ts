/** Canonical JSON contracts. Original source fields remain attached to each record. */
export interface Evidence {
  source_id: string;
  locator: string;
  original?: unknown;
}

export interface Income {
  basis: string;
  period: "year" | "month";
  amount_cents: number;
  [key: string]: unknown;
}

export interface Child {
  age_months: number;
  resident: boolean;
  child_benefit: boolean;
  birthday_in_reference_month?: boolean;
  [key: string]: unknown;
}

export interface LocalInputs {
  incomes?: Income[];
  income_mode?: "highest_band" | "specified";
  pass_id?: string;
  approved_rules?: string[];
  eligibility?: string[];
  care_rank?: number | null;
}

export interface Profile {
  id?: string;
  label?: string;
  as_of: string;
  children: Child[];
  target_child: number;
  weekday_minutes: number[];
  income_mode: "highest_band" | "specified";
  incomes?: Income[];
  care_rank?: number | null;
  pass_id: string;
  approved_rules?: string[];
  eligibility?: string[];
  single_parent: boolean;
  scope: string;
  metric?: string;
  school_entry?: boolean;
  meal_days_per_week?: number;
  allow_published_future?: boolean;
  municipality_overrides?: Record<string, LocalInputs>;
  household?: { parent_count: number; parents_living_together: boolean };
  assumptions?: Record<string, unknown>;
  model_income_snapshot?: { incomes: Income[]; assumptions: Record<string, unknown> } | null;
  [key: string]: unknown;
}

export interface IncomeBand {
  id: string;
  basis: string;
  period: "year" | "month";
  lower_cents: number | null;
  upper_cents: number | null;
  lower_inclusive: boolean;
  upper_inclusive: boolean;
  is_highest: boolean;
  single_parent?: boolean | null;
  [key: string]: unknown;
}

export interface Selectors {
  family_count: number;
  family_count_is_minimum?: boolean;
  care_rank?: number | null;
  care_rank_is_minimum?: boolean;
  income_band_id: string | null;
  pass_id?: string;
}

export interface Price {
  id: string | null;
  offer_id?: string;
  amount_cents: number | null;
  value_status: string;
  selectors?: Selectors;
  evidence: Evidence;
  corroborating_evidence?: Evidence[];
  [key: string]: unknown;
}

export interface Formula {
  threshold_minutes: number;
  below_or_equal_rate_cents: number;
  above_rate_cents: number;
  family_discount_percent: number[];
  minimum_cents: number;
  rounding: string;
}

export interface Offer {
  id: string;
  original_label: string;
  age_group: string;
  age_min_months: number;
  age_max_months_exclusive: number | null;
  valid_from: string | null;
  valid_to: string | null;
  weekly_minutes: number | null;
  weekday_minutes: number[] | null;
  continuous: boolean;
  schedule_status: string;
  payment_months: number | null;
  formula: Formula | null;
  evidence: Evidence;
  payment_evidence: Evidence;
  schedule_evidence: Evidence;
  [key: string]: unknown;
}

export interface Component {
  id: string;
  kind: string;
  amount_cents: number | null;
  unit: string;
  required: boolean | null;
  payment_months: number | null;
  value_status: string;
  evidence: Evidence;
  valid_from?: string | null;
  valid_to?: string | null;
  age_group?: string | null;
  offer_ids?: string[] | null;
  days_per_week?: number;
  minimum_daily_minutes_exclusive?: number;
  pass_id?: string;
  selectors?: Selectors;
  extension_minutes?: number;
  execution_status?: string | null;
  [key: string]: unknown;
}

export interface Rule {
  id: string;
  kind?: string;
  execution_status: string;
  stackable?: boolean;
  requires?: string[];
  parameters?: {
    components?: string[];
    percent?: number;
    income_basis?: string;
    income_period?: "year" | "month";
    income_below_cents?: number;
    threshold_cents?: number;
    bands?: { below_cents: number; percent: number }[];
    rounding?: string;
  };
  evidence: Evidence;
  [key: string]: unknown;
}

export interface MunicipalityCatalog {
  id: string;
  name: string;
  reviewed_at: string;
  family_basis: string;
  age_transition?: string;
  offers: Offer[];
  prices: Price[];
  income_bands: IncomeBand[];
  components: Component[];
  rules: Rule[];
  issues: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface Registry {
  municipalities: {
    id: string; name: string; ags: string; active: boolean;
    tariff_id: string; area_id: string; region_id: string;
  }[];
  [key: string]: unknown;
}

export interface CalculatedComponent extends Component {
  annual_equivalent_cents: number | null;
  calculation?: Record<string, unknown>[];
}

export interface ComparisonResult {
  municipality_id: string;
  municipality: string;
  profile_id: string | null;
  as_of: string;
  reviewed_at: string;
  status: "unavailable" | "comparable" | "ambiguous";
  reasons: string[];
  monthly_care_cents: number | null;
  annual_care_cents: number | null;
  monthly_equivalent_cents: number | null;
  offer_id: string | null;
  offer_label: string | null;
  booked_weekly_minutes: number | null;
  extra_weekly_minutes: number | null;
  payment_months: number | null;
  components: CalculatedComponent[];
  calculation: Record<string, unknown>[];
  evidence: Evidence[];
  issues: Record<string, unknown>[];
  alternatives: { offer_id: string; price_id: string | null; monthly_cents: number }[];
  ags?: string;
  area_id?: string;
  tariff_id?: string;
  family_count?: number;
  care_rank?: number | null;
  selected_price_id?: string | null;
  total_mandatory_monthly_equivalent_cents?: number | null;
  total_status?: string;
}
