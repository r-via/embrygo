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