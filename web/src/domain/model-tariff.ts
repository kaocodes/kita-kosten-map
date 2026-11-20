import { familyCount, incomeValue, validOn } from "./engine.js";
import { Fraction, roundMoney } from "./money.js";
import type { ModelSelection } from "./model-family.js";
import type { Evidence, MunicipalityCatalog, Offer, Price, Profile } from "./types.js";

interface ModelSchedule {
  weekday_minutes?: number[];
  days_per_week?: number;
  weekly_minutes?: number;
  schedule_evidence?: Evidence;
  original_label?: string;
}

interface IncomePercentage {
  percent: string;
  income_floor_cents: number;
  income_cap_cents: number;
}

function modelSchedule(offer: Offer): Offer {
  const schedule = offer.model_schedule as ModelSchedule | undefined;
  if (!schedule) return offer;
  return { ...offer, ...schedule, schedule_status: "verified",
    weekly_minutes: schedule.weekday_minutes?.reduce((total, minutes) => total + minutes, 0)
      ?? schedule.weekly_minutes ?? offer.weekly_minutes };
}

function rankMatches(row: Price, rank: number): boolean {
  const selector = row.selectors;
  return selector?.care_rank == null || (selector.care_rank_is_minimum ? rank >= selector.care_rank : rank === selector.care_rank);
}

function withAmount(row: Price, amount: number | null, missingReason = "unavailable"): Price {
  return { ...row, amount_cents: amount, value_status: amount === null ? missingReason : "known" };
}

/** Prepare an opt-in expansion catalog for one model child using its published tariff rules.
 * The common calculator still selects the offer and annualizes the resulting price rows.
 */
