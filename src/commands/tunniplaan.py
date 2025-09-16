import discord
import asyncio
import concurrent.futures
from src.scraper.voco_scraper import scrape_timetable

def setup_tunniplaan_commands(bot):
    """Setup timetable-related commands"""
    
    @bot.command()
    async def tunniplaan(ctx, period="daily"):
        """Get timetable from VOCO website
        
        Usage:
        !tunniplaan - Get today's lessons
        !tunniplaan daily - Get today's lessons  
        !tunniplaan weekly - Get this week's lessons
        """
        try:
            await ctx.send("🔍 Fetching timetable from VOCO...")
            
            # Run the scraper in a thread to avoid blocking the event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Add a 60-second timeout to prevent hanging
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(executor, scrape_timetable, period),
                    timeout=60.0
                )
            
            if not result['success']:
                await ctx.send(f"❌ Error: {result['error']}")
                return
            
            # Create embed based on period
            if period == "weekly":
                title = f"📚 Weekly Timetable - {result.get('week_range', 'This Week')}"
            else:
                title = f"📅 Today's Lessons - {result.get('date', 'Today')}"
            
            embed = discord.Embed(
                title=title,
                color=0x00ff00,
                description=f"Source: {result.get('source', 'VOCO.ee')}"
            )
            
            # Add lessons for each day
            lessons = result.get('lessons', {})
            for day, day_lessons in lessons.items():
                if day_lessons:
                    # Create a clean table format
                    day_text = "```\n"
                    day_text += f"{'Time':<12} {'Subject':<25} {'Room':<8} {'Teacher':<15}\n"
                    day_text += f"{'-'*12} {'-'*25} {'-'*8} {'-'*15}\n"
                    
                    for lesson in day_lessons:
                        time = lesson.get('time', 'Unknown')[:11]
                        subject = lesson.get('subject', 'Unknown')[:24]
                        room = lesson.get('room', 'N/A')[:7]
                        teacher = lesson.get('teacher', 'N/A')[:14]
                        day_text += f"{time:<12} {subject:<25} {room:<8} {teacher:<15}\n"
                    
                    day_text += "```"
                    
                    embed.add_field(
                        name=f"📅 {day}",
                        value=day_text,
                        inline=False
                    )
            
            if not lessons or not any(lessons.values()):
                embed.add_field(
                    name="📝 No Lessons",
                    value="No lessons found for the selected period.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("⏰ Error: Scraper timed out after 60 seconds. The website might be slow or unresponsive.")
        except Exception as e:
            await ctx.send(f"❌ Error fetching timetable: {str(e)}")
