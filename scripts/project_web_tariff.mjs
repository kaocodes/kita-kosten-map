import { projectAichwaldTariff } from "./project_aichwald_tariff.mjs";

export function projectWebTariff(catalog) {
  if (catalog.id === "aichwald") return projectAichwaldTariff(catalog);
  const excluded = new Set(catalog.offers.filter(offer => offer.scope === "non_municipal").map(offer => offer.id));
  if (excluded.size === 0) return catalog;

  const components = catalog.components.flatMap(part => {
    if (part.offer_ids == null) return [part];
    const offers = part.offer_ids.filter(id => !excluded.has(id));
    return offers.length ? [{ ...part, offer_ids: offers }] : [];
  });
  return {
    ...catalog, components,
    offers: catalog.offers.filter(offer => !excluded.has(offer.id)),
    prices: catalog.prices.filter(row => !excluded.has(row.offer_id)),
  };
}
