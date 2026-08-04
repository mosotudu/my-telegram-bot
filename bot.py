import os
import asyncio
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
import yt_dlp

# --- Dummy Web Server (Render 24/7 Keeping Alive) ---
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

# --- Telegram Credentials ---
API_ID = 35535500
API_HASH = "4fcafabe7785625b2f1a3c6bfb09c2a5"

# ⚠️ यहाँ अपना बोट टोकन भरें
BOT_TOKEN = "8833066297:AAGcPCEdxfjwGVpfpC09kemN3pltTtFcfxM"

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("नमस्ते! 👋\nमुझे वीडियो लिंक भेजें, मैं बड़ी फाइलें (2GB तक) भी आसानी से डाउनलोड करके भेज दूंगा!")

@bot.on(events.NewMessage)
async def download_video(event):
    if event.text.startswith('/'):
        return

    url = event.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await event.respond("कृपया एक सही वीडियो लिंक भेजें।")
        return

    status_msg = await event.respond("⏳ वीडियो डाउनलोड हो रहा है, कृपया इंतज़ार करें...")
    output_file = f"video_{event.message.id}.mp4"

    # Invidious Instance Bypass Configuration
    ydl_opts = {
        'format': 'best[filesize<2000M]/best',
        'outtmpl': output_file,
        'quiet': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'invidious_instance': ['inv.tux.stream', 'invidious.nerdvpn.de'],
                'player_client': ['android', 'ios'],
            }
        }
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if not os.path.exists(output_file):
            await status_msg.edit("❌ वीडियो डाउनलोड नहीं हो सका।")
            return

        await status_msg.edit("📤 बड़ी फाइल Telegram पर अपलोड हो रही है...")

        await bot.send_file(
            event.chat_id,
            file=output_file,
            caption="यह रहा आपका वीडियो! 🎬"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

print("Telethon 2GB बोट चालू हो रहा है...")
bot.run_until_disconnected()
