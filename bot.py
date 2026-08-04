import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# ⚠️ यहाँ अपना Telegram Bot Token डालें
BOT_TOKEN = "8833066297:AAGcPCEdxfjwGVpfpC09kemN3pltTtFcfxM"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "नमस्ते! 👋\nमुझे YouTube, Instagram, Facebook या Twitter का वीडियो लिंक भेजें, मैं उसे डाउनलोड कर दूंगा।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("कृपया एक सही वीडियो लिंक (URL) भेजें।")
        return

    status_msg = await update.message.reply_text("⏳ वीडियो डाउनलोड हो रहा है, कृपया इंतज़ार करें...")
    output_filename = f"video_{update.message.message_id}.mp4"

    # 50MB से छोटी फाइल और सही फॉर्मेट के लिए सेटिंग
    ydl_opts = {
        'format': 'best[filesize<50M]/best[height<=720]/best',
        'outtmpl': output_filename,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await status_msg.edit_text("📤 Telegram पर अपलोड हो रहा है...")

        with open(output_filename, 'rb') as video_file:
            # read_timeout और write_timeout बढ़ाने से Timed Out की दिक्कत ख़त्म हो जाएगी
            await update.message.reply_video(
                video=video_file, 
                caption="यह रहा आपका वीडियो! 🎬",
                read_timeout=300,
                write_timeout=300
            )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ डाउनलोड नहीं हो सका।\nकारण: {str(e)[:100]}")

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    # यहाँ भी Timeouts बढ़ा दिए गए हैं
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(300)
        .write_timeout(300)
        .connect_timeout(300)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("बोट चालू हो गया है...")
    app.run_polling()