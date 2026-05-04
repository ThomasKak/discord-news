import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
import json
from flask import Flask
import threading

# ---------------- FLASK (για uptime) ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Ξεκινάει σε background thread
threading.Thread(target=run_flask, daemon=True).start()
# ---------------------------------------------------


# ---------------- DISCORD BOT ----------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

RSS_URL = "https://eupoliteuesthai.com/feed/"
CHANNEL_NAME = "ανακοινώσεις"
SENT_FILE = "sent_links.json"


# ---------------- FILE HANDLING ----------------
def load_sent_links():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_sent_links(links):
    with open(SENT_FILE, "w") as f:
        json.dump(list(links), f)

sent_links = load_sent_links()


# ---------------- BOT READY ----------------
@bot.event
async def on_ready():
    print(f'✅ {bot.user} online!')
    if not check_rss.is_running():
        check_rss.start()


# ---------------- RSS LOOP ----------------
@tasks.loop(minutes=5)
async def check_rss():
    global sent_links

    print("🔍 Checking RSS...")

    channel = None
    for guild in bot.guilds:
        for ch in guild.text_channels:
            if ch.name == CHANNEL_NAME:
                channel = ch
                break

    if channel is None:
        print("❌ Channel not found")
        return

    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("⚠️ No entries found")
        return

    # 👉 FIRST RUN: save χωρίς send
    if not sent_links:
        for entry in feed.entries:
            sent_links.add(entry.link)
        save_sent_links(sent_links)
        print("📌 First run - stored only")
        return

    new_posts = False

    for entry in reversed(feed.entries):
        if entry.link not in sent_links:
            sent_links.add(entry.link)
            new_posts = True

            message = f"📢 **Νέο άρθρο!**\n**{entry.title}**\n{entry.link}"
            await channel.send(message)
            print(f"✅ Sent: {entry.title}")

            await asyncio.sleep(1)

    if new_posts:
        save_sent_links(sent_links)
        print("💾 Saved new links")


# ---------------- COMMANDS ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

@bot.command()
async def test_rss(ctx):
    await ctx.send("🔍 Testing RSS...")
    await check_rss()


# ---------------- RUN ----------------
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("❌ Missing DISCORD_TOKEN")
    else:
        bot.run(TOKEN)
