import os
import asyncio
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
import yt_dlp

# --- Render Keeping Alive Server ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# --- Self Ping Loop to Prevent Render Sleep ---
async def keep_alive():
    await asyncio.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        if render_url:
            try:
                requests.get(render_url, timeout=10)
            except Exception:
                pass
        await asyncio.sleep(600)  # Ping every 10 mins

# --- Credentials ---
API_ID = 35535500
API_HASH = "4fcafabe7785625b2f1a3c6bfb09c2a5"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("नमस्ते! 👋\nमुझे Instagram, Facebook, X (Twitter), Reddit आदि का लिंक भेजें, मैं वीडियो डाउनलोड करके भेज दूंगा!")

@bot.on(events.NewMessage)
async def download_video(event):
    if event.text.startswith('/'):
        return

    url = event.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await event.respond("कृपया एक सही वीडियो लिंक भेजें।")
        return

    if "youtube.com" in url or "youtu.be" in url:
        await event.respond("⚠️ YouTube के सर्वर ब्लॉकिंग के कारण YouTube सपोर्टेड नहीं है। कृपया Instagram, Facebook, X (Twitter) आदि का लिंक भेजें।")
        return

    status_msg = await event.respond("⏳ वीडियो डाउनलोड हो रहा है, कृपया इंतज़ार करें...")
    output_file = f"video_{event.message.id}.mp4"

    ydl_opts = {
        'format': 'best[filesize<2000M]/best',
        'outtmpl': output_file,
        'quiet': True,
        'nocheckcertificate': True
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            await status_msg.edit("📤 Telegram पर अपलोड हो रहा है...")
            await bot.send_file(
                event.chat_id,
                file=output_file,
                caption="यह रहा आपका वीडियो! 🎬"
            )
            await status_msg.delete()
        else:
            await status_msg.edit("❌ यह वीडियो डाउनलोड नहीं हो सका। कृपया लिंक दोबारा जांचें।")

    except Exception as e:
        await status_msg.edit(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

print("Telegram Multi-Platform Downloader Bot Active...")

# Background task for keepalive
loop = asyncio.get_event_loop()
loop.create_task(keep_alive())

bot.run_until_disconnected()
