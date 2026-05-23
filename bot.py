import os
import sys
import subprocess
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# မိမိ Bot Token ကို ဤနေရာတွင် ထည့်ပါ
BOT_TOKEN = "8552466342:AAEGNebOKjuXgE62oqY_4cfkLSlna8kx8Hw"

def update_ytdlp():
    try:
        logger.info("Updating yt-dlp to latest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except Exception as e:
        logger.error(f"Update failed: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 YouTube Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သင်ဒေါင်းလုဒ်ဆွဲချင်တဲ့ YouTube Video Link ကို ပို့ပေးပါ။ 4K အထိ စိတ်ကြိုက်ရွေးချယ်နိုင်ပါပြီ။ ✨"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ကို ပို့ပေးပါခင်ဗျာ။ ❌")
        return

    checking_msg = await update.message.reply_text("ဗီဒီယိုကို လုံခြုံစိတ်ချရသော Cloud Pipeline ဖြင့် စစ်ဆေးနေပါတယ်... ⏳")

    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("Extract failed")
            video_title = info.get('title', 'YouTube Video')
            # Short URL သို့မဟုတ် ပုံမှန် URL ကို အခြေခံအကျဆုံး ပုံစံထုတ်ယူခြင်း
            video_id = info.get('id')
            
        # Error မတက်စေရန် ခလုတ်ထဲတွင် Video ID ကို တိုက်ရိုက်ထည့်သွင်းခြင်း
        keyboard = [
            [
                InlineKeyboardButton("📁 360p", callback_data=f"360p|{video_id}"),
                InlineKeyboardButton("📁 720p (HD)", callback_data=f"720p|{video_id}")
            ],
            [
                InlineKeyboardButton("📁 1080p (FHD)", callback_data=f"1080p|{video_id}"),
                InlineKeyboardButton("🔥 4K (UltraHD)", callback_data=f"2160p|{video_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await checking_msg.delete()
        await update.message.reply_text(
            f"🎬 **ခေါင်းစဉ်:** {video_title}\n\n"
            f"ဒေါင်းလုဒ်လုပ်လိုသော Quality ကို ရွေးချယ်ပေးပါ 👇",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(str(e))
        # ဒုတိယအရန်စနစ် - တိုက်ရိုက်အကောင်းဆုံး Quality ဖြင့် ဒေါင်းရန် ခလုတ်ပြခြင်း
        keyboard = [[InlineKeyboardButton("📁 တိုက်ရိုက်ဒေါင်းလုဒ်ဆွဲမည်", callback_data=f"best|{url}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await checking_msg.edit_text(
            "⚠️ Resolution စစ်ဆေးရန် အခက်အခဲရှိနေပါသည်။ အောက်ပါခလုတ်ကို သုံးပြီး တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲနိုင်ပါသည်။",
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("|")
    res_choice = data_parts[0]
    target = data_parts[1]

    # ID ဖြစ်ခဲ့လျှင် YouTube Link အဖြစ် ပြန်ပြောင်းခြင်း
    if len(target) == 11:  
        url = f"https://www.youtube.com/watch?v={target}"
    else:
        url = target

    await query.edit_message_text("Cloud Server ပေါ်တွင် ဗီဒီယိုအား စတင်စီစဉ်နေပါပြီ... 📥")

    # Resolution format သတ်မှတ်ချက်
    if res_choice == "360p":
        ydl_format = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif res_choice == "720p":
        ydl_format = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif res_choice == "1080p":
        ydl_format = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif res_choice == "2160p":
        ydl_format = "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
    else:
        ydl_format = "bestvideo+bestaudio/best"

    ydl_opts = {
        'format': ydl_format,
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'restrictfilenames': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
                
            video_title = info.get('title', 'Video')

        await query.edit_message_text("ဒေါင်းလုဒ်ပြီးပါပြီ။ သင်၏ Telegram ဆီသို့ ပေးပို့နေပါပြီ... 📤")
        
        filesize_mb = os.path.getsize(filename) / (1024 * 1024)

        with open(filename, 'rb') as video_file:
            # 50MB အောက်ဆိုလျှင် ပုံမှန် ဗီဒီယိုအတိုင်း ပို့မည်
            if filesize_mb < 49.0:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=f"🎬 {video_title}\n✨ Quality: {res_choice}"
                )
            # Size ကြီးမားပါက Document အဖြစ် ပို့ပေးမည် (2GB အထိ Error လုံးဝ မတက်စေရပါ)
            else:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=video_file,
                    caption=f"🎬 {video_title} ({int(filesize_mb)}MB - ဖိုင်ဆိုဒ်ကြီးသဖြင့် Document အနေဖြင့် ပို့ပေးထားပါသည်)\n✨ Quality: {res_choice}"
                )

        if os.path.exists(filename):
            os.remove(filename)
        await query.message.delete()

    except Exception as e:
        logger.error(str(e))
        await query.edit_message_text("စိတ်မကောင်းပါဘူးခင်ဗျာ။ ဗီဒီယိုအား ဒေါင်းလုဒ်ဆွဲရန် ဆာဗာတွင် အခက်အခဲရှိနေပါသည်။ နောက်ထပ် လင့်ခ်တစ်ခုဖြင့် ပြန်စမ်းကြည့်ပေးပါ။ ❌")

def main():
    update_ytdlp()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Perfect system is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
