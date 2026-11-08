import { incomeValue } from "../domain/index.js";
import type { ComparisonResult, MunicipalityCatalog, Profile } from "../domain/index.js";
import { INCOME_FIELDS } from "../site/personal-profile.js";
import type { SourceReference } from "../site/data.js";
import { formatDate, formatHours, formatMoney, reasonLabel } from "../site/presentation.js";
import styles from "../App.module.css";

interface Props {
  result: ComparisonResult;
  tariff: MunicipalityCatalog;
  sources: Record<string, SourceReference>;
  profile: Profile | null;
  personal: boolean;
}

const unitLabels: Record<string, string> = {
  per_month: " / Monat", per_meal: " / Essen", per_day: " / Tag",
  per_started_quarter_hour: " / angefangene Viertelstunde",
};

export function MunicipalityDetails({ result, tariff, sources, profile, personal }: Props) {
  const offer = tariff.offers.find(item => item.id === result.offer_id);
  const evidence = result.evidence.length ? result.evidence : tariff.offers.map(item => item.evidence);
  const references = [...new Set(evidence.map(reference => reference.source_id))]
    .map(id => sources[id]).filter(Boolean);
  const firstSource = references[0];
  const child = profile?.children[profile.target_child];
  const localProfile = profile ? { ...profile, ...profile.municipality_overrides?.[result.municipality_id] } : null;
  const missingIncome = localProfile && localProfile.pass_id === "none" ? INCOME_FIELDS.filter(field =>
    tariff.income_bands.some(band => band.basis === field.basis) && incomeValue(localProfile, field.basis, field.period) === null) : [];
  return <section className={styles.detailsCard} id="gemeindedetails" aria-labelledby="municipality-title">
    <div className={styles.detailHeader}>
      <span className={styles.eyebrow}>Ausgewählte Kommune</span>
      <span className={styles.locationIcon} aria-hidden="true">↗</span>
    </div>
    <h2 id="municipality-title" tabIndex={-1}>{result.municipality}</h2>
    <p className={styles.detailLocation}>{!child ? "Kommunale Betreuung" : child.age_months < 36 ? "Kommunale Krippenbetreuung" : "Kommunale Kindergartenbetreuung"}</p>
    <div className={styles.priceBlock}>
      <strong className={result.monthly_equivalent_cents === null ? styles.missingPrice : styles.price}>
        {formatMoney(result.monthly_equivalent_cents)}
      </strong>
      {result.monthly_equivalent_cents !== null && <span>pro Monat</span>}
      <p>Betreuung, auf zwölf Monate umgelegt.<br />Essen und Zusatzkosten separat.</p>
    </div>
    {result.reasons.length > 0 && <ul className={styles.reasonList}>
      {result.reasons.map(reason => <li key={reason}>{reasonLabel(reason)}</li>)}
    </ul>}
    {personal && result.status !== "comparable" && <div className={styles.inputHints}>
      {missingIncome.map(field => <a key={field.basis} href={"#income-" + field.basis}>{field.label} ergänzen</a>)}
      {localProfile?.care_rank == null && tariff.prices.some(price => price.selectors?.care_rank != null) && <a href="#care-rank">Betreuungsrang ergänzen</a>}
      <a href="#family-heading">Familienangaben und örtliche Voraussetzungen prüfen</a>
    </div>}
    <dl className={styles.breakdown}>
      <div><dt>Monatsbeitrag laut Tarif</dt><dd>{formatMoney(result.monthly_care_cents)}</dd></div>
      <div><dt>Beitragsmonate im Jahr</dt><dd>{result.payment_months ?? "Nicht belegt"}</dd></div>
      <div><dt>Gebuchte Wochenstunden</dt><dd>{formatHours(result.booked_weekly_minutes)}</dd></div>
      <div><dt>Zusätzlich gebuchte Zeit</dt><dd>{formatHours(result.extra_weekly_minutes)}</dd></div>
    </dl>
    {offer && <div className={styles.offerNote}>
      <span>Gewähltes Betreuungsmodell</span>
      <strong>{offer.original_label}</strong>
      {offer.valid_from && <span>Tarif gültig ab {formatDate(offer.valid_from)}</span>}
    </div>}
    <details className={styles.disclosure}>
      <summary>Verpflegung und Zusatzkosten <span aria-hidden="true">+</span></summary>
      {result.components.length ? <ul className={styles.componentList}>
        {result.components.map(component => <li key={component.id}>
          <span>{typeof component.original_label === "string" ? component.original_label : "Zusatzkosten"}</span>
          <strong>{component.amount_cents === null ? "Nicht belegt"
            : formatMoney(component.amount_cents) + (unitLabels[component.unit] ?? "")}</strong>
          {component.unit === "per_month" && <small>{component.payment_months === null
            ? "Beitragsmonate nicht belegt" : `${component.payment_months} Beitragsmonate im Jahr`}</small>}
          {component.required !== true && <small>{component.kind === "penalty"
            ? "Fällt nur im angegebenen Sonderfall an" : "Abhängig von Buchung oder Angebotsvariante"}</small>}
        </li>)}
      </ul> : <p>Für das gewählte Modell liegen keine berechenbaren Zusatzkosten vor.</p>}
      <p className={styles.smallNote}>Varianten werden getrennt ausgewiesen. Bei unvollständigen Angaben wird kein Gesamtbetrag geschätzt.</p>
    </details>
    <div className={styles.sourceBlock}>
      <span className={styles.sourceKicker}>Aus offiziellen Quellen</span>
      {firstSource && <a href={firstSource.url} target="_blank" rel="noreferrer">{firstSource.title} <span aria-hidden="true">↗</span></a>}
      <small>Quellen geprüft: {formatDate(result.reviewed_at)}</small>
      {references.length > 0 && <details className={styles.sourceDisclosure}>
        <summary>Alle Quellen und Fundstellen ({references.length})</summary>
        <ul>{references.map(source => <li key={source.id}>
          <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>
          <ul>{[...new Set(evidence.filter(reference => reference.source_id === source.id).map(reference => reference.locator))]
            .map(locator => <li key={locator}>{locator}</li>)}</ul>
        </li>)}</ul>
      </details>}
    </div>
  </section>;
}
