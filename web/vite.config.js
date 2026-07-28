import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

// Single-file build: everything (JS, CSS, the baked-in landscape data) is
// inlined into one dist/index.html so it opens by double-click from file://,
// with no dev server and no module-CORS problems. Fonts are the only external
// request and degrade gracefully to system fonts when offline.
export default defineConfig({
  base: "./",
  plugins: [react(), viteSingleFile()],
  build: {
    target: "es2020",
    cssCodeSplit: false,
    assetsInlineLimit: 100000000,
    chunkSizeWarningLimit: 4000,
  },
});
