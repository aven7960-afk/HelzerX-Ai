from __future__ import annotations

import asyncio
import time
from typing import Any

import discord

from .context import discord_context, scope_for
from .gemini import GeminiProvider
from .memory import MemoryStore
from .prompts import build_system_prompt
from .tools import HIGH_RISK, execute, tool_specs
from .triggers import should_respond, strip_trigger


class ConfirmationView(discord.ui.View):
    def __init__(self, agent, key: str):
        super().__init__(timeout=90)
        self.agent = agent
        self.key = key

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        pending = self.agent.pending.pop(self.key, None)
        if not pending:
            await interaction.followup.send("That confirmation expired.", ephemeral=True)
            return
        result = await self.agent.execute_pending(pending)
        await interaction.followup.send(self.agent.result_text(result), ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.agent.pending.pop(self.key, None)
        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.stop()


class HelzerAgent:
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.gemini = GeminiProvider(settings.gemini_api_key, settings.gemini_model)
        self.memory = MemoryStore(settings.database_path, settings.max_memory_messages)
        self.pending: dict[str, dict[str, Any]] = {}
        self._rate_lock = asyncio.Lock()
        self._last_request: dict[int, float] = {}

    def authorized(self, member: discord.Member) -> bool:
        if member.id in self.settings.owner_ids or member.guild_permissions.administrator:
            return True
        return bool({r.id for r in member.roles} & self.settings.allowed_role_ids)

    async def handle_message(self, message: discord.Message):
        if message.author.bot or not should_respond(message, self.bot):
            return
        if self.settings.dm_only and message.guild is not None:
            return
        prompt = strip_trigger(message.content, self.bot).strip()
        if not prompt:
            prompt = "Talk naturally with me and help me with what I need."
        async with self._rate_lock:
            now = time.monotonic()
            previous = self._last_request.get(message.author.id, 0)
            if now - previous < 1.0:
                return
            self._last_request[message.author.id] = now
        async with message.channel.typing():
            try:
                result = await self.respond(message, prompt)
            except Exception:
                result = "I hit an internal error while processing that. Check the bot logs for the exact failure."
            if isinstance(result, discord.ui.View):
                await message.reply("That action needs your confirmation.", view=result, mention_author=False)
            else:
                await self._send_text(message, result)

    async def _send_text(self, message, text: str):
        if len(text) <= 1900:
            await message.reply(text, mention_author=False)
            return
        for start in range(0, len(text), 1900):
            await message.reply(text[start:start + 1900], mention_author=False)

    async def respond(self, message: discord.Message, prompt: str):
        scope = scope_for(message)
        history = await self.memory.recent(scope)
        contents: list[Any] = []
        for role, content in history:
            contents.append(discord_to_gemini_content(role, content))
        current = discord_context(message) + "\nUser request: " + prompt
        contents.append(discord_to_gemini_content("user", current))
        guild_name = message.guild.name if message.guild else None
        system = build_system_prompt(self.settings.timezone, guild_name)
        tools = tool_specs() if message.guild else []

        for _ in range(self.settings.max_tool_rounds):
            response = await self.gemini.generate(contents, system, tools)
            calls = self.gemini.function_calls(response)
            if not calls:
                answer = self.gemini.text(response) or "I’m here. Tell me what you need."
                await self.memory.add(scope, message.author.id, "user", prompt, time.time())
                await self.memory.add(scope, message.author.id, "assistant", answer, time.time())
                return answer

            model_content = response.candidates[0].content
            contents.append(model_content)
            for call in calls:
                name = call.name
                args = dict(call.args or {})
                if name in HIGH_RISK:
                    if not message.guild or not isinstance(message.author, discord.Member) or not self.authorized(message.author):
                        result = {"ok": False, "error": "The requester is not authorized for this server action."}
                        contents.append(self.gemini.function_result(name, result))
                        continue
                    key = f"{message.id}:{name}:{time.time_ns()}"
                    self.pending[key] = {"message": message, "name": name, "args": args}
                    return ConfirmationView(self, key)
                try:
                    result = await execute(message, name, args)
                except Exception as exc:
                    result = {"ok": False, "error": str(exc)}
                contents.append(self.gemini.function_result(name, result))

        return "I stopped the action chain because it reached the safety limit."

    async def execute_pending(self, pending: dict[str, Any]):
        message = pending["message"]
        try:
            return await execute(message, pending["name"], pending["args"])
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def result_text(result: dict[str, Any]) -> str:
        if result.get("ok"):
            return f"Done. `{result.get('action', 'action completed')}` completed successfully."
        return f"I couldn't complete that: {result.get('error', 'unknown error')}"


def discord_to_gemini_content(role: str, text: str):
    from google.genai import types
    return types.Content(role="user" if role == "user" else "model", parts=[types.Part.from_text(text=text)])
