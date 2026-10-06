
import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN পাওয়া যায়নি")

db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")
db.commit()


def add_user(user_id, referred_by=None):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, balance, referrals, referred_by) VALUES (?,0,0,?)",
            (user_id, referred_by)
        )

        if referred_by and referred_by != user_id:
            cur.execute(
                "UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id=?",
                (referred_by,)
            )

        db.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    referred_by = None
    if context.args:
        try:
            referred_by = int(context.args[0])
        except:
            pass

    add_user(user_id, referred_by)

    keyboard = [
        ["📋 Tasks", "💰 Balance"],
        ["👥 Refer"]
    ]

    await update.message.reply_text(
        "স্বাগতম! 🎉\n\nকাজ করে পয়েন্ট সংগ্রহ করুন এবং বন্ধুদের Refer করুন।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    text = update.message.text

    if text == "📋 Tasks":
        await update.message.reply_text(
            "📋 Available Tasks\n\n"
            "1️⃣ আমাদের চ্যানেলে Join করুন\n"
            "2️⃣ Task সম্পন্ন করুন\n\n"
            "বর্তমানে Task reward: 0.50 point"
        )

    elif text == "💰 Balance":
        cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cur.fetchone()[0]

        await update.message.reply_text(
            f"💰 আপনার Balance: {balance:.2f} point"
        )

    elif text == "👥 Refer":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={user_id}"

        cur.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
        referrals = cur.fetchone()[0]

        await update.message.reply_text(
            f"👥 আপনার Refer সংখ্যা: {referrals}\n\n"
            f"🔗 আপনার Refer Link:\n{link}\n\n"
            "বন্ধুকে এই লিংক দিলে সে Join করলে আপনি reward পাবেন।"
        )

    else:
        await update.message.reply_text("মেনু থেকে একটি অপশন নির্বাচন করুন।")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot চলছে...")
    app.run_polling()


if __name__ == "__main__":
    main()
