# Project Purpose

Build a lightweight, client-side web application that helps parents and residents compare daycare costs across Stuttgart-area districts on an interactive map. The application must work entirely in the browser using local JSON and GeoJSON files, without any backend.

# Scope

The MVP displays a static Stuttgart region map, highlights district-level daycare cost data, and allows users to compare district costs by selecting areas. Language switching, responsive layout, and basic accessibility are included. Map zooming, panning, filtering, searching, and data editing are intentionally excluded.

# Functional Requirements

1. Display the Stuttgart region as a map composed of city district polygons loaded from a local GeoJSON file.
2. Color each district based on its daycare cost data, using a diverging color scale where lower cost is green, higher cost is red, and equal cost is neutral.
3. Clicking a district opens an overlay panel showing:
   - Monthly cost
   - Yearly cost
   - Billing period
   - Last increase date
   - Last increase percentage
   - Data source URL
4. When a district is selected, update the other districts’ colors to show whether they are cheaper, more expensive, or equal compared to the selected district.
5. Load all data client-side from local files: a JSON file for daycare costs and a GeoJSON file for district boundaries.
6. Support German and English languages with full translation for UI text, overlays, and labels.
7. Provide a language switch control in the top-right area of the app.
8. Always use a dark theme; no light-mode option is required.
9. Ensure the application is responsive and usable on desktop and mobile screen sizes.
10. The map view is static and must display the full Stuttgart region without requiring zoom or pan.
11. If any displayed field is missing or empty, render `n/a` in the overlay.
12. Highlight the following Stuttgart-area city districts in the GeoJSON map:
   - Leonberg
   - Gerlingen
   - Ditzingen
   - Stuttgart
   - Korntal
   - Kornwestheim
   - Ludwigsburg
   - Leinfelden-Echterdingen
   - Böblingen
   - Sindelfingen
   - Esslingen
   - Fellbach

# Data Requirements

- Daycare cost data must be stored in a local JSON file.
- GeoJSON boundaries must be stored in a local GeoJSON file.
- Both files must share a consistent join key for districts, such as `district_id` or `district_name`.
- The daycare JSON file should include the following fields for each district:
  - `district_id` (string)
  - `monthly_cost` (number)
  - `yearly_cost` (number)
  - `billing_period` (string)
  - `last_increase_date` (ISO 8601 string)
  - `last_increase_percentage` (number)
  - `source_url` (string)
- The GeoJSON feature properties should include the same district identifier used by the JSON file.

# UI / UX Requirements

- Use Vuetify and Material Design principles for layout, typography, spacing, and controls.
- Ensure color contrast meets accessibility guidelines for text and graphics.
- Provide keyboard navigation for district selection and language switching.
- Use ARIA labels for the overlay panel and the language toggle.
- Default language should be German.
- Persist the selected language for the current session, if technically feasible.

# Non-Functional Requirements

1. No backend: all data is loaded client-side.
2. The application should be lightweight and fast to load.
3. Use Vue 3 with the Composition API and Vite as the build tool.
4. Prefer code that is easy to maintain and extend for future features such as filtering or map zoom.
5. Use Vuetify, Leaflet.js, D3.js, and vue-i18n to implement the UI, map rendering, color scales, and translations.

# Acceptance Criteria

- The app loads and renders the Stuttgart area map from local GeoJSON data.
- Clicking any district displays an overlay with all required fields.
- Missing values are shown as `n/a`.
- Selecting a district updates the remaining district colors based on relative cost.
- Language switching updates UI text immediately.
- The app displays correctly on desktop and mobile layouts.
- The app uses a dark theme only.

# Out of Scope

- User authentication
- Data editing or submission
- Filtering or searching districts or costs
- Map zooming or panning

# Tech Stack

- Vue 3 (Composition API)
- Vite (build tool)
- Vuetify (Material Design UI)
- Leaflet.js (map rendering)
- D3.js (color scales)
- vue-i18n (internationalization)
- Local JSON and GeoJSON files for data

# Additional Notes

- Follow Material Design principles for UI consistency.
- Use Vuetify’s accessibility defaults for screen reader support and keyboard navigation.
- Keep the data integration simple by matching district identifiers exactly between JSON and GeoJSON files.


# Geo data
-  get the data from https://www.openstreetmap.org/relation/722090#map=12/48.6975/8.9545
- use the id and request the API https://polygons.openstreetmap.fr/get_geojson.py?id=405293
- copy coordinates from there into a geojson file
