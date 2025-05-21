package web

import (
	"log/slog"
	"strings"
	"github.com/r-via/embrygo/pkg/translations"
	"github.com/r-via/embrygo/webroot/views/layouts"
	"github.com/r-via/embrygo/webroot/views/pages"

	"github.com/a-h/templ"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/adaptor"
	"github.com/r-via/blitzkit"
)

type Handler struct {
	logger *slog.Logger
	server *blitzkit.Server
	// No complex service needed for EmbryGo's welcome page
}

func NewHandler(server *blitzkit.Server, logger *slog.Logger) *Handler {
	if logger == nil || server == nil {
		slog.Error("FATAL: Web Handler for EmbryGo requires non-nil server and logger")
		panic("Web Handler initialization failed: missing critical dependencies")
	}
	return &Handler{logger: logger, server: server}
}

// RegisterRoutes registers the web routes for EmbryGo.
// It expects the rootGroup to be already prefixed with any basePath.
func (h *Handler) RegisterRoutes(rootGroup fiber.Router) {
	h.logger.Info("Registering EmbryGo web routes...")
	
	// The actual path will be basePath + "/welcome"
	rootGroup.Get("/welcome", h.handleWelcomePage)

	// Redirect from the basePath itself to /basePath/welcome
	rootGroup.Get("/", func(c *fiber.Ctx) error {
		// basePath is already handled by the group, so target is just "welcome"
		// However, c.Redirect needs the full path from the server root.
        // We get basePath from locals, which IS the full path from server root.
        currentBasePath, _ := c.Locals("basePath").(string)
        if currentBasePath == "/" { currentBasePath = "" } // Avoid //welcome

		targetRedirectPath := currentBasePath + "/welcome"
        
		h.logger.Debug("Redirecting from root of group to welcome", "from", c.Path(), "to", targetRedirectPath)
		return c.Redirect(targetRedirectPath, fiber.StatusFound)
	})
}

// getBasePathFromLocals retrieves the application's base path from Fiber's context locals.
// This base path is set by a middleware in main.go.
func getBasePathFromLocals(c *fiber.Ctx, logger *slog.Logger) string {
	basePathVal := c.Locals("basePath")
	basePath, ok := basePathVal.(string)
	if !ok {
		basePath = "/" // Default to root if not found or wrong type
		if logger != nil {
			logger.Warn("Could not get 'basePath' from locals or wrong type, defaulting to '/'", "type_found", basePathVal)
		}
	}
	return basePath
}

// getCsrfToken retrieves the CSRF token from Fiber's context locals.
// It checks if CSRF is enabled on the server.
func getCsrfToken(c *fiber.Ctx, server *blitzkit.Server) string {
	if server == nil || !server.GetConfig().EnableCSRF {
		return "" // CSRF not enabled or server not available
	}
	csrfVal := c.Locals(blitzkit.CSRFContextKey) // Use BlitzKit's constant
	if tokenStr, ok := csrfVal.(string); ok && tokenStr != "csrf-disabled" {
		return tokenStr
	}
	return "" // Token not found, or CSRF explicitly disabled for the request
}

func (h *Handler) handleWelcomePage(c *fiber.Ctx) error {
	lang := "en" // Simplified for EmbryGo starter
	trans := translations.GetTranslations(lang) // From pkg/translations
	
	// basePath is the full path from the server root, e.g., "/" or "/myapp"
	basePath := getBasePathFromLocals(c, h.logger)
	csrfToken := getCsrfToken(c, h.server)

	h.logger.Debug("Handling /welcome page", "lang", lang, "basePath", basePath, "csrf_present", csrfToken != "")

	pageData := pages.WelcomePageData{
		Lang:         lang,
		Translations: trans,
		Base: layouts.BaseData{
			Lang:         lang,
			PageTitle:    trans["welcome_title"],
			Translations: trans,
			CSRFToken:    csrfToken,
			BasePath:     basePath,
		},
		Utilities: []pages.UtilityStatus{
			{Name: "Go Backend", Status: "OK", Icon: "check_circle"},
			{Name: "Fiber Framework", Status: "OK", Icon: "check_circle"},
			{Name: "BlitzKit Server Layer", Status: "OK", Icon: "check_circle"},
			{Name: "Templ Templating", Status: "OK", Icon: "check_circle"},
			{Name: "HTMX", Status: "OK", Icon: "check_circle"},
			{Name: "Tailwind CSS", Status: "OK", Icon: "check_circle"},
			{Name: "DaisyUI", Status: "OK", Icon: "check_circle"},
			{Name: "Heroicons (templ-heroicons-generator)", Status: "OK", Icon: "check_circle"},
			{Name: "Slog Logging", Status: "OK", Icon: "check_circle"},
			{Name: "Air Live Reload (Dev)", Status: "OK", Icon: "check_circle"},
		},
	}

	// Use Fiber's adaptor to render the Templ component
	return adaptor.HTTPHandler(templ.Handler(pages.WelcomePage(pageData)))(c)
}