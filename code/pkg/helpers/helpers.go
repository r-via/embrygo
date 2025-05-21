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