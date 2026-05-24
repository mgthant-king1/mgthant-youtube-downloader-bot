import os
import sys
import subprocess
import logging
import yt_dlp

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8925968993:AAF54j8OT9rM20KbcbW6moecBYtmssmr5IQ"

# NEW WORKING PROXY
PROXY_URL = "http://uparhknj:u5ok7mr7s22l@84.247.60.125:6095/"

DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# =========================================================
# UPDATE YT-DLP
# =========================================================

def update_ytdlp():
    try:
        logger.info("Updating yt-dlp...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]
        )
    except Exception as e:
        logger.error(f"yt-dlp update error: {e}")

# =========================================================
# MAIN KEYBOARD
# =========================================================

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("📺 YouTube Download"),
                KeyboardButton("🎵 TikTok Download"),
            ],
            [
                KeyboardButton("📘 Facebook Download"),
                KeyboardButton("🔍 Music Search"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🚀 Ultimate Downloader Bot\n\n"
        "👇 Mode တစ်ခုရွေးပါ",
        reply_markup=get_main_keyboard()
    )

# =========================================================
# YTDLP OPTIONS
# =========================================================

def get_ydl_opts(format_type):

    opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",

        "restrictfilenames": True,
        "noplaylist": True,

        "quiet": True,

        "geo_bypass": True,

        "proxy": PROXY_URL,

        "socket_timeout": 60,

        "retries": 15,
        "fragment_retries": 15,
        "extractor_retries": 15,
        "file_access_retries": 10,

        "nocheckcertificate": True,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android",
                    "ios",
                    "web"
                ],

                "player_skip": [
                    "configs"
                ],
            }
        },

        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/19.09.37 "
                "(Linux; U; Android 11) gzip"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # =========================
    # FORMAT
    # =========================

    if format_type == "yt_mp3":
        opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"

    elif format_type == "yt_4k":
        opts["format"] = (
            "bestvideo[height<=2160][ext=mp4]+"
            "bestaudio[ext=m4a]/best"
        )

    elif format_type == "yt_1080":
        opts["format"] = (
            "bestvideo[height<=1080][ext=mp4]+"
            "bestaudio[ext=m4a]/best"
        )

    elif format_type == "yt_720":
        opts["format"] = (
            "bestvideo[height<=720][ext=mp4]+"
            "bestaudio[ext=m4a]/best"
        )

    elif format_type == "yt_360":
        opts["format"] = (
            "bestvideo[height<=360][ext=mp4]+"
            "bestaudio[ext=m4a]/best"
        )

    elif format_type == "tt_nowm":
        opts["format"] = "bestvideo+bestaudio/best"

    elif format_type == "tt_wm":
        opts["format"] = "worst/best"

    elif format_type == "fb":
        opts["format"] = "best[ext=mp4]/best"

    return opts

# =========================================================
# HANDLE BUTTONS
# =========================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    user_id = str(update.effective_user.id)

    # =========================================
    # NAVIGATION
    # =========================================

    if data.startswith("nav|"):

        _, page, search = data.split("|")

        await query.edit_message_text("🔄 Loading...")

        await search_music(
            query.message,
            search,
            int(page)
        )

        return

    # =========================================
    # MUSIC SELECT
    # =========================================

    if data.startswith("music|"):

        video_id = data.split("|")[1]

        url = f"https://www.youtube.com/watch?v={video_id}"

        context.user_data[user_id] = {
            "url": url
        }

        data = "yt_mp3"

    # =========================================
    # URL
    # =========================================

    if (
        user_id not in context.user_data
        or "url" not in context.user_data[user_id]
    ):
        await query.edit_message_text(
            "❌ Session Expired"
        )
        return

    url = context.user_data[user_id]["url"]

    await query.edit_message_text(
        "📥 Downloading..."
    )

    try:

        ydl_opts = get_ydl_opts(data)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)

            title = info.get(
                "title",
                "Media"
            )

        # =========================
        # FIX EXTENSION
        # =========================

        if data == "yt_mp3":

            if not os.path.exists(filename):

                filename = (
                    os.path.splitext(filename)[0]
                    + ".m4a"
                )

        else:

            if not os.path.exists(filename):

                filename = (
                    os.path.splitext(filename)[0]
                    + ".mp4"
                )

        # =========================
        # SEND FILE
        # =========================

        with open(filename, "rb") as media:

            if data == "yt_mp3":

                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=media,
                    caption=f"🎵 {title}"
                )

            else:

                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=media,
                    caption=f"🎬 {title}"
                )

        # =========================
        # DELETE FILE
        # =========================

        if os.path.exists(filename):
            os.remove(filename)

        await query.message.delete()

    except yt_dlp.utils.DownloadError as e:

        logger.error(e)

        text = str(e)

        if (
            "Sign in to confirm you're not a bot" in text
            or "403" in text
        ):

            msg = (
                "❌ YouTube blocked request\n\n"
                "Residential Proxy လိုအပ်နိုင်ပါတယ်"
            )

        else:

            msg = "❌ Download Failed"

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=msg
        )

    except Exception as e:

        logger.error(e)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Unknown Error"
        )

