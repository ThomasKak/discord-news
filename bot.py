import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

RSS_URL = "https://eupoliteuesthai.com/feed/"
CHANNEL_NAME = "ανακοινώσεις"
sent_links = set()

@bot.event
async def on_ready():
    print(f'✅ Το bot {bot.user} είναι online!')
    print(f'🔍 Παρακολουθώ το RSS feed: {RSS_URL}')
    check_rss.start()

@tasks.loop(minutes=5)
async def check_rss():
    # Βρες το κανάλι
    channel = None
    for guild in bot.guilds:
        for ch in guild.text_channels:
            if ch.name == CHANNEL_NAME:
                channel = ch
                break
    
    if channel is None:
        print(f"❌ Δεν βρέθηκε το κανάλι #{CHANNEL_NAME}")
        return
    
    # Διάβασε το RSS
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("⚠️ Δεν βρέθηκαν άρθρα στο feed")
        return
    
    # Δες τα νέα άρθρα (από το πιο παλιό προς το νεότερο)
    for entry in reversed(feed.entries):
        if entry.link not in sent_links:
            sent_links.add(entry.link)
            message = f"📢 **Νέο άρθρο!**\n**{entry.title}**\n{entry.link}"
            await channel.send(message)
            print(f"✅ Στάλθηκε: {entry.title}")
            await asyncio.sleep(1)

@bot.command()
async def ping(ctx):
    if ctx.channel.name == CHANNEL_NAME:
        await ctx.send("pong!")
    else:
        await ctx.send(f"Το bot λειτουργεί μόνο στο κανάλι #{CHANNEL_NAME}")

@bot.command()
async def test_rss(ctx):
    """Δοκιμαστική εντολή: ελέγχει RSS αμέσως"""
    if ctx.channel.name == CHANNEL_NAME:
        await ctx.send("🔍 Έλεγχος RSS feed...")
        await check_rss()
    else:
        await ctx.send(f"Η εντολή λειτουργεί μόνο στο κανάλι #{CHANNEL_NAME}")

bot.run(os.getenv('DISCORD_TOKEN'))