/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        shell: "rgb(var(--color-shell) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        spruce: "rgb(var(--color-spruce) / <alpha-value>)",
        teal: "rgb(var(--color-teal) / <alpha-value>)",
        mint: "rgb(var(--color-mint) / <alpha-value>)",
        ai: "rgb(var(--color-ai) / <alpha-value>)",
        aisoft: "rgb(var(--color-aisoft) / <alpha-value>)",
        amber: "rgb(var(--color-amber) / <alpha-value>)",
        emergency: "rgb(var(--color-emergency) / <alpha-value>)"
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI", "system-ui", "sans-serif"],
        display: ["Georgia", "Cambria", "serif"]
      },
      boxShadow: {
        calm: "0 18px 45px rgba(23, 33, 38, 0.08)",
        insetline: "inset 0 0 0 1px rgba(23, 33, 38, 0.08)"
      }
    }
  },
  plugins: []
};
