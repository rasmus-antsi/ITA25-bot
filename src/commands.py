import discord
import os
import re
import json
from datetime import datetime
from .scraper import VOCOScraper

# Store the info channel IDs per server (guild)
info_channels = {}
# Store the tunniplaan channel IDs per server (guild)
tunniplaan_channels = {}
# Store role management data per server (guild)
role_management = {}

def load_channels():
    """Load saved channel IDs and role management for all servers"""
    global info_channels, tunniplaan_channels, role_management
    try:
        # Try to load from file first (use data directory if available)
        data_dir = os.getenv('DATA_DIR', '.')
        file_path = os.path.join(data_dir, 'channels.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            info_channels = data.get('info_channels', {})
            tunniplaan_channels = data.get('tunniplaan_channels', {})
            role_management = data.get('role_management', {})
        print(f"📢 Channels loaded from file: {len(info_channels)} info, {len(tunniplaan_channels)} tunniplaan, {len(role_management)} role servers")
    except FileNotFoundError:
        print("📢 No channels set yet")
        info_channels = {}
        tunniplaan_channels = {}
        role_management = {}
    except Exception as e:
        print(f"⚠️ Error loading channels: {e}")
        info_channels = {}
        tunniplaan_channels = {}
        role_management = {}

def save_channels():
    """Save all channel settings and role management to file"""
    try:
        data_dir = os.getenv('DATA_DIR', '.')
        file_path = os.path.join(data_dir, 'channels.json')
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        data = {
            'info_channels': info_channels,
            'tunniplaan_channels': tunniplaan_channels,
            'role_management': role_management
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        print(f"📢 Channels saved to file: {file_path}")
    except Exception as e:
        print(f"⚠️ Could not save to file: {e}")

def setup_info_commands(bot):
    """Setup info-related commands"""
    
    # Remove the built-in help command
    bot.remove_command('help')
    
    @bot.command(name='hello')
    async def hello(ctx):
        await ctx.send("Tere! Olen elus Dockeris 🐳")

    @bot.command(name='help')
    async def help_command(ctx):
        """Näita kõiki saadaolevaid käske"""
        embed = discord.Embed(
            title="🤖 ITA25 Bot - Käsud",
            description="Siin on kõik saadaolevad käsud:",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Tunniplaan commands
        embed.add_field(
            name="📅 Tunniplaan",
            value=(
                "`!tunniplaan` - Näita tänaseid tunde\n"
                "`!tunniplaan homme` - Näita homme tunde\n"
                "`!tunniplaan DD.MM.YYYY` - Näita kindla kuupäeva tunde\n"
                "`!tunniplaan-set [#kanal]` - Määra automaatne tunniplaan kanal\n"
                "`!tunniplaan-remove` - Eemalda tunniplaan kanal"
            ),
            inline=False
        )
        
        # Info commands
        embed.add_field(
            name="📢 Info",
            value=(
                "`!info [sõnum]` - Saada sõnum info kanalile @everyone pingiga\n"
                "`!info-set [#kanal]` - Määra info kanal\n"
                "`!info-remove` - Eemalda info kanal"
            ),
            inline=False
        )
        
        # Role commands
        embed.add_field(
            name="🎭 Rollid",
            value=(
                "`!rollid` - Näita saadaolevaid rolle ja reaktsioone\n"
                "`!rollid-lisa @roll 🎭 [kirjeldus]` - Lisa uus roll\n"
                "`!rollid-eemalda 🎭` - Eemalda roll"
            ),
            inline=False
        )
        
        # Other commands
        embed.add_field(
            name="🔧 Muud",
            value=(
                "`!hello` - Tervitus\n"
                "`!help` - Näita seda abi sõnumit"
            ),
            inline=False
        )
        
        # Examples
        embed.add_field(
            name="💡 Näited",
            value=(
                "`!tunniplaan` - Tänased tunnid\n"
                "`!tunniplaan homme` - Homse tunnid\n"
                "`!tunniplaan 15.01.2025` - Tunnid 15. jaanuaril 2025\n"
                "`!info Tähtis teade!` - Saada teade info kanalile\n"
                "`!rollid-lisa @Student 🎓 ITA25 õpilane` - Lisa õpilase roll"
            ),
            inline=False
        )
        
        embed.set_footer(text="ITA25 Bot - Automaatne tunniplaan ja info süsteem")
        
        await ctx.send(embed=embed)

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
            elif date_param.lower() == 'homme':
                # Tomorrow
                lessons = scraper.get_lessons_for_date('tomorrow')
                date_title = "Homsed tunnid (ITA25)"
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
                elif date_param.lower() == 'homme':
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

    @bot.command(name='rollid')
    async def rollid(ctx):
        """Näita saadaolevaid rolle ja nende reaktsioone"""
        global role_management
        
        guild_id = str(ctx.guild.id)
        if guild_id not in role_management or not role_management[guild_id].get('roles'):
            await ctx.send("❌ Pole ühtegi rolli määratud! Kasuta `!rollid-lisa` rollide lisamiseks.")
            return
        
        embed = discord.Embed(
            title="🎭 Saadaolevad rollid",
            description="Kliki reaktsioonile, et rolli saada või eemaldada:",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        roles_data = role_management[guild_id]['roles']
        for emoji, role_info in roles_data.items():
            role = ctx.guild.get_role(role_info['role_id'])
            if role:
                embed.add_field(
                    name=f"{emoji} {role.name}",
                    value=f"Kirjeldus: {role_info.get('description', 'Pole kirjeldust')}",
                    inline=False
                )
        
        embed.set_footer(text="Kasuta !rollid-lisa uute rollide lisamiseks")
        
        message = await ctx.send(embed=embed)
        
        # Add reactions for each role
        for emoji in roles_data.keys():
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass

    @bot.command(name='rollid-lisa')
    async def rollid_lisa(ctx, role: discord.Role, emoji: str, *, description: str = ""):
        """Lisa uus roll reaktsiooniga. Kasutamine: !rollid-lisa @roll 🎭 Kirjeldus"""
        global role_management
        
        # Check if user has permission to manage roles
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("❌ Sul on vaja 'Rollide haldamine' õigust rollide lisamiseks.")
            return
        
        # Check if bot can manage this role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ Ma ei saa hallata seda rolli - see on minu rollist kõrgemal!")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in role_management:
            role_management[guild_id] = {'roles': {}}
        
        # Check if emoji is already used
        if emoji in role_management[guild_id]['roles']:
            await ctx.send(f"❌ Reaktsioon {emoji} on juba kasutusel!")
            return
        
        # Check if role is already assigned
        for existing_emoji, role_info in role_management[guild_id]['roles'].items():
            if role_info['role_id'] == role.id:
                await ctx.send(f"❌ Roll {role.name} on juba määratud reaktsiooniga {existing_emoji}!")
                return
        
        # Add the role
        role_management[guild_id]['roles'][emoji] = {
            'role_id': role.id,
            'description': description
        }
        
        save_channels()
        
        await ctx.send(f"✅ Roll {role.mention} lisatud reaktsiooniga {emoji}")

    @bot.command(name='rollid-eemalda')
    async def rollid_eemalda(ctx, emoji: str):
        """Eemalda roll reaktsiooniga. Kasutamine: !rollid-eemalda 🎭"""
        global role_management
        
        # Check if user has permission to manage roles
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("❌ Sul on vaja 'Rollide haldamine' õigust rollide eemaldamiseks.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in role_management or emoji not in role_management[guild_id]['roles']:
            await ctx.send(f"❌ Reaktsioon {emoji} pole määratud!")
            return
        
        role_info = role_management[guild_id]['roles'][emoji]
        role = ctx.guild.get_role(role_info['role_id'])
        role_name = role.name if role else "Tundmatu roll"
        
        # Remove the role
        del role_management[guild_id]['roles'][emoji]
        
        # If no more roles, remove the guild entry
        if not role_management[guild_id]['roles']:
            del role_management[guild_id]
        
        save_channels()
        
        await ctx.send(f"✅ Roll {role_name} eemaldatud reaktsiooniga {emoji}")

    @bot.event
    async def on_reaction_add(reaction, user):
        """Handle role assignment when user reacts"""
        if user.bot:
            return
        
        # Check if this is a role management message
        if not reaction.message.embeds:
            return
        
        embed = reaction.message.embeds[0]
        if embed.title != "🎭 Saadaolevad rollid":
            return
        
        guild_id = str(reaction.message.guild.id)
        if guild_id not in role_management:
            return
        
        emoji_str = str(reaction.emoji)
        if emoji_str not in role_management[guild_id]['roles']:
            return
        
        role_info = role_management[guild_id]['roles'][emoji_str]
        role = reaction.message.guild.get_role(role_info['role_id'])
        
        if not role:
            return
        
        try:
            # Add the role to the user
            await user.add_roles(role)
            await user.send(f"✅ Sa said rolli: **{role.name}**")
        except discord.Forbidden:
            await user.send("❌ Ma ei saa sulle rolli anda - kontrolli õigusi!")
        except Exception as e:
            await user.send(f"❌ Viga rolli andmisel: {e}")

    @bot.event
    async def on_reaction_remove(reaction, user):
        """Handle role removal when user removes reaction"""
        if user.bot:
            return
        
        # Check if this is a role management message
        if not reaction.message.embeds:
            return
        
        embed = reaction.message.embeds[0]
        if embed.title != "🎭 Saadaolevad rollid":
            return
        
        guild_id = str(reaction.message.guild.id)
        if guild_id not in role_management:
            return
        
        emoji_str = str(reaction.emoji)
        if emoji_str not in role_management[guild_id]['roles']:
            return
        
        role_info = role_management[guild_id]['roles'][emoji_str]
        role = reaction.message.guild.get_role(role_info['role_id'])
        
        if not role:
            return
        
        try:
            # Remove the role from the user
            await user.remove_roles(role)
            await user.send(f"✅ Roll eemaldatud: **{role.name}**")
        except discord.Forbidden:
            await user.send("❌ Ma ei saa sul rolli eemaldada - kontrolli õigusi!")
        except Exception as e:
            await user.send(f"❌ Viga rolli eemaldamisel: {e}")

    # Load channels on startup
    load_channels()
