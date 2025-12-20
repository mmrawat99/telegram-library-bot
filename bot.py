import os
import json
import asyncio
import logging
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)

# ================= FLASK APP =================
app = Flask(__name__)

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")  # ← Replit Secrets mein TOKEN daal do, ya yaha hardcode (naya token daalna mat bhoolna)
STORAGE_CHANNEL_ID = -1003589161556
ADMIN1_USERNAME = "idlikh"
ADMIN2_USERNAME = "dr_rawat93"
DATA_FILE = "data.json"

# ================= DATA =================
DATA = {
    "shreemali_books": {},
    "other_books": {},
    "magazines": {},
    "audio": {},
    "video": {}
}

# ================= LOAD / SAVE =================
def load_data():
    global DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DATA = json.load(f)
    except:
        save_data()

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2, ensure_ascii=False)

# ================= VERIFY STORAGE =================
async def verify_storage(bot):
    changed = False
    async def check_dict(d):
        nonlocal changed
        for k, mid in list(d.items()):
            try:
                await bot.copy_message(
                    chat_id=STORAGE_CHANNEL_ID,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=mid
                )
            except TelegramError:
                del d[k]
                changed = True
            await asyncio.sleep(0.25)
    for year in list(DATA["magazines"].keys()):
        await check_dict(DATA["magazines"][year])
        if not DATA["magazines"][year]:
            del DATA["magazines"][year]
            changed = True
    for key in ["shreemali_books","other_books","audio","video"]:
        await check_dict(DATA[key])
    if changed:
        save_data()
        print("🧹 Missing files cleaned")

# ================= CHANNEL AUTO SAVE =================
async def channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg or not msg.caption or msg.chat_id != STORAGE_CHANNEL_ID:
        return
    parts = [p.strip() for p in msg.caption.split("|")]
    head = parts[0].upper()
    if head == "BOOK" and len(parts) >= 3 and msg.document:
        cat, name = parts[1].upper(), parts[2]
        if cat == "SHREEMALI":
            DATA["shreemali_books"][name] = msg.message_id
        elif cat == "OTHER":
            DATA["other_books"][name] = msg.message_id
    elif head == "MAGAZINE" and len(parts) >= 3 and msg.document:
        year, month = parts[1], parts[2]
        DATA["magazines"].setdefault(year, {})[month] = msg.message_id
    elif head == "AUDIO" and len(parts) >= 2:
        DATA["audio"][parts[1]] = msg.message_id
    elif head == "VIDEO" and len(parts) >= 2:
        DATA["video"][parts[1]] = msg.message_id
    save_data()
    print("✅ Auto saved:", msg.caption)

