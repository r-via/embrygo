# Makefile pour EmbryGo (github.com/r-via/embrygo)

# --- Variables de Configuration ---
APP_NAME := service-app
CMD_DIR := ./cmd/$(APP_NAME)
MAIN_GO_PATH := $(CMD_DIR)/main.go

BIN_DIR := ./bin
OUTPUT_BINARY := $(BIN_DIR)/$(APP_NAME)

# Outils
TEMPL_CLI_PACKAGE := github.com/a-h/templ/cmd/templ # Pour `go run`
TAILWIND_CLI := npx tailwindcss # Utilise npx pour lancer tailwind localement

# Python pour le générateur d'icônes (environnement virtuel)
PYTHON_VENV_DIR := ./tools/.venv
PYTHON_INTERP := $(PYTHON_VENV_DIR)/bin/python
HEROICONS_GENERATOR_SCRIPT := $(PYTHON_VENV_DIR)/bin/templ-generate-heroicons

# Chemins des fichiers et répertoires pour les assets
WEBROOT_DIR := ./webroot
VIEWS_DIR := $(WEBROOT_DIR)/views
COMPONENTS_DIR := $(VIEWS_DIR)/components
HEROICONS_DIR := $(COMPONENTS_DIR)/heroicons
HEROICONS_OUTPUT_TEMPL := $(HEROICONS_DIR)/heroicons.templ

TOOLS_DIR := ./tools
INPUT_CSS := $(TOOLS_DIR)/input.css
TAILWIND_CONFIG := $(TOOLS_DIR)/tailwind.config.js
PACKAGE_JSON := $(TOOLS_DIR)/package.json
REQUIREMENTS_TXT := $(TOOLS_DIR)/requirements.txt

# Répertoires pour BlitzKit StaticProcessor et service direct
PUBLIC_DIR := $(WEBROOT_DIR)/www     # Destination finale des assets servis (populé par BlitzKit)
STATICS_DIR := $(WEBROOT_DIR)/statics # Fichiers copiés tels quels par BlitzKit (ex: favicon, htmx.min.js, tailwind.css généré)
SOURCES_DIR := $(WEBROOT_DIR)/sources   # Fichiers sources à minifier par BlitzKit (ex: app.js)

# Fichier CSS généré par Tailwind, placé dans STATICS_DIR pour être traité par BlitzKit
OUTPUT_CSS_FILE := $(STATICS_DIR)/tailwind.css

# Cache directory (handled by BlitzKit)
CACHE_DIR := $(WEBROOT_DIR)/cache

# Assurer l'existence de certains répertoires essentiels au démarrage du Makefile lui-même
DUMMY := $(shell mkdir -p $(BIN_DIR) $(STATICS_DIR) $(SOURCES_DIR) $(HEROICONS_DIR) $(TOOLS_DIR) $(PUBLIC_DIR))

# --- Cibles Principales ---

.PHONY: all
all: build
	@echo "Default target: build complete. Binary at $(OUTPUT_BINARY)"

.PHONY: build
build: setup-tools generate-assets-prod go-build
	@echo "-------------------------------------------"
	@echo "✅ Production build complete."
	@echo "   Binary: $(OUTPUT_BINARY)"
	@echo "-------------------------------------------"

.PHONY: run
run: setup-tools generate-assets-dev
	@echo "-------------------------------------------"
	@echo "🚀 Starting application in development mode with Air..."
	@echo "   Live reload enabled. Check .air.toml for config."
	@echo "-------------------------------------------"
	@air -c .air.toml

.PHONY: start-prod
start-prod:
	@if [ ! -f "$(OUTPUT_BINARY)" ]; then \
		echo "Error: Production binary $(OUTPUT_BINARY) not found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "-------------------------------------------"
	@echo "🚀 Starting production build from $(OUTPUT_BINARY)..."
	@echo "   Ensure .env is configured for production."
	@echo "-------------------------------------------"
	APP_ENV=production $(OUTPUT_BINARY)

