// internal/handlers/web/handler.go
package web

import (
	"log/slog"
	// "strings" // Peut ne plus être nécessaire ici
	"github.com/r-via/embrygo/pkg/translations"
	"github.com/r-via/embrygo/webroot/views/layouts"
	"github.com/r-via/embrygo/webroot/views/pages" // pages.WelcomePageData sera plus simple

	"github.com/a-h/templ"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/adaptor"
	"github.com/r-via/blitzkit"
)

type Handler struct {
	logger *slog.Logger
	server *blitzkit.Server
}

func NewHandler(server *blitzkit.Server, logger *slog.Logger) *Handler {
	if logger == nil || server == nil {
		slog.Error("FATAL: Web Handler for EmbryGo requires non-nil server and logger")
		panic("Web Handler initialization failed: missing critical dependencies")
	}
	return &Handler{logger: logger, server: server}
}

func (h *Handler) RegisterRoutes(rootGroup fiber.Router) {
	h.logger.Info("Registering EmbryGo web routes...")
	rootGroup.Get("/welcome", h.handleWelcomePage)
	rootGroup.Get("/", func(c *fiber.Ctx) error {
		currentBasePath, _ := c.Locals("basePath").(string)
		if currentBasePath == "/" {
			currentBasePath = ""
		}
		targetRedirectPath := currentBasePath + "/welcome"
		h.logger.Debug("Redirecting from root of group to welcome", "from", c.Path(), "to", targetRedirectPath)
		return c.Redirect(targetRedirectPath, fiber.StatusFound)
	})
}

func getBasePathFromLocals(c *fiber.Ctx, logger *slog.Logger) string {
	basePathVal := c.Locals("basePath")
	basePath, ok := basePathVal.(string)
	if !ok {
		basePath = "/"
		if logger != nil {
			logger.Warn("Could not get 'basePath' from locals or wrong type, defaulting to '/'", "type_found", basePathVal)
		}
	}
	return basePath
}

func getCsrfToken(c *fiber.Ctx, server *blitzkit.Server) string {
	if server == nil || !server.GetConfig().EnableCSRF {
		return ""
	}
	csrfVal := c.Locals(blitzkit.CSRFContextKey)
	if tokenStr, ok := csrfVal.(string); ok && tokenStr != "csrf-disabled" {
		return tokenStr
	}
	return ""
}

func (h *Handler) handleWelcomePage(c *fiber.Ctx) error {
	lang := "en"
	trans := translations.GetTranslations(lang)

	basePath := getBasePathFromLocals(c, h.logger)
	csrfToken := getCsrfToken(c, h.server)

	h.logger.Debug("Handling /welcome page", "lang", lang, "basePath", basePath, "csrf_present", csrfToken != "")

	// WelcomePageData est maintenant beaucoup plus simple
	pageData := pages.WelcomePageData{
		Lang:         lang,
		Translations: trans, // Passez seulement les traductions générales
		Base: layouts.BaseData{
			Lang:         lang,
			PageTitle:    trans["welcome_title"],
			Translations: trans,
			CSRFToken:    csrfToken,
			BasePath:     basePath,
		},
		// La liste des utilitaires est maintenant définie directement dans welcome.templ
	}

	return adaptor.HTTPHandler(templ.Handler(pages.WelcomePage(pageData)))(c)
}
