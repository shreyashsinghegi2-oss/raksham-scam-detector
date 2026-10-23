/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Inter Variable"', "Inter", "system-ui", "sans-serif"] },
      colors: {
        ink: "#030303",
        surface: "#0a0a0a",
        raised: "#101010",
        accent: "#2dd4bf",
        risk: { low: "#3fb950", medium: "#e3b341", high: "#f0883e", critical: "#ff5c5c" },
      },
    },
  },
  plugins: [],
};
