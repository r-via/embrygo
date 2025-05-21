package router

import (
    "log/slog"
	"github.com/gofiber/fiber/v2"
	// "{GO_MODULE_NAME}/internal/handlers/web" // Example if you had more handlers
)

// SetupRoutes configures the application's routes.
// For EmbryGo, routing is simple and handled in main.go by registering web.Handler.
// This is a placeholder for more complex routing scenarios.
func SetupRoutes(app *fiber.App, logger *slog.Logger /*, webHandler *web.Handler, apiHandler *api.Handler */) {
	logger.Info("Router setup skipped for EmbryGo (placeholder - routing handled in main.go).")
	// Example for a larger app:
	// api := app.Group("/api")
	// apiHandler.RegisterAPIRoutes(api)
	// webHandler.RegisterRoutes(app) // Or a specific web group
}