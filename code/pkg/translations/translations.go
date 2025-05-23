// Package translations provides simple i18n capabilities for the application.
package translations

import "log/slog"

var TranslationsMap = map[string]map[string]string{
	"en": {
		"welcome_title":                "Welcome to EmbryGo!",
		"welcome_message":              "This is a minimal web application built with the EmbryGo stack.",
		"utilities_title":              "Core Technologies & Features Status:",
		"go_backend":                   "Go Backend",
		"fiber_framework":              "Fiber Web Framework",
		"blitzkit_server":              "BlitzKit Server Layer",
		"templ_templating":             "Templ (Type-Safe HTML)",
		"htmx":                         "HTMX (Dynamic HTML)",
		"tailwind_css":                 "Tailwind CSS",
		"daisy_ui":                     "DaisyUI (Tailwind Components)",
		"heroicons_generator":          "Heroicons (templ-heroicons-generator)",
		"slog_logging":                 "Slog (Structured Logging)",
		"air_live_reload":              "Air (Live Reload - Dev)",
		"footer_text":                  "EmbryGo Starter Project",
		"current_year":                 "2024",
		"status_ok":                    "OK",
		"status_error":                 "Error",
		"status_not_found":             "Not Found",
		"status_not_found_or_disabled": "Not Found / Disabled",
		"status_config_issue":          "Config Issue",
		"status_check_failed":          "Check Failed",
		"status_disabled_dev_mode":     "Disabled (Dev Mode)",
		"status_disabled_prod_mode":    "Disabled (Prod Mode)",
		"status_active":                "Active",
		"status_inactive":              "Inactive",
	},
	"fr": {
		"welcome_title":                "Bienvenue sur EmbryGo !",
		"welcome_message":              "Ceci est une application web minimale construite avec la stack EmbryGo.",
		"utilities_title":              "Statut des Technologies & Fonctionnalités Clés :",
		"go_backend":                   "Backend Go",
		"fiber_framework":              "Framework Web Fiber",
		"blitzkit_server":              "Couche Serveur BlitzKit",
		"templ_templating":             "Templ (HTML Typé)",
		"htmx":                         "HTMX (HTML Dynamique)",
		"tailwind_css":                 "Tailwind CSS",
		"daisy_ui":                     "DaisyUI (Composants Tailwind)",
		"heroicons_generator":          "Heroicons (templ-heroicons-generator)",
		"slog_logging":                 "Slog (Journalisation Structurée)",
		"air_live_reload":              "Air (Rechargement à Chaud - Dev)",
		"footer_text":                  "Projet de Démarrage EmbryGo",
		"current_year":                 "2024",
		"status_ok":                    "OK",
		"status_error":                 "Erreur",
		"status_not_found":             "Non Trouvé",
		"status_not_found_or_disabled": "Non Trouvé / Désactivé",
		"status_config_issue":          "Problème Config",
		"status_check_failed":          "Échec Vérif.",
		"status_disabled_dev_mode":     "Désactivé (Mode Dev)",
		"status_disabled_prod_mode":    "Désactivé (Mode Prod)",
		"status_active":                "Actif",
		"status_inactive":              "Inactif",
	},
}

// GetTranslations returns the translation map for the given language.
// It defaults to English ("en") if the requested language is not found.
func GetTranslations(lang string) map[string]string {
	if trans, ok := TranslationsMap[lang]; ok {
		return trans
	}
	slog.Warn("Language not found in translations, defaulting to English", "requested_lang", lang)
	return TranslationsMap["en"]
}
