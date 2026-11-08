import { passRequirements } from "../domain/index.js";
import type { MunicipalityCatalog, Registry } from "../domain/index.js";
import { emptyLocal, INCOME_FIELDS, localIncomeFields, newChild, selectTargetChild } from "../site/personal-profile.js";
import type { IncomeField, LocalDraft, PersonalDraft } from "../site/personal-profile.js";
import styles from "./FamilyForm.module.css";

interface Props {
  draft: PersonalDraft; errors: Record<string, string>; tariffs: MunicipalityCatalog[]; registry: Registry;
  selectedId: string; onChange: (draft: PersonalDraft) => void; onSelect: (id: string) => void; onReset: () => void;
}
const days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];
const passLabels: Record<string, string> = {
  none: "Kein Pass", family_card: "FamilienCard", social_card: "Sozialpass", city_pass: "Stadtpass",
  city_pass_a: "Stadtpass A", city_pass_b: "Stadtpass B", city_pass_c: "Stadtpass C",
};
const ruleLabels: Record<string, string> = {
  family_pass: "Familienpass-Ermäßigung", social_reduction: "Sozialermäßigung",
  income_reduction: "Einkommensabhängige Ermäßigung", social_income_ratio: "Bewilligte Sozialermäßigung",
};
const eligibilityLabels: Record<string, string> = {
  valid_family_card: "Eine gültige FamilienCard liegt vor.", valid_social_card: "Ein gültiger Sozialpass liegt vor.",
  valid_city_pass: "Ein gültiger Stadtpass dieser Stufe liegt vor.", family_pass: "Ein gültiger Familienpass liegt vor.",
  priority_benefits_denied: "Vorrangige Sozialleistungen wurden geprüft und abgelehnt.",
  no_priority_benefit: "Es besteht kein vorrangiger Leistungsanspruch gemäß örtlicher Regelung.",
  approved_social_reduction: "Die Stadt hat die Sozialermäßigung bewilligt.", resident: "Die Wohnsitzvoraussetzung der Stadt ist erfüllt.",
};
function toggle(values: string[], value: string): string[] { return values.includes(value) ? values.filter(item => item !== value) : [...values, value]; }

