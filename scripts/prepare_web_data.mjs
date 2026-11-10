/** Build a reproducible, source-linked browser dataset without changing canonical tariffs. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import mapshaper from "mapshaper";

const root = new URL("../", import.meta.url);
const read = async path => JSON.parse(await readFile(new URL(path, root), "utf8"));
const hash = value => createHash("sha256").update(value).digest("hex");
const output = new URL("web/public/data/", root);
const registry = await read("data/municipality_registry.json");
const provenance = await read("data/geodata/source.json");
const geometryContent = await readFile(new URL(registry.geometry_reference.path, root));
assert.equal(hash(geometryContent), registry.geometry_reference.sha256, "Archived geometry hash mismatch");
assert.equal(hash(geometryContent), provenance.geometry_archive_sha256, "Geometry provenance hash mismatch");
assert.equal(hash(await readFile(new URL(provenance.source_page_path, root))), provenance.source_page_sha256,
  "Archived BKG product page hash mismatch");
const mapshaperPackage = await read("node_modules/mapshaper/package.json");
assert.equal(mapshaperPackage.version, provenance.processing.version, "Update provenance when changing Mapshaper");

// Process all neighbors together, preserving shared topology before any attributes are reduced.
const simplified = await mapshaper.applyCommands(
  "-i municipalities.geojson -simplify weighted 30% keep-shapes -filter-fields gen,ags -o municipalities-web.geojson format=geojson precision=0.00001",
  { "municipalities.geojson": geometryContent.toString("utf8") },
);
const raw = JSON.parse(geometryContent);
const geometry = JSON.parse(simplified["municipalities-web.geojson"].toString());
const active = registry.municipalities.filter(entry => entry.active);
const byAGS = new Map(active.map(entry => [entry.ags, entry]));
const areas = new Map(registry.areas.map(area => [area.id, area]));
assert.equal(geometry.features.length, raw.features.length, "Simplification removed an entire municipality");
const sourceCounts = new Map();

function ringArea(ring) {
  return Math.abs(ring.slice(1).reduce((total, point, index) =>
    total + ring[index][0] * point[1] - point[0] * ring[index][1], 0) / 2);
}

function pointInRing(point, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [x, y] = ring[i], [previousX, previousY] = ring[j];
    if ((y > point[1]) !== (previousY > point[1]) &&
        point[0] < (previousX - x) * (point[1] - y) / (previousY - y) + x) inside = !inside;
  }
  return inside;
}

function labelPoint(shape) {
  const polygons = shape.type === "Polygon" ? [shape.coordinates] : shape.coordinates;
  const polygon = [...polygons].sort((a, b) => ringArea(b[0]) - ringArea(a[0]))[0];
  const exterior = polygon[0];
  const xs = exterior.map(point => point[0]), ys = exterior.map(point => point[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const center = [(minX + maxX) / 2, (minY + maxY) / 2];
  const contains = point => pointInRing(point, exterior) && !polygon.slice(1).some(ring => pointInRing(point, ring));
  if (contains(center)) return center;
  const candidates = [];
  for (let x = 1; x < 20; x++) for (let y = 1; y < 20; y++) {
    const point = [minX + (maxX - minX) * x / 20, minY + (maxY - minY) * y / 20];
    if (contains(point)) candidates.push(point);
  }
  candidates.sort((a, b) => (a[0] - center[0]) ** 2 + (a[1] - center[1]) ** 2 -
    ((b[0] - center[0]) ** 2 + (b[1] - center[1]) ** 2));
  assert.ok(candidates.length > 0, "Could not place a label inside the municipal polygon");
  return candidates[0];
}

for (const feature of geometry.features) {
  assert.ok(["Polygon", "MultiPolygon"].includes(feature.geometry.type), "Unexpected map geometry");
  const ags = feature.properties.ags;
  const municipality = byAGS.get(ags);
  sourceCounts.set(ags, (sourceCounts.get(ags) ?? 0) + 1);
  if (municipality) assert.equal(areas.get(municipality.area_id).geometry_key, ags, "Registry geometry mismatch");
  feature.id = municipality?.area_id ?? "municipality-" + ags;
  feature.properties = {
    ags, name: feature.properties.gen, municipality_id: municipality?.id ?? null,
    area_id: municipality?.area_id ?? null,
    ...(municipality ? { label_point: labelPoint(feature.geometry) } : {}),
  };
}
for (const municipality of active) assert.equal(sourceCounts.get(municipality.ags), 1, "Missing or duplicate active AGS");

// Evidence locators remain available; verbatim research and original-cell copies stay in the archive.
function browserProjection(value) {
  if (Array.isArray(value)) return value.map(browserProjection);
  if (value && typeof value === "object") {
    const evidence = "source_id" in value && "locator" in value;
    return Object.fromEntries(Object.entries(value)
      .filter(([key]) => key !== "original_research" && !(evidence && key === "original"))
      .map(([key, item]) => [key, browserProjection(item)]));
  }
  return value;
}

const tariffIDs = [...new Set(active.map(entry => entry.tariff_id))].sort();
const tariffs = await Promise.all(tariffIDs.map(async id => browserProjection(await read(`data/municipalities/${id}.json`))));
const profiles = { default: await read("data/profiles/default.json"), highest_band: await read("data/profiles/highest_band.json") };
const models = await read("data/models/configuration.json");
const sourceIDs = new Set();
function collectSources(value) {
  if (Array.isArray(value)) value.forEach(collectSources);
  else if (value && typeof value === "object") {
    if (value.source_id) sourceIDs.add(value.source_id);
    Object.values(value).forEach(collectSources);
  }
}
collectSources([tariffs, profiles]);
const manifest = await read("data/source_manifest.json");
const sources = Object.fromEntries(manifest.filter(source => sourceIDs.has(source.id)).map(source => {
  assert.equal(source.http_status, 200, "An unavailable source cannot be published as evidence");
  return [source.id, { id: source.id, title: source.title, url: source.url, retrieved_at: source.retrieved_at }];
}));
assert.equal(Object.keys(sources).length, sourceIDs.size, "Evidence source missing from the browser index");

const bundle = {
  schema_version: "1.0", registry, profiles, models, tariffs, sources,
  geography: {
    boundary_status_date: provenance.boundary_status_date,
    retrieved_at: provenance.geometry_retrieved_at,
    product_url: provenance.product_url,
    attribution_url: provenance.attribution_url,
    license_url: provenance.license_url,
    data_sources_url: provenance.data_sources_url,
    modification: "Municipal boundaries simplified together at 30% point retention; reduced attributes and coordinate precision.",
    max_zoom: provenance.processing.max_map_zoom,
    source_sha256: provenance.geometry_archive_sha256,
  },
};
const geometryJSON = JSON.stringify(geometry) + "\n";
const bundleJSON = JSON.stringify(bundle) + "\n";
function vertexCount(coordinates) {
  return typeof coordinates[0] === "number" ? 1 : coordinates.reduce((total, item) => total + vertexCount(item), 0);
}
const metrics = {
  active_municipalities: active.length,
  context_municipalities: geometry.features.length - active.length,
  source_geometry_bytes: geometryContent.length,
  source_vertices: raw.features.reduce((total, feature) => total + vertexCount(feature.geometry.coordinates), 0),
  web_vertices: geometry.features.reduce((total, feature) => total + vertexCount(feature.geometry.coordinates), 0),
  geometry_bytes: Buffer.byteLength(geometryJSON),
  geometry_gzip_bytes: gzipSync(geometryJSON).length,
  catalog_bytes: Buffer.byteLength(bundleJSON),
  catalog_gzip_bytes: gzipSync(bundleJSON).length,
  geometry_sha256: hash(geometryJSON), catalog_sha256: hash(bundleJSON),
  max_map_zoom: provenance.processing.max_map_zoom,
};
assert.ok(metrics.geometry_bytes <= 200_000, "Geometry exceeds its 200 kB budget");
assert.ok(metrics.catalog_bytes <= 1_500_000, "Browser catalog exceeds its 1.5 MB budget");
assert.ok(metrics.catalog_gzip_bytes + metrics.geometry_gzip_bytes <= 150_000, "Compressed data exceeds its 150 kB budget");
await mkdir(output, { recursive: true });
await Promise.all([
  writeFile(new URL("municipalities.geojson", output), geometryJSON),
  writeFile(new URL("region-stuttgart.json", output), bundleJSON),
  writeFile(new URL("build-metrics.json", output), JSON.stringify(metrics, null, 2) + "\n"),
]);
const licenses = await Promise.all(["react", "react-dom", "leaflet", "zod"].map(async name => {
  const pkg = await read(`node_modules/${name}/package.json`);
  const license = await readFile(new URL(`node_modules/${name}/LICENSE`, root), "utf8");
  return `${name} ${pkg.version}\n${license}`;
}));
const fontLicense = await readFile(new URL("web/public/fonts/OFL.txt", root), "utf8");
await writeFile(new URL("web/public/THIRD_PARTY_NOTICES.txt", root),
  [...licenses, `Bricolage Grotesque (self-hosted Latin variable font)\n${fontLicense}`].join("\n\n") + "\n");
console.log(`Prepared ${active.length} municipalities and ${metrics.context_municipalities} context areas in ${fileURLToPath(output)}.`);
console.log(`Geometry: ${metrics.geometry_bytes} bytes (${metrics.geometry_gzip_bytes} gzip); catalog: ${metrics.catalog_bytes} bytes (${metrics.catalog_gzip_bytes} gzip).`);
