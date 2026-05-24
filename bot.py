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

# --- CONFIGURATION ---
# မိမိ Bot Token ကို ဤနေရာတွင် ထည့်ပါ
BOT_TOKEN = "8925968993:AAF54j8OT9rM20KbcbW6moecBYtmssmr5IQ"

# Proxy အသုံးပြုလိုပါက ဤနေရာတွင် ထည့်ပါ (ဥပမာ: "socks5://user:pass@host:port" သို့မဟုတ် "http://host:port")
PROXY_URL = "http://uparhknj:u5ok7mr7s22l@38.154.203.95:5863/" 

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
        reply_markup=get_main_reply_keyboard(),
        parse_mode='Markdown'
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

    # YouTube Block များကို ကျော်ဖြတ်ရန် အဆင့်မြင့် Network Options များ
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'geo_bypass': True,
        'quiet': True,
        'no_check_certificates': True,
        'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 30,
        'proxy': PROXY_URL,
        'cookiefile': 'cookies.txt',  # ✨ YouTube Ban ကိုကျော်ရန် Cookie File သုံးပါမည်
    }

    # Format Quality ရွေးချယ်မှုများ
    if choice == "yt_mp3":
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    elif choice == "yt_4k":
        ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]/best'
    elif choice == "yt_1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best'
    elif choice == "yt_720p":
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best'
    elif choice == "yt_360p":
        ydl_opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]/best'
    elif choice == "tt_nowm":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif choice == "tt_wm":
        ydl_opts['format'] = 'worst/best'
    elif choice == "fb_best":
        ydl_opts['format'] = 'best[ext=mp4]/best'
        
    filename = None
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

        # Telegram Limit Size စစ်ဆေးခြင်း (50MB အထက်မရပါ)
        if os.path.exists(filename):
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)
            if file_size_mb > 49.5:
                await context.bot.send_message(
                    chat_id=query.message.chat_id, 
                    text=f"❌ **ဖိုင်အရွယ်အစား ကြီးမားလွန်းပါသည် ({file_size_mb:.2f} MB)!**\nTelegram သည် 50MB အောက်သာ ပေးပို့ခွင့်ပြုပါသည်။ Quality လျှော့၍ ဒေါင်းလုဒ်ဆွဲပါ။",
                    parse_mode='Markdown'
                )
                if os.path.exists(filename):
                    os.remove(filename)
                return

        with open(filename, 'rb') as file_to_send:
            if choice == "yt_mp3":
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file_to_send,
                    caption=f"🎵 **{title}**\n\n👨‍💻 *Admin: By MGTHANT*",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=file_to_send,
                    caption=f"🎬 **{title}**\n\n👨‍💻 *Admin: By MGTHANT*",
                    parse_mode='Markdown'
                )
            await query.message.delete()

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download Error: {e}")
        error_msg = str(e).lower()
        if "403" in error_msg or "sign in" in error_msg or "bot" in error_msg or "blocked" in error_msg:
            msg = "❌ **YouTube ကနေ ပိတ်လိုက်ပါပြီ။**\nကျေးဇူးပြု၍ `cookies.txt` ဖိုင်အသစ်ကို Server အတွင်းသို့ ပြန်လည်ထည့်သွင်းပေးပါ။"
        else:
            msg = "❌ ဒေါင်းလုဒ်ဆွဲရာတွင် ပြဿနာဖြစ်ပွားပါသည်။ လင့်ခ်အမှား (သို့) Private Video ဖြစ်နိုင်ပါသည်။"
        await context.bot.send_message(chat_id=query.message.chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(str(e))
        await context.bot.send_message(chat_id=query.message.chat_id, text="❌ အခြားမမျှော်လင့်သော ပြဿနာတစ်ခု ဖြစ်ပွားခဲ့ပါသည်။")
    finally:
        # နေရာမလွတ်ခုံစေရန် ဒေါင်းလုပ်ဆွဲထားသော ဖိုင်များကို ရှင်းထုတ်ပါ
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    if user_input in ["📺 YouTube Download", "🎵 TikTok Download", "📘 Facebook Download", "🔍 Music Mode (သီချင်းရှာ)"]:
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
            
        if user_input == "📺 YouTube Download":
            text = "📺 **YouTube Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော YouTube Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "🎵 TikTok Download":
            text = "🎵 **TikTok Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော TikTok Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "📘 Facebook Download":
            text = "📘 **Facebook Mode သို့ ရောက်ရှိနေပါသည်:**\n\nဒေါင်းလုဒ်ဆွဲလိုသော Facebook Link ကို ပို့ပေးပါခင်ဗျာ၊၊"
        elif user_input == "🔍 Music Mode (သီချင်းရှာ)":
            text = "🔍 **Music Search Mode သို့ ရောက်ရှိနေပါသည်:**\n\nနားထောင်လိုသော သီချင်းအမည်ကို ရိုက်ပို့ပေးပါခင်ဗျာ၊၊"

        await update.message.reply_text(f"{text}\n\n👨‍💻 *Admin: By MGTHANT*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")]]), parse_mode='Markdown')
        return

    if user_input.startswith(("http://", "https://")):
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
        context.user_data[user_id]['link'] = user_input
        
        if "tiktok.com" in user_input:
            keyboard = [[InlineKeyboardButton("🔥 TikTok (No WM)", callback_data="tt_nowm")], [InlineKeyboardButton("📁 TikTok (With WM)", callback_data="tt_wm")]]
        elif "facebook.com" in user_input or "fb.watch" in user_input or "fb.gg" in user_input:
            keyboard = [[InlineKeyboardButton("📁 Facebook Video", callback_data="fb_best")]]
        else:
            keyboard = [
                [InlineKeyboardButton("🎵 High-Speed MP3 Audio", callback_data="yt_mp3")],
                [InlineKeyboardButton("💎 4K Ultra HD", callback_data="yt_4k"), InlineKeyboardButton("✨ 1080p Full HD", callback_data="yt_1080p")],
                [InlineKeyboardButton("📁 720p HD", callback_data="yt_720p"), InlineKeyboardButton("📁 360p Low", callback_data="yt_360p")]
            ]
        keyboard.append([InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")])
        await update.message.reply_text("✅ **လင့်ခ်လက်ခံရရှိပါပြီ!**\n\nQuality ရွေးချယ်ပေးပါရန်။ 👇", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    checking_msg = await update.message.reply_text(f"🔍 '{user_input}' ကို ရှာဖွေနေပါသည်...")
    await search_and_show_playlist(update, checking_msg, user_input, page=0)

async def search_and_show_playlist(update: Update, message_obj, query_text, page=0):
    clean_query = query_text.replace('\n', ' ').strip()
    ydl_opts = {
        'playlistend': 20, 
        'quiet': True, 
        'extract_flat': 'in_playlist', 
        'geo_bypass': True, 
        'proxy': PROXY_URL,
        'cookiefile': 'cookies.txt' # Search ရန်အတွက်ပါ Cookie ထည့်ပေးထားသည်
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch20:{clean_query}", download=False)
            songs = info.get('entries', [])
        if not songs:
            await message_obj.edit_text("❌ ရှာဖွေမှုမတွေ့ရှိပါ။")
            return
        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_songs = songs[start_idx:end_idx]
        keyboard = []
        for idx, song in enumerate(page_songs, start=start_idx + 1):
            s_title = (song.get('title', 'Unknown')[:27] + "...") if len(song.get('title', '')) > 30 else song.get('title', 'Unknown')
            keyboard.append([InlineKeyboardButton(f"{idx}။ {s_title}", callback_data=f"listmp3|{song.get('id')}")])
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"nav|{page-1}|{clean_query[:15]}"))
        if end_idx < len(songs): nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav|{page+1}|{clean_query[:15]}"))
        if nav: keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("💬 Connect Admin", url="https://t.me/mgthantIT")])
        await message_obj.edit_text(f"🎵 **Music Search Mode (Page - {page + 1})**\n\n👨‍💻 *Admin: By MGTHANT*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        logger.error(str(e))
        await message_obj.edit_text("❌ ရှာဖွေရခက်ခဲနေပါသည်။ YouTube က Block ထားခြင်းဖြစ်နိုင်ပါသည်။ (Cookies အသစ်ပြန်ထည့်ပါ)")

def main():
    update_ytdlp()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
