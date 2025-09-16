import discord
import os

# Store the info channel ID
info_channel_id = None

def load_info_channel():
    """Load saved info channel ID"""
    global info_channel_id
    try:
        with open('info_channel.txt', 'r') as f:
            info_channel_id = int(f.read().strip())
        print(f"📢 Info channel loaded: {info_channel_id}")
    except FileNotFoundError:
        print("📢 No info channel set yet")
    except Exception as e:
        print(f"⚠️ Error loading info channel: {e}")

def setup_info_commands(bot):
    """Setup info-related commands"""
    
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
        
        # If no message and no attachments, ask for one
        if not message and not ctx.message.attachments:
            await ctx.send("❌ Please provide a message or image! Usage: `!info Your message here` or attach an image")
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

    # Load info channel on startup
    load_info_channel()
