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
  const labelAnchors = useRef(new Map<string, L.LatLng>());
  const labelLines = useRef(new Map<string, L.Polyline>());
  const selectionOutline = useRef<L.GeoJSON | null>(null);
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
    const outlinePane = instance.createPane("selection-outline");
    outlinePane.style.zIndex = "450";
    outlinePane.style.pointerEvents = "none";
    const linePane = instance.createPane("label-lines");
    linePane.style.zIndex = "575";
    linePane.style.pointerEvents = "none";
    selectionOutline.current = L.geoJSON(undefined, { pane: "selection-outline", interactive: false,
      style: { color: "#363d4b", weight: 3.5, fill: false, lineJoin: "round" } }).addTo(instance);
    L.control.zoom({ position: "topright", zoomInTitle: "Vergrößern", zoomOutTitle: "Verkleinern" }).addTo(instance);
    const context = { ...geometry, features: geometry.features.filter(feature => feature.properties.municipality_id === null) };
    L.geoJSON(context, { interactive: false, style: { color: "#a3adbf", weight: 0.8, fillColor: "#cbd1dc", fillOpacity: 1 } }).addTo(instance);
    const compared = { ...geometry, features: geometry.features.filter(feature => feature.properties.municipality_id !== null) };
    const selectedLayer = L.geoJSON(compared, {
      style: feature => ({ color: "#fffdf8", weight: 1.8, fillColor: feeColor(currentResults.current.get(feature!.properties.municipality_id)), fillOpacity: 1 }),
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
        const anchor = L.latLng(point[1], point[0]);
        labelAnchors.current.set(id, anchor);
        labelLines.current.set(id, L.polyline([anchor, anchor], { pane: "label-lines", interactive: false,
          color: "#515b70", opacity: 0.65, weight: 1 }).addTo(instance));
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
    // Move colliding labels with short leader lines instead of hiding municipalities.
    updateLabels.current = () => {
      const accepted: { left: number; top: number; right: number; bottom: number }[] = [];
      const size = instance.getSize();
      const offsets = [[0, 0], [0, -28], [0, 28], [-45, 0], [45, 0], [0, -56], [0, 56],
        [-60, -28], [60, -28], [-60, 28], [60, 28], [0, -84], [0, 84], [-95, -56], [95, -56], [-95, 56], [95, 56]];
      const ordered = [...labels.current.entries()].sort(([first], [second]) =>
        Number(second === currentSelection.current) - Number(first === currentSelection.current));
      for (const [id, marker] of ordered) {
        const element = marker.getElement();
        if (!element) continue;
        const anchor = labelAnchors.current.get(id)!;
        const point = instance.latLngToContainerPoint(anchor);
        const name = currentResults.current.get(id)?.municipality ?? "";
        const width = element.firstElementChild?.getBoundingClientRect().width || Math.max(55, name.length * 6 + 15);
        let position = point;
        let selectedBox = { left: point.x - width / 2, right: point.x + width / 2, top: point.y - 12, bottom: point.y + 12 };
        // Offscreen towns stay at their geographic anchors while the user pans.
        if (point.x >= 0 && point.x <= size.x && point.y >= 0 && point.y <= size.y) {
          let minimumOverlap = Infinity;
          for (const [dx, dy] of offsets) {
            const x = Math.max(width / 2 + 8, Math.min(size.x - width / 2 - 8, point.x + dx));
            const y = Math.max(74, Math.min(size.y - 65, point.y + dy));
            const box = { left: x - width / 2 - 3, right: x + width / 2 + 3, top: y - 12, bottom: y + 12 };
            const overlap = accepted.reduce((total, other) => total + Math.max(0, Math.min(box.right, other.right) - Math.max(box.left, other.left)) *
              Math.max(0, Math.min(box.bottom, other.bottom) - Math.max(box.top, other.top)), 0);
            if (overlap < minimumOverlap) { minimumOverlap = overlap; position = L.point(x, y); selectedBox = box; }
            if (overlap === 0) break;
          }
        }
        const target = instance.containerPointToLatLng(position);
        marker.setLatLng(target);
        labelLines.current.get(id)?.setLatLngs([anchor, target]);
        marker.setZIndexOffset(id === currentSelection.current ? 1000 : 0);
        element.classList.toggle(styles.selectedLabel, id === currentSelection.current);
        accepted.push(selectedBox);
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
      polygons.current.clear(); labels.current.clear(); labelAnchors.current.clear(); labelLines.current.clear();
      selectionOutline.current = null; map.current = null;
    };
  }, [geometry, maxZoom]);

  useEffect(() => {
    for (const [id, polygon] of polygons.current) {
      const result = currentResults.current.get(id);
      const selected = id === selectedId;
      polygon.setStyle({ fillColor: feeColor(result) });
      const element = polygon.getElement();
      element?.setAttribute("aria-label", `${result?.municipality ?? id}: ${formatMoney(result?.monthly_equivalent_cents ?? null)} pro Monat`);
      element?.setAttribute("aria-pressed", String(selected));
      const tooltip = polygon.getTooltip()?.getContent();
      if (tooltip instanceof HTMLElement && result) tooltip.textContent = `${result.municipality} · ${formatMoney(result.monthly_equivalent_cents)}`;
    }
    selectionOutline.current?.clearLayers();
    const selectedFeature = geometry.features.find(feature => feature.properties.municipality_id === selectedId);
    if (selectedFeature) selectionOutline.current?.addData(selectedFeature);
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
