#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT_NAME = "embrygo-project"  # Nom du dossier racine du projet EmbryGo à créer
BASE_TEST_DIR = "tests"                # Le projet EmbryGo sera créé dans BASE_TEST_DIR/PROJECT_ROOT_NAME
GO_MODULE_NAME = "github.com/r-via/embrygo" # <<< MODIFIEZ CECI !
SERVICE_APP_NAME = "service-app"
PYTHON_VENV_DIR_NAME = ".venv" # Nom du dossier du venv dans tools/

# --- Helper pour créer des fichiers ---
def create_file(filepath: Path, content: str = ""):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"  Created: {filepath}")

def main():
    project_path = Path(BASE_TEST_DIR) / PROJECT_ROOT_NAME
    print(f"🚀 Generating EmbryGo project structure in: {project_path.resolve()}")

    if project_path.exists():
        print(f"⚠️  Warning: Directory '{project_path}' already exists.")
        if input("    Remove existing directory and continue? (y/N): ").lower() != 'y':
            print("Aborted.")
            return
        shutil.rmtree(project_path)
        print(f"  Removed existing directory: {project_path}")

    project_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created root directory: {project_path}")

    # --- Structure des dossiers et fichiers .gitkeep ---
    dirs_to_create = [
        f"cmd/{SERVICE_APP_NAME}",
        "internal/config",
        "internal/database",
        "internal/handlers/api",
        "internal/handlers/web",
        "internal/middleware",
        "internal/models",
        "internal/router",
        "internal/services/welcome",
        "internal/services", # Pour le .gitkeep parent
        "pkg/helpers",
        "pkg/translations",
        "tools",
        # "tools/.heroicons_cache", # Créé par le script d'icônes
        # "tools/node_modules",     # Créé par npm
        f"tools/{PYTHON_VENV_DIR_NAME}", # Le venv lui-même
        "webroot/cache",            # Créé par BlitzKit
        "webroot/sources",
        "webroot/statics",
        "webroot/www",
        "webroot/views/components/heroicons",
        "webroot/views/layouts",
        "webroot/views/pages",
    ]

    gitkeep_dirs = [ # Dossiers qui pourraient être vides au départ
        "internal/database",
        "internal/handlers/api",
        "internal/middleware",
        "internal/models",
        "internal/router",
        "internal/services",
        "internal/services/welcome", # Si les fichiers go sont des placeholders
        "webroot/www", # Important
        "webroot/cache", # BlitzKit le crée, mais on peut le mettre pour la structure Git
        "webroot/sources", # Si app.js est optionnel au début
    ]

    for d_path_str in dirs_to_create:
        dir_path = project_path / d_path_str
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created dir: {dir_path}")

    for gk_dir_str in gitkeep_dirs:
        gitkeep_file = project_path / gk_dir_str / ".gitkeep"
        create_file(gitkeep_file)

    print("\n📝 Generating file contents...")

    # --- Fichiers à la racine ---
    create_file(project_path / ".air.toml", f"""
root = "."
tmp_dir = "tmp"

[build]
  cmd = "make templ-generate && go build -o ./tmp/main ./cmd/{SERVICE_APP_NAME}/main.go"
  bin = "./tmp/main"
  full_bin = "./tmp/main" # Assurez-vous que full_bin est correct pour votre OS si différent
  delay = 1000 # ms
  stop_on_error = true
  log = "air_errors.log"
  send_interrupt = true
  kill_delay = 500 # ms

[watch]
  includes = [
    "cmd/**/*.go",
    "internal/**/*.go",
    "pkg/**/*.go",
    "webroot/views/**/*.templ",
    "go.mod",
    ".env"
  ]
  excludes = [
    "tmp/*",
    "bin/*",
    "vendor/*",
    "webroot/www/*", # Ignorer les fichiers générés dans www
    "webroot/views/**/*_templ.go",
    "tools/node_modules/*",
    "tools/{PYTHON_VENV_DIR_NAME}/*"
  ]

[log]
  time = true

[misc]
  on_watch_event_cmd = '''
    changed_file_ext={{{{.ChangedFileExt}}}};
    changed_file_path={{{{.ChangedFilePath}}}};
    if [[ "$changed_file_ext" == ".css" ]] || [[ "$changed_file_ext" == ".js" ]]; then
      if [[ "$changed_file_path" == tools/input.css ]] || [[ "$changed_file_path" == webroot/sources/app.js ]]; then
        echo 'Frontend source changed, rebuilding CSS/JS...';
        make tailwind;
      fi
    fi
  '''
""")

    create_file(project_path / ".env.example", """
APP_ENV=development # development or production
PORT=8080
APP_BASE_URL=http://localhost:8080
ADMIN_USER=admin
ADMIN_PASS=secret

# BlitzKit Cache (optionnel pour EmbryGo simple, mais bon à montrer)
# CACHE_L1_DEFAULT_TTL=5m
# CACHE_L2_DEFAULT_TTL=24h
# BADGER_GC_INTERVAL=1h
""")

    create_file(project_path / ".gitignore", f"""
# Go binaries and build artifacts
/bin/
/tmp/
{SERVICE_APP_NAME}
{SERVICE_APP_NAME}.exe
*.test
*.prof

# Go Vendor directory (if used)
/vendor/

# Frontend build output & caches
/webroot/www/*
!/webroot/www/.gitkeep
/webroot/cache/*
/tools/node_modules/
/tools/{PYTHON_VENV_DIR_NAME}/
/tools/.heroicons_cache/

# Node log files
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Environment files
.env
.env.*
!.env.example

# OS generated files
.DS_Store
Thumbs.db
ehthumbs.db
._*

# IDE settings & metadata
.idea/
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.sublime-project
*.sublime-workspace

# Air live reload log
air_errors.log

# Miscellaneous
*.bak
*.swp
*~
""")

    create_file(project_path / "Makefile", f"""
.PHONY: all run build clean tailwind heroicons templ-generate setup-tools setup-node-tools setup-python-tools copy-statics minify-sources start-prod fmt tidy

# Variables
APP_NAME={SERVICE_APP_NAME}
CMD_PATH=./cmd/$(APP_NAME)
OUTPUT_DIR=./bin
OUTPUT_BINARY=$(OUTPUT_DIR)/$(APP_NAME)

GO_MODULE_NAME={GO_MODULE_NAME} # Utilisé pour l'information, pas directement dans les commandes ici

TAILWIND_INPUT_CSS=./tools/input.css
TAILWIND_OUTPUT_CSS=./webroot/www/css/tailwind.css # Sortie dans www/css/
TAILWIND_CONFIG=./tools/tailwind.config.js

PYTHON_VENV_DIR=./tools/{PYTHON_VENV_DIR_NAME}
PIP_EXEC=$(PYTHON_VENV_DIR)/bin/pip
HEROICONS_CMD=$(PYTHON_VENV_DIR)/bin/templ-generate-heroicons
HEROICONS_INPUT_DIR=./webroot/views
HEROICONS_OUTPUT_DIR=./webroot/views/components/heroicons
HEROICONS_CACHE_DIR=./tools/.heroicons_cache # Créé par le script d'icônes
EMBRYGO_BASE_ICONS=check_circle,information_circle # Icônes pour la page welcome

# Default target
all: build

# Setup Node.js and Python tools
setup-tools: setup-node-tools setup-python-tools

setup-node-tools:
	@if [ ! -d "./tools/node_modules" ]; then \\
		echo ">>> Installing Node.js dependencies (Tailwind, DaisyUI)..."; \\
		(cd tools && npm install); \\
	else \\
		echo ">>> Node.js tools dependencies already installed."; \\
	fi

setup-python-tools: $(PYTHON_VENV_DIR)/touchfile

$(PYTHON_VENV_DIR)/touchfile: tools/requirements.txt
	@echo ">>> Setting up Python virtual environment and installing templ-heroicons-generator..."
	@if [ ! -d "$(PYTHON_VENV_DIR)" ]; then \\
		python3 -m venv $(PYTHON_VENV_DIR); \\
	fi
	$(PIP_EXEC) install -r tools/requirements.txt
	@touch $(PYTHON_VENV_DIR)/touchfile
	@echo ">>> Python tools setup complete."

# Generate Tailwind CSS
tailwind: setup-node-tools
	@echo ">>> Generating Tailwind CSS..."
	@mkdir -p ./webroot/www/css # Assurer que le dossier de sortie existe
	(cd tools && npx tailwindcss -i ./input.css -o ../$(TAILWIND_OUTPUT_CSS) --minify)
	@echo ">>> Tailwind CSS generated: $(TAILWIND_OUTPUT_CSS)"

# Generate Heroicons Templ components
heroicons: setup-python-tools
	@echo ">>> Generating Heroicons using '$(HEROICONS_CMD)'..."
	@mkdir -p $(HEROICONS_CACHE_DIR)
	@mkdir -p $(HEROICONS_OUTPUT_DIR)
	$(HEROICONS_CMD) \\
		--input-dir $(HEROICONS_INPUT_DIR) \\
		--output-dir $(HEROICONS_OUTPUT_DIR) \\
		--cache-dir $(HEROICONS_CACHE_DIR) \\
		--icons $(EMBRYGO_BASE_ICONS) \\
		--default-class "size-6"
	@echo ">>> Heroicons .templ file generated."
	templ generate $(HEROICONS_OUTPUT_DIR)
	@echo ">>> Templ Go files for Heroicons generated."

# Generate all Templ Go files
templ-generate:
	@echo ">>> Generating all Templ Go files from ./webroot/views/..."
	templ generate ./webroot/views/...
	@echo ">>> All Templ Go files generated."

# Copy static assets from webroot/statics to webroot/www
copy-statics:
	@echo ">>> Copying static assets..."
	@mkdir -p ./webroot/www/js # Assurer que le dossier js existe
	@cp -R ./webroot/statics/* ./webroot/www/ # Copie tout, y compris favicon.ico et htmx.min.js
	# Si htmx.min.js est dans webroot/statics/js/, alors:
	# @cp ./webroot/statics/favicon.ico ./webroot/www/favicon.ico
	# @cp ./webroot/statics/js/htmx.min.js ./webroot/www/js/htmx.min.js
	@echo ">>> Static assets copied."

# Minify source assets (app.js) from webroot/sources to webroot/www
# Note: This is a placeholder. You'd use a JS minifier like esbuild, terser, or BlitzKit's processor.
minify-sources:
	@echo ">>> Minifying source assets (e.g., app.js)..."
	@mkdir -p ./webroot/www/js
	@cp ./webroot/sources/app.js ./webroot/www/js/app.js # Simple copy pour l'instant
	@echo ">>> Source assets 'minified' (copied for now)."


# Build the application: generates all assets and compiles Go
build: clean tailwind heroicons templ-generate copy-statics minify-sources
	@echo ">>> Building Go application $(APP_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	go build -ldflags="-s -w" -o $(OUTPUT_BINARY) $(CMD_PATH)/main.go
	@echo ">>> Build complete: $(OUTPUT_BINARY)"

# Run the application using Air for live reload (development)
# Air's build command already handles templ-generate and go build.
# We ensure frontend assets are built before Air starts.
run: tailwind heroicons copy-statics minify-sources
	@echo ">>> Starting application with Air live reload (module: $(GO_MODULE_NAME))..."
	APP_ENV=development air -c .air.toml

# Run the built binary (production-like)
start-prod: $(OUTPUT_BINARY)
	@echo ">>> Starting production build of $(APP_NAME)..."
	APP_ENV=production $(OUTPUT_BINARY)

# Clean build artifacts and generated files
clean:
	@echo ">>> Cleaning build artifacts, generated files, and virtual environments..."
	@rm -f $(OUTPUT_BINARY)
	@rm -rf ./tmp/*
	@rm -rf ./webroot/www/*
	@touch ./webroot/www/.gitkeep
	@rm -rf ./webroot/cache/*
	@rm -rf ./tools/node_modules
	@rm -rf $(PYTHON_VENV_DIR)
	@rm -rf $(HEROICONS_CACHE_DIR)
	@echo ">>> Clean complete."

# Format Go code
fmt:
	@echo ">>> Formatting Go code..."
	go fmt ./...

# Tidy Go modules
tidy:
	@echo ">>> Tidying Go modules..."
	go mod tidy
""")

    create_file(project_path / "README.md", f"""
# EmbryGo: {GO_MODULE_NAME}

Minimalist Go & Templ Web Starter with HTMX & Tailwind CSS.

Based on the BlitzKit stack, EmbryGo provides a clean foundation to kickstart your Go web projects.
It features a Go backend (powered by Fiber & BlitzKit), server-side Templ components,
HTMX for dynamic UI, and Tailwind CSS with DaisyUI for styling.
Includes live-reload, build tools, and best practices.

## Features

*   **Go Backend**: Fiber framework with a BlitzKit server layer (logging, config, CSRF, security, static file processing).
*   **Templ**: Type-safe HTML templating directly in Go.
*   **HTMX**: For enhancing HTML with AJAX capabilities without complex JavaScript.
*   **Tailwind CSS & DaisyUI**: Utility-first CSS for rapid UI development.
*   **Heroicons**: SVG icons as Templ components, generated by `templ-heroicons-generator`.
*   **Live Reload**: Using Air for development.
*   **Makefile**: For easy build, run, and utility commands.
*   **Configuration**: `.env` file support.
*   **Logging**: Structured logging with `slog`.

## Project Structure

(You can add a brief overview of the generated structure here later)

## Prerequisites (Development)

*   Go (e.g., 1.21+)
*   Node.js and npm (for Tailwind CSS & DaisyUI)
*   Python 3.8+ (with `venv` module)
*   Templ CLI (`go install github.com/a-h/templ/cmd/templ@latest`)
*   Air (`go install github.com/cosmtrek/air@latest`)

The `templ-heroicons-generator` Python package will be installed in a local virtual environment via the Makefile.

## Getting Started

1.  **Clone or Generate:**
    This project is typically generated by a script. If you cloned it, proceed.

2.  **Copy Environment Configuration:**
    ```bash
    cp .env.example .env
    ```
    Modify `.env` as needed (especially `APP_BASE_URL` if not `http://localhost:8080`).

3.  **Install Tools & Dependencies:**
    This command will set up Node.js dependencies (for Tailwind) and Python dependencies (for Heroicons generation) in local `tools/` subdirectories.
    ```bash
    make setup-tools
    ```

4.  **Run in Development Mode (with Live Reload):**
    This will build initial frontend assets and then start the Air live reloader.
    ```bash
    make run
    ```
    The application will be available at `http://localhost:PORT` (default: `http://localhost:8080`).
    The main page is `/welcome`.

5.  **Build for Production:**
    ```bash
    make build
    ```
    This creates an optimized binary in `./bin/{SERVICE_APP_NAME}`.

6.  **Run Production Build:**
    ```bash
    make start-prod
    # or directly:
    # APP_ENV=production ./bin/{SERVICE_APP_NAME}
    ```

## Available Makefile Targets

*   `make all` or `make build`: Builds the entire application.
*   `make run`: Runs the app in development mode with live reload.
*   `make clean`: Removes build artifacts and generated files.
*   `make setup-tools`: Installs Node.js and Python tool dependencies.
*   `make tailwind`: Generates Tailwind CSS.
*   `make heroicons`: Generates Heroicon Templ components.
*   `make templ-generate`: Compiles all `.templ` files to Go.
*   `make copy-statics`: Copies files from `webroot/statics` to `webroot/www`.
*   `make minify-sources`: 'Minifies' (currently copies) `webroot/sources/app.js` to `webroot/www/js/app.js`.
*   `make start-prod`: Runs the production-built binary.
*   `make fmt`: Formats Go code.
*   `make tidy`: Tidies Go module dependencies.

## Technologies Used

*   Go
*   Fiber
*   BlitzKit (Custom Server Layer)
*   Templ
*   HTMX
*   Tailwind CSS
*   DaisyUI
*   Heroicons (via templ-heroicons-generator)
*   Slog
*   Air (Live Reload)
""")

    # --- cmd/service-app/main.go ---
    create_file(project_path / f"cmd/{SERVICE_APP_NAME}/main.go", f"""
package main

import (
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"{GO_MODULE_NAME}/internal/config"
	webHandlerPkg "{GO_MODULE_NAME}/internal/handlers/web"
	"strings"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/basicauth"
	"github.com/gofiber/fiber/v2/middleware/csrf"
    "github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/fiber/v2/middleware/requestid"
	"github.com/joho/godotenv"
	"github.com/r-via/blitzkit" // Assuming blitzkit is a public or accessible module
)

func main() {{
	_ = godotenv.Load(".env")

	isProduction := os.Getenv("APP_ENV") != "development"
	logLevel := slog.LevelInfo
	addSource := false
	environment := "production"

	if !isProduction {{
		logLevel = slog.LevelDebug
		addSource = true
		environment = "development"
	}}

	handlerOpts := &slog.HandlerOptions{{Level: logLevel, AddSource: addSource}}
	logger := slog.New(slog.NewTextHandler(os.Stdout, handlerOpts))
	slog.SetDefault(logger)

	logger.Info("EmbryGo Application Starting...", "environment", environment, "module", "{GO_MODULE_NAME}")

	if err := config.LoadConfig(logger); err != nil {{
		logger.Error("FATAL: Config loading failed", "error", err)
		os.Exit(1)
	}}
    
	basePath := "/"
	if config.AppConfig.AppBaseURL != "" {{
		parsedURL, err := url.Parse(config.AppConfig.AppBaseURL)
		if err != nil {{
			logger.Error("FATAL: Invalid APP_BASE_URL", "url", config.AppConfig.AppBaseURL, "error", err)
			os.Exit(1)
		}}
		if parsedURL.Path != "" && parsedURL.Path != "/" {{
			basePath = strings.TrimSuffix(parsedURL.Path, "/")
			if !strings.HasPrefix(basePath, "/") {{ basePath = "/" + basePath }}
		}}
	}}
	logger.Info("Using application base path for routing", "basePath", basePath, "source_url", config.AppConfig.AppBaseURL)

	if config.AppConfig.AdminUser == "" || config.AppConfig.AdminPass == "" {{
		logger.Warn("ADMIN_USER and/or ADMIN_PASS not set. Example admin routes might be unprotected.")
	}}

	// Default Security Headers from BlitzKit example
	// You might want to refine CSP for EmbryGo's specific needs if it evolves.
	defaultSecurityHeaders := map[string]string{{
		"X-Frame-Options":           "SAMEORIGIN",
		"X-Content-Type-Options":    "nosniff",
		"Referrer-Policy":           "strict-origin-when-cross-origin",
		"Permissions-Policy":        "geolocation=(), microphone=(), camera=(), payment=(), interest-cohort=()",
		"X-XSS-Protection":          "1; mode=block",
		"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
		// CSP for dev (looser for live reload, etc.) vs prod
	}}
    cspDev := "default-src 'self' ws:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'self';"
    cspProd := "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'self';"
    if isProduction {{
        defaultSecurityHeaders["Content-Security-Policy"] = cspProd
    }} else {{
        defaultSecurityHeaders["Content-Security-Policy"] = cspDev
    }}


	serverConfig := blitzkit.Config{{
		Port:               os.Getenv("PORT"), // BlitzKit will default if empty
		DevMode:            !isProduction,
		Logger:             logger,
		PublicDir:          "webroot/www",
		CacheDir:           "webroot/cache", 
		SourcesDir:         "webroot/sources",
		StaticsDir:         "webroot/statics",
		EnableCSRF:         true,
		CSRFCookieName:     "__Host-embrygo_csrf_", // Use __Host- prefix for production
		CSRFKeyLookup:      "header:X-CSRF-Token",
		CSRFExpiration:     12 * time.Hour,
        CSRFCookieSameSite: "Lax",
		SecurityHeaders:    defaultSecurityHeaders,
		EnableMetrics:      true,
        EnableRateLimiter:  false, // Disabled for simple EmbryGo
	}}
    if !isProduction {{
        serverConfig.CSRFCookieName = "embrygo_csrf_" // No __Host- prefix for dev (non-HTTPS)
    }}
	logger.Info("BlitzKit Server Effective Configuration", slog.Any("config", serverConfig))


	server, errServer := blitzkit.NewServer(serverConfig)
	if errServer != nil {{
		logger.Error("FATAL: Failed to initialize BlitzKit server", "error", errServer)
		os.Exit(1)
	}}
	app := server.App() // Get the underlying Fiber app

	webHandler := webHandlerPkg.NewHandler(server, logger)
	logger.Info("Web handlers initialized.")

    // --- Middlewares (BlitzKit's NewServer already sets up some base ones) ---
	app.Use(requestid.New()) // Add request ID

	// Middleware to pass basePath to handlers via c.Locals
	app.Use(func(c *fiber.Ctx) error {{
		c.Locals("basePath", basePath)
		return c.Next()
	}})
	logger.Info("Middleware for 'basePath' in locals set.")

    // CSRF Protection - BlitzKit might also configure this if EnableCSRF is true in its config
    // This is a more explicit setup:
	if serverConfig.EnableCSRF {{
		csrfMw := csrf.New(csrf.Config{{
			KeyLookup:      serverConfig.CSRFKeyLookup,
			CookieName:     serverConfig.CSRFCookieName,
			CookieSameSite: serverConfig.CSRFCookieSameSite,
			Expiration:     serverConfig.CSRFExpiration,
			CookieSecure:   isProduction,
			CookieHTTPOnly: true,
			ContextKey:     blitzkit.CSRFContextKey, // Use BlitzKit's constant if available
            // Next: func(c *fiber.Ctx) bool {{ return false }}, // Protect all by default
            ErrorHandler: func(c *fiber.Ctx, err error) error {{
                reqID := c.Locals("requestid")
				clientIP := blitzkit.GetClientIP(c.Get(fiber.HeaderXForwardedFor), c.IP())
                logger.Warn("CSRF validation failed",
                    slog.String("ip", clientIP), "path", c.Path(), "req_id", reqID, "error", err.Error())
                return fiber.NewError(fiber.StatusForbidden, "CSRF token mismatch or missing")
            }},
		}})
		app.Use(csrfMw)
		logger.Info("CSRF protection middleware enabled globally.")
	}} else {{
        // If CSRF is disabled in config, still set a local for getCsrfToken to work gracefully
		app.Use(func(c *fiber.Ctx) error {{
			c.Locals(blitzkit.CSRFContextKey, "csrf-disabled")
			return c.Next()
		}})
		logger.Warn("CSRF protection middleware IS DISABLED.")
	}}


    // --- Routing ---
	rootGroup := app.Group(basePath) // All app routes will be under basePath
	logger.Info("Registering application routes", "under_base_path", basePath)

	// Example Admin Route (Optional, shows basic auth with BlitzKit config)
	if config.AppConfig.AdminUser != "" && config.AppConfig.AdminPass != "" {{
		adminAuthConfig := basicauth.Config{{
			Users: map[string]string{{config.AppConfig.AdminUser: config.AppConfig.AdminPass}},
			Realm: "EmbryGo Admin Area",
		}}
		adminExampleGroup := rootGroup.Group("/admin-example", basicauth.New(adminAuthConfig))
		adminExampleGroup.Get("/", func(c *fiber.Ctx) error {{
			return c.SendString("Welcome to the (example) protected admin area of EmbryGo!")
		}})
		logger.Info("Example admin route registered", "path", basePath+"/admin-example")
	}} else {{
        rootGroup.Get("/admin-example", func(c *fiber.Ctx) error {{
			return c.SendString("Example admin area (UNPROTECTED - set ADMIN_USER/PASS in .env)")
		}})
		logger.Warn("Admin credentials not set, example admin route is unprotected.")
	}}

	webHandler.RegisterRoutes(rootGroup) // Register /welcome and /
	logger.Info("Web UI routes registered.")

    // Static File Serving (BlitzKit's NewServer can also do this if PublicDir is set)
    // This explicit app.Static ensures it's served under basePath.
	if _, errStat := os.Stat(serverConfig.PublicDir); errStat == nil {{
		logger.Info("Registering static file serving for public assets.", "prefix", basePath, "directory", serverConfig.PublicDir)
		app.Static(basePath, serverConfig.PublicDir, fiber.Static{{
			Compress:      true,
			ByteRange:     true,
			Browse:        !isProduction, // Allow browsing in dev
			CacheDuration: 1 * time.Hour,   // Shorter cache for dev
			MaxAge:        3600,          // MaxAge in seconds
		}})
	}} else {{
		logger.Error("Public static directory not found, web UI may not function correctly!",
			"path", serverConfig.PublicDir, "error", errStat.Error())
	}}
    
    // BlitzKit also sets up /metrics and /health at the true root of the Fiber app.

	// --- Start Server ---
	go func() {{
		if startErr := server.Start(); startErr != nil {{ // server.Start() comes from BlitzKit
			if !errors.Is(startErr, http.ErrServerClosed) {{
				logger.Error("FATAL: Server failed to start or crashed unexpectedly.", "error", startErr)
				p, findErr := os.FindProcess(os.Getpid())
				if findErr == nil {{
					_ = p.Signal(syscall.SIGTERM) // Attempt graceful shutdown of own process
				}} else {{
                    os.Exit(1) // Abrupt exit if can't signal self
                }}
			}}
		}}
	}}()

	// --- Graceful Shutdown ---
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	receivedSignal := <-quit
	logger.Warn("Shutdown signal received.", "signal", receivedSignal.String())

	logger.Info("Initiating graceful shutdown sequence...")
	if shutdownErr := server.Shutdown(); shutdownErr != nil {{ // server.Shutdown() from BlitzKit
		logger.Error("Error during server shutdown", "error", shutdownErr)
	}} else {{
		logger.Info("Server shutdown sequence complete.")
	}}
	logger.Info("EmbryGo application has shut down.")
}}
""")

    # --- internal/config/config.go ---
    create_file(project_path / "internal/config/config.go", f"""
package config

import (
	"fmt"
	"log/slog"
	"os"
	"strings"
)

type Config struct {{
	AdminUser  string
	AdminPass  string
	AppBaseURL string
	DevMode    bool
}}

var AppConfig Config

func LoadConfig(logger *slog.Logger) error {{
	logger.Info("Loading EmbryGo application configuration...")

	AppConfig = Config{{
		AdminUser:  os.Getenv("ADMIN_USER"),
		AdminPass:  os.Getenv("ADMIN_PASS"),
		AppBaseURL: os.Getenv("APP_BASE_URL"),
		DevMode:    os.Getenv("APP_ENV") == "development",
	}}

	// Example: Make APP_BASE_URL required in production
	var missing []string
	if AppConfig.AppBaseURL == "" && AppConfig.DevMode == false {{
		missing = append(missing, "APP_BASE_URL (required for production)")
	}}
	// Add other critical checks if needed

	if len(missing) > 0 {{
		errMsg := fmt.Sprintf("Missing required environment variables: %s", strings.Join(missing, ", "))
		logger.Error(errMsg)
		return fmt.Errorf(errMsg)
	}}

	if AppConfig.AppBaseURL == "" && AppConfig.DevMode == true {{
		defaultBaseURL := "http://localhost:" + os.Getenv("PORT")
        if os.Getenv("PORT") == "" {{ defaultBaseURL = "http://localhost:8080" }}
		logger.Warn("APP_BASE_URL not set in .env, defaulting for development.", "default_base_url", defaultBaseURL)
        AppConfig.AppBaseURL = defaultBaseURL
	}}


	logger.Info("EmbryGo application configuration loaded successfully.")
	return nil
}}
""")
    # --- internal/database/database.go (Placeholder) ---
    create_file(project_path / "internal/database/database.go", """
package database

import (
	"log/slog"
)

// InitDB - Placeholder for database initialization.
// For EmbryGo, this might not be needed initially.
func InitDB(logger *slog.Logger) error {
	logger.Info("Database initialization skipped for EmbryGo (placeholder).")
	return nil
}

// CloseDB - Placeholder for closing database connection.
func CloseDB(logger *slog.Logger) error {
	logger.Info("Database closing skipped for EmbryGo (placeholder).")
	return nil
}
""")

    # --- internal/handlers/api/handler.go (Placeholder) ---
    create_file(project_path / "internal/handlers/api/handler.go", """
package api

import (
	"log/slog"
	"github.com/gofiber/fiber/v2"
	"github.com/r-via/blitzkit"
)

type Handler struct {
	logger *slog.Logger
	server *blitzkit.Server
	// Add services if this API handler needs them
}

func NewAPIHandler(server *blitzkit.Server, logger *slog.Logger) *Handler {
	return &Handler{logger: logger, server: server}
}

// RegisterAPIRoutes - Placeholder for API routes. EmbryGo might not have any initially.
func (h *Handler) RegisterAPIRoutes(apiGroup fiber.Router) {
	h.logger.Info("API routes registration skipped for EmbryGo (placeholder).")
	// Example:
	// apiGroup.Get("/status", func(c *fiber.Ctx) error {
	//    return c.JSON(fiber.Map{"status": "API is active - placeholder"})
	// })
}
""")

    # --- internal/handlers/web/handler.go ---
    create_file(project_path / "internal/handlers/web/handler.go", f"""
package web

import (
	"log/slog"
	"strings"
	"{GO_MODULE_NAME}/pkg/translations"
	"{GO_MODULE_NAME}/webroot/views/layouts"
	"{GO_MODULE_NAME}/webroot/views/pages"

	"github.com/a-h/templ"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/adaptor"
	"github.com/r-via/blitzkit"
)

type Handler struct {{
	logger *slog.Logger
	server *blitzkit.Server
	// No complex service needed for EmbryGo's welcome page
}}

func NewHandler(server *blitzkit.Server, logger *slog.Logger) *Handler {{
	if logger == nil || server == nil {{
		slog.Error("FATAL: Web Handler for EmbryGo requires non-nil server and logger")
		panic("Web Handler initialization failed: missing critical dependencies")
	}}
	return &Handler{{logger: logger, server: server}}
}}

// RegisterRoutes registers the web routes for EmbryGo.
// It expects the rootGroup to be already prefixed with any basePath.
func (h *Handler) RegisterRoutes(rootGroup fiber.Router) {{
	h.logger.Info("Registering EmbryGo web routes...")
	
	// The actual path will be basePath + "/welcome"
	rootGroup.Get("/welcome", h.handleWelcomePage)

	// Redirect from the basePath itself to /basePath/welcome
	rootGroup.Get("/", func(c *fiber.Ctx) error {{
		// basePath is already handled by the group, so target is just "welcome"
		// However, c.Redirect needs the full path from the server root.
        // We get basePath from locals, which IS the full path from server root.
        currentBasePath, _ := c.Locals("basePath").(string)
        if currentBasePath == "/" {{ currentBasePath = "" }} // Avoid //welcome

		targetRedirectPath := currentBasePath + "/welcome"
        
		h.logger.Debug("Redirecting from root of group to welcome", "from", c.Path(), "to", targetRedirectPath)
		return c.Redirect(targetRedirectPath, fiber.StatusFound)
	}})
}}

// getBasePathFromLocals retrieves the application's base path from Fiber's context locals.
// This base path is set by a middleware in main.go.
func getBasePathFromLocals(c *fiber.Ctx, logger *slog.Logger) string {{
	basePathVal := c.Locals("basePath")
	basePath, ok := basePathVal.(string)
	if !ok {{
		basePath = "/" // Default to root if not found or wrong type
		if logger != nil {{
			logger.Warn("Could not get 'basePath' from locals or wrong type, defaulting to '/'", "type_found", basePathVal)
		}}
	}}
	return basePath
}}

// getCsrfToken retrieves the CSRF token from Fiber's context locals.
// It checks if CSRF is enabled on the server.
func getCsrfToken(c *fiber.Ctx, server *blitzkit.Server) string {{
	if server == nil || !server.GetConfig().EnableCSRF {{
		return "" // CSRF not enabled or server not available
	}}
	csrfVal := c.Locals(blitzkit.CSRFContextKey) // Use BlitzKit's constant
	if tokenStr, ok := csrfVal.(string); ok && tokenStr != "csrf-disabled" {{
		return tokenStr
	}}
	return "" // Token not found, or CSRF explicitly disabled for the request
}}

func (h *Handler) handleWelcomePage(c *fiber.Ctx) error {{
	lang := "en" // Simplified for EmbryGo starter
	trans := translations.GetTranslations(lang) // From pkg/translations
	
	// basePath is the full path from the server root, e.g., "/" or "/myapp"
	basePath := getBasePathFromLocals(c, h.logger)
	csrfToken := getCsrfToken(c, h.server)

	h.logger.Debug("Handling /welcome page", "lang", lang, "basePath", basePath, "csrf_present", csrfToken != "")

	pageData := pages.WelcomePageData{{
		Lang:         lang,
		Translations: trans,
		Base: layouts.BaseData{{
			Lang:         lang,
			PageTitle:    trans["welcome_title"],
			Translations: trans,
			CSRFToken:    csrfToken,
			BasePath:     basePath,
		}},
		Utilities: []pages.UtilityStatus{{
			{{Name: "Go Backend", Status: "OK", Icon: "check_circle"}},
			{{Name: "Fiber Framework", Status: "OK", Icon: "check_circle"}},
			{{Name: "BlitzKit Server Layer", Status: "OK", Icon: "check_circle"}},
			{{Name: "Templ Templating", Status: "OK", Icon: "check_circle"}},
			{{Name: "HTMX", Status: "OK", Icon: "check_circle"}},
			{{Name: "Tailwind CSS", Status: "OK", Icon: "check_circle"}},
			{{Name: "DaisyUI", Status: "OK", Icon: "check_circle"}},
			{{Name: "Heroicons (templ-heroicons-generator)", Status: "OK", Icon: "check_circle"}},
			{{Name: "Slog Logging", Status: "OK", Icon: "check_circle"}},
			{{Name: "Air Live Reload (Dev)", Status: "OK", Icon: "check_circle"}},
		}},
	}}

	// Use Fiber's adaptor to render the Templ component
	return adaptor.HTTPHandler(templ.Handler(pages.WelcomePage(pageData)))(c)
}}
""")

    # --- internal/middleware (empty .go for structure, .gitkeep handled) ---
    create_file(project_path / "internal/middleware/middleware.go", """
package middleware

// This package is a placeholder for custom application-specific middlewares.
// For EmbryGo, most common middlewares (CSRF, RequestID, CORS, Recover, Logging, BasicAuth, Limiter)
// are expected to be provided or configured via BlitzKit or Fiber itself in main.go.
""")

    # --- internal/models/common.go (Placeholder) ---
    create_file(project_path / "internal/models/common.go", """
package models

import "time"

// ExampleModel - Placeholder for common data models.
// For EmbryGo's simple welcome page, this might not be used.
// If you were to use a database (e.g., GORM), your models would go here.
type ExampleModel struct {
	ID        uint      `gorm:"primarykey"`
	CreatedAt time.Time
	Name      string
}
""")
    # --- internal/router/router.go (Placeholder) ---
    create_file(project_path / "internal/router/router.go","""
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
""")

    # --- internal/services/welcome/ (Placeholders) ---
    create_file(project_path / "internal/services/welcome/service.go", f"""
package welcome

import (
	"log/slog"
	// "{GO_MODULE_NAME}/internal/services/welcome/model" // If you define specific models
	// "{GO_MODULE_NAME}/internal/services/welcome/repository" // If you had a DB
)

type Service struct {{
	logger *slog.Logger
	// repo   *repository.Repository // Example
}}

func NewWelcomeService(logger *slog.Logger /*, repo *repository.Repository*/) *Service {{
	return &Service{{logger: logger /*, repo: repo*/}}
}}

// GetWelcomeData - Placeholder for fetching data for the welcome page.
// For EmbryGo, the data is static and defined in the web handler.
func (s *Service) GetWelcomeData() (string, error) {{
	s.logger.Info("WelcomeService.GetWelcomeData called (placeholder).")
	return "Data from WelcomeService (placeholder)", nil
}}
""")
    create_file(project_path / "internal/services/welcome/model.go", """
package welcome

// WelcomeDataModel - Placeholder for service-specific models.
type WelcomeDataModel struct {
	Message string
}
""")
    create_file(project_path / "internal/services/welcome/repository.go", """
package welcome

import "log/slog"

// Repository - Placeholder for data access logic for the welcome service.
type Repository struct {
	logger *slog.Logger
	// db *gorm.DB // Example
}

func NewWelcomeRepository(logger *slog.Logger /*, db *gorm.DB*/) *Repository {
	return &Repository{logger: logger /*, db: db*/}
}

// FetchData - Placeholder.
func (r *Repository) FetchData() (string, error) {
	r.logger.Info("WelcomeRepository.FetchData called (placeholder).")
	return "Data from WelcomeRepository (placeholder)", nil
}
""")

    # --- pkg/helpers/helpers.go ---
    create_file(project_path / "pkg/helpers/helpers.go", """
package helpers

import (
	"regexp"
	"strings"
)

var emailRegex = regexp.MustCompile(`^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$`)

// IsValidEmail checks if the email string is a valid format.
func IsValidEmail(email string) bool {
	if email == "" {
		return false
	}
	return emailRegex.MatchString(strings.ToLower(email))
}

// Add other general-purpose helper functions here.
""")

    # --- pkg/translations/translations.go ---
    create_file(project_path / "pkg/translations/translations.go", """
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
""")

    # --- tools/ ---
    create_file(project_path / "tools/requirements.txt", """
# For generating Heroicons Templ components
git+https://github.com/r-via/templ-heroicons-generator.git
# If you publish your package to PyPI, you can use:
# templ-heroicons-generator>=0.1.0
""")

    create_file(project_path / "tools/input.css", """
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom base styles or component overrides can go here if needed */
""")

    create_file(project_path / "tools/package.json", """
{
  "name": "embrygo-frontend-tools",
  "version": "0.1.0",
  "description": "Frontend build tools for EmbryGo project",
  "scripts": {
    "tailwind:build": "tailwindcss -i ./input.css -o ../webroot/www/css/tailwind.css --minify",
    "tailwind:dev": "tailwindcss -i ./input.css -o ../webroot/www/css/tailwind.css --watch"
  },
  "devDependencies": {
    "@tailwindcss/typography": "^0.5.10",
    "daisyui": "^4.7.0",
    "tailwindcss": "^3.4.0"
  }
}
""")
    create_file(project_path / "tools/tailwind.config.js", """
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
""")

    # --- webroot/sources/app.js ---
    create_file(project_path / "webroot/sources/app.js", """
/**
 * @file webroot/sources/app.js
 * @description Main client-side JavaScript for EmbryGo.
 *              Includes HTMX CSRF configuration.
 */

/**
 * Configures HTMX to automatically include the CSRF token in relevant requests.
 * Reads the token from a meta tag named 'csrf-token'.
 */
function configureHtmxCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    let token = null;
    if (meta) {
        token = meta.getAttribute('content');
    }

    if (token && token !== "csrf-disabled" && token !== "csrf-api-excluded") {
        document.body.addEventListener('htmx:configRequest', function(event) {
            const method = event.detail.verb.toUpperCase();
            // Add CSRF token for state-changing HTTP methods
            if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
                event.detail.headers['X-CSRF-Token'] = token;
                // console.debug("CSRF token added to HTMX request:", method, event.detail.path);
            }
        });
        console.info("HTMX CSRF protection configured.");
    } else {
        if (token === "csrf-disabled") {
            console.warn("HTMX CSRF protection explicitly disabled by server config for this page/context.");
        } else if (token === "csrf-api-excluded") {
             console.info("HTMX CSRF protection not applied as this route is likely an API excluded from CSRF.");
        } else {
            console.warn("CSRF token meta tag not found or token is empty. HTMX CSRF protection may not be active.");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("EmbryGo app.js loaded.");
    configureHtmxCsrf();
    // Add any other client-side initializations here
});
""")

    # --- webroot/statics/ (favicon.ico, htmx.min.js) ---
    # Create a dummy favicon.ico (replace with a real one later)
    create_file(project_path / "webroot/statics/favicon.ico", "dummy favicon content")
    # Create a dummy htmx.min.js (user should replace with actual library)
    create_file(project_path / "webroot/statics/htmx.min.js", """
// HTMX vX.Y.Z - Please download the actual htmx.min.js library
// from https://htmx.org/ and place it here or in webroot/statics/js/.
// This is a placeholder.
console.warn("Placeholder htmx.min.js loaded. Please replace with the actual library.");
""")

    # --- webroot/views/components/heroicons/heroicons.templ ---
    create_file(project_path / "webroot/views/components/heroicons/heroicons.templ", """
// This file will be auto-generated by 'templ-generate-heroicons'.
// It will contain Templ components for Heroicons used in your project.
// Example (if 'check_circle' is used and generated):
//
// package heroicons
//
// // Requires: templ v0.2.513 or later
// templ Outline_check_circle(attrs templ.Attributes) {
//	<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" { attrs... } class="size-6">
//		<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
//	</svg>
// }

package heroicons

// Placeholder to ensure the package exists before first generation.
// Remove this if templ-generate-heroicons creates the package declaration.
""")

