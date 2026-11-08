import { useEffect, useMemo, useState } from "react";
import { compareModelFamily } from "./domain/model-family.js";
import type { ModelSelection } from "./domain/model-family.js";
import { ModelConfigurator } from "./components/ModelConfigurator.js";
import { MunicipalityMap } from "./components/MunicipalityMap.js";
import { FamilyDetails } from "./components/FamilyDetails.js";
import { loadSiteData } from "./site/data.js";
import type { SiteData } from "./site/data.js";
import { FEE_BANDS, MISSING_COLOR, feeColor, formatDate, formatHours, formatMoney } from "./site/presentation.js";
import styles from "./App.module.css";

function MapMark() {
  return <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" /></svg>;
}

export function App() {
  const [data, setData] = useState<SiteData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [selection, setSelection] = useState<ModelSelection | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    loadSiteData(controller.signal).then(setData).catch(error => {
      if (!controller.signal.aborted) { console.error("Unable to initialize the comparison", error); setError(true); }
    });
    return () => controller.abort();
  }, [attempt]);
  const profile = data?.bundle.profiles.default;
  const model = selection ?? data?.bundle.models.default;
  const results = useMemo(() => data && profile && model
    ? compareModelFamily(data.bundle.tariffs, profile, model, data.bundle.registry, data.bundle.models) : [], [data, profile, model]);
  const ordered = useMemo(() => [...results].sort((first, second) =>
    (first.monthly_equivalent_cents ?? Infinity) - (second.monthly_equivalent_cents ?? Infinity) ||
    first.municipality.localeCompare(second.municipality, "de")), [results]);
  useEffect(() => {
    if (selectedId === null && ordered.length) setSelectedId(ordered[0].municipality_id);
  }, [ordered, selectedId]);
  const selected = results.find(result => result.municipality_id === selectedId) ?? ordered[0];
  const comparable = results.filter(result => result.status === "comparable");
  const min = comparable.length ? Math.min(...comparable.map(result => result.monthly_equivalent_cents!)) : null;
  const max = comparable.length ? Math.max(...comparable.map(result => result.monthly_equivalent_cents!)) : null;
  function selectMunicipality(id: string) {
    setSelectedId(id);
    window.requestAnimationFrame(() => document.getElementById("municipality-title")?.focus({ preventScroll: true }));
    if (window.matchMedia("(max-width: 780px)").matches) {
      const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
      document.getElementById("gemeindedetails")?.scrollIntoView({ behavior, block: "start" });
    }
  }

  return <>
    <a className={styles.skipLink} href="#vergleich">Zum Gebührenvergleich</a>
    <header className={styles.header}>
      <a className={styles.brand} href="#" aria-label="Kita-Kosten, zur Übersicht">
        <span className={styles.brandMark}><MapMark /></span>
        <span>Kita<span className={styles.brandDash}>-</span>Kosten<small>REGION STUTTGART</small></span>
      </a>
      <nav aria-label="Hauptnavigation"><a className={styles.activeNav} href="#vergleich">Vergleich</a><a href="#grundlage">Grundlage & Quellen</a></nav>
      <span className={styles.headerNote}>Ein kommunaler Gebührenvergleich</span>
    </header>
    <main className={styles.main}>
      <section className={styles.intro} aria-labelledby="page-title">
        <div><p className={styles.eyebrow}>MEHR ÜBERBLICK FÜR FAMILIEN UND POLITIK</p>
          <h1 id="page-title">Kita-Gebühren im Vergleich.</h1>
          <p className={styles.lead}>Was kommunale Betreuung rund um Stuttgart kostet – mit gleichem Betreuungsbedarf und nachvollziehbaren Quellen.</p>
        </div>
        {profile && <span className={styles.dateBadge}><span aria-hidden="true" />Tarifstichtag {formatDate(profile.as_of)}</span>}
      </section>
      {!data || !profile ? <section className={styles.loadingCard} role={error ? "alert" : "status"}>
        <span className={styles.loadingIcon}><MapMark /></span>
        <h2>{error ? "Die Vergleichsdaten konnten nicht geladen werden." : "Der Gebührenvergleich wird geladen …"}</h2>
        <p>{error ? "Bitte lade die Daten erneut. Es wurden keine Ersatzwerte eingesetzt." : "Gemeindegrenzen und geprüfte Tarife werden vorbereitet."}</p>
        {error && <button className={styles.retryButton} onClick={() => setAttempt(value => value + 1)}>Erneut versuchen</button>}
      </section> : <>
        <ModelConfigurator selection={model!} catalog={data.bundle.models} onChange={setSelection} />
        <p className={styles.resultStatus} role="status">{comparable.length} von {results.length} Kommunen berechenbar. Betreuungskosten der gesamten Modellfamilie; Essen separat.</p>
        <div className={styles.workspace} id="vergleich">
          <section className={styles.mapCard} aria-labelledby="map-heading">
            <div className={styles.cardHeading}><div><span className={styles.eyebrow}>DIE REGION AUF EINEN BLICK</span><h2 id="map-heading">Wo liegen die Gebühren?</h2></div><span className={styles.countBadge}>{results.length} Kommunen</span></div>
            <MunicipalityMap geometry={data.geometry} results={results} selectedId={selected?.municipality_id ?? ""}
              maxZoom={data.bundle.geography.max_zoom} attribution={data.bundle.geography} onSelect={selectMunicipality} />
            <div className={styles.legend} aria-label="Gebührenlegende">
              <div className={styles.legendHeading}><strong>Familienbetreuung pro Monat</strong><span>Auf zwölf Monate umgelegt</span></div>
              <div className={styles.legendBands}>{FEE_BANDS.map(band => <span key={band.label}><i style={{ backgroundColor: band.color }} />{band.label}</span>)}</div>
              <span className={styles.missingLegend}><i style={{ backgroundColor: MISSING_COLOR }} />Fehlend oder nicht eindeutig berechenbar</span>
            </div>
          </section>
          {selected && <FamilyDetails result={selected} tariff={data.bundle.tariffs.find(tariff => tariff.id === selected.tariff_id)!} sources={data.bundle.sources} catalog={data.bundle.models} />}
        </div>
        <section className={styles.comparisonCard} aria-labelledby="list-heading">
          <div className={styles.listHeading}><div><span className={styles.eyebrow}>ALLE KOMMUNEN IM VERGLEICH</span><h2 id="list-heading">Eine Familie, unterschiedliche Beiträge.</h2></div>
            <p>{min === null ? "Noch keine Vergleichswerte" : `${formatMoney(min)} – ${formatMoney(max)}`}<small>Monatliches Betreuungsäquivalent der Familie</small></p>
          </div>
          <p className={styles.listNote}>Nach Monatsäquivalent aufsteigend. Eine Kommune auswählen, um Tarif und Quellen anzusehen.</p>
          <ul className={styles.municipalityList}>{ordered.map(result => <li key={result.municipality_id}>
            <button className={result.municipality_id === selected?.municipality_id ? styles.selectedRow : ""}
              aria-pressed={result.municipality_id === selected?.municipality_id} onClick={() => selectMunicipality(result.municipality_id)}>
              <i className={styles.citySwatch} style={{ backgroundColor: feeColor(result) }} aria-hidden="true" />
              <span className={styles.cityName}>{result.municipality}<small>{result.booked_weekly_minutes === null ? "Weitere Angabe oder Klärung erforderlich" : formatHours(result.booked_weekly_minutes) + " / Woche insgesamt gebucht"}</small></span>
              <strong>{formatMoney(result.monthly_equivalent_cents)}</strong><span className={styles.rowArrow} aria-hidden="true">↗</span>
            </button>
          </li>)}</ul>
        </section>
        <section className={styles.methodCard} id="grundlage" aria-labelledby="method-heading">
          <div><span className={styles.eyebrow}>TRANSPARENT VERGLEICHEN</span><h2 id="method-heading">Was steckt in den Zahlen?</h2><p>Gemeinden rechnen unterschiedlich ab. Der Vergleich erhält die tatsächlichen Tarife und macht ihren Zahlungsrhythmus vergleichbar.</p></div>
          <div className={styles.methodExplanation}><strong>Summe der jährlichen Kinderbeiträge ÷ 12</strong><p>Für jedes betreute Kind wird der Monatsbeitrag mit seinen Beitragsmonaten multipliziert. Die Jahresbeiträge werden addiert und durch zwölf geteilt. So werden elf und zwölf Beitragsmonate vergleichbar. Der am Stichtag geltende Tarif wird dafür konstant gehalten. Das Ergebnis ist keine tatsächliche Kalenderjahresabrechnung.</p><p>Essen, Zusatzkosten und zusätzliche Buchungsstunden bleiben separat sichtbar. Verglichen werden kommunale Gebühren für städtische Betreuung.</p></div>
        </section>
        <footer className={styles.footer}>
          <div><strong>Kita-Kosten · Region Stuttgart</strong><span>Tarifstichtag {formatDate(profile.as_of)} · Offizielle kommunale Quellen</span></div>
          <p>Kartendaten © <a href={data.bundle.geography.attribution_url} target="_blank" rel="noreferrer">BKG</a> {data.bundle.geography.retrieved_at.slice(0, 4)} · <a href={data.bundle.geography.license_url} target="_blank" rel="noreferrer">dl-de/by-2-0</a> · Grenzen vereinfacht<br />
            Stand {formatDate(data.bundle.geography.boundary_status_date)} · <a href={data.bundle.geography.product_url} target="_blank" rel="noreferrer">Datenprodukt</a> · <a href={data.bundle.geography.data_sources_url} target="_blank" rel="noreferrer">Datenquellen</a> · <a href={import.meta.env.BASE_URL + "THIRD_PARTY_NOTICES.txt"}>Softwarelizenzen</a></p>
        </footer>
      </>}
    </main>
  </>;
}
