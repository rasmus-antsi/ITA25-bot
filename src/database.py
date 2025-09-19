"""
SQLite Database Management for ITA25 Bot
"""
import aiosqlite
import os
import json
from typing import Dict, List, Optional, Tuple

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use environment variable or default to local file
            data_dir = os.getenv('DATA_DIR', '.')
            db_path = os.getenv('DB_PATH', os.path.join(data_dir, 'bot_data.db'))
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize the database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Channels table for info and tunniplaan channels
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    guild_id TEXT PRIMARY KEY,
                    info_channel_id INTEGER,
                    tunniplaan_channel_id INTEGER
                )
            """)
            
            # Role management messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_messages (
                    message_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    only_one BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Role assignments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS role_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    role_name TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES role_messages(message_id)
                )
            """)
            
            await db.commit()
    
    async def get_channels(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Get info and tunniplaan channels for all guilds"""
        info_channels = {}
        tunniplaan_channels = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT guild_id, info_channel_id, tunniplaan_channel_id FROM channels") as cursor:
                async for row in cursor:
                    guild_id, info_channel_id, tunniplaan_channel_id = row
                    if info_channel_id:
                        info_channels[guild_id] = info_channel_id
                    if tunniplaan_channel_id:
                        tunniplaan_channels[guild_id] = tunniplaan_channel_id
        
        return info_channels, tunniplaan_channels
    
    async def save_channels(self, info_channels: Dict[str, int], tunniplaan_channels: Dict[str, int]):
        """Save info and tunniplaan channels for all guilds"""
        async with aiosqlite.connect(self.db_path) as db:
            # Clear existing data
            await db.execute("DELETE FROM channels")
            
            # Get all unique guild IDs
            all_guild_ids = set(info_channels.keys()) | set(tunniplaan_channels.keys())
            
            # Insert data for each guild
            for guild_id in all_guild_ids:
                info_channel_id = info_channels.get(guild_id)
                tunniplaan_channel_id = tunniplaan_channels.get(guild_id)
                
                await db.execute("""
                    INSERT INTO channels (guild_id, info_channel_id, tunniplaan_channel_id)
                    VALUES (?, ?, ?)
                """, (guild_id, info_channel_id, tunniplaan_channel_id))
            
            await db.commit()
    
    async def save_role_message(self, message_id: str, guild_id: str, channel_id: int, only_one: bool, roles_data: Dict[str, Dict]):
        """Save a role management message and its role assignments"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert the message
            await db.execute("""
                INSERT OR REPLACE INTO role_messages (message_id, guild_id, channel_id, only_one)
                VALUES (?, ?, ?, ?)
            """, (message_id, guild_id, channel_id, only_one))
            
            # Remove existing role assignments for this message
            await db.execute("DELETE FROM role_assignments WHERE message_id = ?", (message_id,))
            
            # Insert new role assignments
            for emoji, role_info in roles_data.items():
                await db.execute("""
                    INSERT INTO role_assignments (message_id, emoji, role_id, role_name)
                    VALUES (?, ?, ?, ?)
                """, (message_id, emoji, role_info['role_id'], role_info.get('role_name', '')))
            
            await db.commit()
    
    async def get_role_message(self, message_id: str) -> Optional[Dict]:
        """Get role message data by message ID"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get message info
            async with db.execute("""
                SELECT guild_id, channel_id, only_one FROM role_messages 
                WHERE message_id = ?
            """, (message_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                guild_id, channel_id, only_one = row
                
                # Get role assignments
                roles = {}
                async with db.execute("""
                    SELECT emoji, role_id, role_name FROM role_assignments 
                    WHERE message_id = ?
                """, (message_id,)) as role_cursor:
                    async for role_row in role_cursor:
                        emoji, role_id, role_name = role_row
                        roles[emoji] = {
                            'role_id': role_id,
                            'role_name': role_name
                        }
                
                return {
                    'guild_id': guild_id,
                    'channel_id': channel_id,
                    'only_one': bool(only_one),
                    'roles': roles
                }
    
    async def delete_role_message(self, message_id: str):
        """Delete a role message and its assignments"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM role_assignments WHERE message_id = ?", (message_id,))
            await db.execute("DELETE FROM role_messages WHERE message_id = ?", (message_id,))
            await db.commit()
    
    async def migrate_from_json(self, json_file_path: str):
        """Migrate data from existing JSON file to SQLite (if exists)"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            info_channels = data.get('info_channels', {})
            tunniplaan_channels = data.get('tunniplaan_channels', {})
            role_management = data.get('role_management', {})
            
            # Migrate channels
            await self.save_channels(info_channels, tunniplaan_channels)
            
            # Migrate role management
            for guild_id, guild_data in role_management.items():
                if 'messages' in guild_data:
                    for message_id, message_data in guild_data['messages'].items():
                        await self.save_role_message(
                            message_id,
                            guild_id,
                            0,  # We don't have channel_id in old data
                            message_data.get('only_one', False),
                            message_data.get('roles', {})
                        )
            
            print(f"✅ Migrated data from {json_file_path} to SQLite")
            
        except FileNotFoundError:
            print(f"📢 No JSON file found at {json_file_path}, starting with empty database")
        except Exception as e:
            print(f"⚠️ Error migrating from JSON: {e}")

# Global database instance
db = Database()
