APP_NAME := service-app
CMD_DIR := ./cmd/$(APP_NAME)
MAIN_GO_PATH := $(CMD_DIR)/main.go

BIN_DIR := ./bin
OUTPUT_BINARY := $(BIN_DIR)/$(APP_NAME)

TOOLS_PYTHON_VENV_NAME ?= .venv-embrygo
TOOLS_PYTHON_VENV_DIR := ./tools/$(TOOLS_PYTHON_VENV_NAME)
TOOLS_PYTHON_INTERP := $(TOOLS_PYTHON_VENV_DIR)/bin/python

PYT_PATROL_CMD := $(TOOLS_PYTHON_VENV_DIR)/bin/pyt-patrol
HEROICONS_GENERATOR_CMD := $(TOOLS_PYTHON_VENV_DIR)/bin/templ-generate-heroicons

NVM_DIR := $(HOME)/.nvm
NVM_SCRIPT := $(NVM_DIR)/nvm.sh

WEBROOT_DIR := ./webroot
VIEWS_DIR := $(WEBROOT_DIR)/views
COMPONENTS_DIR := $(VIEWS_DIR)/components
HEROICONS_DIR := $(COMPONENTS_DIR)/heroicons
HEROICONS_OUTPUT_TEMPL := $(HEROICONS_DIR)/heroicons.templ

TOOLS_EMBRYGO_DIR := ./tools
INPUT_CSS := $(TOOLS_EMBRYGO_DIR)/input.css
TAILWIND_CONFIG := $(TOOLS_EMBRYGO_DIR)/tailwind.config.js
PACKAGE_JSON_EMBRYGO := $(TOOLS_EMBRYGO_DIR)/package.json

PUBLIC_DIR := $(WEBROOT_DIR)/www
STATICS_DIR := $(WEBROOT_DIR)/statics
SOURCES_DIR := $(WEBROOT_DIR)/sources
OUTPUT_CSS_FILE := $(STATICS_DIR)/tailwind.css
CACHE_DIR := $(WEBROOT_DIR)/cache

DUMMY := $(shell mkdir -p $(BIN_DIR) $(STATICS_DIR) $(SOURCES_DIR) $(HEROICONS_DIR) $(TOOLS_EMBRYGO_DIR) $(PUBLIC_DIR) > /dev/null 2>&1)

.SILENT:

.PHONY: all
all: build

.PHONY: build
build: generate-assets-prod go-build
	@echo "-------------------------------------------"
	@echo "✅ Production build complete."
	@echo "   Binary: $(OUTPUT_BINARY)"
	@echo "   Ensure tools were set up previously if this is the first build or tools changed: make setup-tools"
	@echo "-------------------------------------------"

.PHONY: run
run: # Removed dependencies: setup-tools generate-assets-dev
	@echo "-------------------------------------------"
	@echo "🚀 Starting application in development mode with Air..."
	@echo "   Ensure 'make setup-tools' and 'make generate-assets-dev' have been run if needed."
	@echo "-------------------------------------------"
	@if ! command -v air > /dev/null 2>&1; then \
		echo "⚠️ air CLI not found in PATH. Run 'make setup-tools' first to install/verify tools."; \
		exit 1; \
	fi
	@. "$(NVM_SCRIPT)" && nvm use > /dev/null 2>&1 && air -c .air.toml

.PHONY: start-prod
start-prod: build
	@echo "-------------------------------------------"
	@echo "🚀 Starting production build from $(OUTPUT_BINARY)..."
	@echo "-------------------------------------------"
	@APP_ENV=production $(OUTPUT_BINARY)

.PHONY: clean
clean:
	@echo "🧹 Cleaning EmbryGo project artifacts..."
	@rm -rf $(BIN_DIR) > /dev/null 2>&1 || true
	@rm -f $(HEROICONS_OUTPUT_TEMPL) > /dev/null 2>&1 || true
	@find . -name '*_templ.go' -delete > /dev/null 2>&1 || true
	@if [ -d "$(TOOLS_EMBRYGO_DIR)/node_modules" ]; then rm -rf "$(TOOLS_EMBRYGO_DIR)/node_modules"; fi > /dev/null 2>&1 || true
	@if [ -f "$(TOOLS_EMBRYGO_DIR)/node_modules/.installed" ]; then rm -f "$(TOOLS_EMBRYGO_DIR)/node_modules/.installed"; fi > /dev/null 2>&1 || true
	@if [ -d "$(TOOLS_PYTHON_VENV_DIR)" ]; then rm -rf "$(TOOLS_PYTHON_VENV_DIR)"; fi > /dev/null 2>&1 || true
	@if [ -f "$(OUTPUT_CSS_FILE)" ]; then rm -f "$(OUTPUT_CSS_FILE)"; fi > /dev/null 2>&1 || true
	@if [ -d "$(CACHE_DIR)" ]; then rm -rf "$(CACHE_DIR)"; fi > /dev/null 2>&1 || true
	@echo "🧼 Clean complete."

