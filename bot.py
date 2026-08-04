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

# ⚠️ अपना Bot Token यहाँ रखें
BOT_TOKEN = "8833066297:AAGcPCEdxfjwGVpfpC09kemN3pltTtFcfxM"

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def get_youtube_stream_url(youtube_url):
    """Piped / Invidious instances के ज़रिए YouTube ब्लॉक बाईपास"""
    try:
        # YouTube ID निकालना
        video_id = None
        if "shorts/" in youtube_url:
            video_id = youtube_url.split("shorts/")[1].split("?")[0]
        elif "v=" in youtube_url:
            video_id = youtube_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_url:
            video_id = youtube_url.split("youtu.be/")[1].split("?")[0]

        if not video_id:
            return None

        # Piped API से वीडियो स्ट्रीम URL प्राप्त करना
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://api.piped.privacydev.net",
            "https://pipedapi.palvelu.org"
        ]

        for instance in piped_instances:
            try:
                res = requests.get(f"{instance}/streams/{video_id}", timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    video_streams = data.get("videoStreams", [])
                    # सर्वोत्तम ऑडियो-वीडियो कंबाइंड स्ट्रीम चुनना
                    for stream in video_streams:
                        if stream.get("videoOnly") is False:
                            return stream.get("url")
                    if video_streams:
                        return video_streams[0].get("url")
            except Exception:
                continue
    except Exception as e:
        print("Bypass Stream Error:", e)
    return None

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

    try:
        # 1. YouTube लिंक्स के लिए Piped API बायपास
        if "youtube.com" in url or "youtu.be" in url:
            stream_url = get_youtube_stream_url(url)
            if stream_url:
                r = requests.get(stream_url, stream=True, timeout=30)
                with open(output_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)

        # 2. इंस्टाग्राम या अन्य प्लेटफॉर्म्स के लिए yt-dlp Fallback
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            ydl_opts = {
                'format': 'best[filesize<2000M]/best',
                'outtmpl': output_file,
                'quiet': True,
                'nocheckcertificate': True
            }
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        # 3. फाइल अपलोडिंग
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            await status_msg.edit("📤 Telegram पर अपलोड हो रहा है...")
            await bot.send_file(
                event.chat_id,
                file=output_file,
                caption="यह रहा आपका वीडियो! 🎬"
            )
            await status_msg.delete()
        else:
            await status_msg.edit("❌ वीडियो डाउनलोड करने में असमर्थ। कृपया दोबारा प्रयास करें।")

    except Exception as e:
        await status_msg.edit(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

print("Telethon 2GB Stream-Bypass बोट चालू हो रहा है...")
bot.run_until_disconnected()
