#!/bin/sh
set -e

# Run Alembic migrations
uv run alembic upgrade head

# Start the bot
exec uv run main.py
