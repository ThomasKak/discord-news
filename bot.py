import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
import json
from flask import Flask
import threading

# -------- Flask (για να μην κοιμάται στο Render) --------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()
# -------------------------------------------------------


# -------- Discord Bot --------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

RSS_URL = "https://eupoliteuesthai.com/feed/"
CHANNEL_NAME = "ανακοινώσεις"
SENT_FILE = "sent_links.json"


# -------- Load / Save --------
def load_sent_links():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_links(links):
    with open(SENT_FILE, "w") as f:
        json.dump(list(links), f)

sent_links = load_sent_links()


# -------- Bot Ready --------
@bot.event
async def on_ready():
    print(f'✅ {bot.user} είναι online!')
    if not check_rss.is_running():
        check_rss.start()


# -------- RSS Check --------
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
        print("❌ Δεν βρέθηκε κανάλι")
        return

    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("⚠️ Δεν βρέθηκαν άρθρα")
        return

    # 👉 ΠΡΩΤΗ ΦΟΡΑ: μην στείλεις τίποτα
    if not sent_links:
        for entry in feed.entries:
            sent_links.add(entry.link)
        save_sent_links(sent_links)
        print("📌 First run - αποθήκευση χωρίς αποστολή")
        return

    new_found = False

    for entry in reversed(feed.entries):
        if entry.link not in sent_links:
            sent_links.add(entry.link)
            new_found = True

            msg = f"📢 **Νέο άρθρο!**\n**{entry.title}**\n{entry.link}"
            await channel.send(msg)
            print(f"✅ Στάλθηκε: {entry.title}")
            await asyncio.sleep(1)

    if new_found:
        save_sent_links(sent_links)


# -------- Commands --------
@bot.command()
async def ping(ctx):
    await ctx.send("pong!")


@bot.command()
async def test_rss(ctx):
    await ctx.send("🔍 Test RSS...")
    await check_rss()


# -------- Run --------
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
