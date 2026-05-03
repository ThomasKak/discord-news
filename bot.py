import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
import json

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

RSS_URL = "https://eupoliteuesthai.com/feed/"
CHANNEL_NAME = "ανακοινώσεις"
SENT_FILE = "sent_links.json"  # Αρχείο για μόνιμη αποθήκευση

# Φόρτωσε τα links που έχουν ήδη σταλεί
def load_sent_links():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

# Αποθήκευσε τα links
def save_sent_links(links):
    with open(SENT_FILE, "w") as f:
        json.dump(list(links), f)

sent_links = load_sent_links()

@bot.event
async def on_ready():
    print(f'✅ Το bot {bot.user} είναι online!')
    print(f'🔍 Παρακολουθώ το RSS feed: {RSS_URL}')
    print(f'📌 Θυμάμαι {len(sent_links)} άρθρα που έχουν ήδη σταλεί')
    check_rss.start()

@tasks.loop(minutes=5)
async def check_rss():
    global sent_links
    
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
    new_links = []
    for entry in reversed(feed.entries):
        if entry.link not in sent_links:
            sent_links.add(entry.link)
            new_links.append(entry.link)
            message = f"📢 **Νέο άρθρο!**\n**{entry.title}**\n{entry.link}"
            await channel.send(message)
            print(f"✅ Στάλθηκε: {entry.title}")
            await asyncio.sleep(1)
    
    # Αποθήκευσε τα links (για να τα θυμάται μετά από restart)
    if new_links:
        save_sent_links(sent_links)
        print(f"💾 Αποθηκεύτηκαν {len(new_links)} νέα links")

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
