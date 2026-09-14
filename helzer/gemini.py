from __future__ import annotations

import asyncio
from typing import Any

from google import genai
from google.genai import types


class GeminiProvider:
    """Gemini adapter with native multimodal content and function calling."""

    def __init__(self, api_key: str, model: str):
        self.model = model
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

    async def generate(self, contents: list[Any], system_instruction: str, tools=None):
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=4096,
        )
        if tools:
            declarations = self._function_declarations(tools)
            if declarations:
                config.tools = [types.Tool(function_declarations=declarations)]
        return await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

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
        return types.Part.from_function_response(name=name, response=result)
