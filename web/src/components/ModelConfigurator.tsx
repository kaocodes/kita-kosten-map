import type { ModelCatalog, ModelSelection } from "../domain/model-family.js";
import { formatMoney } from "../site/presentation.js";
import styles from "./ModelConfigurator.module.css";

interface Props { selection: ModelSelection; catalog: ModelCatalog; onChange: (selection: ModelSelection) => void }

export function ModelConfigurator({ selection, catalog, onChange }: Props) {
  function resize(count: number) {
    onChange({ ...selection, children: Array.from({ length: count }, (_, index) => selection.children[index] ?? { category: "home", daily_minutes: 480 }) });
  }
  return <section className={styles.card} aria-labelledby="model-heading">
    <div className={styles.heading}><div><span className={styles.kicker}>DEINE VERGLEICHSFAMILIE</span><h2 id="model-heading">Eine Modellfamilie, die zu dir passt.</h2>
      <p>Wenige Auswahlen. Gleiche Annahmen in jeder Kommune.</p></div>
      <button type="button" onClick={() => onChange(structuredClone(catalog.default))}>Standard wiederherstellen</button></div>
    <div className={styles.fields}>
      <label><span>Haushaltskonstellation</span><select value={selection.household} onChange={event => onChange({ ...selection, household: event.target.value as ModelSelection["household"] })}>
        <option value="couple">Zwei zusammenlebende Eltern</option><option value="single">Alleinerziehend</option></select></label>
      <label><span>Anzahl Kinder im Haushalt</span><select value={selection.children.length} onChange={event => resize(Number(event.target.value))}>
        {Array.from({ length: catalog.max_children }, (_, index) => <option value={index + 1} key={index}>{index + 1} {index === 0 ? "Kind" : "Kinder"}</option>)}</select></label>
      <label><span>Haushaltsbrutto pro Jahr · Modellszenario</span><select value={selection.income_id} onChange={event => onChange({ ...selection, income_id: event.target.value })}>
        {catalog.income_scenarios.map(scenario => <option value={scenario.id} key={scenario.id}>{formatMoney(scenario.gross_annual_cents).replace(",00", "")}</option>)}</select></label>
    </div>
    <div className={styles.children}>{selection.children.map((child, index) => {
      const definition = catalog.categories.find(item => item.id === child.category)!;
      function change(values: Partial<typeof child>) { onChange({ ...selection, children: selection.children.map((item, position) => position === index ? { ...item, ...values } : item) }); }
      return <fieldset key={index}><legend>Kind {index + 1}</legend>
        <label><span>Kategorie für Kind {index + 1}</span><select value={child.category} onChange={event => change({ category: event.target.value as typeof child.category })}>
          {catalog.categories.map(item => <option value={item.id} key={item.id}>{item.label}</option>)}</select></label>
        <p>{definition.description}</p>
        {definition.care_enabled ? <label><span>Betreuungsbedarf für Kind {index + 1}</span><select value={child.daily_minutes} onChange={event => change({ daily_minutes: Number(event.target.value) as 360 | 480 })}>
          {catalog.care_options.map(item => <option value={item.minutes} key={item.minutes}>{item.label}</option>)}</select><small>Montag bis Freitag, durchgehend</small></label>
          : <div className={styles.noCare}>Keine Kita-Kosten · als Geschwisterkind berücksichtigt</div>}
      </fieldset>;
    })}</div>
    <p className={styles.notice}>Modellvergleich mit festen örtlichen Einkommensannahmen. Der persönliche Beitrag kann abweichen. Alle Angaben bleiben in diesem Browserfenster.</p>
    <details className={styles.assumptions}><summary>Modellannahmen und Einkommenswerte ansehen</summary>
      <ul>{catalog.assumptions.map(item => <li key={item}>{item}</li>)}</ul>
      <p>Modellalter: Krippe 2 Jahre, Kindergarten 4 Jahre, Schulkind 8 Jahre, zu Hause betreut 2 Jahre. Schulkinder besuchen im Modell keine kostenpflichtige Schulbetreuung.</p>
      <p>{catalog.income_scenarios.find(item => item.id === selection.income_id)!.assumption}</p>
      <div className={styles.tableWrap}><table><caption>Fest hinterlegte Jahreseinkommen in Euro · gewähltes Szenario hervorgehoben</caption>
        <thead><tr><th>Haushaltsbrutto</th><th>Ditzingen: örtlicher Wert</th><th>Esslingen: örtliches Brutto</th><th>Korntal: bereinigter Wert</th></tr></thead>
        <tbody>{catalog.income_scenarios.map(item => <tr key={item.id} className={item.id === selection.income_id ? styles.selected : ""}>
          <th scope="row">{formatMoney(item.gross_annual_cents)}</th>{["taxable_income", "esslingen_gross_income", "adjusted_taxable_income"].map(basis => <td key={basis}>{formatMoney(item.incomes.find(entry => entry.basis === basis)!.amount_cents)}</td>)}
        </tr>)}</tbody></table></div>
      <p>Die steuerlich bezeichneten Modellwerte sind eigenständige Vergleichsannahmen und keine aus persönlichen Daten ermittelte Steuerberechnung. Ditzingens Tabellenbezeichnung wird nach der örtlichen Definition in § 7 verstanden. Für die Monatstabelle in Korntal wird ausschließlich derselbe Jahreswert durch zwölf geteilt.</p>
    </details>
  </section>;
}
