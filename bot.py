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

BOT_TOKEN = "8552466342:AAEGNebOKjuXgE62oqY_4cfkLSlna8kx8Hw"

# Bot စတင်ပွင့်ချိန်တွင် yt-dlp ကို ချက်ချင်း Version အသစ်ဆုံးဖြစ်အောင် Update လုပ်ခိုင်းခြင်း
def update_ytdlp():
    try:
        logger.info("Updating yt-dlp to the latest version...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        logger.info("yt-dlp updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update yt-dlp: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 စွမ်းဆောင်ရည်မြှင့် YouTube Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သင်ဒေါင်းလုဒ်ဆွဲချင်တဲ့ YouTube Video Link ကို ပို့ပေးပါ။ 4K အထိ စိတ်ကြိုက်ရွေးချယ်နိုင်ပါပြီ။"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://", "youtu.be")):
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ကို ပို့ပေးပါခင်ဗျာ။ ❌")
        return

    checking_msg = await update.message.reply_text("ဗီဒီယိုကို လုံခြုံစိတ်ချရသော Cloud Pipeline ဖြင့် စစ်ဆေးနေပါတယ်... ⏳")

    # YouTube Block မလုပ်နိုင်အောင် သုံးမည့် Network Options
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        # ဗီဒီယို အချက်အလက်ကို ရှာဖွေခြင်း
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info ကို force_generic မပါဘဲ လုံခြုံစွာ ခေါ်ယူခြင်း
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("No info extracted")
                
            video_title = info.get('title', 'YouTube Video')
            
        context.user_data[str(update.effective_user.id)] = url

        keyboard = [
            [
                InlineKeyboardButton("📁 360p", callback_data="res_360"),
                InlineKeyboardButton("📁 720p (HD)", callback_data="res_720")
            ],
            [
                InlineKeyboardButton("📁 1080p (FHD)", callback_data="res_1080"),
                InlineKeyboardButton("🔥 4K (UltraHD)", callback_data="res_2160")
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
        logger.error(f"Extraction Error: {str(e)}")
        # Error တက်ပါက ယာယီဖြေရှင်းချက်အနေနဲ့ အခြေခံအကျဆုံး Option နဲ့ တိုက်ရိုက်ဒေါင်းဖို့ ခလုတ်ပြပေးမယ်
        keyboard = [[InlineKeyboardButton("📁 ပုံမှန် Quality အတိုင်း တိုက်ရိုက်ဒေါင်းမည်", callback_data="res_best")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await checking_msg.edit_text(
            "⚠️ YouTube စနစ်ပြောင်းလဲမှုကြောင့် အဆင့်မြင့် အရည်အသွေး ရွေးချယ်မှု စစ်ဆေးရခက်ခဲနေပါသည်။ အောက်ပါခလုတ်ကို သုံးပြီး တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲနိုင်ပါသည်။",
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    url = context.user_data.get(user_id)

    if not url:
        await query.edit_message_text("သက်တမ်းကုန်ဆုံးသွားပါပြီ။ Link ကို ပြန်ပို့ပေးပါ။ ❌")
        return

    res_choice = query.data
    await query.edit_message_text("Cloud Server ပေါ်တွင် ဗီဒီယိုအား စတင်စီစဉ်နေပါပြီ... 📥")

    # Resolution အလိုက် ခွဲခြားခြင်း
    if res_choice == "res_360":
        ydl_format = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif res_choice == "res_720":
        ydl_format = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif res_choice == "res_1080":
        ydl_format = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif res_choice == "res_2160":
        ydl_format = "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
    else:
        ydl_format = "best[ext=mp4]/best"

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
            if filesize_mb < 49.0:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=f"🎬 {video_title}"
                )
            else:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=video_file,
                    caption=f"🎬 {video_title} (ဖိုင်ဆိုဒ် 50MB ကျော်သဖြင့် ဖိုင်အမျိုးအစားဖြင့် ပို့ပေးထားပါသည်)"
                )

        if os.path.exists(filename):
            os.remove(filename)
        await query.message.delete()

    except Exception as e:
        logger.error(str(e))
        await query.edit_message_text("စိတ်မကောင်းပါဘူးခင်ဗျာ။ ဗီဒီယိုအား ဒေါင်းလုဒ်ဆွဲရန် ဆာဗာတွင် အခက်အခဲရှိနေပါသည်။ နောက်ထပ် လင့်ခ်တစ်ခုဖြင့် ပြန်စမ်းကြည့်ပေးပါ။ ❌")

def main():
    # Bot မပွင့်ခင် yt-dlp ကို အရင်ဆုံး Update လုပ်ခိုင်းခြင်း
    update_ytdlp()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
