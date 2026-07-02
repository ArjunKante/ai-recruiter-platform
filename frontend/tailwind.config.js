/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand colors used throughout the dark UI
        violet: {
          950: "#1e0845",
        },
        surface: {
          DEFAULT: "rgba(255,255,255,0.03)",
          hover:   "rgba(255,255,255,0.06)",
          border:  "rgba(255,255,255,0.08)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "fade-up": "fadeUp 0.3s ease forwards",
        "glow":    "glow 3s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%,100%": { boxShadow: "0 0 20px rgba(124,58,237,0.2)" },
          "50%":     { boxShadow: "0 0 40px rgba(124,58,237,0.5)" },
        },
      },
    },
  },
  plugins: [],
};
