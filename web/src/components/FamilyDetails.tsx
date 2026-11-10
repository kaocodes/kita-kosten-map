import type { MunicipalityCatalog } from "../domain/index.js";
import type { FamilyResult, ModelCatalog } from "../domain/model-family.js";
import type { SourceReference } from "../site/data.js";
import { formatDate, formatHours, formatMoney, reasonLabel } from "../site/presentation.js";
import styles from "../Atlas.module.css";

interface Props { result: FamilyResult; tariff: MunicipalityCatalog; sources: Record<string, SourceReference>; catalog: ModelCatalog; id?: string; embedded?: boolean }
const units: Record<string, string> = { per_month: " / Monat", per_meal: " / Essen", per_day: " / Tag", per_started_quarter_hour: " / angefangene Viertelstunde" };

export function FamilyDetails({ result, tariff, sources, catalog, id = "gemeindedetails", embedded = false }: Props) {
  const evidence = result.evidence.length ? result.evidence : tariff.offers.map(item => item.evidence);
  const references = [...new Set(evidence.map(item => item.source_id))].map(id => sources[id]).filter(Boolean);
  return <section className={embedded ? styles.inlineDetails : styles.detailsCard} id={id} aria-labelledby={`${id}-title`}>
    <span className={styles.eyebrow}>Ausgewählte Kommune</span>
    <div className={styles.detailHeading}>
    <h3 id={`${id}-title`} tabIndex={-1}>{result.municipality}</h3>
    <div className={styles.priceBlock}><strong className={result.monthly_equivalent_cents === null ? styles.missingPrice : styles.price}>{formatMoney(result.monthly_equivalent_cents)}</strong>
      {result.monthly_equivalent_cents !== null && <span>für die Familie pro Monat</span>}</div>
    </div>
    <p className={styles.detailLocation}>Modellfamilie · {result.children.length} {result.children.length === 1 ? "Kind" : "Kinder"} · {result.care_child_count} in Kita-Betreuung</p>
    <p className={styles.costNote}>Betreuung aller Kita-Kinder, auf zwölf Monate umgelegt. Essen und Zusatzkosten separat.</p>
    {result.care_child_count === 0 && <p className={styles.familyNote}>Im gewählten Modell besucht kein Kind eine Kita. Daher entstehen im Vergleich keine Kita-Betreuungskosten. Schul- und Hortkosten sind nicht enthalten.</p>}
    {result.reasons.length > 0 && <ul className={styles.reasonList}>{result.reasons.map(reason => <li key={reason}>{reasonLabel(reason)}</li>)}</ul>}
    {result.monthly_equivalent_cents === null && <p className={styles.familyNote}>Die Familiensumme bleibt offen. Bekannte Einzelbeiträge sind unten sichtbar und werden nicht als vollständige Summe ausgegeben.</p>}
    <div className={styles.childBreakdowns}>{result.children.map(child => {
      const category = catalog.categories.find(item => item.id === child.category)!;
      const row = child.result;
      const offer = tariff.offers.find(item => item.id === row?.offer_id);
      const uncertain = child.possible_monthly_cents;
      return <details className={styles.childBreakdown} key={child.index}>
        <summary><span>Kind {child.index + 1} · {category.label}</span><strong>{!child.in_care ? "Keine Kita-Kosten" : uncertain ? `${formatMoney(uncertain[0])} – ${formatMoney(uncertain[1])}` : formatMoney(row?.monthly_equivalent_cents ?? null)}</strong><i aria-hidden="true">+</i></summary>
        <div className={styles.childContent}>
        {!child.in_care ? <p>Keine Kita-Kosten · als Geschwisterkind berücksichtigt</p> : row && <>
          <div className={styles.childPrice}>{uncertain ? `${formatMoney(uncertain[0])} – ${formatMoney(uncertain[1])}` : formatMoney(row.monthly_equivalent_cents)}<small>Monatsäquivalent{uncertain ? " · Geschwisterrang offen" : ""}</small></div>
          <dl className={styles.breakdown}>
            <div><dt>Bedarf pro Tag, Mo–Fr</dt><dd>{formatHours(child.daily_minutes)}</dd></div>
            <div><dt>Monatsbeitrag laut Tarif</dt><dd>{uncertain ? "Zuordnung offen" : formatMoney(row.monthly_care_cents)}</dd></div>
            <div><dt>Beitragsmonate im Jahr</dt><dd>{row.payment_months ?? "Nicht belegt"}</dd></div>
            <div><dt>Gebuchte Wochenstunden</dt><dd>{formatHours(row.booked_weekly_minutes)}</dd></div>
            <div><dt>Zusätzlich gebuchte Zeit</dt><dd>{formatHours(row.extra_weekly_minutes)}</dd></div>
          </dl>
          {row.reasons.length > 0 && <ul className={styles.reasonList}>{row.reasons.map(reason => <li key={reason}>{reasonLabel(reason)}</li>)}</ul>}
          {offer && <div className={styles.offerNote}><span>Gewähltes Betreuungsmodell</span><strong>{offer.original_label}</strong>{offer.valid_from && <span>Tarif gültig ab {formatDate(offer.valid_from)}</span>}</div>}
          <section className={styles.extraCosts} aria-labelledby={`${id}-child-${child.index}-extras`}><h4 id={`${id}-child-${child.index}-extras`}>Verpflegung und Zusatzkosten</h4>
            {row.components.length ? <ul className={styles.componentList}>{row.components.map(component => <li key={component.id}>
              <span>{typeof component.original_label === "string" ? component.original_label : "Zusatzkosten"}</span>
              <strong>{component.amount_cents === null ? "Nicht belegt" : formatMoney(component.amount_cents) + (units[component.unit] ?? "")}</strong>
              {component.unit === "per_month" && <small>{component.payment_months === null ? "Beitragsmonate nicht belegt" : `${component.payment_months} Beitragsmonate im Jahr`}</small>}
              {component.required !== true && <small>{component.kind === "penalty" ? "Nur im angegebenen Sonderfall" : "Abhängig von Buchung oder Angebotsvariante"}</small>}
            </li>)}</ul> : <p>Für dieses Modell liegen keine berechenbaren Zusatzkosten vor.</p>}
            <p className={styles.smallNote}>Varianten bleiben getrennt. Ein Gesamtbetrag für Essen und Zusatzkosten wird nicht geschätzt.</p>
          </section>
        </>}
        </div>
      </details>;
    })}</div>
    <p className={styles.familyNote}>Für die Familiensumme werden die Jahresbeiträge addiert und durch zwölf geteilt. Gerundete Einzelwerte können zusammen geringfügig von der Familiensumme abweichen.</p>
    <div className={styles.sourceBlock}><span className={styles.sourceKicker}>Aus offiziellen Quellen</span>
      {references[0] && <a href={references[0].url} target="_blank" rel="noreferrer">{references[0].title} ↗</a>}
      <small>Quellen geprüft: {formatDate(result.reviewed_at)}</small>
      {references.length > 0 && <details className={styles.sourceDisclosure}><summary>Alle Quellen und Fundstellen ({references.length})</summary>
        <ul>{references.map(source => <li key={source.id}><a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>
          <ul>{[...new Set(evidence.filter(item => item.source_id === source.id).map(item => item.locator))].map(locator => <li key={locator}>{locator}</li>)}</ul></li>)}</ul>
      </details>}
    </div>
  </section>;
}
