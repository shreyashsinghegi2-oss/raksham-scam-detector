import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds straight into deploy/public, which Vercel serves as static files next to the /api function.
export default defineConfig({
  plugins: [react()],
  base: "/",
  build: { outDir: "../deploy/public", emptyOutDir: true, sourcemap: false },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
