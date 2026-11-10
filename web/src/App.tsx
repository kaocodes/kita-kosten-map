import { useEffect, useMemo, useState } from "react";
import { compareModelFamily } from "./domain/model-family.js";
import type { ModelSelection } from "./domain/model-family.js";
import { ModelConfigurator } from "./components/ModelConfigurator.js";
import { MunicipalityMap } from "./components/MunicipalityMap.js";
import { MunicipalityHeadline } from "./components/MunicipalityHeadline.js";
import { FamilyDetails } from "./components/FamilyDetails.js";
import { loadSiteData } from "./site/data.js";
import type { SiteData } from "./site/data.js";
import { FEE_BANDS, MISSING_COLOR, compareMonthlyFeesDescending, feeColor, formatDate, formatHours, formatMoney, sourceCollectionDate } from "./site/presentation.js";
import styles from "./Atlas.module.css";

export function App() {
  const [data, setData] = useState<SiteData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [selection, setSelection] = useState<ModelSelection | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    loadSiteData(controller.signal).then(setData).catch(error => {
      if (!controller.signal.aborted) { console.error("Unable to initialize the comparison", error); setError(true); }
    });
    return () => controller.abort();
  }, [attempt]);
  const profile = data?.bundle.profiles.default;
  const municipalityNames = useMemo(() => data?.bundle.registry.municipalities
    .filter(municipality => municipality.active).map(municipality => municipality.name) ?? [], [data]);
  const model = selection ?? data?.bundle.models.default;
  const results = useMemo(() => data && profile && model
    ? compareModelFamily(data.bundle.tariffs, profile, model, data.bundle.registry, data.bundle.models) : [], [data, profile, model]);
  const ordered = useMemo(() => [...results].sort(compareMonthlyFeesDescending), [results]);
  const initial = [...ordered].reverse().find(result => result.monthly_equivalent_cents !== null) ?? ordered[0];
  useEffect(() => {
    if (selectedId === null && initial) setSelectedId(initial.municipality_id);
  }, [selectedId, initial?.municipality_id]);
  const selected = results.find(result => result.municipality_id === selectedId) ?? initial;
  const comparable = results.filter(result => result.status === "comparable");
  const collectedOn = data ? sourceCollectionDate(Object.values(data.bundle.sources)) : null;
  function selectMunicipality(id: string, fromList = false) {
    setSelectedId(id);
    setExpandedId(fromList ? expandedId === id ? null : id : null);
  }

  return <>
    <a className={styles.skipLink} href="#vergleich">Zum Gebührenvergleich</a>
    <header className={styles.header}>
      <a className={styles.brand} href="#" aria-label="Kita-Kosten, zur Übersicht">
        <img className={styles.brandImage} src={import.meta.env.BASE_URL + "images/icons/kita-pin-bold.webp"} alt="" width="60" height="60" />
        <span>Kita<span className={styles.brandDash}>-</span>Kosten<small>REGION STUTTGART</small></span>
      </a>
      <nav aria-label="Hauptnavigation"><a href="#vergleich">Vergleich</a><a href="#grundlage">Grundlage & Quellen</a></nav>
      <span className={styles.dateBadge}>{collectedOn ? `Datenerhebung ${formatDate(collectedOn)}` : "Offizielle kommunale Quellen"}</span>
    </header>
    <main className={styles.main}>
      <section className={styles.intro} aria-labelledby="page-title">
        <MunicipalityHeadline names={municipalityNames} />
      </section>
      {!data || !profile ? <section className={styles.loadingCard} role={error ? "alert" : "status"}>
        <h2>{error ? "Die Vergleichsdaten konnten nicht geladen werden." : "Der Gebührenvergleich wird geladen …"}</h2>
        <p>{error ? "Bitte lade die Daten erneut. Es wurden keine Ersatzwerte eingesetzt." : "Gemeindegrenzen und geprüfte Tarife werden vorbereitet."}</p>
        {error && <button className={styles.retryButton} onClick={() => setAttempt(value => value + 1)}>Erneut versuchen</button>}
      </section> : <>
        <section className={styles.mapCard} id="vergleich" aria-label="Kita-Gebühren im Kartenvergleich">
          <MunicipalityMap geometry={data.geometry} results={results} selectedId={selected?.municipality_id ?? ""}
            maxZoom={data.bundle.geography.max_zoom} attribution={data.bundle.geography} onSelect={selectMunicipality} />
          <div className={styles.legend} aria-label="Gebührenlegende von günstig bis teuer">
            <div className={styles.legendScale}><div className={styles.legendBands} aria-hidden="true">{FEE_BANDS.map(band => <i key={band.label} style={{ backgroundColor: band.color }} />)}</div>
              <div className={styles.legendLabels}><span>günstig</span><span>teuer</span></div></div>
            <span className={styles.missingLegend}><i style={{ backgroundColor: MISSING_COLOR }} />Umgebung ohne Vergleichsdaten · fehlende oder uneindeutige Tarife</span>
          </div>
          {selected && <FamilyDetails result={selected} tariff={data.bundle.tariffs.find(tariff => tariff.id === selected.tariff_id)!} sources={data.bundle.sources} catalog={data.bundle.models} />}
        </section>
        <ModelConfigurator selection={model!} catalog={data.bundle.models} onChange={setSelection} />
        <p className={styles.resultStatus} role="status">{comparable.length} von {results.length} Kommunen berechenbar. Betreuungskosten der gesamten Modellfamilie; Essen separat.
          {selected && <span className={styles.visuallyHidden}> Ausgewählt: {selected.municipality}, {formatMoney(selected.monthly_equivalent_cents)} pro Monat.</span>}</p>
        <section className={styles.comparisonCard} aria-labelledby="list-heading">
          <div className={styles.listHeading}><h2 id="list-heading">Alle Kommunen im Vergleich</h2><span>Teuer → günstig</span></div>
          <ul className={styles.municipalityList}>{ordered.map(result => {
            const expanded = expandedId === result.municipality_id;
            return <li key={result.municipality_id}>
              <button className={styles.municipalityButton} aria-expanded={expanded} aria-controls={`comparison-${result.municipality_id}`}
                onClick={() => selectMunicipality(result.municipality_id, true)}>
                <i className={styles.citySwatch} style={{ backgroundColor: feeColor(result) }} aria-hidden="true" />
                <span className={styles.cityName}>{result.municipality}<small>{result.booked_weekly_minutes === null ? "Weitere Angabe oder Klärung erforderlich" : formatHours(result.booked_weekly_minutes) + " / Woche insgesamt gebucht"}</small></span>
                <strong>{formatMoney(result.monthly_equivalent_cents)}</strong><span className={styles.rowArrow} aria-hidden="true">{expanded ? "−" : "+"}</span>
              </button>
              <div id={`comparison-${result.municipality_id}`} hidden={!expanded}>{expanded && <FamilyDetails id={`list-${result.municipality_id}`} embedded result={result}
                tariff={data.bundle.tariffs.find(tariff => tariff.id === result.tariff_id)!} sources={data.bundle.sources} catalog={data.bundle.models} />}</div>
            </li>;
          })}</ul>
          <p className={styles.listNote}>Eine Kommune auswählen: Familienbetrag, Kinderdetails und Quellen öffnen direkt darunter.</p>
        </section>
        <section className={styles.methodCard} id="grundlage" aria-labelledby="method-heading">
          <div><span className={styles.eyebrow}>Transparent vergleichen</span><h2 id="method-heading">Was steckt in den Zahlen?</h2>
            <p>Kommunen rechnen unterschiedlich ab. Wir erhalten die tatsächlichen Tarife und machen ihren Zahlungsrhythmus vergleichbar.</p></div>
          <div className={styles.methodExplanation}><strong>Summe der jährlichen Kinderbeiträge ÷ 12</strong>
            <p>Für jedes Kita-Kind wird der Monatsbeitrag mit seinen Beitragsmonaten multipliziert. Die Summe aller Jahresbeiträge wird durch zwölf geteilt. So werden elf und zwölf Beitragsmonate vergleichbar. Der Tarif am Berechnungsstichtag bleibt dabei konstant; das Ergebnis ist keine tatsächliche Kalenderjahresabrechnung.</p>
            <p>Berechnungsstichtag: {formatDate(profile.as_of)}. Verglichen werden kommunale Gebühren für städtische Betreuung mit festgelegten örtlichen Einkommensannahmen. Der persönliche Beitrag kann abweichen.</p></div>
        </section>
        <footer className={styles.footer}>
          <div><strong>Kita-Kosten · Region Stuttgart</strong><span>{collectedOn && `Datenerhebung ${formatDate(collectedOn)} · `}Offizielle kommunale Quellen</span></div>
          <p>Kartendaten © <a href={data.bundle.geography.attribution_url} target="_blank" rel="noreferrer">BKG</a> · <a href={data.bundle.geography.license_url} target="_blank" rel="noreferrer">dl-de/by-2-0</a> · Grenzen vereinfacht<br />
            Stand {formatDate(data.bundle.geography.boundary_status_date)} · <a href={data.bundle.geography.product_url} target="_blank" rel="noreferrer">Datenprodukt</a> · <a href={data.bundle.geography.data_sources_url} target="_blank" rel="noreferrer">Datenquellen</a> · <a href={import.meta.env.BASE_URL + "THIRD_PARTY_NOTICES.txt"}>Softwarelizenzen</a></p>
        </footer>
      </>}
    </main>
  </>;
}
