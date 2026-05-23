import os
import sys
import re
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

# YouTube Link ထဲမှ ဗီဒီယို ID ကို သန့်ရှင်းစွာ ထုတ်ယူသည့် စနစ် (IP Block သက်သာစေရန်)
def extract_video_id(url):
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S+\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 စွမ်းဆောင်ရည်မြင့် အမှားအယွင်းကင်းစင်သော YouTube Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သင်ဒေါင်းလုဒ်ဆွဲချင်တဲ့ YouTube Video Link ကို ပို့ပေးပါ။ 4K အထိ စိတ်ကြိုက်ရွေးချယ်နိုင်ပါပြီ။ ✨"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    video_id = extract_video_id(url)
    
    if not video_id:
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ကို ပို့ပေးပါခင်ဗျာ။ ❌")
        return

    checking_msg = await update.message.reply_text("ဗီဒီယိုကို လုံခြုံစိတ်ချရသော Cloud Pipeline ဖြင့် စစ်ဆေးနေပါတယ်... ⏳")

    # Cloud IP Block ကို ကျော်ဖြတ်ရန် အဆင့်မြင့် Options များ
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    try:
        # သန့်ရှင်းပြီးသား Standard Link ဖြင့် အချက်အလက် ရှာဖွေခြင်း
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise Exception("Extract failed")
            video_title = info.get('title', 'YouTube Video')
            
        # ခလုတ်ထဲတွင် ဗီဒီယို ID ကို တိုက်ရိုက်သိမ်းဆည်းခြင်း
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
        # ဒုတိယအရန်စနစ် - အကယ်၍ IP ကန့်သတ်ခံရပါက တိုက်ရိုက်စနစ်ဖြင့် အမြန်ဆုံးဆွဲရန် စီစဉ်ခြင်း
        keyboard = [[InlineKeyboardButton("📁 ပုံမှန်အတိုင်း တိုက်ရိုက်ဒေါင်းလုဒ်ဆွဲမည်", callback_data=f"best|{video_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await checking_msg.edit_text(
            "⚠️ ဆာဗာ၏ Resolution ခွဲခြားမှုစနစ် အနည်းငယ် ကြန့်ကြာနေပါသည်။ အောက်ပါခလုတ်ကို သုံးပြီး တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲနိုင်ပါသည်။",
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("|")
    res_choice = data_parts[0]
    video_id = data_parts[1]

    url = f"https://www.youtube.com/watch?v={video_id}"
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
        ydl_format = "best[ext=mp4]/best"

    ydl_opts = {
        'format': ydl_format,
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'restrictfilenames': True,
        'noplaylist': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
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
            if filesize_mb < 49.0:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=f"🎬 {video_title}\n✨ Quality: {res_choice}"
                )
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
        await query.edit_message_text("စိတ်မကောင်းပါဘူးခင်ဗျာ။ ဗီဒီယိုအား ဒေါင်းလုဒ်ဆွဲရန် ဆာဗာ IP ကန့်သတ်ချက် ရှိနေပါသည်။ ခေတ္တစောင့်ပြီးမှ ပြန်စမ်းကြည့်ပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။ ❌")

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
