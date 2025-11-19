import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from database import add_payment, get_monthly_report

# Load environment variable
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing from .env")

# States for conversation
AMOUNT, METHOD = range(2)
user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Welcome! Use /add to log a payment or /report YYYY-MM to see monthly stats."
        )
    else:
        print("No message in this update")

# /add payment flow
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Enter payment amount (e.g. 82.50):"
        )
    else:
        print("No message in this update")
    return AMOUNT

async def add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            user_data[update.effective_user.id] = {"amount": float(update.message.text)}
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
            return AMOUNT

        reply_keyboard = [["Terminal", "Cash App", "Venmo", "Cash", "Other"]]
        await update.message.reply_text(
            "Select payment method:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
    else:
        print("No message in this update")
    return METHOD

async def add_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        uid = update.effective_user.id
        method = update.message.text
        amount = user_data[uid]["amount"]
        user = update.message.from_user.username or update.message.from_user.first_name
        add_payment(amount, method, user)

        await update.message.reply_text(f"✅ Recorded: ${amount:.2f} via {method}")
    else:
        print("No message in this update")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("❌ Payment entry canceled.")
    else:
        print("No message in this update")
    return ConversationHandler.END

# /report YYYY-MM
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        if context.args:
            month = context.args[0]
        else:
            await update.message.reply_text("Please provide a month like: /report 2025-11")
            return

        rows = get_monthly_report(month)
        if not rows:
            await update.message.reply_text("No records found.")
            return

        total = sum(r[2] for r in rows)
        breakdown = {}
        for r in rows:
            breakdown[r[3]] = breakdown.get(r[3], 0) + r[2]

        summary = f"📊 Report for {month}\nTotal: ${total:.2f}\n"
        for method, amt in breakdown.items():
            summary += f"• {method}: ${amt:.2f}\n"

        await update.message.reply_text(summary)
    else:
        print("No message in this update")

# Main entry
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
            METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_method)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()