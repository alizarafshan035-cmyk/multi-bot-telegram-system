import os
import sys
import json
import logging
import requests
import multiprocessing
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

CONFIG_JSON = os.getenv('CONFIG_JSON', 'config.json')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')

def load_bot_configs():
    try:
        with open(CONFIG_JSON, 'r') as f:
            config = json.load(f)
        bot_configs = config.get('bots', [])
        if not bot_configs:
            sys.exit("❌ No 'bots' configuration found in JSON file.")
        return bot_configs
    except FileNotFoundError:
        sys.exit(f"❌ Bot configuration file not found: {CONFIG_JSON}")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Invalid JSON in bot configuration file: {e}")
    except Exception as e:
        sys.exit(f"❌ Error loading bot configuration: {e}")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def call_ollama(prompt: str, model: str, system_prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
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

def create_message_handler(bot_config):
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
        reply = call_ollama(
            prompt,
            bot_config.get('model', 'llama3'),
            bot_config.get('system_prompt', 'You are a helpful assistant.')
        )
        await message.reply_text(reply)

    return message_handler

def run_bot(bot_config):
    token = bot_config.get('token', '')
    bot_name = bot_config.get('name', 'unnamed')

    if not token:
        logging.error(f"No token provided for bot: {bot_name}")
        return

    try:
        logging.basicConfig(
            format=f'%(asctime)s - {bot_name} - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), create_message_handler(bot_config)))

        print(f"✅ {bot_name} is running...")
        app.run_polling()

    except Exception as e:
        logging.error(f"Error running bot {bot_name}: {e}")

def main():
    bot_configs = load_bot_configs()

    print(f"✅ Starting {len(bot_configs)} bot(s) in separate processes...")

    processes = []
    for config in bot_configs:
        process = multiprocessing.Process(target=run_bot, args=(config,))
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all bots...")
        for process in processes:
            process.terminate()
            process.join()

if __name__ == '__main__':
    main()