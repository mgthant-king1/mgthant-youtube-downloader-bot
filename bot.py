import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Error Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# သင့် Bot Token ကို ဒီမှာ ထည့်ပါ
BOT_TOKEN = "8552466342:AAEGNebOKjuXgE62oqY_4cfkLSlna8kx8Hw"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📥 YouTube Downloader Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သင်ဒေါင်းလုဒ်ဆွဲချင်တဲ့ YouTube Video Link ကို ပို့ပေးပါ။ ပြီးရင် Resolution ရွေးချယ်နိုင်ပါတယ်ခင်ဗျာ။"
    )

# Link ရောက်လာရင် ရွေးချယ်စရာ Button များ ပြသခြင်း
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ကို ပို့ပေးပါခင်ဗျာ။ ❌")
        return

    # ခေတ္တစစ်ဆေးခြင်း
    checking_msg = await update.message.reply_text("ဗီဒီယို အချက်အလက်ကို စစ်ဆေးနေပါတယ်... ⏳")

    try:
        # ဗီဒီယို ရနိုင်တဲ့ Resolution တွေကို စစ်ဆေးဖို့ အချက်အလက်အရင်ယူမယ်
        with yt_dlp.YoutubeDL({'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Video')
            
        # Button အပြင်အဆင် (360p, 720p, 1080p, 4K)
        # callback_data ထဲမှာ format_id နဲ့ url ကို တွဲသိမ်းဖို့အတွက် context သုံးပါမယ်
        context.user_data[str(update.effective_user.id)] = url

        keyboard = [
            [
                InlineKeyboardButton("📁 360p (Low Size)", callback_data="res_360"),
                InlineKeyboardButton("📁 720p (HD)", callback_data="res_720")
            ],
            [
                InlineKeyboardButton("📁 1080p (Full HD)", callback_data="res_1080"),
                InlineKeyboardButton("🔥 4K (Ultra HD)", callback_data="res_2160")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await checking_msg.delete()
        await update.message.reply_text(
            f"🎬 **ခေါင်းစဉ်:** {video_title}\n\n"
            f"သင်ဒေါင်းလုဒ်လုပ်လိုသော ဗီဒီယို အရည်အသွေး (Resolution) ကို ရွေးချယ်ပေးပါ 👇",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(str(e))
        await checking_msg.edit_text("ဗီဒီယို အချက်အလက်ကို ယူလို့မရနိုင်ဖြစ်နေပါတယ်။ Link မှန်မမှန် ပြန်စစ်ပေးပါ။ ❌")

# Button တစ်ခုခုကို နှိပ်လိုက်ချိန် အလုပ်လုပ်မည့်အပိုင်း
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

    # ရွေးချယ်လိုက်တဲ့ resolution အလိုက် yt-dlp format သတ်မှတ်ခြင်း
    # video ကော audio ကော ပေါင်းပြီး အကောင်းဆုံးအရည်အသွေး ရအောင်လုပ်တာပါ (4K အထိ ရစေရမယ်)
    if res_choice == "res_360":
        ydl_format = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif res_choice == "res_720":
        ydl_format = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif res_choice == "res_1080":
        ydl_format = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif res_choice == "res_2160":  # 4K
        ydl_format = "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
    else:
        ydl_format = "best"

    # ဒေါင်းလုဒ် လုပ်မည့် Options
    ydl_opts = {
        'format': ydl_format,
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'merge_output_format': 'mp4', # ဗီဒီယိုနဲ့ အော်ဒီယို ပေါင်းရင် mp4 ထွက်လာအောင် လုပ်ခြင်း
        'restrictfilenames': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # အကယ်၍ merge ဖြစ်သွားရင် .mp4 ဖြစ်သွားမှာမို့ လိုက်စစ်တာပါ
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
                
            video_title = info.get('title', 'Downloaded Video')

        await query.edit_message_text("ဒေါင်းလုဒ်လုပ်ပြီးပါပြီ။ သင်၏ Telegram ဆီသို့ ပေးပို့နေပါပြီ... 📤")
        
        # ဖိုင်ဆိုဒ်ကို စစ်ဆေးခြင်း
        filesize_mb = os.path.getsize(filename) / (1024 * 1024)

        with open(filename, 'rb') as video_file:
            # ဖိုင်ဆိုဒ် 50MB အောက်ဆိုရင် ပုံမှန် ဗီဒီယိုအတိုင်း ပို့မယ်
            if filesize_mb < 49.0:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=f"🎬 {video_title}\n\n✨ Resolution: {res_choice.split('_')[1]}p"
                )
            # ဖိုင်ဆိုဒ် 50MB ကနေ 2GB အထိဆိုရင် Document (ဖိုင်အမျိုးအစား) အနေနဲ့ ပို့ပေးမယ် (ဒါဆို Error မတက်တော့ပါ)
            else:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=video_file,
                    caption=f"🎬 {video_title} (ဖိုင်ဆိုဒ်ကြီးသောကြောင့် Document အနေဖြင့် ပို့ပေးထားပါသည်)\n\n✨ Resolution: {res_choice.split('_')[1]}p"
                )

        # နေရာလွတ်ရှင်းလင်းရေး
        if os.path.exists(filename):
            os.remove(filename)
        await query.message.delete()

    except Exception as e:
        logger.error(str(e))
        await query.edit_message_text("စိတ်မကောင်းပါဘူးခင်ဗျာ။ ဒီ Resolution နဲ့ ဒေါင်းလုဒ်ဆွဲလို့ မရနိုင်ပါဘူး။ (သို့မဟုတ် ၎င်း Resolution ယူကျုပေါ်မှာ မရှိတာမျိုး ဖြစ်နိုင်ပါတယ်) ❌")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot စတင်ပွင့်ပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
