import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Store the info channel ID
info_channel_id = None

@bot.event
async def on_ready():
    global info_channel_id
    print(f"✅ Logged in as {bot.user}")
    
    # Load saved info channel ID
    try:
        with open('info_channel.txt', 'r') as f:
            info_channel_id = int(f.read().strip())
        print(f"📢 Info channel loaded: {info_channel_id}")
    except FileNotFoundError:
        print("📢 No info channel set yet")
    except Exception as e:
        print(f"⚠️ Error loading info channel: {e}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm alive inside Docker 🐳")

@bot.command()
async def info(ctx, *, message=None):
    """Send important information to the info channel with @everyone ping"""
    global info_channel_id
    
    # Check if info channel is set
    if info_channel_id is None:
        await ctx.send("❌ Info channel not set! Use `!info-set` to set the channel first.")
        return
    
    # Get the info channel
    info_channel = bot.get_channel(info_channel_id)
    if info_channel is None:
        await ctx.send("❌ Info channel not found! Use `!info-set` to set a valid channel.")
        return
    
    # Check if user has permission to send messages in the info channel
    if not info_channel.permissions_for(ctx.author).send_messages:
        await ctx.send("❌ You don't have permission to send messages in the info channel.")
        return
    
    # If no message provided, ask for one
    if not message:
        await ctx.send("❌ Please provide a message! Usage: `!info Your message here`")
        return
    
    # Send the message with @everyone ping to the info channel
    await info_channel.send("@everyone")
    
    # Create embed with sender info
    embed = discord.Embed(
        description=message,
        color=0x00ff00
    )
    embed.set_author(
        name=f"From: {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )
    embed.set_footer(text="ITA25 Bot")
    
    await info_channel.send(embed=embed)
    
    # Confirm to the user
    await ctx.send(f"✅ Info sent to {info_channel.mention}")

@bot.command()
async def info_set(ctx, channel: discord.TextChannel = None):
    """Set the channel where info messages will be sent"""
    global info_channel_id
    
    if channel is None:
        # If no channel mentioned, use current channel
        channel = ctx.channel
    
    # Check if user has permission to manage channels
    if not ctx.author.guild_permissions.manage_channels:
        await ctx.send("❌ You need 'Manage Channels' permission to set the info channel.")
        return
    
    # Set the info channel
    info_channel_id = channel.id
    await ctx.send(f"✅ Info channel set to {channel.mention}")
    
    # Save to file for persistence
    with open('info_channel.txt', 'w') as f:
        f.write(str(channel.id))


bot.run(TOKEN)