import os
import asyncio
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events

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

# --- Credentials ---
API_ID = 35535500
API_HASH = "4fcafabe7785625b2f1a3c6bfb09c2a5"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("नमस्ते! 👋\nमुझे कोई भी वीडियो लिंक भेजें, मैं डाउनलोड करके भेज दूंगा!")

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
        # YouTube Fast API Download Endpoint
        download_api = f"https://api.v2.savefrom.net/api/convert?url={url}"
        
        # 3rd Party API request to bypass YouTube IP Block
        api_res = requests.get(f"https://co.wuk.sh/api/json", json={"url": url}, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
        
        video_download_url = None
        if api_res.status_code == 200 and "url" in api_res.json():
            video_download_url = api_res.json()["url"]

        if video_download_url:
            r = requests.get(video_download_url, stream=True, timeout=120)
            with open(output_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                await status_msg.edit("📤 Telegram पर अपलोड हो रहा है...")
                await bot.send_file(
                    event.chat_id,
                    file=output_file,
                    caption="यह रहा आपका वीडियो! 🎬"
                )
                await status_msg.delete()
                return

        await status_msg.edit("❌ सर्वर ब्लॉक के कारण यह वीडियो डाउनलोड नहीं हो सका।")

    except Exception as e:
        await status_msg.edit(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

print("Telegram Bot Active...")
bot.run_until_disconnected()
