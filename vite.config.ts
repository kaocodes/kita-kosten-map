import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  root: fileURLToPath(new URL("./web", import.meta.url)),
  base: "./",
  plugins: [react(), {
    name: "expansion-preview-data",
    apply: "serve",
    configureServer(server) {
      if (mode !== "expansion-preview") return;
      const files = new Set(["municipalities.geojson", "region-stuttgart.json", "build-metrics.json"]);
      server.middlewares.use("/data", async (request, response, next) => {
        const file = request.url?.split("?")[0].slice(1);
        if (!file || !files.has(file)) return next();
        try {
          const body = await readFile(new URL(`./build/expansion-preview/${file}`, import.meta.url));
          response.setHeader("Content-Type", "application/json; charset=utf-8");
          response.setHeader("Cache-Control", "no-store");
          response.end(body);
        } catch (error) {
          next(error);
        }
      });
    },
  }],
  build: {
    outDir: fileURLToPath(new URL("./dist", import.meta.url)),
    emptyOutDir: true,
    target: "es2022",
  },
  server: { host: "127.0.0.1", port: mode === "expansion-preview" ? 5174 : 5173, strictPort: true },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
}));
