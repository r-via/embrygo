// Package web provides handlers for the web-facing (HTML) parts of the EmbryGo application.
package web

import (
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	// "github.com/r-via/embrygo/internal/config" // Uncomment if you need to access EmbryGo's specific AppConfig
	"github.com/r-via/embrygo/pkg/translations"
	"github.com/r-via/embrygo/webroot/views/components/heroicons" // Assumes this package is generated and correct
	"github.com/r-via/embrygo/webroot/views/layouts"
	"github.com/r-via/embrygo/webroot/views/pages"

	"github.com/a-h/templ"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/adaptor"
	"github.com/r-via/blitzkit"
)

// Handler holds dependencies for web handlers, such as the logger and BlitzKit server instance.
type Handler struct {
	logger *slog.Logger
	server *blitzkit.Server
}

// NewHandler creates a new Handler for web routes.
// It panics if the server or logger is nil.
func NewHandler(server *blitzkit.Server, logger *slog.Logger) *Handler {
	if logger == nil || server == nil {
		slog.Error("FATAL: Web Handler for EmbryGo requires non-nil server and logger")
		panic("Web Handler initialization failed: missing critical dependencies")
	}
	return &Handler{logger: logger, server: server}
}

// RegisterRoutes registers all web UI routes for the EmbryGo application.
func (h *Handler) RegisterRoutes(rootGroup fiber.Router) {
	h.logger.Info("Registering EmbryGo web routes...")
	rootGroup.Get("/welcome", h.handleWelcomePage)
	rootGroup.Get("/", func(c *fiber.Ctx) error {
		currentBasePath, _ := c.Locals("basePath").(string)
		if currentBasePath == "/" { // Avoid double slash if basePath is root
			currentBasePath = ""
		}
		targetRedirectPath := currentBasePath + "/welcome"
		h.logger.Debug("Redirecting from group root to welcome page", "from", c.Path(), "to", targetRedirectPath)
		return c.Redirect(targetRedirectPath, fiber.StatusFound)
	})
}

// getBasePathFromLocals retrieves the application's base path from Fiber's context locals.
// Defaults to "/" if not found or if the type is incorrect.
func getBasePathFromLocals(c *fiber.Ctx, logger *slog.Logger) string {
	basePathVal := c.Locals("basePath")
	basePath, ok := basePathVal.(string)
	if !ok {
		basePath = "/"
		if logger != nil { // Check logger for nil to prevent panic during early init issues
			logger.Warn("Could not get 'basePath' from locals or wrong type, defaulting to '/'", "type_found", fmt.Sprintf("%T", basePathVal))
		}
	}
	return basePath
}

// getCsrfToken retrieves the CSRF token from Fiber's context locals, if CSRF is enabled.
// Returns an empty string if CSRF is disabled or the token is not found.
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

// checkExecutable attempts to find an executable in PATH and optionally get its version.
// Returns true if found, and a status detail string (version or simple "Found"/"Not found").
func checkExecutable(logger *slog.Logger, execName string, versionArgs ...string) (isOk bool, detail string) {
	path, err := exec.LookPath(execName)
	if err != nil {
		logger.Debug("Executable not found in PATH", "executable", execName, "error", err)
		return false, "Not found in PATH"
	}
	logger.Debug("Executable found", "executable", execName, "path", path)

	if len(versionArgs) > 0 {
		cmd := exec.Command(execName, versionArgs...)
		output, errCmd := cmd.CombinedOutput()
		if errCmd != nil {
			logger.Warn("Failed to get version for executable", "executable", execName, "error", errCmd, "output", string(output))
			return true, fmt.Sprintf("Found (version check failed: %s)", strings.TrimSpace(string(output)))
		}
		versionStr := strings.TrimSpace(string(output))
		if lines := strings.Split(versionStr, "\n"); len(lines) > 0 {
			versionStr = strings.TrimSpace(lines[0])
		}
		if len(versionStr) > 50 { // Truncate long version strings
			versionStr = versionStr[:47] + "..."
		}
		return true, fmt.Sprintf("Found: %s", versionStr)
	}
	return true, "Found in PATH"
}

// checkFileExists checks if a file exists at the given absolute path.
// Returns true if found, and a status detail string.
func checkFileExists(logger *slog.Logger, filePath string, description string) (isOk bool, detail string) {
	_, err := os.Stat(filePath)
	if err == nil {
		logger.Debug("File exists", "description", description, "path", filePath)
		return true, fmt.Sprintf("Exists: %s", filePath)
	}
	if os.IsNotExist(err) {
		logger.Debug("File does not exist", "description", description, "path", filePath)
		return false, fmt.Sprintf("Not found: %s", filePath)
	}
	logger.Warn("Error checking file existence", "description", description, "path", filePath, "error", err)
	return false, fmt.Sprintf("Error checking: %s (%v)", filePath, err)
}

