import os
import asyncio
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
import yt_dlp

# --- Render Keeping Alive Web Server ---
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
    await event.respond("नमस्ते! 👋\nमुझे इंस्टाग्राम, यूट्यूब या कोई भी वीडियो लिंक भेजें, मैं डाउनलोड करके भेज दूंगा!")

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

    # 1️⃣ सबसे पहले Cobalt API से यूट्यूब डाउनलोड करने की कोशिश (No IP Block Error)
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {"url": url, "videoQuality": "max"}
        
        response = requests.post("https://api.cobalt.tools/api/json", json=data, headers=headers, timeout=15)
        res_data = response.json()

        if response.status_code == 200 and "url" in res_data:
            direct_link = res_data["url"]
            video_bytes = requests.get(direct_link, stream=True)
            with open(output_file, 'wb') as f:
                for chunk in video_bytes.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print("Cobalt Fallback Error:", e)

    # 2️⃣ अगर Cobalt काम न करे, तो yt-dlp यूज़ होगा (Instagram/X/Other sites के लिए)
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        ydl_opts = {
            'format': 'best[filesize<2000M]/best',
            'outtmpl': output_file,
            'quiet': True,
            'nocheckcertificate': True
        }
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        except Exception as e:
            pass

    # 3️⃣ अपलोडिंग
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        await status_msg.edit("📤 Telegram पर अपलोड हो रहा है...")
        await bot.send_file(
            event.chat_id,
            file=output_file,
            caption="यह रहा आपका वीडियो! 🎬"
        )
        await status_msg.delete()
        os.remove(output_file)
    else:
        await status_msg.edit("❌ वीडियो डाउनलोड करने में असमर्थ। कृपया दूसरा लिंक ट्राई करें।")

print("Telethon 2GB Cobalt-Supported बोट चालू हो रहा है...")
bot.run_until_disconnected()
