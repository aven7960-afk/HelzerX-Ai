from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from helzer.agent import HelzerAgent
from helzer.context import scope_for
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


@bot.tree.command(name="helzer", description="Talk to Helzer AI")
@app_commands.describe(message="What you want Helzer to help with")
async def helzer_command(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    try:
        result = await bot.agent.respond(interaction, message)
        if isinstance(result, discord.ui.View):
            await interaction.followup.send("This action needs confirmation.", view=result, ephemeral=True)
        else:
            await interaction.followup.send(result)
    except Exception:
        log.exception("Slash command failed")
        await interaction.followup.send("I couldn't process that request. Check the bot logs.", ephemeral=True)


@bot.tree.command(name="forget", description="Clear your Helzer conversation memory in this scope")
async def forget_command(interaction: discord.Interaction):
    await bot.agent.memory.clear(scope_for(interaction))
    await interaction.response.send_message("Your conversation memory for this scope has been cleared.", ephemeral=True)


@bot.tree.command(name="ping", description="Check whether Helzer is online")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong — {round(bot.latency * 1000)}ms", ephemeral=True)


bot.run(settings.discord_token)
