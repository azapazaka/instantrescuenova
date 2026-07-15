/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        shell: "#F6F7F2",
        ink: "#172126",
        muted: "#66756F",
        line: "#DDE4DC",
        spruce: "#214E46",
        teal: "#1D8A78",
        mint: "#DCEFE6",
        ai: "#5368C7",
        aisoft: "#E7EBFF",
        amber: "#B87910",
        emergency: "#B23A35"
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
