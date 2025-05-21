/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../webroot/views/**/*.templ", // Scan .templ files for Tailwind classes
    "../webroot/sources/**/*.js",  // Scan source JS if you use Tailwind classes there
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/typography"), // For 'prose' class styling
    require("daisyui"),
  ],
  daisyui: {
    themes: ["light", "night"], // Available themes
    darkTheme: "night",       // Default dark theme
    base: true,               // Applies DaisyUI base styles
    styled: true,             // Applies DaisyUI component styles
    utils: true,              // Applies DaisyUI utility classes
    logs: true,               // Show DaisyUI logs in console (dev only)
  },
}