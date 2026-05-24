import os
import sys
import subprocess
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# မိမိ Bot Token ကို ဤနေရာတွင် ထည့်ပါ
BOT_TOKEN = "8925968993:AAF54j8OT9rM20KbcbW6moecBYtmssmr5IQ"

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def update_ytdlp():
    try:
        logger.info("Updating yt-dlp to latest version...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except Exception as e:
        logger.error(f"Update failed: {e}")

# Typing Keyboard ဘေးတွင် အမြဲပေါ်နေမည့် ခလုတ်ကြီး ၄ ခု
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📺 YouTube Download"), KeyboardButton("🎵 TikTok Download")],
            [KeyboardButton("📘 Facebook Download"), KeyboardButton("🔍 Music Mode (သီချင်းရှာ)")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in context.user_data:
        context.user_data[user_id].clear()

    await update.message.reply_text(
        "🚀 **Ultimate Multi-Platform Downloader Bot မှ ကြိုဆိုပါတယ်!**\n\n"
        "✨ အသုံးပြုလိုသော စနစ်ကို အောက်ပါ **စာရိုက်သည့်ဘေးရှိ Keyboard ခလုတ်များ** တွင် တိုက်ရိုက်ရွေးချယ် အသုံးပြုနိုင်ပါပြီခင်ဗျာ။ 👇\n\n"
        "👨‍💻 *Admin: By MGTHANT*",
        reply_markup=get_main_reply_keyboard()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = str(update.effective_user.id)

    # Music List စာမျက်နှာလှန်ခြင်း
    if data.startswith("nav|"):
        await query.answer()
        _, target_page, query_text = data.split("|")
        await query.edit_message_text("🔄 စာမျက်နှာကို ပြောင်းလဲနေပါသည်...")
        await search_and_show_playlist(update, query.message, query_text, page=int(target_page))
        return

    # ဒေါင်းလုဒ်စတင်ခြင်းအပိုင်း
    choice = data
    if data.startswith("listmp3|"):
        video_id = data.split("|")[1]
        target_url = f"https://www.youtube.com/watch?v={video_id}"
        await query.answer(text="🎧 MP3 ကို ဆာဗာမှ ဖမ်းယူနေပါပြီ... 📥", show_alert=False)
        choice = "yt_mp3"
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
        context.user_data[user_id]['link'] = target_url
    else:
        await query.answer()
        if user_id not in context.user_data or 'link' not in context.user_data[user_id]:
            await query.edit_message_text("❌ သက်တမ်းကုန်ဆုံးသွားပါပြီ။ လင့်ခ်ကို ပြန်လည်ပေးပို့ပေးပါ။")
            return
        target_url = context.user_data[user_id]['link']
        await query.edit_message_text("📥 ဆာဗာတွင် ဖိုင်ကို စတင်ဆွဲယူနေပါပြီ... ခေတ္တစောင့်ပါ။")

    # YouTube Block များကို ကျော်ဖြတ်ရန် Network Options များ ဖြည့်စွက်ခြင်း
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'geo_bypass': True,
        'quiet': True,
        'no_check_certificates': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'retries': 5,
        'fragment_retries': 10,
        'socket_timeout': 10,
        'sleep_interval': 5,
        'max_sleep_interval': 60,
    }

    # Format Quality ရွေးချယ်မှုများ (4K အထိ ပါဝင်အောင် ပြန်လည်ပြင်ဆင်ထားပါသည်)
    if choice == "yt_mp3":
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    elif choice == "yt_4k":
        ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]'
    elif choice == "yt_1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
    elif choice == "yt_720p":
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
    elif choice == "yt_360p":
        ydl_opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]'
    elif choice == "tt_nowm":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif choice == "tt_wm":
        ydl_opts['format'] = 'worst/best'
    elif choice == "fb_best":
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            filename = ydl.prepare_filename(info)
            
            if choice == "yt_mp3":
                if not os.path.exists(filename):
                    filename = os.path.splitext(filename)[0] + ".m4a"
            elif not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
                
            title = info.get('title', 'Media File')

        with open(filename, 'rb') as file_to_send:
            if choice == "yt_mp3":
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file_to_send,
                    caption=f"🎵 **{title}**\n\n👨‍💻 *Admin: By MGTHANT*"
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=file_to_send,
                    caption=f"🎬 **{title}**\n\n👨‍💻 *Admin: By MGTHANT*"
                )
                await query.message.delete()

        if os.path.exists(filename):
            os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download Error: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text="❌ ဒေါင်းလုဒ်ဆွဲရာတွင် ပြဿနာဖြစ်ပွားပါသည်။ လင့်ခ်မှန်ကန်မှုရှိမရှိ စစ်ဆေးပါ သို့မဟုတ် နောက်မှ ထပ်ကြိုးစားပါ။"
        )
    except yt_dlp.utils.ExtractorError as e:
        logger.error(f"Extractor Error: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text="❌ ဗီဒီယိုအချက်အလက်များ ရယူရာတွင် ပြဿနာဖြစ်ပွားပါသည်။ YouTube မှ ပိတ်ပင်ထားခြင်း သို့မဟုတ် ဗီဒီယိုမရှိတော့ခြင်း ဖြစ်နိုင်ပါသည်။"
        )
    except Exception as e:
        logger.error(str(e))
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text="❌ အခြားမမျှော်လင့်သော ပြဿနာတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။ နောက်မှ ထပ်ကြိုးစားပါ။"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    # 1. Reply Keyboard ခလုတ်များကို နှိပ်လိုက်သည့်အခါ
    if user_input in ["📺 YouTube Download", "🎵 TikTok Download", "📘 Facebook Download", "🔍 Music Mode (သီချင်းရှာ)"]:
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
            
        if user_input == "📺 YouTube Download":
            context.user_data[user_id]['current_mode'] = "youtube"
            text = "📺 **YouTube Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော YouTube ဗီဒီယို (သို့) Shorts Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "🎵 TikTok Download":
            context.user_data[user_id]['current_mode'] = "tiktok"
            text = "🎵 **TikTok Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော TikTok ဗီဒီယို Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "📘 Facebook Download":
            context.user_data[user_id]['current_mode'] = "facebook"
            text = "📘 **Facebook Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော Facebook ဗီဒီယို (သို့) Reels Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "🔍 Music Mode (သီချင်းရှာ)":
            context.user_data[user_id]['current_mode'] = "music"
            text = "🔍 **Music Search Mode သို့ ရောက်ရှိနေပါသည်:**\n\nနားထောင်လိုသော အဆိုတော်အမည် (သို့) သီချင်းအမည်ကို စာသားအတိုင်း ရိုက်ပို့ပေးပါခင်ဗျာ၊၊"

        await update.message.reply_text(f"{text}\n\n👨‍💻 *Admin: By MGTHANT*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")]]))
        return

    # 2. လင့်ခ် (URL) တစ်ခုခု ပို့လာပါက အလိုအလျောက် ခွဲခြားပြီး 4K အထိ Quality ပြပေးမည့်စနစ်
    if user_input.startswith(("http://", "https://")):
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
            
        context.user_data[user_id]['link'] = user_input
        
        if "tiktok.com" in user_input:
            keyboard = [
                [InlineKeyboardButton("🔥 TikTok (No WM)", callback_data="tt_nowm")],
                [InlineKeyboardButton("📁 TikTok (With WM)", callback_data="tt_wm")]
            ]
        elif "facebook.com" in user_input or "fb.watch" in user_input or "fb.gg" in user_input:
            keyboard = [[InlineKeyboardButton("📁 Facebook Video/Reels", callback_data="fb_best")]]
        else:
            # YouTube & Others အတွက် 4K အထိ ခလုတ်များ စုံလင်စွာ ပြန်လည်ထည့်သွင်းခြင်း
            keyboard = [
                [InlineKeyboardButton("🎵 High-Speed MP3 Audio", callback_data="yt_mp3")],
                [InlineKeyboardButton("💎 4K Ultra HD", callback_data="yt_4k"), InlineKeyboardButton("✨ 1080p Full HD", callback_data="yt_1080p")],
                [InlineKeyboardButton("📁 720p HD", callback_data="yt_720p"), InlineKeyboardButton("📁 360p Low", callback_data="yt_360p")]
            ]
            
        keyboard.append([InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")])
        
        await update.message.reply_text(
            "✅ **လင့်ခ်လက်ခံရရှိပါပြီ!**\n\nအောက်ပါ Inline ခလုတ်များထဲမှ မိမိဒေါင်းလုဒ်ဆွဲလိုသော Quality ကို ရွေးချယ်နှိပ်ပေးပါရန်။ 👇\n\n👨‍💻 *Admin: By MGTHANT*", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 3. စာသားသက်သက်ရိုက်ပို့လာပါက Music Search ပြုလုပ်ပေးခြင်း
    if user_id not in context.user_data:
        context.user_data[user_id] = {}
    context.user_data[user_id]['current_mode'] = "music"
    
    checking_msg = await update.message.reply_text(f"🔍 '{user_input}' ကို ရှာဖွေနေပါသည်...")
    await search_and_show_playlist(update, checking_msg, user_input, page=0)

async def search_and_show_playlist(update: Update, message_obj, query_text, page=0):
    clean_query = query_text.replace('\n', ' ').strip()
    ydl_opts = {'playlistend': 20, 'quiet': True, 'extract_flat': 'in_playlist', 'geo_bypass': True, 'no_check_certificates': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch20:{clean_query}", download=False)
            songs = info.get('entries', [])

        if not songs:
            await message_obj.edit_text("❌ ရှာဖွေမှုမတွေ့ရှိပါ။ အခြားနာမည်တစ်ခုဖြင့် ပြန်ရှာကြည့်ပါ။")
            return

        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_songs = songs[start_idx:end_idx]

        keyboard = []
        for idx, song in enumerate(page_songs, start=start_idx + 1):
            s_title = song.get('title', 'Unknown Title')
            if len(s_title) > 30:
                s_title = s_title[:27] + "..."
            s_id = song.get('id')
            keyboard.append([InlineKeyboardButton(f"{idx}။ {s_title}", callback_data=f"listmp3|{s_id}")])

        nav_buttons = []
        short_query = clean_query[:15]
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"nav|{page-1}|{short_query}"))
        if end_idx < len(songs):
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav|{page+1}|{short_query}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
            
        keyboard.append([InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        msg_caption = f"🎵 **Music Search Mode (စာမျက်နှာ - {page + 1})**\n💡 *ခလုတ်နှိပ်လျှင် မူလစာရင်းမပျောက်ဘဲ MP3 ကျလာပါမည်။*\n\n👨‍💻 *Admin: By MGTHANT*"
        
        if isinstance(update, Update) and update.callback_query:
            await message_obj.edit_text(msg_caption, reply_markup=reply_markup)
        else:
            await message_obj.delete()
            await update.message.reply_text(msg_caption, reply_markup=reply_markup)

    except Exception as e:
        logger.error(str(e))
        await message_obj.edit_text("❌ ဆာဗာအတွင်း ရှာဖွေရခက်ခဲနေပါသည်။")

def main():
    update_ytdlp()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 Auto-detection with Resolution Menu Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
