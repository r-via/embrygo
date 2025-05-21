package config

import (
	"fmt"
	"log/slog"
	"os"
	"strings"
)

type Config struct {
	AdminUser  string
	AdminPass  string
	AppBaseURL string
	DevMode    bool
}

var AppConfig Config

func LoadConfig(logger *slog.Logger) error {
	logger.Info("Loading EmbryGo application configuration...")

	AppConfig = Config{
		AdminUser:  os.Getenv("ADMIN_USER"),
		AdminPass:  os.Getenv("ADMIN_PASS"),
		AppBaseURL: os.Getenv("APP_BASE_URL"),
		DevMode:    os.Getenv("APP_ENV") == "development",
	}

	// Example: Make APP_BASE_URL required in production
	var missing []string
	if AppConfig.AppBaseURL == "" && AppConfig.DevMode == false {
		missing = append(missing, "APP_BASE_URL (required for production)")
	}
	// Add other critical checks if needed

	if len(missing) > 0 {
		errMsg := fmt.Sprintf("Missing required environment variables: %s", strings.Join(missing, ", "))
		logger.Error(errMsg)
		return fmt.Errorf(errMsg)
	}

	if AppConfig.AppBaseURL == "" && AppConfig.DevMode == true {
		defaultBaseURL := "http://localhost:" + os.Getenv("PORT")
        if os.Getenv("PORT") == "" { defaultBaseURL = "http://localhost:8080" }
		logger.Warn("APP_BASE_URL not set in .env, defaulting for development.", "default_base_url", defaultBaseURL)
        AppConfig.AppBaseURL = defaultBaseURL
	}


	logger.Info("EmbryGo application configuration loaded successfully.")
	return nil
}