.PHONY: generate-assets-prod
generate-assets-prod: tailwind-prod heroicons templ-generate
	@echo "📦 All production assets generated."

.PHONY: generate-assets-dev
generate-assets-dev: tailwind-dev heroicons templ-generate
	@echo "🛠️ All development assets generated."

.PHONY: check-deps
check-deps:
	@echo "🛡️ Checking EmbryGo project tools dependencies with Pyt-Patrol (context: ./tools)..."
	@if [ ! -f "$(PYT_PATROL_CMD)" ]; then \
		echo "⚠️ Pyt-Patrol script not found at $(PYT_PATROL_CMD). Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@$(PYT_PATROL_CMD) --context-dir ./tools
	@echo "👍 Pyt-Patrol check complete for tools."

.PHONY: setup-tools
setup-tools: check-nvm-node
	@echo "🛠️ Setting up/verifying EmbryGo project tools environment (Pyt-Patrol will manage its venv)..."
	@if [ ! -f "$(TOOLS_PYTHON_VENV_DIR)/bin/activate" ]; then \
		echo "Creating Python venv for tools at $(TOOLS_PYTHON_VENV_DIR)..."; \
		python3 -m venv $(TOOLS_PYTHON_VENV_DIR) > /dev/null 2>&1; \
	fi
	@echo "Ensuring Pyt-Patrol and its dependencies are in $(TOOLS_PYTHON_VENV_DIR)...";
	@$(TOOLS_PYTHON_INTERP) -m pip install --upgrade pip setuptools wheel -q --disable-pip-version-check
	@$(TOOLS_PYTHON_INTERP) -m pip install -r ./tools/requirements.txt -q --disable-pip-version-check
	@echo "Running Pyt-Patrol setup for tools in $(TOOLS_EMBRYGO_DIR)...";
	@$(PYT_PATROL_CMD) --context-dir ./tools --setup
	@echo "✅ Pyt-Patrol setup complete for tools. Tools environment should be ready."
	@$(MAKE) npm-install-tools > /dev/null

.PHONY: check-nvm-node
check-nvm-node:
	@echo "🔎 Checking NVM and Node.js for EmbryGo..."
	@if [ -s "$(NVM_SCRIPT)" ]; then \
		. "$(NVM_SCRIPT)"; \
		if ! command -v nvm > /dev/null 2>&1; then \
			echo "❌ Error: NVM command not available. Check NVM installation."; exit 1; \
		fi; \
		if ! nvm current > /dev/null 2>&1 || ! node -v > /dev/null 2>&1 ; then \
			echo "⚠️ Node.js not active via NVM. Attempting 'nvm use' (from .nvmrc if present)..."; \
			nvm use > /dev/null 2>&1 || (echo "❌ Failed to activate Node.js via NVM. Ensure .nvmrc is correct or Node is installed." && exit 1); \
		fi; \
		echo "✅ NVM and Node.js OK."; \
	else \
		echo "❌ Error: NVM script not found at $(NVM_SCRIPT). Install NVM."; exit 1; \
	fi

$(TOOLS_EMBRYGO_DIR)/node_modules/.installed: $(PACKAGE_JSON_EMBRYGO) check-nvm-node
	@echo "📦 Installing/Updating Node.js dependencies for tools from $(PACKAGE_JSON_EMBRYGO)..."
	@. "$(NVM_SCRIPT)" && nvm use > /dev/null 2>&1 && cd $(TOOLS_EMBRYGO_DIR) && npm install --silent --no-fund --no-audit > /dev/null
	@touch $@

.PHONY: npm-install-tools
npm-install-tools: $(TOOLS_EMBRYGO_DIR)/node_modules/.installed

.PHONY: tailwind-prod
tailwind-prod: npm-install-tools
	@echo "🎨 Generating minified Tailwind CSS for production -> $(OUTPUT_CSS_FILE)"
	@. "$(NVM_SCRIPT)" && nvm use > /dev/null 2>&1 && cd $(TOOLS_EMBRYGO_DIR) && npx tailwindcss -i ./input.css -c ./tailwind.config.js -o ../$(OUTPUT_CSS_FILE) --minify > /dev/null

.PHONY: tailwind-dev
tailwind-dev: npm-install-tools
	@echo "🎨 Generating Tailwind CSS for development -> $(OUTPUT_CSS_FILE)"
	@. "$(NVM_SCRIPT)" && nvm use > /dev/null 2>&1 && cd $(TOOLS_EMBRYGO_DIR) && npx tailwindcss -i ./input.css -c ./tailwind.config.js -o ../$(OUTPUT_CSS_FILE) > /dev/null