export function FamilyForm({ draft, errors, tariffs, registry, selectedId, onChange, onSelect, onReset }: Props) {
  const active = registry.municipalities.filter(item => item.active);
  const municipality = active.find(item => item.id === selectedId) ?? active[0];
  const city = tariffs.find(item => item.id === municipality.tariff_id)!;
  const local = draft.local[municipality.id] ?? emptyLocal();
  const passes = [...new Set(["none", ...city.prices.map(price => price.selectors?.pass_id ?? "none")])];
  const rules = city.rules.filter(rule => rule.execution_status === "supported");
  const conditions = [...new Set([...passRequirements(city, local.passId), ...rules.filter(rule => local.rules.includes(rule.id)).flatMap(rule => rule.requires ?? [])])];
  function updateLocal(next: LocalDraft) { onChange({ ...draft, local: { ...draft.local, [municipality.id]: next } }); }
  function fieldError(id: string) { return errors[id] ? <span id={id + "-error"} className={styles.error}>{errors[id]}</span> : null; }
  function inputProps(id: string) { return { id, "aria-invalid": !!errors[id], "aria-describedby": errors[id] ? id + "-error" : undefined }; }
  function incomeInput(field: IncomeField, values: Record<string, string>, prefix: string, change: (values: Record<string, string>) => void) {
    const id = prefix + field.basis;
    return <label className={styles.field} key={id} htmlFor={id}><span>{field.label}</span>
      <input {...inputProps(id)} type="text" inputMode="decimal" placeholder="Noch nicht angegeben" value={values[field.basis] ?? ""}
        aria-describedby={`${id}-help${errors[id] ? ` ${id}-error` : ""}`} onChange={event => change({ ...values, [field.basis]: event.target.value })} />
      <small id={id + "-help"}>{field.help}</small>{fieldError(id)}</label>;
  }
  const target = draft.children[draft.targetChild];
  return <section className={styles.form} aria-labelledby="family-heading">
    <div className={styles.heading}><div><h2 id="family-heading">Deine Familie, dein Betreuungsbedarf</h2><p>Familie und Zeiten sind vorbelegt. Einkommen und Berechtigungen bitte selbst angeben. Alle Angaben beziehen sich auf den Tarifstichtag.</p></div>
      <button type="button" onClick={onReset}>Modellfamilie wiederherstellen</button></div>
    <p className={styles.privacy}>Die Eingaben bleiben in diesem Browserfenster. Sie werden weder gespeichert noch an einen Server gesendet.</p>
    <a className={styles.resultsLink} href="#vergleich">Zu Karte und Vergleichsergebnissen ↓</a>
    {Object.keys(errors).length > 0 && <div className={styles.errorSummary} role="alert"><strong>Bitte die markierten Eingaben prüfen.</strong> Bis dahin werden keine Gebühren angezeigt.
      <ul>{Object.entries(errors).map(([id, message]) => <li key={id}><a href={"#" + id}>{message}</a></li>)}</ul></div>}
    <fieldset id="family"><legend>1 · Familie und zu vergleichendes Kind</legend>
      <div className={styles.grid}><label className={styles.field}><span>Eltern im Haushalt</span><select value={draft.household} onChange={event => onChange({ ...draft, household: event.target.value as PersonalDraft["household"] })}>
        <option value="together">Zwei zusammenlebende Eltern</option><option value="single">Alleinerziehend</option><option value="separate">Getrennt lebend, nicht alleinerziehend</option></select></label>
        <label className={styles.field}><span>Gebühren berechnen für</span><select value={draft.targetChild} onChange={event => onChange(selectTargetChild(draft, Number(event.target.value)))}>
          {draft.children.map((_, index) => <option key={index} value={index}>Kind {index + 1}</option>)}</select></label></div>
      <p>Alle zu berücksichtigenden Kinder erfassen, auch ältere Geschwister. Die Stadt bestimmt anhand ihrer Gebührenordnung, welche Kinder mitzählen.</p>
      <div className={styles.children}>{draft.children.map((child, index) => {
        function change(values: Partial<typeof child>) { onChange({ ...draft, children: draft.children.map((entry, position) => position === index ? { ...entry, ...values } : entry) }); }
        return <fieldset className={styles.child} key={index}><legend>Kind {index + 1}{index === draft.targetChild ? " · Vergleichskind" : ""}</legend>
          <div className={styles.grid}><label className={styles.field}><span>Alter: volle Jahre</span><input {...inputProps(`child-${index}-years`)} type="text" inputMode="numeric" value={child.years} onChange={event => change({ years: event.target.value })} />{fieldError(`child-${index}-years`)}</label>
            <label className={styles.field}><span>Zusätzliche Monate (0–11)</span><input {...inputProps(`child-${index}-months`)} type="text" inputMode="numeric" value={child.months} onChange={event => change({ months: event.target.value })} />{fieldError(`child-${index}-months`)}</label></div>
          <label className={styles.check}><input type="checkbox" checked={child.resident} onChange={event => change({ resident: event.target.checked })} />Lebt im Haushalt</label>
          <label className={styles.check}><input type="checkbox" checked={child.childBenefit} onChange={event => change({ childBenefit: event.target.checked })} />Kindergeldberechtigung besteht</label>
          {draft.children.length > 1 && <button type="button" className={styles.textButton} onClick={() => onChange({ ...draft,
            children: draft.children.filter((_, position) => position !== index), targetChild: index === draft.targetChild ? 0 : draft.targetChild - Number(index < draft.targetChild),
            ...(index === draft.targetChild ? { careRank: "", schoolEntry: false } : {}) })}>Kind {index + 1} entfernen</button>}
        </fieldset>;
      })}</div>
      <button type="button" onClick={() => onChange({ ...draft, children: [...draft.children, newChild()] })}>Weiteres Kind hinzufügen</button>
      <label className={styles.check}><input type="checkbox" checked={draft.schoolEntry} onChange={event => onChange({ ...draft, schoolEntry: event.target.checked })} />Das Vergleichskind ist bereits eingeschult</label>
      {draft.schoolEntry && <p>Schulkinder liegen außerhalb dieses Krippen- und Kindergartenvergleichs.</p>}
      {target && Number(target.years) * 12 + Number(target.months) === 36 && <label className={styles.field}><span>Hat das Vergleichskind im Monat des Tarifstichtags seinen 3. Geburtstag?</span>
        <select value={target.birthdayMonth} onChange={event => onChange({ ...draft, children: draft.children.map((child, index) => index === draft.targetChild ? { ...child, birthdayMonth: event.target.value as typeof child.birthdayMonth } : child) })}>
          <option value="unknown">Noch nicht angegeben</option><option value="yes">Ja</option><option value="no">Nein</option></select><small>Für Städte mit Tarifwechsel im Folgemonat erforderlich.</small></label>}
      <label className={styles.field}><span>Sindelfingen: Betreuungsrang im städtischen System</span><input {...inputProps("care-rank")} type="text" inputMode="numeric" placeholder="Noch nicht angegeben" value={draft.careRank} onChange={event => onChange({ ...draft, careRank: event.target.value })} />
        <small>1 für das erste, 2 für das zweite gleichzeitig betreute Kind usw. Dieser Rang ist unabhängig von der Zahl aller Geschwister.</small>{fieldError("care-rank")}</label>
    </fieldset>
    <fieldset><legend>2 · Durchgehende Betreuung pro Tag</legend><p>Stunden je Wochentag, z. B. 7,5. Leer oder 0 bedeutet kein Bedarf. Gewählt wird ein belegtes Paket, das jeden Tag abdeckt; zusätzliche Buchungszeit bleibt sichtbar.</p>
      <div className={styles.days}>{days.map((day, index) => <label className={styles.field} key={day}><span>{day} (Std.)</span><input {...inputProps(`hours-${index}`)} type="text" inputMode="decimal" value={draft.hours[index]} onChange={event => onChange({ ...draft, hours: draft.hours.map((value, position) => position === index ? event.target.value : value) })} />{fieldError(`hours-${index}`)}</label>)}</div>
    </fieldset>
    <fieldset id="personal-incomes"><legend>3 · Einkommen nach örtlicher Definition</legend><p>Alle Beträge in Euro. Leer bleibt unbekannt; 0 ist ein bestätigtes Nulleinkommen. Ohne erforderliche Einkommensangabe bleibt die jeweilige Stadt unberechenbar. Brutto und steuerliches Einkommen werden nicht ineinander umgerechnet.</p>
      <div className={styles.grid}>{INCOME_FIELDS.map(field => incomeInput(field, draft.incomes, "income-", values => onChange({ ...draft, incomes: values })))}</div>
    </fieldset>
    <details className={styles.local}><summary>4 · Örtliche Pässe und Ermäßigungen (optional)</summary>
      <p>Nur bestätigte Berechtigungen auswählen. Angaben gelten ausschließlich für die gewählte Stadt. Unbestätigte Voraussetzungen führen dort zu einem fehlenden Ergebnis.</p>
      <label className={styles.field}><span>Ermäßigung bearbeiten für</span><select value={municipality.id} onChange={event => onSelect(event.target.value)}>{active.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {passes.length > 1 && <label className={styles.field}><span>Örtlicher Pass in {municipality.name}</span><select value={local.passId} onChange={event => updateLocal({ ...local, passId: event.target.value, eligibility: [] })}>{passes.map(pass => <option key={pass} value={pass}>{passLabels[pass] ?? pass}</option>)}</select></label>}
      {rules.map(rule => <label className={styles.check} key={rule.id}><input type="checkbox" checked={local.rules.includes(rule.id)} onChange={() => updateLocal({ ...local, rules: toggle(local.rules, rule.id), eligibility: [] })} />{ruleLabels[rule.id] ?? "Örtliche Ermäßigung"}</label>)}
      {passes.length === 1 && rules.length === 0 && <p>Für diese Stadt ist keine zusätzliche, im Rechenkern ausführbare Ermäßigung hinterlegt.</p>}
      {conditions.length > 0 && <fieldset><legend>Voraussetzungen ausdrücklich bestätigen</legend>{conditions.map(condition => <label className={styles.check} key={condition}><input type="checkbox" checked={local.eligibility.includes(condition)} onChange={() => updateLocal({ ...local, eligibility: toggle(local.eligibility, condition) })} />{eligibilityLabels[condition] ?? "Örtliche Voraussetzung bestätigt"}</label>)}</fieldset>}
      {localIncomeFields(city, local.rules).map(field => incomeInput(field, local.incomes, `local-${municipality.id}-`, values => updateLocal({ ...local, incomes: values })))}
      <p>Definitionen und Voraussetzungen bitte anhand der offiziellen Quellen in den Gemeindedetails prüfen. Eine Berechtigung wird nicht aus dem Einkommen abgeleitet.</p>
    </details>
    <a className={styles.resultsLink} href="#vergleich">Vergleichsergebnisse ansehen ↓</a>
  </section>;
}
