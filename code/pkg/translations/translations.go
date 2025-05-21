package translations

import "log/slog"

// TranslationsMap holds translations for different languages.
var TranslationsMap = map[string]map[string]string{
	"en": {
		"welcome_title":             "Welcome to EmbryGo!",
		"welcome_message":           "This is a minimal web application built with the EmbryGo stack.",
		"utilities_title":           "Core Technologies & Features Status:",
		"go_backend":                "Go Backend",
		"fiber_framework":           "Fiber Web Framework",
		"blitzkit_server":           "BlitzKit Server Layer",
		"templ_templating":          "Templ (Type-Safe HTML)",
		"htmx":                      "HTMX (Dynamic HTML)",
		"tailwind_css":              "Tailwind CSS",
		"daisy_ui":                  "DaisyUI (Tailwind Components)",
		"heroicons_generator":       "Heroicons (via templ-heroicons-generator)",
		"slog_logging":              "Slog (Structured Logging)",
		"air_live_reload":           "Air (Live Reload - Dev)",
        "status_ok":                 "OK",
        "footer_text":               "EmbryGo Starter Project",
        "current_year":              "2024", // This could be dynamic
	},
	"fr": { // Example for another language
		"welcome_title":             "Bienvenue sur EmbryGo !",
		"welcome_message":           "Ceci est une application web minimale construite avec la stack EmbryGo.",
		"utilities_title":           "Statut des Technologies & Fonctionnalités Clés :",
		"go_backend":                "Backend Go",
		"fiber_framework":           "Framework Web Fiber",
		"blitzkit_server":           "Couche Serveur BlitzKit",
		"templ_templating":          "Templ (HTML Typé)",
		"htmx":                      "HTMX (HTML Dynamique)",
		"tailwind_css":              "Tailwind CSS",
		"daisy_ui":                  "DaisyUI (Composants Tailwind)",
		"heroicons_generator":       "Heroicons (via templ-heroicons-generator)",
		"slog_logging":              "Slog (Journalisation Structurée)",
		"air_live_reload":           "Air (Rechargement à Chaud - Dev)",
        "status_ok":                 "OK",
        "footer_text":               "Projet de Démarrage EmbryGo",
        "current_year":              "2024",
	},
}

// GetTranslations returns the translation map for the given language.
// Defaults to English if the language is not found.
func GetTranslations(lang string) map[string]string {
	if trans, ok := TranslationsMap[lang]; ok {
		return trans
	}
	slog.Warn("Language not found in translations, defaulting to English", "requested_lang", lang)
	return TranslationsMap["en"] // Default to English
}