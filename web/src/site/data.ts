import type { FeatureCollection, MultiPolygon, Polygon } from "geojson";
import { normalizeProfile } from "../domain/index.js";
import type { MunicipalityCatalog, Profile, Registry } from "../domain/index.js";

export interface AreaProperties {
  ags: string;
  name: string;
  municipality_id: string | null;
  area_id: string | null;
  label_point?: [number, number];
}

export type MunicipalGeometry = FeatureCollection<Polygon | MultiPolygon, AreaProperties>;
export interface SourceReference { id: string; title: string; url: string; retrieved_at: string }
export interface SiteBundle {
  schema_version: string;
  registry: Registry;
  profiles: { default: Profile; highest_band: Profile };
  tariffs: MunicipalityCatalog[];
  sources: Record<string, SourceReference>;
  geography: {
    boundary_status_date: string;
    retrieved_at: string;
    product_url: string;
    attribution_url: string;
    license_url: string;
    data_sources_url: string;
    max_zoom: number;
  };
}
export interface SiteData { bundle: SiteBundle; geometry: MunicipalGeometry }

async function fetchJSON(path: string, signal: AbortSignal): Promise<unknown> {
  const response = await fetch(new URL(import.meta.env.BASE_URL + path, document.baseURI), { signal });
  if (!response.ok) throw new Error(`Unable to load ${path}: HTTP ${response.status}`);
  return response.json();
}

/** Only generated local assets are fetched; canonical source archives stay outside the site. */
export async function loadSiteData(signal: AbortSignal): Promise<SiteData> {
  const [rawBundle, rawGeometry] = await Promise.all([
    fetchJSON("data/region-stuttgart.json", signal), fetchJSON("data/municipalities.geojson", signal),
  ]);
  const bundle = rawBundle as SiteBundle;
  const geometry = rawGeometry as MunicipalGeometry;
  if (bundle.schema_version !== "1.0" || !Array.isArray(bundle.tariffs) ||
      !Array.isArray(bundle.registry?.municipalities) || geometry.type !== "FeatureCollection" ||
      !Array.isArray(geometry.features)) throw new Error("Unsupported generated site data.");
  bundle.profiles.default = normalizeProfile(bundle.profiles.default);
  bundle.profiles.highest_band = normalizeProfile(bundle.profiles.highest_band);
  for (const municipality of bundle.registry.municipalities.filter(entry => entry.active)) {
    const matches = geometry.features.filter(feature => feature.properties.municipality_id === municipality.id);
    if (matches.length !== 1 || matches[0].properties.ags !== municipality.ags ||
        matches[0].properties.area_id !== municipality.area_id) throw new Error("Municipality geometry assignment mismatch.");
  }
  return { bundle, geometry };
}