.PHONY: clean
clean:
	@echo "🧹 Cleaning build artifacts, generated files, and caches..."
	@echo "   Current project directory: $(shell pwd)"

	# Nettoyage sécurisé du contenu du répertoire public
	@if [ -z "$(PUBLIC_DIR)" ]; then \
		echo "Error: PUBLIC_DIR is not set. Aborting clean to prevent accidental deletion."; \
		exit 1; \
	elif [ "$(PUBLIC_DIR)" = "/" ] || [ "$(PUBLIC_DIR)" = "." ] || [ "$(PUBLIC_DIR)" = ".." ]; then \
		echo "Error: PUBLIC_DIR is set to a dangerous path ('$(PUBLIC_DIR)'). Aborting clean."; \
		exit 1; \
	elif ! case "$(abspath $(PUBLIC_DIR))" in "$(abspath .)"/*) exit 0;; *) exit 1;; esac; then \
		echo "Error: PUBLIC_DIR ('$(abspath $(PUBLIC_DIR))') seems outside project ('$(abspath .)'). Aborting clean."; \
		exit 1; \
	fi
	@echo "   Cleaning content of public asset directory: $(PUBLIC_DIR)..."
	@if [ -d "$(PUBLIC_DIR)" ]; then \
		find "$(PUBLIC_DIR)" -mindepth 1 -delete; \
		echo "   Content of $(PUBLIC_DIR) removed."; \
	else \
		echo "   Directory $(PUBLIC_DIR) does not exist, skipping content removal. Ensuring it exists..."; \
		mkdir -p "$(PUBLIC_DIR)"; \
	fi

	@echo "   Removing Go build binary directory: $(BIN_DIR)..."
	@if [ -d "$(BIN_DIR)" ]; then rm -rf "$(BIN_DIR)"; fi

	@echo "   Removing generated Heroicons .templ file: $(HEROICONS_OUTPUT_TEMPL)..."
	@if [ -f "$(HEROICONS_OUTPUT_TEMPL)" ]; then rm -f "$(HEROICONS_OUTPUT_TEMPL)"; fi

	@echo "   Removing generated Templ Go files (*_templ.go)..."
	@find . -name '*_templ.go' -delete

	@echo "   Removing Node.js modules and Python virtual environment from $(TOOLS_DIR)..."
	@if [ -d "$(TOOLS_DIR)/node_modules" ]; then rm -rf "$(TOOLS_DIR)/node_modules"; fi
	@if [ -d "$(PYTHON_VENV_DIR)" ]; then rm -rf "$(PYTHON_VENV_DIR)"; fi
	@if [ -f "$(TOOLS_DIR)/node_modules/.installed" ]; then rm -f "$(TOOLS_DIR)/node_modules/.installed"; fi
	@if [ -f "$(PYTHON_VENV_DIR)/.installed" ]; then rm -f "$(PYTHON_VENV_DIR)/.installed"; fi

	@echo "   Removing generated CSS file: $(OUTPUT_CSS_FILE)..."
	@if [ -f "$(OUTPUT_CSS_FILE)" ]; then rm -f "$(OUTPUT_CSS_FILE)"; fi
	
	@echo "   Removing BlitzKit L2 cache directory: $(CACHE_DIR)..."
	@if [ -d "$(CACHE_DIR)" ]; then \
		rm -rf "$(CACHE_DIR)"; \
		echo "   Removed $(CACHE_DIR)"; \
	else \
		echo "   Cache directory $(CACHE_DIR) does not exist, skipping its removal."; \
	fi

	@echo "🧼 Clean complete."

# --- Génération d'Assets ---

.PHONY: generate-assets-prod
generate-assets-prod: tailwind-prod heroicons templ-generate
	@echo "📦 All production assets generated."

.PHONY: generate-assets-dev
generate-assets-dev: tailwind-dev heroicons templ-generate
	@echo "🛠️ All development assets generated."


# --- Outils et Dépendances ---

.PHONY: setup-tools
setup-tools: npm-install python-venv-setup heroicons-script-check
	@echo "🛠️ Tooling setup complete (Node.js & Python)."

$(TOOLS_DIR)/node_modules/.installed: $(PACKAGE_JSON)
	@echo "📦 Installing/Updating Node.js dependencies from $(PACKAGE_JSON)..."
	@cd $(TOOLS_DIR) && npm install
	@touch $@

.PHONY: npm-install
npm-install: $(TOOLS_DIR)/node_modules/.installed

# MODIFICATION ICI pour installer setuptools et wheel explicitement AVANT requirements.txt
$(PYTHON_VENV_DIR)/.installed: $(REQUIREMENTS_TXT)
	@echo "🐍 Setting up Python virtual environment at $(PYTHON_VENV_DIR)..."
	@if [ ! -d "$(PYTHON_VENV_DIR)" ]; then \
		python3 -m venv $(PYTHON_VENV_DIR); \
	fi
	@echo "🐍 Upgrading pip in venv..."
	@$(PYTHON_INTERP) -m pip install --upgrade pip
	@echo "🐍 Installing core build tools (setuptools, wheel) in venv..."
	@$(PYTHON_INTERP) -m pip install setuptools wheel
	@echo "🐍 Installing Python dependencies from $(REQUIREMENTS_TXT)..."
	@$(PYTHON_INTERP) -m pip install -r $(REQUIREMENTS_TXT)
	@touch $@ # Crée le fichier marqueur

.PHONY: python-venv-setup
python-venv-setup: $(PYTHON_VENV_DIR)/.installed

.PHONY: heroicons-script-check
heroicons-script-check: python-venv-setup
	@echo "🔎 Verifying templ-heroicons-generator script..."
	@if ! $(PYTHON_INTERP) -m pip show templ-heroicons-generator > /dev/null 2>&1; then \
		echo "Warning: templ-heroicons-generator not found in venv. Attempting to install/reinstall from $(REQUIREMENTS_TXT)."; \
		$(PYTHON_INTERP) -m pip install -r $(REQUIREMENTS_TXT); \
	fi
	@if [ ! -f "$(HEROICONS_GENERATOR_SCRIPT)" ]; then \
		echo "Error: templ-generate-heroicons script not found at $(HEROICONS_GENERATOR_SCRIPT) even after attempting install."; \
		echo "Please check your Python environment, $(REQUIREMENTS_TXT), and ensure the package provides this script."; \
		exit 1; \
	fi
	@echo "👍 templ-heroicons-generator script verified."


# --- Cibles de Génération Spécifiques ---

.PHONY: tailwind-prod
tailwind-prod: npm-install $(INPUT_CSS) $(TAILWIND_CONFIG) $(VIEWS_DIR)/**/*.templ $(SOURCES_DIR)/**/*.js
	@echo "🎨 Generating minified Tailwind CSS for production -> $(OUTPUT_CSS_FILE)"
	@$(TAILWIND_CLI) -i $(INPUT_CSS) -o $(OUTPUT_CSS_FILE) --minify

