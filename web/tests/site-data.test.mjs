import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";
import { gzipSync } from "node:zlib";
import { compareMunicipalities } from "../../build/domain/index.js";
import { feeColor, formatMoney, MISSING_COLOR, FEE_BANDS } from "../../build/site/presentation.js";

const read = path => JSON.parse(readFileSync(new URL("../../" + path, import.meta.url), "utf8"));
const bytes = path => readFileSync(new URL("../../" + path, import.meta.url));
const hash = value => createHash("sha256").update(value).digest("hex");
const bundle = read("web/public/data/region-stuttgart.json");
const geometry = read("web/public/data/municipalities.geojson");
const rawGeometry = read("output/municipalities-original.geojson");
const registry = read("data/municipality_registry.json");
const metrics = read("web/public/data/build-metrics.json");
const active = registry.municipalities.filter(entry => entry.active);
const canonical = readdirSync(new URL("../../data/municipalities/", import.meta.url)).sort()
  .filter(name => name.endsWith(".json")).map(name => read("data/municipalities/" + name));

test("Every active municipality has exactly one matching AGS, area ID and tariff", () => {
  assert.deepEqual(bundle.registry, registry);
  assert.equal(metrics.active_municipalities, active.length);
  for (const municipality of active) {
    const matches = geometry.features.filter(feature => feature.properties.municipality_id === municipality.id);
    assert.equal(matches.length, 1, municipality.id);
    assert.equal(matches[0].properties.ags, municipality.ags);
    assert.equal(matches[0].properties.area_id, municipality.area_id);
    assert.ok(bundle.tariffs.some(tariff => tariff.id === municipality.tariff_id));
    assert.equal(matches[0].properties.label_point.length, 2);
  }
});

test("Neighbor context has no invented comparison identity or fee", () => {
  const context = geometry.features.filter(feature => feature.properties.municipality_id === null);
  assert.equal(context.length, rawGeometry.features.length - active.length);
  for (const feature of context) {
    assert.equal(feature.properties.area_id, null);
    assert.equal(feature.properties.monthly_equivalent_cents, undefined);
  }
});

function rings(feature) {
  return feature.geometry.type === "Polygon" ? feature.geometry.coordinates : feature.geometry.coordinates.flat();
}

test("All polygons survive simplification and retain valid closed coordinate rings", () => {
  assert.equal(geometry.features.length, rawGeometry.features.length);
  assert.deepEqual(geometry.features.map(feature => feature.properties.ags).sort(),
    rawGeometry.features.map(feature => feature.properties.ags).sort());
  for (const feature of geometry.features) {
    assert.ok(["Polygon", "MultiPolygon"].includes(feature.geometry.type));
    for (const ring of rings(feature)) {
      assert.ok(ring.length >= 4);
      assert.deepEqual(ring[0], ring.at(-1));
      for (const point of ring) {
        assert.equal(point.length, 2);
        assert.ok(point.every(Number.isFinite));
        assert.ok(point[0] > 8 && point[0] < 10 && point[1] > 48 && point[1] < 50);
      }
    }
  }
});

function neighbors(collection) {
  const edges = new Map();
  for (const feature of collection.features) {
    for (const ring of rings(feature)) {
      for (let index = 1; index < ring.length; index++) {
        const key = [JSON.stringify(ring[index - 1]), JSON.stringify(ring[index])].sort().join("|");
        if (!edges.has(key)) edges.set(key, new Set());
        edges.get(key).add(feature.properties.ags);
      }
    }
  }
  const result = new Set();
  for (const owners of edges.values()) {
    const values = [...owners].sort();
    for (let first = 0; first < values.length; first++) for (let second = first + 1; second < values.length; second++) {
      result.add(values[first] + ":" + values[second]);
    }
  }
  return result;
}

