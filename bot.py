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
BOT_TOKEN = "8630051632:AAHtXxGcIgH10mHwGBdHalUSFDBD05uDd-o"

def update_ytdlp():
    try:
        logger.info("Updating yt-dlp to latest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except Exception as e:
        logger.error(f"Update failed: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 YouTube Video & MP3 Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "✨ **အသုံးပြုနည်းများ:**\n"
        "၁။ YouTube Link ကို တိုက်ရိုက် ပို့နိုင်ပါသည်။\n"
        "၂။ သီချင်းနာမည် သို့မဟုတ် အဆိုတော်နာမည်ကို ရိုက်နှိပ်၍လည်း ရှာဖွေနိုင်ပါသည်။\n\n"
        "ပို့ပြီးပါက Video သို့မဟုတ် MP3 စိတ်ကြိုက် ရွေးချယ်နိုင်ပါပြီခင်ဗျာ။ 🙏"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    checking_msg = await update.message.reply_text("YouTube ပေါ်တွင် ရှာဖွေနေပါတယ်... ခေတ္တစောင့်ပေးပါဦး။ ⏳")

    # Cloud IP Block သက်သာစေရန် Options
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    # Input က Link ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if user_input.startswith(("http://", "https://")):
        search_query = user_input
    else:
        # Link မဟုတ်ပါက YouTube Search စနစ် သုံးခြင်း
        search_query = f"ytsearch1:{user_input}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if 'entries' in info:  # Search လုပ်လို့ ထွက်လာတဲ့ ရလဒ်ထဲက ပထမဆုံးဖိုင်ကို ယူခြင်း
                info = info['entries'][0]
                
            video_title = info.get('title', 'YouTube Music/Video')
            video_id = info.get('id')
            
        if not video_id:
            raise Exception("Video ID not found")

        # ကီးဘုတ်တွင် MP3 ဒေါင်းလုဒ်ဆွဲရန် ခလုတ်ပါ ထပ်ဖြည့်ထားသည်
        keyboard = [
            [
                InlineKeyboardButton("🎵 High Quality MP3 (Audio)", callback_data=f"mp3|{video_id}")
            ],
            [
                InlineKeyboardButton("📁 360p (Video)", callback_data=f"360p|{video_id}"),
                InlineKeyboardButton("📁 720p HD (Video)", callback_data=f"720p|{video_id}")
            ],
            [
                InlineKeyboardButton("📁 1080p FHD (Video)", callback_data=f"1080p|{video_id}"),
                InlineKeyboardButton("🔥 4K UltraHD (Video)", callback_data=f"2160p|{video_id}")
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
        await checking_msg.edit_text("❌ စိတ်မကောင်းပါဘူး၊ ရှာဖွေမှုမတွေ့ရှိပါ။ သီချင်းနာမည်ကို သေချာပြန်ရိုက်ရှာပေးပါခင်ဗျာ။")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("|")
    res_choice = data_parts[0]
    video_id = data_parts[1]

    url = f"https://www.youtube.com/watch?v={video_id}"
    await query.edit_message_text("Cloud Server ပေါ်တွင် စတင်လုပ်ဆောင်နေပါပြီ... 📥")

    # MP3 သို့မဟုတ် Video ရွေးချယ်မှုအလိုက် Options ပြောင်းလဲခြင်း
    if res_choice == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'geo_bypass': True,
            # အသံဖိုင်ကို MP3 စစ်စစ်ဖြစ်အောင် ပြောင်းလဲပေးသည့်စနစ်
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # 320kbps အကောင်းဆုံး အသံအရည်အသွေး
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
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
            ydl_format = "best[ext=mp4]/best"

        ydl_opts = {
            'format': ydl_format,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'restrictfilenames': True,
            'noplaylist': True,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # MP3 ဖြစ်သွားပါက Extension လိုက်ပြောင်းပေးခြင်း
            if res_choice == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
            elif not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
                
            video_title = info.get('title', 'Audio/Video')

        await query.edit_message_text("အဆင်သင့်ဖြစ်ပါပြီ။ Telegram ဆီသို့ ပေးပို့နေပါပြီ... 📤")
        
        filesize_mb = os.path.getsize(filename) / (1024 * 1024)

        with open(filename, 'rb') as file_to_send:
            if res_choice == "mp3":
                # MP3 သီချင်းဖိုင်အဖြစ် ပို့ပေးခြင်း
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file_to_send,
                    caption=f"🎵 {video_title}\n✨ Quality: 320kbps MP3 Audio"
                )
            else:
                # ဗီဒီယိုဖိုင်အဖြစ် ပို့ပေးခြင်း
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
        await query.edit_message_text("❌ ဒေါင်းလုဒ်ဆွဲရာတွင် ပြဿနာရှိနေပါသည်။ အခြားသီချင်းဖြင့် ထပ်မံစမ်းသပ်ကြည့်ပါ။")

def main():
    update_ytdlp()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("All-In-One Downloader system is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
