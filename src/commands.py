import discord
import os
import re
from datetime import datetime
from .scraper import VOCOScraper

# Store the info channel IDs per server (guild)
info_channels = {}
# Store the tunniplaan channel IDs per server (guild)
tunniplaan_channels = {}

def load_channels():
    """Load saved channel IDs for all servers"""
    global info_channels, tunniplaan_channels
    try:
        # Try to load from file first (use data directory if available)
        data_dir = os.getenv('DATA_DIR', '.')
        file_path = os.path.join(data_dir, 'channels.json')
        
        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
            info_channels = data.get('info_channels', {})
            tunniplaan_channels = data.get('tunniplaan_channels', {})
        print(f"📢 Channels loaded from file: {len(info_channels)} info, {len(tunniplaan_channels)} tunniplaan servers")
    except FileNotFoundError:
        print("📢 No channels set yet")
        info_channels = {}
        tunniplaan_channels = {}
    except Exception as e:
        print(f"⚠️ Error loading channels: {e}")
        info_channels = {}
        tunniplaan_channels = {}

def save_channels():
    """Save all channel settings to file"""
    try:
        data_dir = os.getenv('DATA_DIR', '.')
        file_path = os.path.join(data_dir, 'channels.json')
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        import json
        data = {
            'info_channels': info_channels,
            'tunniplaan_channels': tunniplaan_channels
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        print(f"📢 Channels saved to file: {file_path}")
    except Exception as e:
        print(f"⚠️ Could not save to file: {e}")

def setup_info_commands(bot):
    """Setup info-related commands"""
    
    @bot.command(name='hello')
    async def hello(ctx):
        await ctx.send("Tere! Olen elus Dockeris 🐳")

    @bot.command(name='tunniplaan')
    async def tunniplaan(ctx, *, date_param=None):
        """Näita tunde ITA25-le. Kasutamine: !tunniplaan, !tunniplaan homme, !tunniplaan 15.01.2025"""
        await ctx.send("🔍 Laen tunde...")
        
        try:
            scraper = VOCOScraper()
            
            # Determine which date to fetch
            if date_param is None:
                # Today
                lessons = scraper.get_todays_lessons()
                date_title = "Tänased tunnid (ITA25)"
            elif date_param.lower() in ['homme', 'tomorrow']:
                # Tomorrow
                lessons = scraper.get_lessons_for_date('tomorrow')
                date_title = "Homse tunnid (ITA25)"
            else:
                # Specific date
                try:
                    # Parse date in DD.MM.YYYY format
                    parsed_date = datetime.strptime(date_param, '%d.%m.%Y')
                    lessons = scraper.get_lessons_for_date(parsed_date.strftime('%d.%m.%Y'))
                    date_title = f"Tunnid {date_param} (ITA25)"
                except ValueError:
                    await ctx.send("❌ Vale kuupäeva formaat! Kasuta: DD.MM.YYYY (nt. 15.01.2025)")
                    return
            
            if not lessons:
                if date_param is None:
                    await ctx.send("📅 **Täna tunde ei ole** - Vaba päev! 🎉")
                elif date_param.lower() in ['homme', 'tomorrow']:
                    await ctx.send("📅 **Homme tunde ei ole** - Vaba päev! 🎉")
                else:
                    await ctx.send(f"📅 **{date_param} tunde ei ole** - Vaba päev! 🎉")
                return
            
            # Sort lessons by time
            lessons.sort(key=lambda x: x.get('start_time', ''))
            
            # Create embed
            embed = discord.Embed(
                title=f"📅 {date_title}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Add lessons to embed
            for i, lesson in enumerate(lessons):
                time = f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}"
                
                # Format lesson info
                lesson_info = ""
                
                # Handle multiple subjects/teachers/rooms (grouped by time)
                if 'teachers' in lesson and 'rooms' in lesson and 'subjects' in lesson:
                    # Multiple subjects/teachers/rooms (grouped by time slot)
                    teachers = lesson['teachers']
                    rooms = lesson['rooms']
                    subjects = lesson['subjects']
                    
                    for j, (teacher, room, subject) in enumerate(zip(teachers, rooms, subjects)):
                        # Clean subject name for display
                        clean_subject = re.sub(r'_\s*Rühm\s*\d+|_\s*R\d+', '', subject).strip()
                        clean_subject = re.sub(r'\s*Rühm\s*\d+|\s*R\d+', '', clean_subject).strip()
                        clean_subject = re.sub(r'_\s*$', '', clean_subject).strip()
                        
                        lesson_info += f"**{clean_subject}**\n"
                        
                        # Show group info if present
                        group_suffix = re.search(r'_\s*Rühm\s*\d+|_\s*R\d+', subject)
                        if group_suffix:
                            lesson_info += f"📚 {group_suffix.group(0).replace('_', ' ').strip()}: "
                        elif 'Rühm' in subject or 'R1' in subject or 'R2' in subject:
                            # Extract group info from subject name
                            group_match = re.search(r'(Rühm\s*\d+|R\d+)', subject)
                            if group_match:
                                lesson_info += f"📚 {group_match.group(0)}: "
                        
                        if teacher and teacher != 'Tundmatu':
                            lesson_info += f"👨‍🏫 {teacher}"
                        if room and room != 'Tundmatu ruum':
                            lesson_info += f" - 🏫 {room}"
                        if j < len(teachers) - 1:
                            lesson_info += "\n\n"
                else:
                    # Single subject/teacher/room (original format)
                    subject = lesson.get('subject', 'Tundmatu aine')
                    clean_subject = re.sub(r'_\s*Rühm\s*\d+|_\s*R\d+', '', subject).strip()
                    clean_subject = re.sub(r'\s*Rühm\s*\d+|\s*R\d+', '', clean_subject).strip()
                    clean_subject = re.sub(r'_\s*$', '', clean_subject).strip()
                    
                    lesson_info += f"**{clean_subject}**\n"
                    
                    teacher = lesson.get('teacher', 'Tundmatu')
                    room = lesson.get('room', 'Tundmatu ruum')
                    if teacher and teacher != 'Tundmatu':
                        lesson_info += f"👨‍🏫 {teacher}"
                    if room and room != 'Tundmatu ruum':
                        lesson_info += f" - 🏫 {room}"
                
                embed.add_field(
                    name=f"Tund {i+1} - ⏰ {time}",
                    value=lesson_info,
                    inline=False
                )
            
            embed.set_footer(text=f"Kokku {len(lessons)} tundi")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Viga tundide laadimisel: {e}")
            print(f"Error in tunniplaan command: {e}")

    @bot.command(name='info')
    async def info(ctx, *, message=None):
        """Saada olulist teavet info kanalile @everyone pingiga"""
        global info_channels
        
        # Check if info channel is set for this server
        guild_id = str(ctx.guild.id)
        if guild_id not in info_channels:
            await ctx.send("❌ Info kanal pole määratud! Kasuta `!info-set` kanali määramiseks.")
            return
        
        # Get the info channel
        info_channel_id = info_channels[guild_id]
        info_channel = bot.get_channel(info_channel_id)
        if info_channel is None:
            await ctx.send("❌ Info kanalit ei leitud! Kasuta `!info-set` kehtiva kanali määramiseks.")
            return
        
        # Check if user has permission to send messages in the info channel
        if not info_channel.permissions_for(ctx.author).send_messages:
            await ctx.send("❌ Sul pole õigust sõnumeid saata info kanalisse.")
            return
        
        # If no message and no attachments, ask for one
        if not message and not ctx.message.attachments:
            await ctx.send("❌ Palun anna sõnum või pilt! Kasutamine: `!info Sinu sõnum siia` või lisa pilt")
            return
        
        # Delete the original command message first
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            # Bot doesn't have permission to delete messages
            pass
        except Exception as e:
            print(f"⚠️ Could not delete message: {e}")
            pass
        
        # Check if there are attachments (images)
        if ctx.message.attachments:
            # If there are images, send them with @everyone ping
            await info_channel.send("@everyone")
            
            # Send each attachment
            for attachment in ctx.message.attachments:
                await info_channel.send(file=await attachment.to_file())
        else:
            # If no images, send text with @everyone ping and attribution
            await info_channel.send(f"@everyone {message} by {ctx.author.display_name}")
        
        # Send a confirmation message to the user (like info-set does)
        await ctx.send(f"✅ Info saadetud {info_channel.mention}")

    @bot.command(name='info-set')
    async def info_set(ctx, channel: discord.TextChannel = None):
        """Määra kanal, kuhu info sõnumid saadetakse"""
        global info_channels
        
        if channel is None:
            # If no channel mentioned, use current channel
            channel = ctx.channel
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust info kanali määramiseks.")
            return
        
        # Set the info channel for this server
        guild_id = str(ctx.guild.id)
        info_channels[guild_id] = channel.id
        await ctx.send(f"✅ Info kanal määratud {channel.mention}")
        
        # Save to file for persistence (automatic, no user notification)
        save_channels()

    @bot.command(name='info-remove')
    async def info_remove(ctx):
        """Eemalda info kanal"""
        global info_channels
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust info kanali eemaldamiseks.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in info_channels:
            await ctx.send("❌ Info kanal pole määratud.")
            return
        
        # Get the current info channel for display
        info_channel_id = info_channels[guild_id]
        info_channel = bot.get_channel(info_channel_id)
        channel_mention = info_channel.mention if info_channel else f"ID: {info_channel_id}"
        
        # Clear the info channel for this server
        del info_channels[guild_id]
        
        # Save updated channels to file
        save_channels()
        
        await ctx.send(f"✅ Info kanal eemaldatud: {channel_mention}")

    @bot.command(name='tunniplaan-set')
    async def tunniplaan_set(ctx, channel: discord.TextChannel = None):
        """Määra kanal, kuhu saadetakse automaatsed tunniplaan sõnumid"""
        global tunniplaan_channels
        
        if channel is None:
            # If no channel mentioned, use current channel
            channel = ctx.channel
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust tunniplaan kanali määramiseks.")
            return
        
        # Set the tunniplaan channel for this server
        guild_id = str(ctx.guild.id)
        tunniplaan_channels[guild_id] = channel.id
        await ctx.send(f"✅ Tunniplaan kanal määratud {channel.mention}")
        await ctx.send("📅 Automaatsed tunniplaan sõnumid saadetakse igal tööpäeval kell 06:00")
        
        # Save to file for persistence (automatic, no user notification)
        save_channels()

    @bot.command(name='tunniplaan-remove')
    async def tunniplaan_remove(ctx):
        """Eemalda tunniplaan kanal"""
        global tunniplaan_channels
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust tunniplaan kanali eemaldamiseks.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in tunniplaan_channels:
            await ctx.send("❌ Tunniplaan kanal pole määratud.")
            return
        
        # Get the current tunniplaan channel for display
        tunniplaan_channel_id = tunniplaan_channels[guild_id]
        tunniplaan_channel = bot.get_channel(tunniplaan_channel_id)
        channel_mention = tunniplaan_channel.mention if tunniplaan_channel else f"ID: {tunniplaan_channel_id}"
        
        # Clear the tunniplaan channel for this server
        del tunniplaan_channels[guild_id]
        
        # Save updated channels to file
        save_channels()
        
        await ctx.send(f"✅ Tunniplaan kanal eemaldatud: {channel_mention}")

    # Load channels on startup
    load_channels()
