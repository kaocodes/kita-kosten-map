import { useEffect, useRef } from "react";
import L from "leaflet";
import type { ComparisonResult } from "../domain/index.js";
import type { MunicipalGeometry } from "../site/data.js";
import { feeColor, formatMoney } from "../site/presentation.js";
import styles from "./MunicipalityMap.module.css";

interface Props {
  geometry: MunicipalGeometry;
  results: ComparisonResult[];
  selectedId: string;
  maxZoom: number;
  attribution: { attribution_url: string; license_url: string; retrieved_at: string };
  onSelect: (id: string) => void;
}

export function MunicipalityMap({ geometry, results, selectedId, maxZoom, attribution, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const bounds = useRef<L.LatLngBounds | null>(null);
  const polygons = useRef(new Map<string, L.Path>());
  const labels = useRef(new Map<string, L.Marker>());
  const currentResults = useRef(new Map(results.map(result => [result.municipality_id, result])));
  const currentSelection = useRef(selectedId);
  const select = useRef(onSelect);
  const updateLabels = useRef(() => {});
  currentResults.current = new Map(results.map(result => [result.municipality_id, result]));
  currentSelection.current = selectedId;
  select.current = onSelect;

  useEffect(() => {
    const instance = L.map(container.current!, {
      zoomControl: false, attributionControl: false, scrollWheelZoom: false,
      minZoom: 8, maxZoom, zoomSnap: 0.25, zoomDelta: 0.5,
    });
    map.current = instance;
    L.control.zoom({ position: "topright", zoomInTitle: "Vergrößern", zoomOutTitle: "Verkleinern" }).addTo(instance);
    const context = { ...geometry, features: geometry.features.filter(feature => feature.properties.municipality_id === null) };
    L.geoJSON(context, { interactive: false, style: { color: "#e0e5dd", weight: 0.8, fillColor: "#f1f3ee", fillOpacity: 1 } }).addTo(instance);
    const compared = { ...geometry, features: geometry.features.filter(feature => feature.properties.municipality_id !== null) };
    const selectedLayer = L.geoJSON(compared, {
      style: feature => ({ color: "#fff", weight: 1.8, fillColor: feeColor(currentResults.current.get(feature!.properties.municipality_id)), fillOpacity: 1 }),
      onEachFeature(feature, layer) {
        const id = feature.properties.municipality_id;
        const path = layer as L.Path;
        polygons.current.set(id, path);
        layer.on("click", () => select.current(id));
        const point = feature.properties.label_point as [number, number];
        const label = document.createElement("span");
        label.textContent = feature.properties.name;
        label.className = styles.label;
        label.setAttribute("aria-hidden", "true");
        const marker = L.marker([point[1], point[0]], { interactive: false, keyboard: false,
          icon: L.divIcon({ html: label, className: styles.labelMarker, iconSize: [0, 0] }),
        }).addTo(instance);
        labels.current.set(id, marker);
        const tooltip = document.createElement("span");
        layer.bindTooltip(tooltip, { direction: "top", className: styles.tooltip });
        layer.on("tooltipopen", () => {
          tooltip.textContent = `${feature.properties.name} · ${formatMoney(currentResults.current.get(id)?.monthly_equivalent_cents ?? null)}`;
        });
      },
    }).addTo(instance);
    bounds.current = selectedLayer.getBounds();
    const fit = () => instance.fitBounds(bounds.current!, { padding: [30, 30], animate: false });
    fit();
    selectedLayer.eachLayer(layer => {
      const path = layer as L.Path & { feature?: { properties: { municipality_id: string; name: string } } };
      const element = path.getElement();
      if (!element || !path.feature) return;
      const id = path.feature.properties.municipality_id;
      element.setAttribute("tabindex", "0");
      element.setAttribute("role", "button");
      element.addEventListener("keydown", event => {
        const key = (event as KeyboardEvent).key;
        if (key === "Enter" || key === " ") { event.preventDefault(); select.current(id); }
      });
    });
    // Keep municipal labels legible without relying on a fixed list or manual label positions.
    updateLabels.current = () => {
      const accepted: { left: number; top: number; right: number; bottom: number }[] = [];
      const ordered = [...labels.current.entries()].sort(([first], [second]) =>
        Number(second === currentSelection.current) - Number(first === currentSelection.current));
      for (const [id, marker] of ordered) {
        const element = marker.getElement();
        if (!element) continue;
        const point = instance.latLngToContainerPoint(marker.getLatLng());
        const name = currentResults.current.get(id)?.municipality ?? "";
        const width = Math.max(55, name.length * 6 + 15);
        const box = { left: point.x - width / 2, right: point.x + width / 2, top: point.y - 13, bottom: point.y + 13 };
        const collision = accepted.some(other => box.left < other.right && box.right > other.left && box.top < other.bottom && box.bottom > other.top);
        const visible = !collision || id === currentSelection.current;
        element.style.visibility = visible ? "visible" : "hidden";
        element.classList.toggle(styles.selectedLabel, id === currentSelection.current);
        if (visible) accepted.push(box);
      }
    };
    instance.on("zoomend moveend resize", () => updateLabels.current());
    updateLabels.current();
    const observer = new ResizeObserver(() => {
      instance.invalidateSize({ pan: false });
      fit();
    });
    observer.observe(container.current!);
    return () => {
      observer.disconnect();
      instance.remove();
      polygons.current.clear(); labels.current.clear(); map.current = null;
    };
  }, [geometry, maxZoom]);

  useEffect(() => {
    for (const [id, polygon] of polygons.current) {
      const result = currentResults.current.get(id);
      const selected = id === selectedId;
      polygon.setStyle({ fillColor: feeColor(result), color: selected ? "#173f31" : "#ffffff", weight: selected ? 3 : 1.8 });
      const element = polygon.getElement();
      element?.setAttribute("aria-label", `${result?.municipality ?? id}: ${formatMoney(result?.monthly_equivalent_cents ?? null)} pro Monat`);
      element?.setAttribute("aria-pressed", String(selected));
      const tooltip = polygon.getTooltip()?.getContent();
      if (tooltip instanceof HTMLElement && result) tooltip.textContent = `${result.municipality} · ${formatMoney(result.monthly_equivalent_cents)}`;
      if (selected) polygon.bringToFront();
    }
    updateLabels.current();
  }, [results, selectedId, geometry]);

  return <div className={styles.frame}>
    <div className={styles.map} ref={container} role="region" aria-label="Gemeindekarte mit Kita-Gebühren" />
    <button className={styles.reset} onClick={() => {
      if (map.current && bounds.current) map.current.fitBounds(bounds.current, { padding: [30, 30] });
    }}>
      <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 3H3v4m10-4h4v4M3 13v4h4m10-4v4h-4M8 10h4m-2-2v4" /></svg>
      Region anzeigen
    </button>
    <div className={styles.mapNote}>
      <span>Gemeindegebiete · Umgebung ohne Vergleichsdaten</span>
      <span>Grenzen © <a href={attribution.attribution_url} target="_blank" rel="noreferrer">BKG</a> {attribution.retrieved_at.slice(0, 4)} · <a href={attribution.license_url} target="_blank" rel="noreferrer">dl-de/by-2-0</a> · vereinfacht</span>
    </div>
  </div>;
}
