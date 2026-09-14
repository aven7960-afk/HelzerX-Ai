# Helzer AI

Helzer is a conversational Discord AI assistant powered by the Gemini API. It is designed to feel natural in English, Sinhala, Singlish, and mixed-language conversations while retaining recent conversational memory and safely using Discord tools when requested.

## Features

- Natural multi-turn conversation and persistent SQLite memory
- Sinhala, Singlish, English, and mixed-language understanding
- Trigger by `Helzer`, bot mention, reply to Helzer, or DM
- Context from replies, mentions, channel, server, and requester IDs
- Gemini function calling for Discord actions
- Server/member inspection
- Messaging and DMs
- Timeout, kick, ban, unban, role management
- Channel creation, deletion, rename, lock/unlock, slowmode
- Message purge
- Confirmation UI for destructive actions
- Configurable owner/role authorization
- Docker deployment
- No giveaway functionality; this repository is Helzer AI only

## Requirements

- Python 3.12+
- A Discord bot application with Message Content and Server Members intents enabled as required by your deployment
- A Gemini API key

Google's current Gemini documentation recommends the Google GenAI SDK and supports function calling for connecting the model to application tools. See the official Gemini documentation before selecting a model for production. citehttps://ai.google.dev/gemini-api/docs

## Setup

```bash
git clone https://github.com/aven7960-afk/HelzerX-Ai.git
cd HelzerX-Ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set at minimum:

```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

For server actions, configure the user IDs or role IDs allowed to perform administrative actions:

```env
HELZER_OWNER_IDS=123456789012345678
HELZER_ALLOWED_ROLE_IDS=123456789012345678
```

Start:

```bash
python main.py
```

## Docker

```bash
docker compose up -d --build
```

The SQLite database is stored under `./data` and is not committed to Git.

## Discord permissions

Give the bot only the permissions it actually needs. Server-management tools depend on the bot's own Discord permissions and role hierarchy. A Gemini tool call never bypasses Discord permissions.

Destructive actions are presented for confirmation before execution. The bot also checks the requester's configured owner/admin/role authorization for high-risk operations.

## Privacy

Conversation memory is stored locally in SQLite. Do not commit `.env` or the database. If you deploy publicly, document your own retention policy and comply with applicable privacy requirements.

## License

Add the license you want to use before publishing a formal release.
