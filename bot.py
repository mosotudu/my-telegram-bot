import os
import asyncio
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events

# --- Render 24/7 Server Active Keeper ---
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

# ⚠️ यहाँ अपना टेलीग्राम बोट टोकन डालें
BOT_TOKEN = "8833066297:AAGcPCEdxfjwGVpfpC09kemN3pltTtFcfxM"

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("नमस्ते! 👋\nमुझे यूट्यूब (Shorts/Videos) का लिंक भेजें, मैं डाउनलोड करके भेज दूंगा!")

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

    try:
        # YouTube Bot-Block Bypass via Direct Service API
        api_url = f"https://api.cohttps.workers.dev/?url={url}"
        
        # API से वीडियो डेटा डाउनलोड करना
        response = requests.get(api_url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(output_file) and os.path.getsize(output_file) > 10000:
                await status_msg.edit("📤 Telegram पर अपलोड हो रहा है...")
                await bot.send_file(
                    event.chat_id,
                    file=output_file,
                    caption="यह रहा आपका वीडियो! 🎬"
                )
                await status_msg.delete()
                return

        await status_msg.edit("❌ वीडियो डाउनलोड नहीं हो पाया। YouTube ने सर्वर IP ब्लॉक किया है।")

    except Exception as e:
        await status_msg.edit(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

print("Telegram Bot Active...")
bot.run_until_disconnected()
