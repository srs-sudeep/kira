import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vitest/config";

/** Host dev server; Docker sets PORT=3000 (see docker/docker-compose.yml). */
function devServerPort(): number {
  const raw = process.env.VITE_DEV_PORT ?? process.env.PORT ?? "3000";
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : 3000;
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
  server: {
    port: devServerPort(),
    strictPort: true,
    host: true,
    proxy: {
      "/api": {
        // In Docker, set API_PROXY_TARGET=http://kong:8000 (see docker-compose web-app)
        target: process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
