# ITA25 Discord Bot

A Discord bot designed specifically for ITA25 students at VOCO (Tartu Kutsehariduskeskus). The bot provides automatic lesson schedules, info announcements, timetable management, and role management with a fully Estonian interface.

## 🚀 Features

### 📅 Timetable Management
- **Automatic daily lessons**: Posts today's lessons every weekday at 6:00 AM
- **On-demand timetable**: `!tunniplaan`, `!tunniplaan homme`, `!tunniplaan DD.MM.YYYY`
- **Grouped lessons**: Organizes multiple subjects/teachers/rooms for the same time slot
- **ITA25 specific**: Fetches timetable for ITA25 group (course ID 2078)

### 📢 Info Announcements
- **Info announcements**: Send important messages to designated info channels
- **@everyone ping**: Automatic ping for important announcements
- **Image support**: Send images along with messages
- **Message cleanup**: Original command messages are automatically deleted

### ⚙️ Server Management
- **Server-specific settings**: Each Discord server has independent configurations
- **Persistent storage**: Settings survive bot restarts and Docker deployments
- **Permission-based**: Only users with "Manage Channels" permission can configure settings

### 🎭 Role Management
- **Reaction-based roles**: Users can get/remove roles by clicking reactions
- **Easy setup**: Simple commands to add/remove roles with emojis
- **Single or multiple selection**: Choose one role or multiple roles
- **Toggle behavior**: Click reaction to add role, click again to remove
- **Permission checks**: Only users with "Manage Roles" permission can configure

## 🛠️ Installation

### Prerequisites
- Python 3.8+ or Docker
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- Discord server with appropriate permissions

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rasmus-antsi/ITA25-bot.git
   cd ITA25-bot
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   Create a file named `.env` in the root directory with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_token_here
   ```

5. **Run the bot:**
   ```bash
   python main.py
   ```

### Docker Setup (Recommended for Deployment)

1. **Create `.env` file:**
   Create a file named `.env` in the root directory with your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_token_here
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```
   This will build the Docker image, create a persistent volume for data, and run the bot in the background.

3. **View logs (optional):**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the bot:**
   ```bash
   docker-compose down
   ```

## 📋 Commands (Estonian)

All commands are in Estonian and require appropriate permissions.

### 📅 Tunniplaan (Timetable)
- `!tunniplaan` - Näita tänaseid tunde (Show today's lessons)
- `!tunniplaan homme` - Näita homme tunde (Show tomorrow's lessons)
- `!tunniplaan DD.MM.YYYY` - Näita kindla kuupäeva tunde (Show lessons for a specific date)
- `!tunniplaan-set [#kanal]` - Määra automaatne tunniplaan kanal (Set automatic lesson notifications channel)
- `!tunniplaan-remove` - Eemalda tunniplaan kanal (Remove lesson notifications channel)

### 📢 Info (Info)
- `!info [sõnum]` - Saada sõnum info kanalile @everyone pingiga (Send message to info channel)
- `!info-set [#kanal]` - Määra info kanal (Set info channel)
- `!info-remove` - Eemalda info kanal (Remove info channel)

### 🎭 Rollid (Roles)
- `!vota-rollid @roll1 🎭1 @roll2 🎭2 True` - Loo rollide valimise sõnum (Create role selection message)
  - Use `True` or `true` for single role selection
  - Users click reactions to get/remove roles
  - Toggle behavior: click to add, click again to remove

### 🔧 Muud (Others)
- `!hello` - Tervitus (Greeting)
- `!help` - Näita kõiki käske (Show all commands)

## ⚙️ Configuration

### Data Storage
- **Location**: `/app/data/bot_data.db` (Docker) or `./bot_data.db` (local)
- **Persistence**: Data is stored in an SQLite database and persists across bot restarts and Docker deployments using a named volume (`bot_data`).
- **Migration**: Automatically migrates from `channels.json` to `bot_data.db` on first run if `channels.json` exists.

### Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token.
- `DATA_DIR`: Directory for persistent data (default: `/app/data` in Docker, `.` locally).
- `DB_PATH`: Full path to the SQLite database file (default: `/app/data/bot_data.db` in Docker, `./bot_data.db` locally).

### Permissions Required
- **Bot permissions**: Send Messages, Embed Links, Manage Messages, Add Reactions, Manage Roles
- **User permissions**: 
  - Manage Channels (for info/tunniplaan configuration)
  - Manage Roles (for role management setup)

## 🏗️ Architecture

- **`main.py`**: Bot entry point, handles Discord events, schedules daily tasks.
- **`src/commands.py`**: Defines all bot commands and event handlers for reactions.
- **`src/scraper.py`**: Web scraping logic for VOCO timetable.
- **`src/database.py`**: SQLite database management for persistent settings.
- **`Dockerfile`**: Defines the Docker image for the bot.
- **`docker-compose.yml`**: Orchestrates Docker containers for easy deployment.

## 🔒 Security

- **No hardcoded tokens**: Discord token is loaded from `.env` file.
- **`.gitignore`**: Excludes sensitive files (`.env`, `channels.json`, `data/`, `venv/`, `__pycache__/`).
- **Data isolation**: Server-specific settings are stored securely in the database.
- **Permission-based commands**: Critical commands require specific Discord permissions.

## 🚀 Deployment

### Production Setup
1. Create Discord application and bot
2. Set up environment variables
3. Deploy using Docker Compose
4. Configure channels using bot commands
5. Monitor logs for any issues

### Docker Volume Management
The bot uses a named Docker volume (`bot_data`) for persistent data storage. This ensures your settings survive container restarts and updates.

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Contact the maintainer
- Check the Discord server for community support

---

**Made with ❤️ by ITA25 student for ITA25 students at VOCO**