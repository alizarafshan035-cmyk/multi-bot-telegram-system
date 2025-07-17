import os
import sys
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# === ENVIRONMENT CONFIGURATION ===
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', '')

if not TELEGRAM_BOT_TOKEN or not OLLAMA_API_URL:
    sys.exit("❌ TELEGRAM_BOT_TOKEN and OLLAMA_API_URL environment variables must be set.")

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'You are a helpful assistant.')

# === LOGGING ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === FUNCTION TO QUERY OLLAMA ===
def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL + "/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "No response received from Ollama.")
    except Exception as e:
        logging.error(f"Error calling Ollama: {e}")
        return f"Error calling Ollama: {e}"

# === TELEGRAM HANDLER ===
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message is None or message.text is None:
        return

    message_text = message.text.strip()
    bot_info = await context.bot.get_me()
    if not bot_info.username:
        logging.error("Bot username is empty or None")
        return
    bot_username = bot_info.username.lower()

    # Group chat: only respond if mentioned
    if message.chat.type in ("group", "supergroup"):
        if f"@{bot_username}" not in message_text.lower():
            return
        prompt = message_text.replace(f"@{bot_username}", "").strip()

    # Private chat: respond to all messages
    elif message.chat.type == "private":
        prompt = message_text

    else:
        return  # Skip other chat types like channels

    if not prompt:
        await message.reply_text("Please include a prompt.")
        return

    await message.chat.send_action(action="typing")
    reply = call_ollama(prompt)
    await message.reply_text(reply)

# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("✅ Bot is running...")
    app.run_polling()

# === ENTRY POINT ===
if __name__ == '__main__':
    main()