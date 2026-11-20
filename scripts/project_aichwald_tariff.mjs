/** Use care-only prices in the browser while leaving Aichwald's filed tariff intact. */
import assert from "node:assert/strict";

export function projectAichwaldTariff(catalog) {
  const components = new Map(catalog.components.map(part => [part.id, part]));
  const offersByLabel = new Map(catalog.offers.map(offer => [offer.original_label, offer]));
  const redundantOffers = new Set();
  const optionalMeals = [];

  // The two packages in each pair have identical care. Keep the base package
  // as the comparable offer and show the meal as an option.
  for (const [baseLabel, mealLabel] of [
    ["VÖ7 ohne Mittagessen", "VÖ7 mit Mittagessen"],
    ["Krippe 7–12 Uhr ohne Mittagessen", "Krippe 7–12 Uhr mit Mittagessen"],
  ]) {
    const base = offersByLabel.get(baseLabel);
    const withMeal = offersByLabel.get(mealLabel);
    assert.ok(base && withMeal, "Aichwald meal offer pair is missing");
    for (const field of ["age_group", "age_min_months", "age_max_months_exclusive", "weekday_minutes", "continuous", "valid_from", "valid_to", "payment_months"]) {
      assert.deepEqual(base[field], withMeal[field], `Aichwald meal variant differs in ${field}`);
    }
    const basePrices = catalog.prices.filter(row => row.offer_id === base.id);
    const mealPrices = catalog.prices.filter(row => row.offer_id === withMeal.id);
    const [component] = catalog.components.filter(part => part.offer_ids?.includes(withMeal.id));
    assert.ok(basePrices.length && component?.kind === "meal", "Aichwald meal variant is missing");
    assert.deepEqual(
      mealPrices.map(row => [row.selectors, row.care_only_amount_cents]),
      basePrices.map(row => [row.selectors, row.amount_cents]),
      "Aichwald meal variant has different care prices",
    );
    redundantOffers.add(withMeal.id);
    optionalMeals.push({
      ...component, id: `${component.id}-optional`, original_label: "Mittagessen optional",
      offer_ids: [base.id], required: false, inclusion: "optional", additional_charge: true,
    });
  }

  const prices = catalog.prices.map(row => {
    if (row.care_only_amount_cents === undefined) {
      assert.ok(!row.included_components.some(part => components.get(part.component_id)?.inclusion === "included"),
        "Aichwald care-only price is missing for an included meal");
      return row;
    }
    const [included] = row.included_components;
    const meal = components.get(included?.component_id);
    assert.ok(row.included_components.length === 1 && meal?.kind === "meal" &&
      meal.inclusion === "included" && meal.offer_ids?.includes(row.offer_id), "Aichwald meal is unverified for this offer");
    assert.ok(Number.isInteger(row.care_only_amount_cents) && row.care_only_amount_cents >= 0 &&
      Number.isInteger(meal.amount_cents) && meal.amount_cents > 0, "Aichwald care or meal price is invalid");
    assert.equal(row.amount_cents - meal.amount_cents, row.care_only_amount_cents, "Aichwald meal deduction does not match");
    return {
      ...row, amount_cents: row.care_only_amount_cents,
      corroborating_evidence: [...(row.corroborating_evidence ?? []), meal.evidence],
    };
  }).filter(row => !redundantOffers.has(row.offer_id));

  return {
    ...catalog, prices,
    offers: catalog.offers.filter(offer => !redundantOffers.has(offer.id)),
    components: [
      ...catalog.components.map(part => part.inclusion === "included" ? {
        ...part, required: true, separated_from_care_price: true, offer_ids: part.offer_ids.filter(id => !redundantOffers.has(id)),
      } : part),
      ...optionalMeals,
    ],
  };
}
