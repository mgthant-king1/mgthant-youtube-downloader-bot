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
        logger.info("Updating yt-dlp to latest version...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except Exception as e:
        logger.error(f"Update failed: {e}")

# YouTube Link ထဲမှ ဗီဒီယို ID ကို တိကျစွာ ခွဲထုတ်ပေးသည့် စနစ်
def extract_video_id(url):
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S+\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 YouTube Video & MP3 Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "✨ **အသုံးပြုနည်းများ:**\n"
        "၁။ YouTube Link ကို တိုက်ရိုက် ပို့နိုင်ပါသည်။\n"
        "၂။ သီချင်းနာမည် သို့မဟုတ် အဆိုတော်နာမည်ကို ရိုက်နှိပ်၍ ရှာဖွေနိုင်ပါသည်။\n\n"
        "ဗီဒီယိုနှင့် MP3 များကို အမှားအယွင်းမရှိ ၄ကေ အထိ ဒေါင်းလုဒ်ဆွဲနိုင်ပါပြီ။ 🙏"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    checking_msg = await update.message.reply_text("YouTube ပေါ်တွင် ရှာဖွေနေပါတယ်... ခေတ္တစောင့်ပေးပါဦး။ ⏳")

    # Cloud Platform များတွင် အသုံးပြုရန် အငြိမ်ဆုံး Network Options
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    video_id = extract_video_id(user_input)
    
    if video_id:
        # Link ပို့လာပါက ကမ္ဘာသုံး အငြိမ်ဆုံး Standard Link အဖြစ် ပြောင်းလဲခြင်း
        search_query = f"https://www.youtube.com/watch?v={video_id}"
    else:
        # စာသားရိုက်ရှာပါက စနစ်တကျ ရှာဖွေခိုင်းခြင်း
        search_query = f"ytsearch1:{user_input}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
                
            video_title = info.get('title', 'YouTube Music/Video')
            final_video_id = info.get('id')
            
        if not final_video_id:
            raise Exception("Video ID could not be retrieved")

        # ကီးဘုတ်တွင် ခလုတ်များ တွဲဖက်ပြင်ဆင်ခြင်း
        keyboard = [
            [InlineKeyboardButton("🎵 High Quality MP3 (Audio)", callback_data=f"mp3|{final_video_id}")],
            [
                InlineKeyboardButton("📁 360p (Video)", callback_data=f"360p|{final_video_id}"),
                InlineKeyboardButton("📁 720p HD (Video)", callback_data=f"720p|{final_video_id}")
            ],
            [
                InlineKeyboardButton("📁 1080p FHD (Video)", callback_data=f"1080p|{final_video_id}"),
                InlineKeyboardButton("🔥 4K UltraHD (Video)", callback_data=f"2160p|{final_video_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await checking_msg.delete()
        await update.message.reply_text(
            f"🎬 **တွေ့ရှိသောရလဒ်:** {video_title}\n\n"
            f"သင်ဒေါင်းလုဒ်လုပ်လိုသော အမျိုးအစား (Format) ကို ရွေးချယ်ပေးပါ 👇",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(str(e))
        await checking_msg.edit_text("❌ စိတ်မကောင်းပါဘူး၊ ရှာဖွေမှုမတွေ့ရှိပါ။ သီချင်းနာမည် (သို့မဟုတ်) လင့်ခ်ကို သေချာပြန်စစ်ပြီး ပို့ပေးပါခင်ဗျာ။")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("|")
    res_choice = data_parts[0]
    video_id = data_parts[1]

    # အငြိမ်ဆုံး Standard URL သုံး၍ ဆွဲခြင်း
    url = f"https://www.youtube.com/watch?v={video_id}"
    await query.edit_message_text("Cloud Server ပေါ်တွင် ဗီဒီယိုအား စတင်စီစဉ်နေပါပြီ... 📥")

    if res_choice == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'geo_bypass': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }
    else:
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
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if res_choice == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
            elif not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
                
            video_title = info.get('title', 'Audio/Video')

        await query.edit_message_text("အဆင်သင့်ဖြစ်ပါပြီ။ Telegram ဆီသို့ ပေးပို့နေပါပြီ... 📤")
        
        filesize_mb = os.path.getsize(filename) / (1024 * 1024)

        with open(filename, 'rb') as file_to_send:
            if res_choice == "mp3":
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file_to_send,
                    caption=f"🎵 {video_title}\n✨ Quality: 320kbps MP3 Audio"
                )
            else:
                if filesize_mb < 49.0:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=file_to_send,
                        caption=f"🎬 {video_title}\n✨ Quality: {res_choice}"
                    )
                else:
                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=file_to_send,
                        caption=f"🎬 {video_title} ({int(filesize_mb)}MB - ဖိုင်ဆိုဒ်ကြီးသဖြင့် Document အနေဖြင့် ပို့ပေးထားပါသည်)\n✨ Quality: {res_choice}"
                    )

        if os.path.exists(filename):
            os.remove(filename)
        await query.message.delete()

    except Exception as e:
        logger.error(str(e))
        await query.edit_message_text("❌ ဒေါင်းလုဒ်ဆွဲရာတွင် ပြဿနာရှိနေပါသည်။ အခြားဗီဒီယို/သီချင်းဖြင့် ထပ်မံစမ်းသပ်ကြည့်ပါ။")

def main():
    update_ytdlp()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Stable Downloader system is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
