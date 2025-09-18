# ITA25 Discord Bot

Discord bot for ITA25 group with lesson schedule and info management features.

## Features

- **`!tunniplaan`** - Show today's lessons for ITA25
- **`!tunniplaan-set [#channel]`** - Set channel for automatic daily lesson notifications (6 AM weekdays)
- **`!tunniplaan-remove`** - Remove tunniplaan channel
- **`!info [message/image]`** - Send important info to designated channel with @everyone ping
- **`!info-set [#channel]`** - Set info channel
- **`!info-remove`** - Remove info channel
- **`!hello`** - Basic test command

## Docker Setup

### Using docker-compose (Recommended)

1. Create `.env` file with your Discord token:
   ```
   DISCORD_TOKEN=your_discord_token_here
   ```

2. Run with docker-compose:
   ```bash
   docker-compose up -d
   ```

### Using Docker directly

1. Build the image:
   ```bash
   docker build -t ita25-bot .
   ```

2. Run with persistent volume:
   ```bash
   docker run -d \
     --name ita25-bot \
     -e DISCORD_TOKEN=your_token \
     -v bot_data:/app/data \
     ita25-bot
   ```

## Data Persistence

- Channel settings are stored in `/app/data/channels.json`
- Data persists across container restarts and updates
- Each Discord server has its own channel settings
- `channels.json` is excluded from git to prevent data loss on updates

## Commands

All commands are in Estonian and require appropriate permissions.

### Manual Commands
- `!hello` - Test if bot is working
- `!tunniplaan` - Show today's lessons (works anywhere)

### Channel Management
- `!tunniplaan-set [#channel]` - Set automatic lesson notifications channel
- `!tunniplaan-remove` - Remove lesson notifications channel
- `!info-set [#channel]` - Set info announcements channel
- `!info-remove` - Remove info announcements channel

### Info Commands
- `!info [message]` - Send message to info channel with @everyone ping
- `!info [image]` - Send image to info channel with @everyone ping

## Automatic Features

- **Daily lesson posting**: Every weekday at 6:00 AM to configured tunniplaan channels
- **Server-specific settings**: Each Discord server has independent channel configurations
- **Persistent storage**: Settings survive bot restarts and Docker deployments

## Requirements

- Python 3.11+
- Discord.py
- Requests
- BeautifulSoup4
- python-dotenv