.PHONY: heroicons
heroicons:
	@echo "🖼️ Generating Heroicons Templ components..."
	@if [ ! -f "$(HEROICONS_GENERATOR_CMD)" ]; then \
		echo "⚠️ Heroicons generator script not found at $(HEROICONS_GENERATOR_CMD). Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@$(HEROICONS_GENERATOR_CMD) --input="./webroot/views" --output-dir="./webroot/views/components/heroicons" > /dev/null
	# No automatic templ-generate-specific here; covered by generate-assets-dev or templ-generate target

.PHONY: templ-generate
templ-generate:
	@echo "✨ Generating Go code from ALL Templ files (using 'templ' CLI)..."
	@if ! command -v templ > /dev/null 2>&1; then \
		echo "⚠️ templ CLI not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@templ generate ./... > /dev/null

.PHONY: templ-generate-specific
templ-generate-specific:
	@if [ -z "$(TARGET_DIR)" ]; then \
		echo "Error: TARGET_DIR not set for templ-generate-specific."; \
		exit 1; \
	fi
	@echo "✨ Generating Go code from Templ files in $(TARGET_DIR) (using 'templ' CLI)..."
	@if ! command -v templ > /dev/null 2>&1; then \
		echo "⚠️ templ CLI not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@templ generate $(TARGET_DIR) > /dev/null

.PHONY: go-build
go-build:
	@echo "🏗️ Building Go application '$(APP_NAME)' for production..."
	@if ! command -v go > /dev/null 2>&1; then \
		echo "⚠️ Go compiler (go) not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@mkdir -p $(BIN_DIR) > /dev/null 2>&1
	@go build -ldflags="-s -w" -o $(OUTPUT_BINARY) $(MAIN_GO_PATH)

.PHONY: tidy
tidy:
	@echo "🧹 Running go mod tidy..."
	@if ! command -v go > /dev/null 2>&1; then \
		echo "⚠️ Go compiler (go) not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@go mod tidy > /dev/null

.PHONY: fmt
fmt:
	@echo "🎨 Formatting Go code..."
	@if ! command -v go > /dev/null 2>&1; then \
		echo "⚠️ Go compiler (go) not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@go fmt ./... > /dev/null

.PHONY: test
test:
	@echo "🧪 Running Go tests..."
	@if ! command -v go > /dev/null 2>&1; then \
		echo "⚠️ Go compiler (go) not found in PATH. Run 'make setup-tools' first."; \
		exit 1; \
	fi
	@go test ./... -v

.PHONY: help
help:
	@echo "EmbryGo Makefile - Available commands:"
	@echo ""
	@echo "  Dependency Management & Setup (Pyt-Patrol for ./tools context):"
	@echo "    make setup-tools           - Crucial first step: Sets up/verifies all tool dependencies."
	@echo "    make check-deps            - Checks all tool dependencies (run 'make setup-tools' first if checks fail)."
	@echo ""
	@echo "  Development:"
	@echo "    make run                   - Starts app with live reload (Air). Assumes tools & assets are ready."
	@echo "    make generate-assets-dev   - Generates non-minified assets. (Run 'make setup-tools' if needed)."
	@echo ""
	@echo "  Production & Build:"
	@echo "    make all                   - Alias for 'make build'."
	@echo "    make build                 - Builds production binary and assets. (Run 'make setup-tools' if needed)."
	@echo "    make start-prod            - Runs the production-built binary."
	@echo "    make generate-assets-prod  - Generates minified assets. (Run 'make setup-tools' if needed)."
	@echo ""
	@echo "  Individual Asset Generation (Assumes tools are set up):"
	@echo "    make tailwind-dev          - Generate Tailwind CSS for development."
	@echo "    make tailwind-prod         - Generate Tailwind CSS for production."
	@echo "    make heroicons             - Generate Heroicon Templ components (generates .templ file ONLY)."
	@echo "    make templ-generate        - Generate Go code from ALL .templ files (including heroicons)."
	@echo "    make templ-generate-specific TARGET_DIR=<dir> - Generate Go code from .templ files in a specific directory."
	@echo ""
	@echo "  Maintenance (Assumes Go is set up):"
	@echo "    make check-nvm-node        - Verify NVM/Node prerequisites for EmbryGo (used by setup-tools)."
	@echo "    make npm-install-tools     - Install frontend dependencies for tools from $(TOOLS_EMBRYGO_DIR)/package.json."
	@echo "    make clean                 - Remove build artifacts, generated files, and caches."
	@echo "    make tidy                  - Run 'go mod tidy'."
	@echo "    make fmt                   - Format Go code."
	@echo ""
	@echo "  Testing (Assumes Go is set up):"
	@echo "    make test                  - Run Go tests."
	@echo ""