import { defineConfig } from "vite";
import legacy from "@vitejs/plugin-legacy";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    legacy({
      targets: ["defaults", "iOS >= 12", "Android >= 7"],
      modernPolyfills: true
    })
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
