import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
import json
from flask import Flask
import threading

# ------ Flask για το Render (τρέχει σε ξεχωριστό thread) ------
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
# ---------------------------------------------------------------

# ------ Discord Bot ------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

RSS_URL = "https://eupoliteuesthai.com/feed/"
CHANNEL_NAME = "ανακοινώσεις"
SENT_FILE = "sent_links.json"

def load_sent_links():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_links(links):
    with open(SENT_FILE, "w") as f:
        json.dump(list(links), f)

sent_links = load_sent_links()

@bot.event
async def on_ready():
    print(f'✅ Το bot {bot.user} είναι online!')
    print(f'🔍 Παρακολουθώ RSS: {RSS_URL}')
    print(f'📌 Θυμάμαι {len(sent_links)} άρθρα')
    check_rss.start()

@tasks.loop(minutes=5)
async def check_rss():
    global sent_links
    channel = None
    for guild in bot.guilds:
        for ch in guild.text_channels:
            if ch.name == CHANNEL_NAME:
                channel = ch
                break
    if channel is None:
        print(f"❌ Δεν βρέθηκε το κανάλι #{CHANNEL_NAME}")
        return
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("⚠️ Δεν βρέθηκαν άρθρα")
        return
    new_links = []
    for entry in reversed(feed.entries):
        if entry.link not in sent_links:
            sent_links.add(entry.link)
            new_links.append(entry.link)
            message = f"📢 **Νέο άρθρο!**\n**{entry.title}**\n{entry.link}"
            await channel.send(message)
            print(f"✅ Στάλθηκε: {entry.title}")
            await asyncio.sleep(1)
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
    if ctx.channel.name == CHANNEL_NAME:
        await ctx.send("🔍 Έλεγχος RSS...")
        await check_rss()
    else:
        await ctx.send(f"Η εντολή λειτουργεί μόνο στο κανάλι #{CHANNEL_NAME}")

bot.run(os.getenv('DISCORD_TOKEN'))