// handleWelcomePage serves the main welcome page.
// It dynamically checks the status of various project components and tools.
func (h *Handler) handleWelcomePage(c *fiber.Ctx) error {
	lang := "en"
	trans := translations.GetTranslations(lang)

	basePath := getBasePathFromLocals(c, h.logger)
	csrfToken := getCsrfToken(c, h.server)
	bkConfig := h.server.GetConfig()

	h.logger.Debug("Handling /welcome page request", "lang", lang, "basePath", basePath)

	features := make([]pages.FeatureStatus, 0, 10)

	// Define icons for different states
	okIcon := heroicons.Outline_Check_Circle(templ.Attributes{"class": "w-5 h-5 text-success"})
	// Ensure Outline_X_Circle and Outline_Exclamation_Triangle (or similar) are generated in your heroicons package
	errorIcon := heroicons.Outline_X_Circle(templ.Attributes{"class": "w-5 h-5 text-error"})
	// warningIcon := heroicons.Outline_Exclamation_Triangle(templ.Attributes{"class": "w-5 h-5 text-warning"}) // Example for a warning state

	addFeature := func(nameKey string, isOk bool, statusKey string, detail string, icon templ.Component) {
		actualIcon := icon
		if icon == nil { // If no specific icon provided, choose based on IsOk
			if isOk {
				actualIcon = okIcon
			} else {
				actualIcon = errorIcon // Default error icon
			}
		}
		features = append(features, pages.FeatureStatus{
			Name:         nameKey,
			IsOk:         isOk,
			StatusText:   statusKey,
			StatusDetail: detail,
			Icon:         actualIcon,
		})
	}

	// 1. Go Backend
	addFeature("go_backend", true, "status_ok", "Running", okIcon)
	// 2. Fiber Framework
	addFeature("fiber_framework", true, "status_ok", "Active", okIcon)
	// 3. BlitzKit Server Layer
	addFeature("blitzkit_server", true, "status_ok", fmt.Sprintf("DevMode: %t", bkConfig.DevMode), okIcon)

	// 4. Templ CLI
	templOk, templDetail := checkExecutable(h.logger, "templ", "version")
	addFeature("templ_templating", templOk, ternStatusKey(templOk), templDetail, nil) // Let addFeature decide icon

	// 5. HTMX
	htmxAssetPath := filepath.Join(bkConfig.PublicDir, "htmx.min.js")
	htmxOk, htmxDetail := checkFileExists(h.logger, htmxAssetPath, "HTMX library")
	addFeature("htmx", htmxOk, ternStatusKey(htmxOk), htmxDetail, heroicons.Outline_Beaker(templ.Attributes{"class": "w-5 h-5 text-info"}))

	// 6. Tailwind CSS
	tailwindAssetPath := filepath.Join(bkConfig.PublicDir, "tailwind.css")
	tailwindOk, tailwindDetail := checkFileExists(h.logger, tailwindAssetPath, "Tailwind CSS file")
	addFeature("tailwind_css", tailwindOk, ternStatusKey(tailwindOk), tailwindDetail, heroicons.Outline_Paint_Brush(templ.Attributes{"class": "w-5 h-5 text-accent"}))

	// 7. DaisyUI
	daisyUIDetail := "Enabled via Tailwind plugin"
	if !tailwindOk {
		daisyUIDetail = "Depends on Tailwind CSS"
	}
	addFeature("daisy_ui", tailwindOk, ternStatusKey(tailwindOk, "status_ok", "status_config_issue"), daisyUIDetail, heroicons.Outline_Sparkles(templ.Attributes{"class": "w-5 h-5 text-primary"}))

	// 8. Heroicons Generator
	var heroiconsInputPath string
	if wd, err := os.Getwd(); err == nil {
		heroiconsInputPath = filepath.Join(wd, "webroot", "views", "components", "heroicons", "heroicons.templ")
	} else {
		heroiconsInputPath = "webroot/views/components/heroicons/heroicons.templ" // Fallback, might not be reliable
		h.logger.Warn("Could not get current working directory for heroicons path construction", "error", err)
	}
	heroiconsOk, heroiconsDetail := checkFileExists(h.logger, heroiconsInputPath, "Heroicons source .templ")
	addFeature("heroicons_generator", heroiconsOk, ternStatusKey(heroiconsOk), heroiconsDetail, heroicons.Outline_Code_Bracket(templ.Attributes{"class": "w-5 h-5 text-secondary"}))

	// 9. Slog Logging
	addFeature("slog_logging", h.logger != nil, ternStatusKey(h.logger != nil), "Logger configured", heroicons.Outline_Document_Text(templ.Attributes{"class": "w-5 h-5 text-warning"}))

	// 10. Air Live Reload
	airIsOk, airDetail := false, "Disabled (only active in dev mode with 'make run')"
	if bkConfig.DevMode {
		airIsOk, airDetail = checkExecutable(h.logger, "air", "-v")
	}
	addFeature("air_live_reload", airIsOk, ternStatusKey(airIsOk, "status_ok", "status_not_found_or_disabled"), airDetail, heroicons.Outline_Arrow_Path(templ.Attributes{"class": "w-5 h-5 text-neutral"}))

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
		Features: features,
	}

	return adaptor.HTTPHandler(templ.Handler(pages.WelcomePage(pageData)))(c)
}

// ternStatusKey is a helper to choose a status translation key based on a condition.
// It defaults to "status_ok" or "status_error".
func ternStatusKey(condition bool, trueKeyOptional ...string) string {
	trueKey := "status_ok"
	falseKey := "status_error" // Default false key

	if len(trueKeyOptional) > 0 && trueKeyOptional[0] != "" {
		trueKey = trueKeyOptional[0]
	}
	// If you want to specify a different false key
	if len(trueKeyOptional) > 1 && trueKeyOptional[1] != "" {
		falseKey = trueKeyOptional[1]
	}

	if condition {
		return trueKey
	}
	return falseKey
}
