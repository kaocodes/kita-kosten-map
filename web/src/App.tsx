import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { compareMunicipalities } from "./domain/index.js";
import { createPersonalDraft, personalResults } from "./site/personal-profile.js";
import type { PersonalDraft } from "./site/personal-profile.js";
import { FEATURES } from "./site/features.js";
import { MunicipalityMap } from "./components/MunicipalityMap.js";
import { MunicipalityDetails } from "./components/MunicipalityDetails.js";
import { loadSiteData } from "./site/data.js";
import type { SiteData } from "./site/data.js";
import { FEE_BANDS, MISSING_COLOR, feeColor, formatDate, formatHours, formatMoney } from "./site/presentation.js";
import styles from "./App.module.css";

const FamilyForm = lazy(() => import("./components/FamilyForm.js").then(module => ({ default: module.FamilyForm })));

function MapMark() {
  return <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" /></svg>;
}

export function App() {
  const [data, setData] = useState<SiteData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [profileName, setProfileName] = useState<"default" | "highest_band" | "personal">("default");
  const [personalDraft, setPersonalDraft] = useState<PersonalDraft | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    loadSiteData(controller.signal).then(setData).catch(error => {
      if (!controller.signal.aborted) { console.error("Unable to initialize the comparison", error); setError(true); }
    });
    return () => controller.abort();
  }, [attempt]);
  const personal = useMemo(() => data && personalDraft
    ? personalResults(data.bundle.profiles.default, personalDraft, data.bundle.tariffs, data.bundle.registry) : null, [data, personalDraft]);
  const profile = data ? profileName === "personal" ? personal?.profile ?? data.bundle.profiles.default : data.bundle.profiles[profileName] : null;
  const results = useMemo(() => data && profile
    ? profileName === "personal" ? personal?.results ?? [] : compareMunicipalities(data.bundle.tariffs, profile, data.bundle.registry)
    : [], [data, profile, profileName, personal]);
  function enterPersonal() {
    if (data && !personalDraft) setPersonalDraft(createPersonalDraft(data.bundle.profiles.default));
    setProfileName("personal");
  }
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
        <section className={styles.profileCard} aria-label="Vergleichsprofil">
          <div className={styles.profileTitle}><span className={styles.profileIcon} aria-hidden="true">↔</span><div><strong>Gleiche Familie. Gleicher Bedarf.</strong><span>Die Kommune macht den Unterschied.</span></div></div>
          {(FEATURES.personalProfiles || FEATURES.highestBandReference) && <fieldset className={styles.profileSwitch}>
            <legend className={styles.visuallyHidden}>Vergleichsprofil wählen</legend>
            <label><input type="radio" name="profile" value="default" checked={profileName === "default"} onChange={() => setProfileName("default")} /><span>Modellfamilie</span></label>
            {FEATURES.highestBandReference && <label><input type="radio" name="profile" value="highest_band" checked={profileName === "highest_band"} onChange={() => setProfileName("highest_band")} /><span>Höchsttarif</span></label>}
            {FEATURES.personalProfiles && <label><input type="radio" name="profile" value="personal" checked={profileName === "personal"} onChange={enterPersonal} /><span>Eigene Familie</span></label>}
          </fieldset>}
          {profileName !== "personal" && <><div className={styles.profileFacts}><span><strong>1 Kind, 2 Jahre</strong>Krippenbetreuung</span><span><strong>Mo–Fr, mind. 8 Std.</strong>Durchgehend pro Tag</span><span><strong>{profileName === "default" ? "80.000 € Brutto / Jahr" : "Höchste Einkommensstufe"}</strong>{profileName === "default" ? "60.000 € steuerlich, separat angenommen" : "Ohne Pass- und Sozialermäßigung"}</span></div>
          <details className={styles.assumptions}><summary>Vergleichsannahmen ansehen</summary>
            <p>{profileName === "default"
              ? "Zwei zusammenlebende Eltern, ein zweijähriges Kind ohne Geschwister. 80.000 € Haushaltsbrutto und unabhängig angenommene 60.000 € zu versteuerndes Einkommen. Keine weiteren Einkünfte oder Vermietungsverluste; unverändertes Einkommen im Vorjahr und laufenden Jahr. Für Esslingen sind ausdrücklich 80.000 € nach örtlicher Einkommensdefinition angesetzt, ohne optionalen Arbeitnehmer-Pauschbetrag. Korntal-Münchingen verwendet 60.000 € bereinigtes steuerliches Jahreseinkommen. Das sind Modellannahmen, keine steuerliche Umrechnung und kein statistischer Durchschnittshaushalt."
              : "Ein zweijähriges Kind ohne Geschwister, höchste reguläre Einkommensstufe. Pässe und zusätzliche Sozialermäßigungen sind nicht berücksichtigt. Dieses Profil ist eine Vollzahlerreferenz und kein durchschnittlicher Haushalt."}</p>
            <p>Gewählt wird das kleinste belegte Paket, das an jedem Wochentag mindestens acht Stunden durchgehende Betreuung abdeckt. Ein veröffentlichtes Angebot garantiert keinen freien Platz.</p>
          </details></>}
          {FEATURES.personalProfiles && profileName === "personal" && personalDraft && personal && <details open className={styles.personalPanel}>
            <summary>Eigene Angaben bearbeiten <span>{personalDraft.children.length} {personalDraft.children.length === 1 ? "Kind" : "Kinder"} · {comparable.length} von {results.length} Kommunen berechenbar</span></summary>
            <Suspense fallback={<p role="status">Familienformular wird geladen …</p>}><FamilyForm draft={personalDraft} errors={personal.errors}
            tariffs={data.bundle.tariffs} registry={data.bundle.registry} selectedId={selected?.municipality_id ?? ""}
            onChange={setPersonalDraft} onSelect={setSelectedId} onReset={() => {
              setPersonalDraft(createPersonalDraft(data.bundle.profiles.default)); setProfileName("default");
            }} /></Suspense></details>}
        </section>
        <p className={styles.resultStatus} role="status">{comparable.length} von {results.length} Kommunen berechenbar.
          {profileName === "personal" && " Fehlende Angaben werden nicht durch Modellwerte ersetzt. Preise aktualisieren sich bei jeder Eingabe."}</p>
        <div className={styles.workspace} id="vergleich">
          <section className={styles.mapCard} aria-labelledby="map-heading">
            <div className={styles.cardHeading}><div><span className={styles.eyebrow}>DIE REGION AUF EINEN BLICK</span><h2 id="map-heading">Wo liegen die Gebühren?</h2></div><span className={styles.countBadge}>{results.length} Kommunen</span></div>
            <MunicipalityMap geometry={data.geometry} results={results} selectedId={selected?.municipality_id ?? ""}
              maxZoom={data.bundle.geography.max_zoom} attribution={data.bundle.geography} onSelect={selectMunicipality} />
            <div className={styles.legend} aria-label="Gebührenlegende">
              <div className={styles.legendHeading}><strong>Betreuung pro Monat</strong><span>Auf zwölf Monate umgelegt</span></div>
              <div className={styles.legendBands}>{FEE_BANDS.map(band => <span key={band.label}><i style={{ backgroundColor: band.color }} />{band.label}</span>)}</div>
              <span className={styles.missingLegend}><i style={{ backgroundColor: MISSING_COLOR }} />Fehlend oder nicht eindeutig berechenbar</span>
            </div>
          </section>
          {selected && <MunicipalityDetails result={selected} tariff={data.bundle.tariffs.find(tariff => tariff.id === selected.tariff_id)!} sources={data.bundle.sources} profile={profileName === "personal" ? personal?.profile ?? null : profile} personal={profileName === "personal"} />}
        </div>
        <section className={styles.comparisonCard} aria-labelledby="list-heading">
          <div className={styles.listHeading}><div><span className={styles.eyebrow}>ALLE KOMMUNEN IM VERGLEICH</span><h2 id="list-heading">Ein Bedarf, unterschiedliche Beiträge.</h2></div>
            <p>{min === null ? "Noch keine Vergleichswerte" : `${formatMoney(min)} – ${formatMoney(max)}`}<small>Monatliches Betreuungsäquivalent</small></p>
          </div>
          <p className={styles.listNote}>Nach Monatsäquivalent aufsteigend. Eine Kommune auswählen, um Tarif und Quellen anzusehen.</p>
          <ul className={styles.municipalityList}>{ordered.map(result => <li key={result.municipality_id}>
            <button className={result.municipality_id === selected?.municipality_id ? styles.selectedRow : ""}
              aria-pressed={result.municipality_id === selected?.municipality_id} onClick={() => selectMunicipality(result.municipality_id)}>
              <i className={styles.citySwatch} style={{ backgroundColor: feeColor(result) }} aria-hidden="true" />
              <span className={styles.cityName}>{result.municipality}<small>{result.booked_weekly_minutes === null ? "Weitere Angabe oder Klärung erforderlich" : formatHours(result.booked_weekly_minutes) + " / Woche gebucht"}</small></span>
              <strong>{formatMoney(result.monthly_equivalent_cents)}</strong><span className={styles.rowArrow} aria-hidden="true">↗</span>
            </button>
          </li>)}</ul>
        </section>
        <section className={styles.methodCard} id="grundlage" aria-labelledby="method-heading">
          <div><span className={styles.eyebrow}>TRANSPARENT VERGLEICHEN</span><h2 id="method-heading">Was steckt in den Zahlen?</h2><p>Gemeinden rechnen unterschiedlich ab. Der Vergleich erhält die tatsächlichen Tarife und macht ihren Zahlungsrhythmus vergleichbar.</p></div>
          <div className={styles.methodExplanation}><strong>Monatsbeitrag × Beitragsmonate ÷ 12</strong><p>So werden beispielsweise elf und zwölf Beitragsmonate vergleichbar. Der am Stichtag geltende Tarif wird dafür konstant gehalten. Das Ergebnis ist keine tatsächliche Kalenderjahresabrechnung.</p><p>Essen, Zusatzkosten und zusätzliche Buchungsstunden bleiben separat sichtbar. Verglichen werden kommunale Gebühren für städtische Betreuung.</p></div>
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
