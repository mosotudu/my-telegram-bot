import os
import asyncio
from pyrogram import Client, filters
import yt_dlp

# आपकी Telegram API डिटेल्स
API_ID = 35535500
API_HASH = "4fcafabe7785625b2f1a3c6bfb09c2a5"

# ⚠️ यहाँ अपना BotFather वाला टोकन डालें
BOT_TOKEN = "8833066297:AAGcPCEdxfjwGVpfpC09kemN3pltTtFcfxM"

app = Client(
    "my_large_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("नमस्ते! 👋\nमुझे वीडियो लिंक भेजें, मैं बड़ी फाइलें (2GB तक) भी आसानी से डाउनलोड करके भेज दूंगा!")

@app.on_message(filters.text & ~filters.command(["start"]))
async def download_video(client, message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.reply_text("कृपया एक सही लिंक भेजें।")
        return

    status_msg = await message.reply_text("⏳ वीडियो डाउनलोड हो रहा है, कृपया इंतज़ार करें...")
    output_file = f"video_{message.id}.mp4"

    ydl_opts = {
        'format': 'best[filesize<2000M]/best',
        'outtmpl': output_file,
        'quiet': True,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if not os.path.exists(output_file):
            await status_msg.edit_text("❌ वीडियो डाउनलोड नहीं हो सका।")
            return

        await status_msg.edit_text("📤 बड़ी फाइल Telegram पर अपलोड हो रही है...")

        await client.send_video(
            chat_id=message.chat.id,
            video=output_file,
            caption="यह रहा आपका वीडियो! 🎬"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ एरर आ गया:\n{str(e)[:150]}")

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    print("2GB सपोर्ट वाला बोट चालू हो गया है...")
    app.run()