export function projectModelTariff(city: MunicipalityCatalog, profile: Profile, children: ModelSelection["children"], target: number, monthlyChildBenefitCents: number): MunicipalityCatalog {
  const mode = city.model_tariff;
  const count = familyCount(city, profile)!;
  const gross = incomeValue(profile, "gross_income", "year");
  const household = profile.children.map((child, index) => ({ age: child.age_months, index, ...children[index] }));
  const enrolled = household.filter(child => child.category === "nursery" || child.category === "kindergarten");
  const current = household[target];
  const sameAgeGroup = enrolled.filter(child => child.category === current.category);
  const oldestFirst = (first: typeof current, second: typeof current) => second.age - first.age || first.index - second.index;
  const youngestFirst = (first: typeof current, second: typeof current) => first.age - second.age || first.index - second.index;
  const birthRank = [...household].sort(oldestFirst).findIndex(child => child.index === target) + 1;
  const youngestCareRank = [...enrolled].sort(youngestFirst).findIndex(child => child.index === target) + 1;
  const offers = city.offers.map(modelSchedule);
  const reducedIncome = gross?.compare(282600 * 12) === -1;
  const applicableOffers = mode === "erdmannhausen"
    ? offers.filter(offer => offer.model_reduced_income === reducedIncome) : offers;
  const offersById = new Map(offers.map(offer => [offer.id, offer]));
  const single = profile.single_parent === true;
  const keepWithinPublishedTiers = (offset: number) => Math.min(4, count + offset);
  const prices = city.prices.flatMap(row => {
    const offer = offersById.get(row.offer_id!)!;
    const selectors = row.selectors!;
    const staged = (family: number) => selectors.family_count === family
      ? [{ ...row, selectors: { ...selectors, family_count: count } }] : [];
    const ranked = (rank: number) => rankMatches(row, rank)
      ? [{ ...row, selectors: { ...selectors, care_rank: null } }] : [];

    switch (mode) {
      case "household_rows":
        return selectors.single_parent != null && selectors.single_parent !== single ? [] : [row];
      case "youngest_in_care":
        return ranked(youngestCareRank);
      case "birth_order":
        return ranked(birthRank);
      case "freiberg":
        if (offer.age_group === "o3") return ranked(youngestCareRank);
        // The authorized provider refers to municipal reductions but publishes no U3 rank amounts.
        return youngestCareRank > 1 ? [withAmount(row, null, "sibling_discount_not_confirmed")] : [row];
      case "erdmannhausen": {
        if (offer.model_reduced_income !== reducedIncome) return [];
        const concurrentFullDay = enrolled.filter(child => child.daily_minutes === 480).length > 1;
        const surcharge = (row.derivation as { gt_surcharge_cents: number }).gt_surcharge_cents;
        return staged(keepWithinPublishedTiers(Number(single))).map(price => withAmount(price,
          Number(row.care_only_amount_cents) - (current.daily_minutes === 480 && concurrentFullDay ? surcharge / 2 : 0)));
      }
      case "kernen": {
        if (!offer.model_schedule || row.amount_cents === null) return [row];
        let amount = new Fraction(row.amount_cents);
        if (count >= 2) amount = amount.multiply(80).divide(100);
        if (single) amount = amount.multiply(90).divide(100);
        return [withAmount(row, roundMoney(amount))];
      }
      case "scheduled_prices":
        return typeof row.model_amount_cents === "number" ? [withAmount(row, row.model_amount_cents)] : [row];
      case "separate_age_tiers": {
        const u3 = offer.age_group === "u3";
        const effectiveCount = keepWithinPublishedTiers(Number(single) + Number(u3 && sameAgeGroup.length > 1));
        const matching = staged(effectiveCount);
        if (u3 || effectiveCount === 4) return matching;
        // The Ü3 table provides two ranks. Different schedules may change the total,
        // and the source does not define which child receives the lower contribution.
        const ambiguous = sameAgeGroup.length > 2 || sameAgeGroup.some(child => child.daily_minutes !== current.daily_minutes);
        if (ambiguous) return matching.filter(price => rankMatches(price, 1))
          .map(price => withAmount(price, null, "sibling_rank_not_confirmed"));
        const rank = sameAgeGroup.findIndex(child => child.index === target) + 1;
        return matching.filter(price => rankMatches(price, rank)).map(price => ({
          ...price, selectors: { ...price.selectors!, care_rank: null },
        }));
      }
      case "rutesheim": {
        if (offer.age_group === "o3" && offer.gt_days_per_week == null) return [row];
        if (offer.category === "mixed_age" && offer.weekly_minutes !== 2400) return [row];
        const eligible = enrolled.filter(child => child.daily_minutes === 480).sort(oldestFirst);
        const rank = eligible.findIndex(child => child.index === target) + 1;
        if (offer.age_group === "o3") return ranked(Math.max(1, rank));
        if (rank < 2 || row.amount_cents === null) return [row];
        // The city's offer list classifies the mixed-age booking until 15:00 as GT1.
        return [withAmount(row, row.amount_cents - 5000)];
      }
      default:
        return [row];
    }
  });

  let incomeBands = city.income_bands;
  if (mode === "kernen") {
    // Model only: prior-year gross wages equal the selected annual gross.
    incomeBands = city.income_bands.map(band => ({ ...band, basis: "gross_income" }));
  }
  let components = city.components.flatMap(part => {
    if (part.model_family_count != null && part.model_family_count !== Math.min(3, count)) return [];
    if (Array.isArray(part.model_offer_ids)) {
      if (!part.model_offer_ids.length) return [];
      return [{ ...part, offer_ids: part.model_offer_ids as string[] }];
    }
    return [part];
  });
  if (mode === "kernen") {
    // Both published meal bookings remain visible as separate options.
    components = components.map(part => part.kind === "meal" ? { ...part, days_per_week: undefined } : part);
  }
  if (mode === "remseck") {
    components = components.filter(part => part.age_group !== "u3" || !part.model_age_band ||
      part.model_age_band === (current.age <= 24 ? "1–2 Jahre" : "über 2 Jahre"))
      .map(part => part.required_when_age_matches === true ? { ...part, required: true } : part);
  }

  if (mode === "renningen") {
    for (const offer of offers.filter(item => item.age_group === "o3" && (item.weekly_minutes ?? 0) > 1800)) {
      prices.push({ id: offer.id + "-model", offer_id: offer.id, selectors: { family_count: count, income_band_id: null },
        amount_cents: null, evidence: offer.evidence, value_status: "monthly_conversion_not_confirmed" });
    }
  }

  if (mode === "waiblingen") {
    const eligibleChildren = profile.children.filter(child => child.resident && child.child_benefit).length;
    const annualChildBenefit = monthlyChildBenefitCents * eligibleChildren * 12;
    for (const offer of offers) {
      if (!offer.model_schedule || !offer.formula || !validOn(offer, profile.as_of)) continue;
      const formula = offer.formula as unknown as IncomePercentage;
      const income = gross!.add(annualChildBenefit);
      const assessable = income.compare(formula.income_floor_cents) < 0 ? new Fraction(formula.income_floor_cents)
        : income.compare(formula.income_cap_cents) > 0 ? new Fraction(formula.income_cap_cents) : income;
      const percentageInBasisPoints = Math.round(Number(formula.percent) * 100);
      const payablePerThousand = [1000, 500, 250, 125][birthRank - 1];
      const amount = roundMoney(assessable.multiply(percentageInBasisPoints).divide(10000).multiply(payablePerThousand).divide(1000));
      prices.push({ id: offer.id + "-model", offer_id: offer.id, selectors: { family_count: count, income_band_id: null },
        amount_cents: amount, evidence: offer.evidence, value_status: "known" });
      offer.formula = null;
    }
  }
  return { ...city, offers: applicableOffers, prices, income_bands: incomeBands, components };
}
