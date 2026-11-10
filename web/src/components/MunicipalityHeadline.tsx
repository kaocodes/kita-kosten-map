import { useEffect, useState } from "react";
import styles from "../Atlas.module.css";

interface Props { names: string[] }

export function MunicipalityHeadline({ names }: Props) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(true);
  const labels = names.length ? names : ["deiner Kommune"];
  const currentName = labels[index % labels.length];

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(preference.matches);
    update();
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (paused || reducedMotion || names.length < 2) return;
    const timer = window.setInterval(() => {
      if (!document.hidden) setIndex(previous => (previous + 1) % names.length);
    }, 3500);
    return () => window.clearInterval(timer);
  }, [paused, reducedMotion, names.length]);

  return <>
    <h1 id="page-title">
      <span className={styles.headlineQuestion}>Was kostet ein Kita-Platz in</span>{" "}
      <span className={styles.headlineTrack} aria-hidden="true">
        {labels.map(name => <span className={styles.headlineMeasure} key={name}>
          <span className={styles.headlineHighlight}>{name}</span><span>?</span>
        </span>)}
        <span className={styles.headlineWord} data-current-municipality={currentName} key={currentName}>
          <span className={styles.headlineHighlight}>{currentName}</span><span>?</span>
        </span>
      </span>
      <span className={styles.visuallyHidden}>deiner Kommune?</span>
    </h1>
    <div className={styles.introCaption}>
      <p className={styles.lead}>Die gleiche Berechnungsgrundlage in jeder Kommune.</p>
      {names.length > 1 && !reducedMotion && <button className={styles.headlinePause} type="button"
        aria-pressed={paused} onClick={() => setPaused(value => !value)}>
        Namenwechsel {paused ? "fortsetzen" : "pausieren"}
      </button>}
    </div>
  </>;
}
