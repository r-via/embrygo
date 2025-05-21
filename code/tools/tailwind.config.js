// tools/tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../webroot/views/**/*.templ", 
    "../webroot/sources/**/*.js",  
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("daisyui")({ // Passer l'objet de configuration ICI
      themes: ["light", "night"], // ou vos thèmes désirés
      darkTheme: "night",       
      base: true,               
      styled: true,             
      utils: true,              
      logs: false, // Mettre à false pour la production, true pour le débogage si besoin
    }),
  ],
  // PAS DE SECTION daisyui: { ... } ICI
}