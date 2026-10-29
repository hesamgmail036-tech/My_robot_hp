import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN", "").strip()

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 راهنما", callback_data="help"),
     InlineKeyboardButton("🛠 مدیریت گروه", callback_data="admin_help")],
    [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("سلام! 👋\nمن ربات مدیریت گروه هستم. از دکمه‌های زیر استفاده کن:", reply_markup=MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "دستورها:\n/start منوی اصلی\n/help راهنما\n/id شناسه‌ها\n\n"
        "مدیریت گروه (فقط مدیر گروه):\n"
        "/ban با ریپلای به پیام کاربر\n"
        "/kick با ریپلای به پیام کاربر\n"
        "/unban USER_ID برای رفع مسدودی\n\n"
        "ربات باید مدیر گروه باشد و مجوز مسدود کردن کاربران داشته باشد."
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"شناسه چت: {update.effective_chat.id}\nشناسه شما: {update.effective_user.id}")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user, msg = update.effective_chat, update.effective_user, update.effective_message
    if not chat or chat.type not in ("group", "supergroup") or not user:
        await msg.reply_text("این دستور را داخل گروه استفاده کن.")
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            await msg.reply_text("فقط مدیر گروه می‌تواند این دستور را اجرا کند.")
            return False
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await msg.reply_text("اول ربات را مدیر گروه کن.")
            return False
        return True
    except Exception:
        await msg.reply_text("نمی‌توانم دسترسی‌ها را بررسی کنم؛ مطمئن شو ربات داخل گروه است.")
        return False

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    msg, chat = update.effective_message, update.effective_chat
    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text("روی پیام کاربر ریپلای کن و /ban بفرست.")
        return
    target = msg.reply_to_message.from_user
    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            await msg.reply_text("نمی‌توانم مدیر گروه را بن کنم.")
            return
        await context.bot.ban_chat_member(chat.id, target.id)
        await msg.reply_text(f"✅ {target.full_name} مسدود شد.")
    except Exception:
        logging.exception("ban failed")
        await msg.reply_text("بن نشد؛ به ربات مجوز مسدود کردن کاربران بده.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    msg, chat = update.effective_message, update.effective_chat
    if not context.args:
        await msg.reply_text("شناسه عددی کاربر را بنویس: /unban USER_ID")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(chat.id, user_id, only_if_banned=True)
        await msg.reply_text("✅ درخواست رفع مسدودی انجام شد.")
    except ValueError:
        await msg.reply_text("شناسه باید عددی باشد؛ نمونه: /unban 123456789")
    except Exception:
        logging.exception("unban failed")
        await msg.reply_text("رفع مسدودی نشد؛ شناسه و دسترسی‌ها را بررسی کن.")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    msg, chat = update.effective_message, update.effective_chat
    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text("روی پیام کاربر ریپلای کن و /kick بفرست.")
        return
    target = msg.reply_to_message.from_user
    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            await msg.reply_text("نمی‌توانم مدیر گروه را اخراج کنم.")
            return
        await context.bot.ban_chat_member(chat.id, target.id)
        await context.bot.unban_chat_member(chat.id, target.id)
        await msg.reply_text(f"👢 {target.full_name} از گروه اخراج شد.")
    except Exception:
        logging.exception("kick failed")
        await msg.reply_text("اخراج نشد؛ دسترسی‌های ربات را بررسی کن.")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "help":
        text = "راهنما:\n/start منو\n/help دستورها\n/id شناسه‌ها"
    elif q.data == "admin_help":
        text = "مدیریت گروه:\nربات را مدیر کن و مجوز مسدود/اخراج اعضا بده.\nبرای بن یا اخراج، روی پیام کاربر ریپلای کن و /ban یا /kick بفرست.\nرفع بن: /unban USER_ID"
    else:
        text = "ربات مدیریت گروه با پایتون."
    await q.edit_message_text(text, reply_markup=MENU)

async def normal_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_chat.type == "private":
        await update.effective_message.reply_text("برای دیدن امکانات، /start را بزن.")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN در تنظیمات امن هاست تنظیم نشده است.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, normal_text))
    app.run_polling()

if __name__ == "__main__":
    main()
