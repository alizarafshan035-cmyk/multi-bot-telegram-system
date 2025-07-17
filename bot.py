import os
import sys
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

CONFIG_JSON = os.getenv('CONFIG_JSON', 'config.json')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', '')

if not OLLAMA_API_URL:
    sys.exit("❌ OLLAMA_API_URL environment variable must be set.")

def load_bot_config():
    try:
        with open(CONFIG_JSON, 'r') as f:
            config = json.load(f)
        bot_config = config.get('bot', {})
        if not bot_config:
            sys.exit("❌ No 'bot' configuration found in JSON file.")
        return bot_config
    except FileNotFoundError:
        sys.exit(f"❌ Bot configuration file not found: {CONFIG_JSON}")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Invalid JSON in bot configuration file: {e}")
    except Exception as e:
        sys.exit(f"❌ Error loading bot configuration: {e}")

bot_config = load_bot_config()
TELEGRAM_BOT_TOKEN = bot_config.get('token', '')
OLLAMA_MODEL = bot_config.get('model', 'llama3')
SYSTEM_PROMPT = bot_config.get('system_prompt', 'You are a helpful assistant.')

if not TELEGRAM_BOT_TOKEN:
    sys.exit("❌ Bot token not found in configuration file.")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

    if message.chat.type in ("group", "supergroup"):
        if f"@{bot_username}" not in message_text.lower():
            return
        prompt = message_text.replace(f"@{bot_username}", "").strip()

    elif message.chat.type == "private":
        prompt = message_text

    else:
        return

    if not prompt:
        await message.reply_text("Please include a prompt.")
        return

    await message.chat.send_action(action="typing")
    reply = call_ollama(prompt)
    await message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()