print("Bot jalan!")

TOKEN = "9004951350:AAGS0JLBbQ7wpEdhLN-hjC5O4gERFrZbBrI"

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Bot udah jalan ✅")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
