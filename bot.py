import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Error များကို စောင့်ကြည့်ရန် Logging စနစ်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# အဆင့် (၁) ကရလာတဲ့ Token ကို ဒီနေရာမှာ အစားထိုးပါ
BOT_TOKEN = "8552466342:AAEGNebOKjuXgE62oqY_4cfkLSlna8kx8Hw"

# Bot စတင်ချိန်တွင် ပြသမည့်စာ
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"မင်္ဂလာပါ {user_name} ရေ... 🙏\n\n"
        "ကျွန်တော်က YouTube ဗီဒီယိုတွေကို အခမဲ့ ဒေါင်းလုဒ်ဆွဲပေးမယ့် Bot ပါ။\n"
        "သင်ဒေါင်းလုဒ်လုပ်ချင်တဲ့ YouTube Video Link (URL) ကို ပို့ပေးရုံပါပဲခင်ဗျာ။ 📥"
    )

# ဗီဒီယို ဒေါင်းလုဒ်လုပ်ပြီး ပြန်ပို့ပေးမည့် အပိုင်း
async def handle_video_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # ၎င်းပို့လိုက်တာ Link ဟုတ်မဟုတ် အကြမ်းဖျင်းစစ်ဆေးခြင်း
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link တစ်ခုကို ပို့ပေးပါခင်ဗျာ။ ❌")
        return

    # အခြေအနေပြစာသား ပို့ခြင်း
    status_msg = await update.message.reply_text("ဗီဒီယိုကို စစ်ဆေးနေပါပြီ... ခေတ္တစောင့်ပေးပါဦး။ ⏳")

    # ဗီဒီယို သိမ်းမည့်နေရာနှင့် Format သတ်မှတ်ချက် (အရည်အသွေးအသင့်အတင့်နှင့် MP4 format)
    # ဖုန်းဗီဒီယိုဖိုင်ဆိုဒ် 50MB ကျော်လျှင် Telegram က ပို့ခွင့်မပြုသောကြောင့် Quality အသင့်အတင့်ကို ရွေးထားပါတယ်
    ydl_opts = {
        'format': 'best[ext=mp4][filesize<50M]/worst[ext=mp4]', 
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
    }

    try:
        await status_msg.edit_text("ဗီဒီယိုကို Cloud Server ပေါ်သို့ ဒေါင်းလုဒ်ဆွဲနေပါပြီ... 📥")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ဗီဒီယို အချက်အလက်ရယူခြင်းနှင့် ဒေါင်းလုဒ်လုပ်ခြင်း
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_title = info.get('title', 'Downloaded Video')

        await status_msg.edit_text("ဒေါင်းလုဒ်ပြီးပါပြီ။ သင်၏ဖုန်းဆီသို့ ပေးပို့နေပါပြီ... 📤")
        
        # ဗီဒီယိုကို Telegram သို့ ပြန်ပို့ခြင်း
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file, 
                caption=f"🎬 **ခေါင်းစဉ်:** {video_title}\n\n@mmytdl_2026_bot မှ ကူညီပေးထားပါသည်။"
            )
        
        # ဒေါင်းလုဒ်လုပ်ထားသောဖိုင်အား Server ထဲမှ ပြန်ဖျက်၍ နေရာလွတ်ရှင်းလင်းခြင်း
        if os.path.exists(filename):
            os.remove(filename)
            
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        await status_msg.edit_text(
            "စိတ်မကောင်းပါဘူးခင်ဗျာ။ ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရာမှာ အမှားအယွင်းတစ်ခု ရှိသွားပါတယ်။ ❌\n"
            "(မှတ်ချက်- ဗီဒီယိုဖိုင်ဆိုဒ် အလွန်ကြီးမားနေခြင်း သို့မဟုတ် Link ပျက်နေခြင်းကြောင့် ဖြစ်နိုင်ပါတယ်)"
        )

# ပရိုဂရမ် အဓိကပတ်လမ်း
def main():
    # Application ဆောက်ခြင်း
    app = Application.builder().token(BOT_TOKEN).build()

    # စာသားများနှင့် Command များကို Handle လုပ်မည့်နေရာ ချိတ်ဆက်ခြင်း
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_download))

    # Bot အား အလုပ်လုပ်ခိုင်းခြင်း
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
