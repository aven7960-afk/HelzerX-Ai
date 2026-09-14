from __future__ import annotations

import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from helzer.agent import HelzerAgent
from helzer.config import Settings

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("helzer")


class HelzerBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=None)
        self.settings = settings
        self.agent = HelzerAgent(self, settings)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        log.info("Logged in as %s (%s) in %s guild(s)", self.user, self.user.id, len(self.guilds))

    async def on_message(self, message: discord.Message):
        await self.agent.handle_message(message)

    async def close(self):
        self.agent.gemini.client.close()
        await super().close()


settings = Settings.from_env()
bot = HelzerBot(settings)
bot.run(settings.discord_token)