# =========================================================
# HANDLE MESSAGE
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = str(update.effective_user.id)

    text = update.message.text.strip()

    # =========================================
    # MENU
    # =========================================

    if text == "📺 YouTube Download":

        await update.message.reply_text(
            "📺 YouTube Link ပို့ပါ"
        )

        return

    elif text == "🎵 TikTok Download":

        await update.message.reply_text(
            "🎵 TikTok Link ပို့ပါ"
        )

        return

    elif text == "📘 Facebook Download":

        await update.message.reply_text(
            "📘 Facebook Link ပို့ပါ"
        )

        return

    elif text == "🔍 Music Search":

        await update.message.reply_text(
            "🔍 Song Name ရိုက်ပါ"
        )

        return

    # =========================================
    # LINK
    # =========================================

    if text.startswith("http://") or text.startswith("https://"):

        context.user_data[user_id] = {
            "url": text
        }

        # =========================
        # TIKTOK
        # =========================

        if "tiktok.com" in text:

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔥 No Watermark",
                        callback_data="tt_nowm"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📁 With Watermark",
                        callback_data="tt_wm"
                    )
                ],
            ]

        # =========================
        # FACEBOOK
        # =========================

        elif (
            "facebook.com" in text
            or "fb.watch" in text
        ):

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📘 Download Video",
                        callback_data="fb"
                    )
                ]
            ]

        # =========================
        # YOUTUBE
        # =========================

        else:

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🎵 MP3",
                        callback_data="yt_mp3"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "💎 4K",
                        callback_data="yt_4k"
                    ),

                    InlineKeyboardButton(
                        "✨ 1080P",
                        callback_data="yt_1080"
                    ),
                ],

                [
                    InlineKeyboardButton(
                        "📁 720P",
                        callback_data="yt_720"
                    ),

                    InlineKeyboardButton(
                        "📁 360P",
                        callback_data="yt_360"
                    ),
                ],
            ]

        keyboard.append(
            [
                InlineKeyboardButton(
                    "💬 Admin",
                    url="https://t.me/mgthantIT"
                )
            ]
        )

        await update.message.reply_text(
            "✅ Quality ရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =========================================
    # MUSIC SEARCH
    # =========================================

    loading = await update.message.reply_text(
        "🔍 Searching..."
    )

    await search_music(
        loading,
        text,
        0
    )

# =========================================================
# SEARCH MUSIC
# =========================================================

async def search_music(message_obj, query, page=0):

    opts = {
        "quiet": True,

        "extract_flat": "in_playlist",

        "playlistend": 20,

        "proxy": PROXY_URL,

        "geo_bypass": True,
    }

    try:

        with yt_dlp.YoutubeDL(opts) as ydl:

            results = ydl.extract_info(
                f"ytsearch20:{query}",
                download=False
            )

            songs = results.get(
                "entries",
                []
            )

        if not songs:

            await message_obj.edit_text(
                "❌ No Results"
            )

            return

        items_per_page = 5

        start = page * items_per_page

        end = start + items_per_page

        current = songs[start:end]

        keyboard = []

        for idx, song in enumerate(current, start=start + 1):

            title = song.get(
                "title",
                "Unknown"
            )

            if len(title) > 35:
                title = title[:35] + "..."

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{idx}. {title}",
                        callback_data=f"music|{song.get('id')}"
                    )
                ]
            )

        # =========================
        # NAVIGATION
        # =========================

        nav = []

        if page > 0:

            nav.append(
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"nav|{page-1}|{query}"
                )
            )

        if end < len(songs):

            nav.append(
                InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=f"nav|{page+1}|{query}"
                )
            )

        if nav:
            keyboard.append(nav)

        keyboard.append(
            [
                InlineKeyboardButton(
                    "💬 Admin",
                    url="https://t.me/mgthantIT"
                )
            ]
        )

        await message_obj.edit_text(
            f"🎵 Search Results\n\nPage {page+1}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:

        logger.error(e)

        await message_obj.edit_text(
            "❌ Search Failed"
        )

# =========================================================
# MAIN
# =========================================================

def main():

    update_ytdlp()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .proxy(PROXY_URL)
        .get_updates_proxy(PROXY_URL)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_handler(
        CallbackQueryHandler(button_callback)
    )

    print("🚀 BOT RUNNING...")

    app.run_polling()

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
