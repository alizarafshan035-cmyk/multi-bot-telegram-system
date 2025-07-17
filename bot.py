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

        # Load models configuration
        models_config = config.get('models', [])
        if not models_config:
            sys.exit("❌ No 'models' configuration found in JSON file.")

        # Create models lookup dictionary
        models_dict = {model['name']: model for model in models_config}

        # Load bots configuration
        bot_configs = config.get('bots', [])
        if not bot_configs:
            sys.exit("❌ No 'bots' configuration found in JSON file.")

        # Validate that all bots reference valid models
        for bot_config in bot_configs:
            model_name = bot_config.get('model')
            if model_name not in models_dict:
                sys.exit(f"❌ Bot '{bot_config.get('name')}' references unknown model '{model_name}'")

        # Support environment variables for API keys in models
        for model in models_dict.values():
            if model.get('type') == 'openai' and not model.get('api_key'):
                env_key = f"{model.get('name', 'model').upper()}_API_KEY"
                model['api_key'] = os.getenv(env_key, '')

        return bot_configs, models_dict

    except FileNotFoundError:
        sys.exit(f"❌ Bot configuration file not found: {CONFIG_JSON}")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Invalid JSON in bot configuration file: {e}")
    except Exception as e:
        sys.exit(f"❌ Error loading bot configuration: {e}")



def call_ollama(prompt: str, model_config: dict, system_prompt: str, logger) -> str:
    """Call Ollama API using model configuration"""
    base_url = model_config.get('base_url', OLLAMA_API_URL)  # Fallback to env variable
    model_id = model_config['model_id']

    payload = {
        "model": model_id,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(f"{base_url}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "No response received from Ollama.")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return f"Error calling Ollama: {e}"

def call_openai_compatible(prompt: str, model_config: dict, system_prompt: str, logger) -> str:
    """Call OpenAI compatible API using model configuration"""
    base_url = model_config['base_url']
    model_id = model_config['model_id']
    api_key = model_config.get('api_key', '')

    if not api_key:
        logger.error("No API key provided for OpenAI compatible API")
        return "Error: No API key configured for OpenAI compatible API"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error calling OpenAI compatible API: {e}")
        return f"Error calling OpenAI compatible API: {e}"

def call_ai_model(prompt: str, bot_config: dict, models_dict: dict, logger) -> str:
    """Call the appropriate AI API based on model configuration"""
    model_name = bot_config['model']
    model_config = models_dict[model_name]
    system_prompt = bot_config.get('system_prompt', 'You are a helpful assistant.')

    api_type = model_config['type'].lower()

    if api_type == 'ollama':
        return call_ollama(prompt, model_config, system_prompt, logger)
    elif api_type == 'openai':
        return call_openai_compatible(prompt, model_config, system_prompt, logger)
    else:
        logger.error(f"Unsupported API type: {api_type}")
        return f"Error: Unsupported API type: {api_type}"

def create_message_handler(bot_config, models_dict, logger):
    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if message is None or message.text is None:
            return

        message_text = message.text.strip()
        bot_info = await context.bot.get_me()
        if not bot_info.username:
            logger.error("Bot username is empty or None")
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
        reply = call_ai_model(prompt, bot_config, models_dict, logger)
        await message.reply_text(reply)

    return message_handler

def run_bot(bot_config, models_dict):
    token = bot_config.get('token', '')
    bot_name = bot_config.get('name', 'unnamed')

    # Set up bot-specific logging
    logging.basicConfig(
        format=f'%(asctime)s - {bot_name} - %(levelname)s - %(message)s',
        level=logging.INFO,
        force=True  # This forces reconfiguration in each process
    )
    logger = logging.getLogger(bot_name)

    if not token:
        logger.error(f"No token provided for bot: {bot_name}")
        return

    try:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), create_message_handler(bot_config, models_dict, logger)))

        logger.info(f"✅ {bot_name} is running...")
        app.run_polling()

    except Exception as e:
        logger.error(f"Error running bot {bot_name}: {e}")

def main():
    # Set up main process logging
    logging.basicConfig(
        format='%(asctime)s - MAIN - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main_logger = logging.getLogger('MAIN')

    bot_configs, models_dict = load_bot_configs()

    main_logger.info(f"Starting {len(bot_configs)} bot(s) in separate processes...")

    processes = []
    for config in bot_configs:
        process = multiprocessing.Process(target=run_bot, args=(config, models_dict))
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        main_logger.info("\n🛑 Shutting down all bots...")
        for process in processes:
            process.terminate()
            process.join()

if __name__ == '__main__':
    main()