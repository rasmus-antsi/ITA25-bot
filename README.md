# ITA25 Discord Bot

A Discord bot designed specifically for ITA25 students at VOCO (Tartu Kutsehariduskeskus). The bot provides automatic lesson schedules, info announcements, and timetable management with a fully Estonian interface.

## 🚀 Features

### 📅 Lesson Management
- **Automatic daily posting**: Lesson schedules posted every weekday at 6:00 AM
- **Manual lesson queries**: Check today's, tomorrow's, or specific date lessons
- **Smart grouping**: Lessons at the same time are grouped together with multiple teachers/rooms
- **Real-time data**: Fetches live data from VOCO's official timetable system

### 📢 Info System
- **Info announcements**: Send important messages to designated info channels
- **@everyone ping**: Automatic ping for important announcements
- **Image support**: Send images along with messages
- **Message cleanup**: Original command messages are automatically deleted

### ⚙️ Server Management
- **Server-specific settings**: Each Discord server has independent configurations
- **Persistent storage**: Settings survive bot restarts and Docker deployments
- **Permission-based**: Only users with "Manage Channels" permission can configure settings

## 🛠️ Installation

### Prerequisites
- Python 3.8+ or Docker
- Discord Bot Token
- Discord server with appropriate permissions

### Method 1: Local Installation

1. **Clone the repository:**
```bash
git clone https://github.com/rasmus-antsi/ITA25-bot.git
cd ITA25-bot
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create `.env` file:**
```env
DISCORD_TOKEN=your_discord_token_here
```

5. **Run the bot:**
```bash
python main.py
```

### Method 2: Docker (Recommended)

1. **Create `.env` file:**
```env
DISCORD_TOKEN=your_discord_token_here
```

2. **Run with Docker Compose:**
```bash
docker-compose up -d
```

3. **Or build and run manually:**
```bash
docker build -t ita25-bot .
docker run -d \
  --name ita25-bot \
  -e DISCORD_TOKEN=your_token \
  -v bot_data:/app/data \
  ita25-bot
```

## 📋 Commands

### 📅 Tunniplaan (Timetable)
- `!tunniplaan` - Näita tänaseid tunde (Show today's lessons)
- `!tunniplaan homme` - Näita homme tunde (Show tomorrow's lessons)
- `!tunniplaan DD.MM.YYYY` - Näita kindla kuupäeva tunde (Show specific date lessons)
- `!tunniplaan-set [#kanal]` - Määra automaatne tunniplaan kanal (Set automatic lesson channel)
- `!tunniplaan-remove` - Eemalda tunniplaan kanal (Remove lesson channel)

### 📢 Info
- `!info [sõnum]` - Saada sõnum info kanalile @everyone pingiga (Send message to info channel)
- `!info-set [#kanal]` - Määra info kanal (Set info channel)
- `!info-remove` - Eemalda info kanal (Remove info channel)

### 🔧 Muud (Others)
- `!hello` - Tervitus (Greeting)
- `!help` - Näita kõiki käske (Show all commands)

## ⚙️ Configuration

### Data Storage
- **Location**: `/app/data/channels.json` (Docker) or `./channels.json` (local)
- **Format**: JSON with server-specific channel mappings
- **Backup**: Automatically created and maintained

### Permissions Required
- **Bot permissions**: Send Messages, Embed Links, Manage Messages
- **User permissions**: Manage Channels (for configuration commands)

## 🏗️ Architecture

### File Structure
```
ITA25-Bot/
├── main.py                 # Bot entry point
├── src/
│   ├── commands.py         # Discord command handlers
│   └── scraper.py          # VOCO timetable scraper
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── README.md              # This file
```

### Key Components
- **Discord.py**: Bot framework and Discord API integration
- **BeautifulSoup4**: HTML parsing for VOCO timetable scraping
- **Requests**: HTTP requests for data fetching
- **Python-dotenv**: Environment variable management

## 🔒 Security

### Data Protection
- ✅ No sensitive data in repository
- ✅ Environment variables for tokens
- ✅ `.gitignore` configured for data files
- ✅ Server-specific data isolation

### Files Ignored
- `.env` - Environment variables
- `channels.json` - Channel configuration data
- `data/` - Persistent data directory
- `venv/` - Virtual environment
- `__pycache__/` - Python cache files

## 🚀 Deployment

### Production Setup
1. Create Discord application and bot
2. Set up environment variables
3. Deploy using Docker Compose
4. Configure channels using bot commands
5. Monitor logs for any issues

### Environment Variables
```env
DISCORD_TOKEN=your_discord_bot_token
DATA_DIR=/app/data  # Optional, defaults to current directory
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Contact the maintainer
- Check the Discord server for community support

---

**Made with ❤️ by ITA25 student for ITA25 students at VOCO**