#!/bin/bash

# Stop on any error
set -e

# Go to the bot directory
cd "$(dirname "$0")"

echo "📦 Pulling latest changes from Git..."
git pull

echo "🐳 Rebuilding Docker image..."
docker build -t ita25-bot .

echo "🔄 Stopping current container (if running)..."
docker stop ita25-bot 2>/dev/null || true
docker rm ita25-bot 2>/dev/null || true

echo "▶️ Starting new container..."
docker run -d --name ita25-bot --restart unless-stopped -e DISCORD_TOKEN="${DISCORD_TOKEN}" ita25-bot

echo "✅ Update complete!"
