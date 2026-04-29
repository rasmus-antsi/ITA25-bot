import discord
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from .scraper import VOCOScraper
from .database import db

# Load environment variables
load_dotenv()

async def init_database():
    """Initialize the database and migrate from JSON if needed"""
    try:
        # Initialize database
        await db.init_db()
        
        # Migrate from JSON if it exists
        data_dir = os.getenv('DATA_DIR', '.')
        json_file_path = os.path.join(data_dir, 'channels.json')
        await db.migrate_from_json(json_file_path)
        
        print(f"📢 Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Error initializing database: {e}")

def setup_info_commands(bot):
    """Setup info-related commands"""
    
    # Blacklisted user IDs from environment variable (comma-separated)
    blacklist_env = os.getenv("BLACKLISTED_USER_IDS", "")
    BLACKLISTED_USER_IDS = [
        user_id.strip() 
        for user_id in blacklist_env.split(",") 
        if user_id.strip()
    ]
    
    def is_blacklisted(user_id: str) -> bool:
        """Check if a user is blacklisted"""
        return user_id in BLACKLISTED_USER_IDS
    
    # Remove the built-in help command
    bot.remove_command('help')
    
    @bot.command(name='hello')
    async def hello(ctx):
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        await ctx.send("Tere! Olen elus Dockeris 🐳")

    @bot.command(name='help')
    async def help_command(ctx):
        """Näita kõiki saadaolevaid käske"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
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
                "`!tunniplaan-set [#kanal]` - (Admin) Määra automaatne tunniplaan kanal\n"
                "`!tunniplaan-remove` - (Admin) Eemalda tunniplaan kanal"
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
                "`!vota-rollid @roll1 🎭1 @roll2 🎭2 True` - Loo rollide valimise sõnum\n"
                "Lisa `True` või `true` kui kasutajad saavad valida ainult ühe rolli\n"
                "Kliki sama reaktsiooni uuesti, et rolli eemaldada"
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
                "`!vota-rollid @Student 🎓 @Mentor 👨‍🏫 True` - Loo rollide valimine"
            ),
            inline=False
        )
        
        embed.set_footer(text="ITA25 Bot - Automaatne tunniplaan ja info süsteem")
        
        await ctx.send(embed=embed)

    @bot.command(name='tunniplaan')
    async def tunniplaan(ctx, *, date_param=None):
        """Näita tunde ITA25-le. Kasutamine: !tunniplaan, !tunniplaan homme, !tunniplaan 15.01.2025"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
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
                            lesson_info += "\n"
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
                    value=lesson_info + "\n\u200b",
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
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        # Get info channel from database
        info_channels, _ = await db.get_channels()
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
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        if channel is None:
            # If no channel mentioned, use current channel
            channel = ctx.channel
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust info kanali määramiseks.")
            return
        
        # Get current channels and update info channel
        info_channels, tunniplaan_channels = await db.get_channels()
        guild_id = str(ctx.guild.id)
        info_channels[guild_id] = channel.id
        
        # Save to database
        await db.save_channels(info_channels, tunniplaan_channels)
        await ctx.send(f"✅ Info kanal määratud {channel.mention}")

    @bot.command(name='info-remove')
    async def info_remove(ctx):
        """Eemalda info kanal"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust info kanali eemaldamiseks.")
            return
        
        # Get current channels
        info_channels, tunniplaan_channels = await db.get_channels()
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
        
        # Save updated channels to database
        await db.save_channels(info_channels, tunniplaan_channels)
        
        await ctx.send(f"✅ Info kanal eemaldatud: {channel_mention}")

    @bot.command(name='tunniplaan-set')
    async def tunniplaan_set(ctx, channel: discord.TextChannel = None):
        """Määra kanal, kuhu saadetakse automaatsed tunniplaan sõnumid"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        if channel is None:
            # If no channel mentioned, use current channel
            channel = ctx.channel
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust tunniplaan kanali määramiseks.")
            return
        
        # Get current channels and update tunniplaan channel
        info_channels, tunniplaan_channels = await db.get_channels()
        guild_id = str(ctx.guild.id)
        tunniplaan_channels[guild_id] = channel.id
        
        # Save to database
        await db.save_channels(info_channels, tunniplaan_channels)
        await ctx.send(f"✅ Tunniplaan kanal määratud {channel.mention}")
        await ctx.send("📅 Automaatsed tunniplaan sõnumid saadetakse igal tööpäeval kell 06:00")

    @bot.command(name='tunniplaan-remove')
    async def tunniplaan_remove(ctx):
        """Eemalda tunniplaan kanal"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        # Check if user has permission to manage channels
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ Sul on vaja 'Kanalite haldamine' õigust tunniplaan kanali eemaldamiseks.")
            return
        
        # Get current channels
        info_channels, tunniplaan_channels = await db.get_channels()
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
        
        # Save updated channels to database
        await db.save_channels(info_channels, tunniplaan_channels)
        
        await ctx.send(f"✅ Tunniplaan kanal eemaldatud: {channel_mention}")

    @bot.command(name='vota-rollid')
    async def vota_rollid(ctx, *, args):
        """Loo rollide valimise sõnum. Kasutamine: !vota-rollid @roll1 🎭1 @roll2 🎭2 True"""
        # Check blacklist
        if is_blacklisted(str(ctx.author.id)):
            return
        
        # Check if user has permission to manage roles
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("❌ Sul on vaja 'Rollide haldamine' õigust rollide valimise sõnumi loomiseks.")
            return
        
        # Parse arguments
        parts = args.split()
        if len(parts) < 2:
            await ctx.send("❌ Vale kasutamine! Kasutamine: `!vota-rollid @roll1 🎭1 @roll2 🎭2 True`")
            return
        
        # Check if "True" or "true" is specified for single selection
        only_one = "True" in parts or "true" in parts
        if only_one:
            parts = [p for p in parts if p not in ["True", "true"]]
        
        # Parse role-emoji pairs
        roles_data = []
        i = 0
        while i < len(parts):
            if parts[i].startswith('<@&') and parts[i].endswith('>'):
                # Role mention found
                role_id = int(parts[i][3:-1])
                role = ctx.guild.get_role(role_id)
                if not role:
                    await ctx.send(f"❌ Rolli ID {role_id} ei leitud!")
                    return
                
                # Check if bot can manage this role
                if role.position >= ctx.guild.me.top_role.position:
                    await ctx.send(f"❌ Ma ei saa hallata rolli {role.name} - see on minu rollist kõrgemal!")
                    return
                
                # Get emoji
                if i + 1 < len(parts):
                    emoji = parts[i + 1]
                    roles_data.append((role, emoji))
                    i += 2
                else:
                    await ctx.send(f"❌ Emoji puudub rolli {role.name} jaoks!")
                    return
            else:
                await ctx.send(f"❌ Vale formaat: {parts[i]} - kasuta @roll formaati!")
                return
        
        if not roles_data:
            await ctx.send("❌ Pole ühtegi kehtivat rolli-emoji paari!")
            return
        
        # Create embed
        embed = discord.Embed(
            title="🎭 Vali oma rollid",
            description="Kliki reaktsioonile, et rolli saada või eemaldada:",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        if only_one:
            embed.add_field(
                name="ℹ️ Märkus",
                value="Saad valida ainult ühe rolli!",
                inline=False
            )
        
        for role, emoji in roles_data:
            embed.add_field(
                name=f"{emoji} {role.name}",
                value=f"Kliki reaktsioonile, et rolli saada",
                inline=False
            )
        
        embed.set_footer(text="Kasuta !vota-rollid uue sõnumi loomiseks")
        
        message = await ctx.send(embed=embed)
        
        # Add reactions for each role
        for role, emoji in roles_data:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass
        
        # Store role data for this message in database
        guild_id = str(ctx.guild.id)
        roles_dict = {emoji: {'role_id': role.id, 'role_name': role.name} for role, emoji in roles_data}
        
        await db.save_role_message(
            str(message.id),
            guild_id,
            ctx.channel.id,
            only_one,
            roles_dict
        )

    @bot.event
    async def on_reaction_add(reaction, user):
        """Handle role assignment when user reacts"""
        if user.bot:
            return
        
        # Check if this is a role selection message
        if not reaction.message.embeds:
            return
        
        embed = reaction.message.embeds[0]
        if embed.title != "🎭 Vali oma rollid":
            return
        
        # Get role message data from database
        message_data = await db.get_role_message(str(reaction.message.id))
        if not message_data:
            return
        emoji_str = str(reaction.emoji)
        
        if emoji_str not in message_data['roles']:
            return
        
        role_id = message_data['roles'][emoji_str]
        role = reaction.message.guild.get_role(role_id)
        
        if not role:
            return
        
        try:
            # Check if user already has this role (toggle behavior)
            if role in user.roles:
                # User already has the role, remove it
                await user.remove_roles(role)
                print(f"✅ Toggled off role {role.name} for {user.name}")
                return
            
            # If only one role allowed, remove other roles first
            if message_data['only_one']:
                # Remove all other roles from this message first
                for other_emoji, other_role_id in message_data['roles'].items():
                    if other_emoji != emoji_str:
                        other_role = reaction.message.guild.get_role(other_role_id)
                        if other_role and other_role in user.roles:
                            await user.remove_roles(other_role)
                            # Remove the reaction for the other role
                            try:
                                await reaction.message.remove_reaction(other_emoji, user)
                            except:
                                pass
            
            # Add the role to the user
            await user.add_roles(role)
            print(f"✅ Added role {role.name} to {user.name}")
        except discord.Forbidden:
            print(f"❌ Forbidden: Cannot manage role {role.name}")
        except Exception as e:
            print(f"❌ Error managing role: {e}")

    @bot.event
    async def on_reaction_remove(reaction, user):
        """Handle role removal when user removes reaction"""
        if user.bot:
            return
        
        print(f"🔍 Reaction removed: {reaction.emoji} by {user.name}")
        
        # Check if this is a role selection message
        if not reaction.message.embeds:
            print("❌ No embeds in message")
            return
        
        embed = reaction.message.embeds[0]
        if embed.title != "🎭 Vali oma rollid":
            print(f"❌ Wrong embed title: {embed.title}")
            return
        
        # Get role message data from database
        message_data = await db.get_role_message(str(reaction.message.id))
        if not message_data:
            print(f"❌ Message not found in database: {reaction.message.id}")
            return
        emoji_str = str(reaction.emoji)
        
        if emoji_str not in message_data['roles']:
            print(f"❌ Emoji not found in roles: {emoji_str}")
            return
        
        role_id = message_data['roles'][emoji_str]
        role = reaction.message.guild.get_role(role_id)
        
        if not role:
            print(f"❌ Role not found: {role_id}")
            return
        
        print(f"✅ Removing role {role.name} from {user.name}")
        
        try:
            # Remove the role from the user
            await user.remove_roles(role)
            print(f"✅ Successfully removed role {role.name} from {user.name}")
        except discord.Forbidden:
            print(f"❌ Forbidden: Cannot remove role {role.name} from {user.name}")
        except Exception as e:
            print(f"❌ Error removing role: {e}")

    @bot.event
    async def on_raw_reaction_remove(payload):
        """Handle raw reaction removal - more reliable than on_reaction_remove"""
        if payload.user_id == bot.user.id:
            return
        
        print(f"🔍 Raw reaction removed: {payload.emoji} by user {payload.user_id}")
        
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print("❌ Raw: Guild not found")
            return
        
        user = guild.get_member(payload.user_id)
        if not user:
            # Try to fetch the user if not in cache
            try:
                user = await guild.fetch_member(payload.user_id)
                print(f"✅ Raw: Fetched user {user.name}")
            except:
                print("❌ Raw: User not found and cannot fetch")
                return
        
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not message or not message.embeds:
            print("❌ Raw: Message or embeds not found")
            return
        
        embed = message.embeds[0]
        if embed.title != "🎭 Vali oma rollid":
            print(f"❌ Raw: Wrong embed title: {embed.title}")
            return
        
        # Get role message data from database
        message_data = await db.get_role_message(str(payload.message_id))
        if not message_data:
            print(f"❌ Raw: Message not found in database: {payload.message_id}")
            return
        emoji_str = str(payload.emoji)
        
        print(f"🔍 Raw: Looking for emoji: {emoji_str}")
        print(f"🔍 Raw: Available emojis: {list(message_data['roles'].keys())}")
        
        if emoji_str not in message_data['roles']:
            print(f"❌ Raw: Emoji not found in roles: {emoji_str}")
            return
        
        role_id = message_data['roles'][emoji_str]
        role = guild.get_role(role_id)
        
        if not role:
            print(f"❌ Raw: Role not found: {role_id}")
            return
        
        print(f"✅ Raw: Removing role {role.name} from {user.name}")
        
        try:
            await user.remove_roles(role)
            print(f"✅ Raw: Successfully removed role {role.name} from {user.name}")
        except discord.Forbidden:
            print(f"❌ Raw: Forbidden: Cannot remove role {role.name} from {user.name}")
        except Exception as e:
            print(f"❌ Raw: Error removing role: {e}")

    # Load channels on startup will be called from main.py
