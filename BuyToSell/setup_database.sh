#!/bin/bash

echo "Setting up BestBuyAndSell Database..."

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "PostgreSQL is not running. Please start PostgreSQL service."
    exit 1
fi

# Create database (optional - you might need to adjust based on your setup)
echo "Creating database 'buytosell'..."
createdb buytosell 2>/dev/null || echo "Database may already exist"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo "Database setup complete!"
echo "You can now run the application with: uvicorn app.main:app --reload"
