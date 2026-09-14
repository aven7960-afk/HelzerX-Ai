from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

from google import genai
from google.genai import types

log = logging.getLogger("helzer.gemini")


class GeminiQuotaError(RuntimeError):
    """Raised when Gemini rejects a request because the project quota is exhausted."""


class GeminiProvider:
    """Gemini adapter with native multimodal content and function calling."""

    VALID_THINKING_LEVELS = {"minimal", "low", "medium", "high"}

    def __init__(self, api_key: str, model: str, thinking_level: str = "low"):
        self.model = model
        self.thinking_level = thinking_level if thinking_level in self.VALID_THINKING_LEVELS else "low"
        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _function_declarations(tools: list[dict[str, Any]]) -> list[types.FunctionDeclaration]:
        declarations = []
        for tool in tools:
            if tool.get("type") != "function":
                continue
            declarations.append(types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {"type": "object", "properties": {}}),
            ))
        return declarations

    @staticmethod
    def _is_quota_exhausted(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(marker in message for marker in (
            "quota exceeded",
            "free_tier_requests",
            "generate requests per day",
            "requests per day",
            "daily quota",
            "resource_exhausted",
        ))

    async def generate(self, contents: list[Any], system_instruction: str, tools=None):
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_level=self.thinking_level),
            max_output_tokens=2048,
        )
        if tools:
            declarations = self._function_declarations(tools)
            if declarations:
                config.tools = [types.Tool(function_declarations=declarations)]

        started = time.perf_counter()
        for attempt in range(3):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                log.info(
                    "Gemini response: model=%s thinking=%s latency=%.2fs tools=%s",
                    self.model,
                    self.thinking_level,
                    time.perf_counter() - started,
                    bool(tools),
                )
                return response
            except Exception as exc:
                if self._is_quota_exhausted(exc):
                    log.error("Gemini quota exhausted: model=%s", self.model)
                    raise GeminiQuotaError(
                        f"Gemini quota exhausted for model {self.model}."
                    ) from exc

                status = getattr(exc, "status_code", None)
                message = str(exc).lower()
                transient = status in {429, 500, 502, 503, 504} or any(
                    marker in message for marker in ("429", "500", "502", "503", "504", "unavailable", "temporarily")
                )
                if not transient or attempt == 2:
                    raise
                delay = min(1.5 * (2 ** attempt) + random.uniform(0, 0.25), 4.0)
                log.warning("Transient Gemini failure (%s); retrying in %.2fs", type(exc).__name__, delay)
                await asyncio.sleep(delay)

    @staticmethod
    def parts(response):
        candidate = response.candidates[0] if response.candidates else None
        return list(candidate.content.parts) if candidate and candidate.content else []

    @staticmethod
    def text(response) -> str:
        return (getattr(response, "text", None) or "").strip()

    @staticmethod
    def function_calls(response):
        return [p.function_call for p in GeminiProvider.parts(response) if getattr(p, "function_call", None)]

    @staticmethod
    def function_result(name: str, result: dict[str, Any]):
        return types.Content(
            role="user",
            parts=[types.Part.from_function_response(name=name, response=result)],
        )