test("Known shared municipal borders remain shared after joint simplification", () => {
  const originalPairs = neighbors(rawGeometry);
  const simplifiedPairs = neighbors(geometry);
  const keys = new Set(active.map(entry => entry.ags));
  const comparedPairs = [...originalPairs].filter(pair => pair.split(":").some(ags => keys.has(ags)));
  assert.ok(comparedPairs.length > 0);
  for (const pair of comparedPairs) assert.ok(simplifiedPairs.has(pair), `Lost shared border: ${pair}`);
});

function monetaryContract(result) {
  const fields = ["municipality_id", "status", "monthly_care_cents", "annual_care_cents", "monthly_equivalent_cents",
    "payment_months", "booked_weekly_minutes", "extra_weekly_minutes", "selected_price_id", "offer_id", "reasons",
    "total_mandatory_monthly_equivalent_cents", "total_status"];
  return {
    ...Object.fromEntries(fields.map(field => [field, result[field]])),
    components: result.components.map(part => ({ id: part.id, kind: part.kind, amount: part.amount_cents,
      months: part.payment_months, equivalent: part.annual_equivalent_cents, status: part.value_status })),
    evidence: result.evidence.map(reference => ({ id: reference.source_id, locator: reference.locator })),
  };
}

test("Browser projection preserves all comparison amounts, packages, extra costs and source locators", () => {
  for (const name of ["default", "highest_band"]) {
    assert.deepEqual(bundle.profiles[name], read(`data/profiles/${name}.json`));
    const source = compareMunicipalities(canonical, bundle.profiles[name], registry);
    const browser = compareMunicipalities(bundle.tariffs, bundle.profiles[name], bundle.registry);
    assert.deepEqual(browser.map(monetaryContract), source.map(monetaryContract));
    for (const result of browser) {
      for (const evidence of result.evidence) assert.ok(bundle.sources[evidence.source_id]);
    }
  }
  assert.ok(bundle.tariffs.every(tariff => !("original_research" in tariff)));
});

test("BKG product page, boundary status, attribution and source hashes are pinned", () => {
  const metadata = read("data/geodata/source.json");
  assert.equal(hash(bytes(metadata.source_page_path)), metadata.source_page_sha256);
  assert.equal(hash(bytes(metadata.geometry_archive_path)), metadata.geometry_archive_sha256);
  assert.equal(bundle.geography.boundary_status_date, metadata.boundary_status_date);
  assert.equal(bundle.geography.license_url, metadata.license_url);
  assert.equal(bundle.geography.source_sha256, registry.geometry_reference.sha256);
  assert.ok(metadata.data_sources_url.startsWith("https://sgx.geodatenzentrum.de/"));
});

test("Prepared assets match their hashes and the documented data budgets", () => {
  const geo = bytes("web/public/data/municipalities.geojson");
  const data = bytes("web/public/data/region-stuttgart.json");
  assert.equal(hash(geo), metrics.geometry_sha256);
  assert.equal(hash(data), metrics.catalog_sha256);
  assert.equal(geo.length, metrics.geometry_bytes);
  assert.equal(data.length, metrics.catalog_bytes);
  assert.ok(geo.length <= 200000);
  assert.ok(data.length <= 1500000);
  assert.ok(gzipSync(data).length + gzipSync(geo).length <= 150000);
  assert.ok(metrics.web_vertices < metrics.source_vertices);
  assert.equal(bundle.geography.max_zoom, metrics.max_map_zoom);
});

test("Fee colors distinguish zero from missing data and use unambiguous band boundaries", () => {
  assert.equal(feeColor({ status: "comparable", monthly_equivalent_cents: 0 }), FEE_BANDS[0].color);
  assert.equal(feeColor({ status: "comparable", monthly_equivalent_cents: 30000 }), FEE_BANDS[0].color);
  assert.equal(feeColor({ status: "comparable", monthly_equivalent_cents: 30001 }), FEE_BANDS[1].color);
  assert.equal(feeColor({ status: "unavailable", monthly_equivalent_cents: null }), MISSING_COLOR);
  assert.equal(feeColor({ status: "ambiguous", monthly_equivalent_cents: 0 }), MISSING_COLOR);
  assert.notEqual(formatMoney(0), formatMoney(null));
});
