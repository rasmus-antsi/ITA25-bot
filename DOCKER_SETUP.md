# Docker Setup Guide for ITA25 Bot

This guide shows how to set up the ITA25 Discord Bot using Docker with SQLite database persistence.

## 🐳 Docker Setup

### Prerequisites
- Docker and Docker Compose installed
- Discord Bot Token

### 1. Environment Setup

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token_here
DATA_DIR=/app/data
DB_PATH=/app/data/bot_data.db
```

### 2. Build and Run with Docker Compose

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### 3. Manual Docker Commands

```bash
# Build the image
docker build -t ita25-bot .

# Run with persistent volume
docker run -d \
  --name ita25-bot \
  --env-file .env \
  -v bot_data:/app/data \
  ita25-bot

# View logs
docker logs -f ita25-bot

# Stop and remove
docker stop ita25-bot
docker rm ita25-bot
```

## 📊 Database Management

### SQLite Database Location
- **Docker**: `/app/data/bot_data.db`
- **Local**: `./bot_data.db` (or `./data/bot_data.db` if DATA_DIR is set)

### Database Schema

#### Channels Table
```sql
CREATE TABLE channels (
    guild_id TEXT PRIMARY KEY,
    info_channel_id INTEGER,
    tunniplaan_channel_id INTEGER
);
```

#### Role Messages Table
```sql
CREATE TABLE role_messages (
    message_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    only_one BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Role Assignments Table
```sql
CREATE TABLE role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    emoji TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    role_name TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES role_messages(message_id)
);
```

### Database Access

#### From Host Machine
```bash
# Access the database file
docker cp ita25-bot:/app/data/bot_data.db ./bot_data.db

# Use sqlite3 to query
sqlite3 bot_data.db
.tables
SELECT * FROM channels;
SELECT * FROM role_messages;
SELECT * FROM role_assignments;
```

#### From Inside Container
```bash
# Enter the container
docker exec -it ita25-bot /bin/bash

# Access SQLite database
sqlite3 /app/data/bot_data.db
.tables
SELECT * FROM channels;
```

## 🔄 Data Migration

The bot automatically migrates data from the old JSON format (`channels.json`) to SQLite on first startup.

### Manual Migration
If you have existing data in `channels.json`:

1. Place `channels.json` in the data directory
2. Start the bot - it will automatically migrate the data
3. The JSON file will remain as backup

## 📁 Volume Management

### Docker Volume
- **Name**: `bot_data`
- **Mount Point**: `/app/data`
- **Contains**: SQLite database and any other persistent data

### Backup Database
```bash
# Create backup
docker exec ita25-bot cp /app/data/bot_data.db /app/data/bot_data_backup_$(date +%Y%m%d_%H%M%S).db

# Copy backup to host
docker cp ita25-bot:/app/data/bot_data_backup_20240101_120000.db ./
```

### Restore Database
```bash
# Copy database file to container
docker cp ./bot_data.db ita25-bot:/app/data/bot_data.db

# Restart container
docker restart ita25-bot
```

## 🚀 Production Deployment

### 1. Environment Variables
```env
DISCORD_TOKEN=your_production_token
DATA_DIR=/app/data
DB_PATH=/app/data/bot_data.db
```

### 2. Docker Compose for Production
```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file:
      - .env
    volumes:
      - bot_data:/app/data
    restart: unless-stopped
    environment:
      - DATA_DIR=/app/data
      - DB_PATH=/app/data/bot_data.db
    # Add resource limits for production
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

volumes:
  bot_data:
    driver: local
```

### 3. Monitoring
```bash
# Check container status
docker ps

# View resource usage
docker stats ita25-bot

# View logs
docker logs -f ita25-bot
```

## 🔧 Troubleshooting

### Common Issues

#### Database Permission Errors
```bash
# Fix permissions
docker exec ita25-bot chown -R 1000:1000 /app/data
docker exec ita25-bot chmod -R 755 /app/data
```

#### Database Corruption
```bash
# Check database integrity
docker exec ita25-bot sqlite3 /app/data/bot_data.db "PRAGMA integrity_check;"

# Recover if needed
docker exec ita25-bot sqlite3 /app/data/bot_data.db ".recover" | sqlite3 /app/data/bot_data_recovered.db
```

#### Bot Not Starting
```bash
# Check logs
docker logs ita25-bot

# Check environment variables
docker exec ita25-bot env | grep -E "(DISCORD_TOKEN|DATA_DIR|DB_PATH)"
```

### Reset Everything
```bash
# Stop and remove container
docker-compose down

# Remove volume (WARNING: This deletes all data!)
docker volume rm ita25-bot_bot_data

# Start fresh
docker-compose up -d
```

## 📈 Performance

### Database Optimization
- SQLite is very fast for this use case
- Database file is typically < 1MB
- No additional database server needed
- Automatic backups recommended

### Resource Usage
- **Memory**: ~50-100MB
- **CPU**: Minimal (only during commands)
- **Disk**: < 10MB for database
- **Network**: Only Discord API calls

## 🔒 Security

### File Permissions
- Database file: 644 (readable by owner, group)
- Data directory: 755 (executable by owner, group)
- Bot runs as non-root user

### Data Protection
- Database is stored in Docker volume
- No sensitive data in container image
- Environment variables for configuration
- Automatic data migration on startup