# --- webroot/views/layouts/base.templ ---
    # Note: GO_MODULE_NAME est utilisé ici, donc c'est une f-string.
    # Les accolades pour Templ doivent être doublées {{{{ ... }}}}
    # Les commentaires Templ également: {{{{/* ... */}}}}
    create_file(project_path / "webroot/views/layouts/base.templ", f"""
package layouts

import "strings"
import "net/url"
import "time"
// import "{GO_MODULE_NAME}/pkg/translations" // Translations are in BaseData

type BaseData struct {{
	Lang         string
	PageTitle    string
	Translations map[string]string
	CSRFToken    string
	BasePath     string
}}

func assetUrl(basePath, assetPath string) string {{
	if !strings.HasPrefix(assetPath, "/") {{
		assetPath = "/" + assetPath
	}}
	if basePath == "/" {{
		return assetPath
	}}
	finalPath, _ := url.JoinPath(basePath, assetPath)
    if !strings.HasPrefix(finalPath, "/") && basePath != "/" {{
        //
    }} else if basePath == "/" && !strings.HasPrefix(finalPath, "/") {{
         return "/" + finalPath
    }}
	return finalPath
}}

templ Base(data BaseData) {{
	<!DOCTYPE html>
	<html lang={{data.Lang}} class="h-full antialiased" data-theme="night"> {{/* Default to night theme */}}
		<head>
			<meta charset="UTF-8"/>
			<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
			if data.CSRFToken != "" && data.CSRFToken != "csrf-disabled" {{
				<meta name="csrf-token" content={{data.CSRFToken}}/>
			}}
			<title>{{data.PageTitle}}</title>
			<link href={{assetUrl(data.BasePath, "/favicon.ico")}} rel="icon" type="image/x-icon"/>
			<link href={{assetUrl(data.BasePath, "/tailwind.css")}} rel="stylesheet"/>
			<script src={{assetUrl(data.BasePath, "/htmx.min.js")}} defer></script>
			<script src={{assetUrl(data.BasePath, "/app.js")}} defer></script>
		</head>
		<body class="min-h-screen bg-base-200 text-base-content flex flex-col">
			<header class="bg-base-300 shadow-md sticky top-0 z-50">
				<div class="container mx-auto px-4 py-4">
					<h1 class="text-2xl font-bold text-primary">
						<a href={{assetUrl(data.BasePath, "/welcome")}}>{{data.Translations["welcome_title"]}}</a>
					</h1>
				</div>
			</header>

			<main id="main-content" class="container mx-auto px-4 py-8 flex-grow">
				{{children...}}
			</main>

			<footer class="bg-base-300 text-base-content/70 text-center py-6 mt-auto">
				<p>© {{time.Now().Format("2006")}} {{data.Translations["footer_text"]}}. All rights reserved.</p>
			</footer>
		</body>
	</html>
}}
""")

    # --- webroot/views/pages/welcome.templ ---
    create_file(project_path / "webroot/views/pages/welcome.templ", f"""
package pages

import (
	"{GO_MODULE_NAME}/webroot/views/layouts"
	"{GO_MODULE_NAME}/webroot/views/components/heroicons" // Assuming heroicons package will be generated here
    "html/template" // For Raw HTML if needed, or just use templ syntax
)

// UtilityStatus represents the status of a core technology/feature.
type UtilityStatus struct {{
	Name   string
	Status string
	Icon   string // Name of the Heroicon component (e.g., "Outline_check_circle")
}}

// WelcomePageData holds all data needed for the welcome page.
type WelcomePageData struct {{
	Lang         string
	Translations map[string]string
	Base         layouts.BaseData
	Utilities    []UtilityStatus
}}

// Helper function to render an icon if its name is provided.
func renderIcon(iconName string) templ.Component {{
    switch iconName {{
        case "check_circle":
            return heroicons.Outline_check_circle(templ.Attributes{{"class": "w-5 h-5 mr-3 text-success flex-shrink-0"}})
        case "information_circle":
            return heroicons.Outline_information_circle(templ.Attributes{{"class": "w-5 h-5 mr-3 text-info flex-shrink-0"}})
        // Add more cases for other icons if needed
        default:
            // Return an empty component or a default icon if name is unknown
            return templ.Raw("") 
    }}
}}


templ WelcomePageContent(data WelcomePageData) {{
	<div class="prose max-w-4xl mx-auto bg-base-100 p-6 md:p-8 rounded-lg shadow-lg">
		<h2 class="text-3xl font-semibold mb-6 text-center border-b border-base-300 pb-4">{{ data.Translations["welcome_message"] }}</h2>
		
		<p class="text-lg">
			This page demonstrates the basic setup of the EmbryGo starter project. 
			It integrates several modern web technologies to provide a solid foundation for your Go applications.
		</p>

		<h3 class="text-2xl font-semibold mt-8 mb-4">{{ data.Translations["utilities_title"] }}</h3>
		<ul class="list-none p-0 space-y-3">
			for _, util := range data.Utilities {{
				<li class="flex items-center py-3 px-4 bg-base-200 rounded-md shadow-sm hover:shadow-md transition-shadow">
                    @renderIcon(util.Icon)
					<span class="font-medium text-base-content flex-grow">{{ data.Translations[util.Name] }}</span>
					<span class="font-semibold text-success ml-4 badge badge-success badge-outline">{{ data.Translations["status_ok"] }}</span>
				</li>
			}}
		</ul>
        
        <div class="mt-10 p-4 bg-base-200 rounded-md text-sm">
            <p>
                <strong class="text-info">Next Steps:</strong>
            </p>
            <ul class="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Explore the <code class="bg-base-300 px-1 rounded">Makefile</code> for common commands like <code>make run</code> or <code>make build</code>.</li>
                <li>Check your <code>.env</code> file (created from <code>.env.example</code>) for configuration.</li>
                <li>The BlitzKit server exposes <code>/metrics</code> (Prometheus) and <code>/health</code> endpoints.</li>
                <li>An example admin route is at <code>/admin-example</code> (if <code>ADMIN_USER</code>/<code>PASS</code> are set in <code>.env</code>).</li>
            </ul>
        </div>
	</div>
}}

// WelcomePage is the main component for the welcome page, embedding the content within the base layout.
templ WelcomePage(data WelcomePageData) {{
	@layouts.Base(data.Base) {{
		@WelcomePageContent(data)
	}}
}}
""")

    # Create dummy Go module files (user will run `go mod tidy` or `make tidy`)
    create_file(project_path / "go.mod", f"module {GO_MODULE_NAME}\n\ngo 1.21\n") # Adjust Go version if needed
    create_file(project_path / "go.sum", "")

    try:
        # Calcule le chemin relatif depuis le répertoire de travail actuel vers le projet généré
        relative_path_for_cd = os.path.relpath(project_path, Path.cwd())
        # Remplacer les backslashes par des slashes pour un affichage plus "shell-friendly"
        relative_path_for_cd = relative_path_for_cd.replace('\\', '/')
    except ValueError:
        # Si une erreur se produit (ex: sur des lecteurs différents sous Windows),
        # affiche simplement le chemin absolu résolu.
        relative_path_for_cd = str(project_path.resolve())

    print(f"\n🎉 EmbryGo project '{PROJECT_ROOT_NAME}' generated successfully in '{project_path.resolve()}'!")
    print(f"   Go Module Name: {GO_MODULE_NAME}")
    print("\nNext steps:")
    print(f"1. cd {relative_path_for_cd}") # MODIFIÉ ICI
    print("2. Review and update `.env` from `.env.example` (especially `APP_BASE_URL`).")
    print("3. Run `make setup-tools` to install Node.js and Python tool dependencies.")
    print("4. Run `go mod tidy` or `make tidy` to fetch Go dependencies.")
    print("5. Run `make run` for development (requires Air, Templ CLI).")
    print("   (You might need to install Templ CLI: `go install github.com/a-h/templ/cmd/templ@latest`)")
    print("   (And Air: `go install github.com/cosmtrek/air@latest`)")
    print("6. Or, `make build` then `make start-prod` for a production-like build.")
    print("\n👉 Remember to download the actual htmx.min.js library and replace the placeholder in webroot/statics/htmx.min.js.")

if __name__ == "__main__":
    main()