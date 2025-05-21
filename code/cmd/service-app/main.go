// File: cmd/service-app/main.go
package main

import (
	"errors"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	// EmbryGo internal packages
	"github.com/r-via/embrygo/internal/config"
	webHandlerPkg "github.com/r-via/embrygo/internal/handlers/web"

	// Third-party packages
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/basicauth"
	"github.com/gofiber/fiber/v2/middleware/csrf"
	"github.com/gofiber/fiber/v2/middleware/requestid"
	"github.com/joho/godotenv"

	// BlitzKit (assumed to be an accessible module, e.g., github.com/r-via/blitzkit)
	"github.com/r-via/blitzkit"
)

func main() {
	// Attempt to load .env file. If it doesn't exist, continue gracefully.
	_ = godotenv.Load(".env")

	// Determine environment and logging settings
	isProduction := os.Getenv("APP_ENV") != "development"
	logLevel := slog.LevelInfo
	addSourceLog := false // Add source file/line to logs only in dev
	environmentName := "production"

	if !isProduction {
		logLevel = slog.LevelDebug
		addSourceLog = true
		environmentName = "development"
	}

	// Initialize structured logger (slog)
	handlerOpts := &slog.HandlerOptions{Level: logLevel, AddSource: addSourceLog}
	logger := slog.New(slog.NewTextHandler(os.Stdout, handlerOpts))
	slog.SetDefault(logger) // Make this logger the default for the application

	logger.Info("EmbryGo Application Starting...",
		"environment", environmentName,
		"module_path", "github.com/r-via/embrygo", // Replace with your actual module path from go.mod
	)

	// Load application-specific configuration from internal/config
	if err := config.LoadConfig(logger); err != nil {
		logger.Error("FATAL: Application config loading failed", "error", err)
		os.Exit(1)
	}

	// Determine the base path for the application from APP_BASE_URL
	// This is crucial for routing and asset URLs if deploying to a sub-path.
	basePath := "/"
	if config.AppConfig.AppBaseURL != "" {
		parsedURL, err := url.Parse(config.AppConfig.AppBaseURL)
		if err != nil {
			logger.Error("FATAL: Invalid APP_BASE_URL in .env or environment",
				"url", config.AppConfig.AppBaseURL, "error", err)
			os.Exit(1)
		}
		// Use the path component of the URL, ensuring it starts with '/' and doesn't end with one (unless it's just "/")
		if parsedURL.Path != "" && parsedURL.Path != "/" {
			basePath = strings.TrimSuffix(parsedURL.Path, "/")
			if !strings.HasPrefix(basePath, "/") {
				basePath = "/" + basePath
			}
		}
	}
	logger.Info("Using application base path for routing and assets",
		"derived_basePath", basePath,
		"source_APP_BASE_URL", config.AppConfig.AppBaseURL,
	)

	// Check for admin credentials (used for an example route)
	if config.AppConfig.AdminUser == "" || config.AppConfig.AdminPass == "" {
		logger.Warn("ADMIN_USER and/or ADMIN_PASS not set in .env. Example admin route will be unprotected or use defaults.")
	}

	// Define security headers (CSP is differentiated for dev/prod)
	defaultSecurityHeaders := map[string]string{
		"X-Frame-Options":           "SAMEORIGIN",
		"X-Content-Type-Options":    "nosniff",
		"Referrer-Policy":           "strict-origin-when-cross-origin",
		"Permissions-Policy":        "geolocation=(), microphone=(), camera=(), payment=(), interest-cohort=()",
		"X-XSS-Protection":          "1; mode=block",
		"Strict-Transport-Security": "max-age=31536000; includeSubDomains", // For HTTPS sites
	}
	// Looser CSP for development (allows WebSocket for live reload, inline styles/scripts if necessary)
	cspDev := "default-src 'self' ws:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; object-src 'none'; frame-ancestors 'self';"
	// Stricter CSP for production
	cspProd := "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; object-src 'none'; frame-ancestors 'self';" // Allow 'unsafe-inline' for Tailwind/DaisyUI if no better solution for now

	if isProduction {
		defaultSecurityHeaders["Content-Security-Policy"] = cspProd
	} else {
		defaultSecurityHeaders["Content-Security-Policy"] = cspDev
	}

	// Configure BlitzKit server
	// Paths are relative to the project root where the binary is run.
	serverConfig := blitzkit.Config{
		Port:               os.Getenv("PORT"), // BlitzKit will default to 8080 if empty or invalid
		DevMode:            !isProduction,
		Logger:             logger,
		PublicDir:          "webroot/www",     // Processed static files are served from here
		CacheDir:           "webroot/cache",   // For L2 cache (BadgerDB)
		SourcesDir:         "webroot/sources", // JS/CSS to be minified by BlitzKit's StaticProcessor
		StaticsDir:         "webroot/statics", // Files to be copied as-is by BlitzKit's StaticProcessor
		EnableCSRF:         true,
		CSRFKeyLookup:      "header:X-CSRF-Token",  // HTMX sends token in this header
		CSRFCookieName:     "__Host-embrygo_csrf_", // Secure prefix for production (HTTPS)
		CSRFExpiration:     12 * time.Hour,         // CSRF token validity
		CSRFCookieSameSite: "Lax",                  // Recommended SameSite policy
		SecurityHeaders:    defaultSecurityHeaders, // Apply our defined security headers
		EnableMetrics:      true,                   // Expose Prometheus metrics at /metrics
		EnableRateLimiter:  false,                  // Keep false for simple EmbryGo starter
		// ErrorComponentGenerator: func(err error, code int, isDev bool) templ.Component { ... } // Optional: For custom error pages via Templ
	}
	if !isProduction {
		// For local development (often HTTP), __Host- prefix won't work.
		serverConfig.CSRFCookieName = "embrygo_csrf_dev_"
	}
	logger.Info("BlitzKit Server Effective Configuration Initializing...", slog.Any("config_summary",
		map[string]interface{}{
			"Port": serverConfig.Port, "DevMode": serverConfig.DevMode, "PublicDir": serverConfig.PublicDir,
			"CacheDir": serverConfig.CacheDir, "EnableCSRF": serverConfig.EnableCSRF, "EnableMetrics": serverConfig.EnableMetrics,
			"CSRFCookieName": serverConfig.CSRFCookieName,
		}))

	// Create the BlitzKit server instance
	// BlitzKit handles initialization of Fiber, its own base middlewares, static processing, and monitoring.
	server, errServer := blitzkit.NewServer(serverConfig)
	if errServer != nil {
		logger.Error("FATAL: Failed to initialize BlitzKit server", "error", errServer)
		os.Exit(1)
	}
	app := server.App() // Get the underlying Fiber app instance from BlitzKit

	// Initialize EmbryGo-specific web handlers
	webHandler := webHandlerPkg.NewHandler(server, logger)
	logger.Info("EmbryGo web handlers initialized.")

	// --- Application-Specific Middlewares (added after BlitzKit's base middlewares) ---
	app.Use(requestid.New()) // Add a unique Request ID to each request

	// Middleware to set the calculated `basePath` into Fiber's context locals.
	// This makes it available to handlers (e.g., for `assetUrl` in templates).
	app.Use(func(c *fiber.Ctx) error {
		c.Locals("basePath", basePath) // basePath is derived from APP_BASE_URL
		return c.Next()
	})
	logger.Info("Middleware for 'basePath' in locals has been set.")

	// Explicit CSRF Protection Middleware configuration (supplements/overrides BlitzKit's if it also sets one)
	// This gives EmbryGo direct control over CSRF settings.
	if serverConfig.EnableCSRF {
		csrfMw := csrf.New(csrf.Config{
			KeyLookup:      serverConfig.CSRFKeyLookup,
			CookieName:     serverConfig.CSRFCookieName,
			CookieSameSite: serverConfig.CSRFCookieSameSite,
			Expiration:     serverConfig.CSRFExpiration,
			CookieSecure:   isProduction,            // CSRF cookie should be secure in production (HTTPS)
			CookieHTTPOnly: true,                    // CSRF cookie should be HTTPOnly
			ContextKey:     blitzkit.CSRFContextKey, // Key to store token in c.Locals
			ErrorHandler: func(c *fiber.Ctx, err error) error {
				reqIDVal := c.Locals("requestid")
				reqID, _ := reqIDVal.(string)
				clientIP := blitzkit.GetClientIP(c.Get(fiber.HeaderXForwardedFor), c.IP())
				logger.Warn("CSRF validation failed",
					"ip", clientIP, "path", c.Path(), "request_id", reqID, "error_message", err.Error())
				// For HTMX, it's often better to return 403 and let HTMX handle it,
				// or a specific HTMX response if configured.
				// Defaulting to a standard 403 error page for now.
				return fiber.NewError(fiber.StatusForbidden, "CSRF token mismatch or missing. Please refresh the page and try again.")
			},
		})
		app.Use(csrfMw) // Apply CSRF protection globally or to specific groups
		logger.Info("CSRF protection middleware enabled explicitly by EmbryGo.")
	} else {
		// If CSRF is disabled, set a local so `getCsrfToken` in handlers can know.
		app.Use(func(c *fiber.Ctx) error {
			c.Locals(blitzkit.CSRFContextKey, "csrf-disabled")
			return c.Next()
		})
		logger.Warn("CSRF protection middleware IS DISABLED based on BlitzKit config.")
	}

	// --- Routing Setup ---
	// All application-specific routes will be grouped under the calculated `basePath`.
	// If basePath is "/", this is effectively `app.Group("/")`.
	// If basePath is "/myapp", routes will be `/myapp/welcome`, etc.
	rootGroup := app.Group(basePath)
	logger.Info("Registering EmbryGo application routes", "under_group_path_prefix", basePath)

	// Example Admin Route (optional, demonstrates BasicAuth with credentials from .env)
	if config.AppConfig.AdminUser != "" && config.AppConfig.AdminPass != "" {
		adminAuthConfig := basicauth.Config{
			Users: map[string]string{config.AppConfig.AdminUser: config.AppConfig.AdminPass},
			Realm: "EmbryGo Admin Area (Example)",
		}
		// This group will be at `basePath/admin-example`
		adminExampleGroup := rootGroup.Group("/admin-example", basicauth.New(adminAuthConfig))
		adminExampleGroup.Get("/", func(c *fiber.Ctx) error {
			return c.Status(fiber.StatusOK).SendString("Welcome to the (example) protected admin area of EmbryGo!")
		})
		logger.Info("Example admin route registered and protected", "full_path_example", basePath+"/admin-example")
	} else {
		// Unprotected version if credentials are not set
		rootGroup.Get("/admin-example", func(c *fiber.Ctx) error {
			return c.Status(fiber.StatusOK).SendString("Example admin area (Currently UNPROTECTED - Set ADMIN_USER/ADMIN_PASS in .env to protect).")
		})
		logger.Warn("Admin credentials not set; example admin route is UNPROTECTED.", "full_path_example", basePath+"/admin-example")
	}

	// Register web UI routes (e.g., /welcome) under the `rootGroup`
	webHandler.RegisterRoutes(rootGroup)
	logger.Info("EmbryGo Web UI routes (e.g., /welcome) registered successfully.")

	// Static File Serving for `webroot/www`
	// BlitzKit's `StaticProcessor` (run during `NewServer`) populates `webroot/www`.
	// This `app.Static` serves those files.
	// The first argument to `app.Static` is the URL prefix.
	// Since `webroot/www` contains `tailwind.css`, `app.js` at its root,
	// and `basePath` is our app's root, we serve from `basePath`.
	if _, errStat := os.Stat(serverConfig.PublicDir); errStat == nil {
		logger.Info("Registering static file serving for public assets.",
			"url_prefix", basePath, // Files in PublicDir will be available under this prefix
			"physical_directory", serverConfig.PublicDir)

		// Example: if basePath = "/myapp", then a file `webroot/www/style.css`
		// will be accessible at `http://host/myapp/style.css`.
		// If basePath = "/", then `webroot/www/style.css` is at `http://host/style.css`.
		app.Static(basePath, serverConfig.PublicDir, fiber.Static{
			Compress:      true,
			ByteRange:     true,
			Browse:        !isProduction, // Allow directory browsing in development for easier debugging
			CacheDuration: 1 * time.Hour, // Browser cache duration for static assets
			MaxAge:        3600,          // Corresponds to CacheDuration in seconds
		})
	} else {
		logger.Error("Public static directory not found, web UI assets (CSS, JS) may not be served!",
			"expected_path", serverConfig.PublicDir, "stat_error", errStat.Error())
	}
	// Note: BlitzKit's `setupMonitoring` registers /metrics and /health at the *true* root of the Fiber app (ignoring basePath).

	// --- Start Server ---
	// Run the server in a goroutine so it doesn't block the main thread (for graceful shutdown).
	go func() {
		if startErr := server.Start(); startErr != nil { // server.Start() is from BlitzKit
			// http.ErrServerClosed is expected on graceful shutdown, so don't treat it as a fatal crash.
			if !errors.Is(startErr, http.ErrServerClosed) {
				logger.Error("FATAL: Server failed to start or crashed unexpectedly.", "error", startErr)
				// Attempt to signal the current process to terminate for graceful shutdown handling.
				p, findErr := os.FindProcess(os.Getpid())
				if findErr == nil {
					// Send SIGTERM, which is caught by our signal handler below.
					if sigErr := p.Signal(syscall.SIGTERM); sigErr != nil {
						logger.Error("Failed to send SIGTERM to self after server crash", "error", sigErr)
						os.Exit(1) // Fallback to abrupt exit
					}
				} else {
					logger.Error("Failed to find own process after server crash", "error", findErr)
					os.Exit(1) // Fallback to abrupt exit
				}
			}
		}
	}()

	// --- Graceful Shutdown Handling ---
	// Wait for interrupt signals (Ctrl+C) or termination signals.
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	receivedSignal := <-quit // Block until a signal is received
	logger.Warn("Shutdown signal received.", "signal", receivedSignal.String())

	logger.Info("Initiating graceful shutdown sequence...")
	if shutdownErr := server.Shutdown(); shutdownErr != nil { // server.Shutdown() is from BlitzKit
		logger.Error("Error during server shutdown procedures", "error", shutdownErr)
	} else {
		logger.Info("Server shutdown sequence completed successfully.")
	}

	logger.Info("EmbryGo application has shut down.")
}