.PHONY: tailwind-dev
tailwind-dev: npm-install $(INPUT_CSS) $(TAILWIND_CONFIG) $(VIEWS_DIR)/**/*.templ $(SOURCES_DIR)/**/*.js
	@echo "🎨 Generating Tailwind CSS for development -> $(OUTPUT_CSS_FILE)"
	@$(TAILWIND_CLI) -i $(INPUT_CSS) -o $(OUTPUT_CSS_FILE)

.PHONY: heroicons
heroicons: heroicons-script-check $(VIEWS_DIR)/**/*.templ
	@echo "🖼️ Generating Heroicons Templ components..."
	@echo "   Scanning: $(VIEWS_DIR)/**/*.templ"
	@echo "   Outputting to: $(HEROICONS_OUTPUT_TEMPL)"
	@$(HEROICONS_GENERATOR_SCRIPT) --input="$(VIEWS_DIR)/**/*.templ" --output="$(HEROICONS_OUTPUT_TEMPL)" --package="heroicons" --preserve-input-attrs
	@$(MAKE) templ-generate-specific TARGET_DIR=$(HEROICONS_DIR)

.PHONY: templ-generate
templ-generate:
	@echo "✨ Generating Go code from ALL Templ files (using 'go run $(TEMPL_CLI_PACKAGE)')..."
	@go run $(TEMPL_CLI_PACKAGE) generate ./...

.PHONY: templ-generate-specific
templ-generate-specific:
	@if [ -z "$(TARGET_DIR)" ]; then \
		echo "Error: TARGET_DIR not set for templ-generate-specific."; \
		exit 1; \
	fi
	@echo "✨ Generating Go code from Templ files in $(TARGET_DIR) (using 'go run $(TEMPL_CLI_PACKAGE)')..."
	@go run $(TEMPL_CLI_PACKAGE) generate $(TARGET_DIR)


# --- Compilation Go ---

.PHONY: go-build
go-build:
	@echo "🏗️ Building Go application '$(APP_NAME)' for production..."
	@mkdir -p $(BIN_DIR) # Assurer que le répertoire bin existe
	@go build -ldflags="-s -w" -o $(OUTPUT_BINARY) $(MAIN_GO_PATH)

# --- Utilitaires Go ---

.PHONY: tidy
tidy:
	@echo "🧹 Running go mod tidy..."
	@go mod tidy

.PHONY: fmt
fmt:
	@echo "🎨 Formatting Go code..."
	@go fmt ./...

.PHONY: test
test:
	@echo "🧪 Running Go tests..."
	@go test ./... -v

# --- Documentation et Aide ---
.PHONY: help
help:
	@echo "EmbryGo Makefile - Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make run                   - Run the application in development mode with live reload (Air)."
	@echo "    make generate-assets-dev   - Generate assets (CSS, icons, Templ) for development."
	@echo "    make tailwind-dev          - Generate Tailwind CSS for development (non-minified)."
	@echo ""
	@echo "  Production & Build:"
	@echo "    make all                   - Alias for 'make build'."
	@echo "    make build                 - Build the production-ready binary."
	@echo "    make start-prod            - Run the production-built binary (ensure .env is set for prod)."
	@echo "    make generate-assets-prod  - Generate assets for production (minified)."
	@echo "    make tailwind-prod         - Generate Tailwind CSS for production (minified)."
	@echo ""
	@echo "  Asset Generation (general):"
	@echo "    make heroicons             - Generate Heroicon Templ components and their Go code."
	@echo "    make templ-generate        - Generate Go code from ALL .templ files."
	@echo ""
	@echo "  Setup & Maintenance:"
	@echo "    make setup-tools           - Install/setup Node.js and Python tool dependencies."
	@echo "    make clean                 - Remove build artifacts, generated files, and caches."
	@echo "    make tidy                  - Run 'go mod tidy'."
	@echo "    make fmt                   - Format Go code."
	@echo ""
	@echo "  Testing:"
	@echo "    make test                  - Run Go tests."
	@echo ""