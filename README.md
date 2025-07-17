# Multi-Bot Telegram System

A Python-based system for running multiple Telegram bots simultaneously, each with their own personality and AI model, powered by Ollama.

## Features

- 🤖 **Multiple Bots**: Run multiple Telegram bots concurrently in separate processes
- 🎭 **Individual Personalities**: Each bot can have its own AI model and system prompt
- 🔄 **Process Isolation**: Each bot runs in its own process for stability and independence
- 💬 **Smart Chat Handling**: Supports both private chats and group chats (with @mentions)
- 🔧 **Easy Configuration**: JSON-based configuration with environment variable support
- 🦙 **Ollama Integration**: Uses local Ollama installation for AI responses

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Telegram Bot API tokens (one for each bot)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shp-bots
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install python-telegram-bot requests
   ```

4. **Set up Ollama**
   - Install Ollama from [ollama.ai](https://ollama.ai/)
   - Pull your desired models:
     ```bash
     ollama pull llama3
     ollama pull gemma3:4b
     ollama pull codellama
     ```

## Configuration

### Environment Variables (Optional)

Create a `.env` file or set environment variables:

```env
CONFIG_JSON=config.json                    # Path to bot configuration file (default: config.json)
OLLAMA_API_URL=http://localhost:11434      # Ollama API URL (default: http://localhost:11434)
```

### Bot Configuration

Create a `config.json` file with your bot configurations:

```json
{
  "bots": [
    {
      "name": "assistant_bot",
      "token": "YOUR_BOT_TOKEN_HERE",
      "model": "llama3",
      "system_prompt": "You are a helpful assistant."
    },
    {
      "name": "coding_bot",
      "token": "YOUR_SECOND_BOT_TOKEN",
      "model": "codellama",
      "system_prompt": "You are a coding expert who helps with programming tasks."
    }
  ]
}
```

#### Configuration Options

- **`name`**: Friendly name for the bot (used in logs)
- **`token`**: Telegram Bot API token from [@BotFather](https://t.me/botfather)
- **`model`**: Ollama model to use (e.g., `llama3`, `gemma3:4b`, `codellama`)
- **`system_prompt`**: Personality and behavior instructions for the bot

## Usage

### Running the Bots

```bash
python bot.py
```

This will start all configured bots in separate processes. You'll see output like:

```
✅ Starting 2 bot(s) in separate processes...
✅ assistant_bot is running...
✅ coding_bot is running...
```

### Stopping the Bots

Press `Ctrl+C` to gracefully shut down all bots:

```
🛑 Shutting down all bots...
```

### Chat Interaction

**Private Chats**: Send any message directly to the bot

**Group Chats**: Mention the bot with `@botusername` followed by your message

Example:
```
@assistant_bot What's the weather like today?
```

## Development

### VS Code/Cursor Setup

The project includes a launch configuration for debugging:

- Press `F5` to run the bot with the debugger attached
- Breakpoints and debugging work as expected

### Project Structure

```
shp-bots/
├── bot.py              # Main bot application
├── config.json         # Bot configurations (gitignored)
├── .env               # Environment variables (gitignored)
├── .vscode/
│   └── launch.json    # VS Code debug configuration
├── .venv/             # Virtual environment (gitignored)
└── README.md          # This file
```

## Adding New Bots

1. **Create a new Telegram bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Copy the provided API token

2. **Add to configuration**:
   ```json
   {
     "bots": [
       // ... existing bots ...
       {
         "name": "new_bot",
         "token": "NEW_BOT_TOKEN_HERE",
         "model": "llama3",
         "system_prompt": "Your custom personality here."
       }
     ]
   }
   ```

3. **Restart the application**:
   ```bash
   python bot.py
   ```

## Troubleshooting

### Common Issues

- **"Bot configuration file not found"**: Ensure `config.json` exists and is valid JSON
- **"No token provided for bot"**: Check that each bot has a valid `token` field
- **"Error calling Ollama"**: Verify Ollama is running (`ollama serve`) and the model exists
- **Connection errors**: Check that Ollama is accessible at the configured URL

### Logs

Each bot logs with its own name prefix to help identify issues:

```
2024-01-01 12:00:00 - assistant_bot - INFO - ✅ Starting bot: assistant_bot
2024-01-01 12:00:01 - coding_bot - INFO - ✅ Starting bot: coding_bot
```

## Security Notes

- Keep your bot tokens secure and never commit them to version control
- The `config.json` file is gitignored to prevent accidental token exposure
- Consider using environment variables for tokens in production environments

## License

This project is open source. See the license file for details.