# ================= MENUS & HANDLERS (exactly same as yours) =================
async def start(update, context):
    context.user_data["lvl"] = "MAIN"
    kb = [
        ["📚 Books","📰 Magazine"],
        ["🎵 Audio","🎬 Video"],
        ["ℹ️ Help"]
    ]
    await update.message.reply_text(
        "📦 Welcome\nOption select karo 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def books_menu(update, context):
    context.user_data["lvl"] = "BOOKS"
    kb = [
        ["SHREEMALI JI BOOKS 🙏","OTHER BOOKS 📚"],
        ["🔙 BACK"]
    ]
    await update.message.reply_text(
        "📚 Books category select karo 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def magazine_year_menu(update, context):
    context.user_data["lvl"] = "MAG_YEAR"
    years = [[str(y)] for y in range(1981, 2011)]
    years.append(["🔙 BACK"])
    await update.message.reply_text(
        "📰 Year select karo 👇",
        reply_markup=ReplyKeyboardMarkup(years, resize_keyboard=True)
    )

async def magazine_month_menu(update, context):
    context.user_data["lvl"] = "MAG_MONTH"
    months = [
        ["January","February","March"],
        ["April","May","June"],
        ["July","August","September"],
        ["October","November","December"],
        ["🔙 BACK"]
    ]
    y = context.user_data["year"]
    await update.message.reply_text(
        f"📰 {y} ke month select karo 👇",
        reply_markup=ReplyKeyboardMarkup(months, resize_keyboard=True)
    )

async def help_menu(update, context):
    context.user_data["lvl"] = "HELP"
    kb = [
        ["📖 Guide","📩 Contact Admin"],
        ["🔙 BACK"]
    ]
    await update.message.reply_text(
        "ℹ️ Help Menu 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def admin_menu(update, context):
    context.user_data["lvl"] = "ADMIN"
    kb = [
        ["📩 Admin M M","📩 Admin VED"],
        ["🔙 BACK"]
    ]
    await update.message.reply_text(
        "Admin select karo 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def audio_menu(update, context):
    context.user_data["lvl"] = "AUDIO"
    kb = [[f"🎵 {n}"] for n in DATA["audio"]] or [["❌ No audio"]]
    kb.append(["🔙 BACK"])
    await update.message.reply_text(
        "🎵 Audio select karo 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def video_menu(update, context):
    context.user_data["lvl"] = "VIDEO"
    kb = [[f"🎬 {n}"] for n in DATA["video"]] or [["❌ No video"]]
    kb.append(["🔙 BACK"])
    await update.message.reply_text(
        "🎬 Video select karo 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def back_button_handler(update, context):
    t = update.message.text
    if t != "🔙 BACK":
        return
    # (tera poora back logic same hai – copy kiya)
    lvl = context.user_data.get("lvl", "MAIN")
    if lvl == "SHREEMALI" or lvl == "OTHER":
        context.user_data["lvl"] = "BOOKS"
        kb = [["SHREEMALI JI BOOKS 🙏","OTHER BOOKS 📚"], ["🔙 BACK"]]
        await update.message.reply_text("📚 Books category select karo 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif lvl == "MAG_MONTH":
        context.user_data["lvl"] = "MAG_YEAR"
        years = [[str(y)] for y in range(1981, 2011)]
        years.append(["🔙 BACK"])
        await update.message.reply_text("📰 Year select karo 👇", reply_markup=ReplyKeyboardMarkup(years, resize_keyboard=True))
    elif lvl == "MAG_YEAR":
        context.user_data["lvl"] = "MAIN"
        kb = [["📚 Books","📰 Magazine"], ["🎵 Audio","🎬 Video"], ["ℹ️ Help"]]
        await update.message.reply_text("📦 Main Menu 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif lvl in ["BOOKS", "AUDIO", "VIDEO"]:
        context.user_data["lvl"] = "MAIN"
        kb = [["📚 Books","📰 Magazine"], ["🎵 Audio","🎬 Video"], ["ℹ️ Help"]]
        await update.message.reply_text("📦 Main Menu 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif lvl == "HELP":
        context.user_data["lvl"] = "MAIN"
        kb = [["📚 Books","📰 Magazine"], ["🎵 Audio","🎬 Video"], ["ℹ️ Help"]]
        await update.message.reply_text("📦 Main Menu 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif lvl == "ADMIN":
        context.user_data["lvl"] = "HELP"
        kb = [["📖 Guide","📩 Contact Admin"], ["🔙 BACK"]]
        await update.message.reply_text("ℹ️ Help Menu 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handler(update, context):
    t = update.message.text
    lvl = context.user_data.get("lvl","MAIN")
    if t=="📚 Books": return await books_menu(update, context)
    if t=="📰 Magazine": return await magazine_year_menu(update, context)
    if t=="🎵 Audio": return await audio_menu(update, context)
    if t=="🎬 Video": return await video_menu(update, context)
    if t=="ℹ️ Help": return await help_menu(update, context)

    if lvl=="BOOKS" and t=="SHREEMALI JI BOOKS 🙏":
        context.user_data["lvl"]="SHREEMALI"
        kb=[[f"📖 {n}"] for n in DATA["shreemali_books"]] or [["❌ No books"]]
        kb.append(["🔙 BACK"])
        return await update.message.reply_text("🙏 Shreemali Books 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    if lvl=="BOOKS" and t=="OTHER BOOKS 📚":
        context.user_data["lvl"]="OTHER"
        kb=[[f"📖 {n}"] for n in DATA["other_books"]] or [["❌ No books"]]
        kb.append(["🔙 BACK"])
        return await update.message.reply_text("📚 Other Books 👇", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    if lvl in ["SHREEMALI","OTHER"] and t.startswith("📖 "):
        name=t[2:]
        mid=DATA["shreemali_books"].get(name) if lvl=="SHREEMALI" else DATA["other_books"].get(name)
        if mid:
            return await context.bot.copy_message(update.effective_chat.id, STORAGE_CHANNEL_ID, mid)

    if lvl=="MAG_YEAR" and t.isdigit():
        context.user_data["year"]=t
        return await magazine_month_menu(update, context)
    if lvl=="MAG_MONTH" and t not in ["🔙 BACK"]:
        y=context.user_data["year"]
        mid=DATA["magazines"].get(y,{}).get(t)
        if mid:
            return await context.bot.copy_message(update.effective_chat.id, STORAGE_CHANNEL_ID, mid)
        return await update.message.reply_text("❌ Is month ki magazine nahi hai")

    if lvl=="AUDIO" and t.startswith("🎵 "):
        name = t[2:]
        mid = DATA["audio"].get(name)
        if mid:
            return await context.bot.copy_message(update.effective_chat.id, STORAGE_CHANNEL_ID, mid)

    if lvl=="VIDEO" and t.startswith("🎬 "):
        name = t[2:]
        mid = DATA["video"].get(name)
        if mid:
            return await context.bot.copy_message(update.effective_chat.id, STORAGE_CHANNEL_ID, mid)

    if lvl=="HELP" and t=="📖 Guide":
        return await update.message.reply_text("🙏 Ye bot M M RAWAT ne bnaya h jisme aap Sadgurudev ke sbhi books magazine or video aaram se receive kr skte h 🙏")
    if lvl=="HELP" and t=="📩 Contact Admin":
        context.user_data["lvl"]="ADMIN"
        return await admin_menu(update, context)

    if lvl=="ADMIN":
        if t=="📩 Admin M M": return await update.message.reply_text(f"https://t.me/{ADMIN1_USERNAME}")
        if t=="📩 Admin VED": return await update.message.reply_text(f"https://t.me/{ADMIN2_USERNAME}")

async def on_startup(application):
    load_data()
    await verify_storage(application.bot)

# ================= APPLICATION SETUP =================
application = Application.builder().token(TOKEN).post_init(on_startup).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_handler))
application.add_handler(MessageHandler(filters.Regex("🔙 BACK"), back_button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("🔙 BACK"), handler))

# ================= WEBHOOK ROUTES =================
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Bot is alive! 🚀"

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
