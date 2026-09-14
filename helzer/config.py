from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv_ints(value: str) -> set[int]:
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if item:
            try:
                result.add(int(item))
            except ValueError:
                pass
    return result


@dataclass(frozen=True)
class Settings:
    discord_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_thinking_level: str = "low"
    timezone: str = "Asia/Colombo"
    owner_ids: set[int] = field(default_factory=set)
    allowed_role_ids: set[int] = field(default_factory=set)
    database_path: str = "data/helzer.db"
    max_memory_messages: int = 40
    max_tool_rounds: int = 5
    dm_only: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not token:
            raise RuntimeError("DISCORD_TOKEN is missing")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is missing")
        thinking = os.getenv("GEMINI_THINKING_LEVEL", "low").strip().lower()
        if thinking not in {"low", "medium", "high"}:
            thinking = "low"
        return cls(
            discord_token=token,
            gemini_api_key=key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
            gemini_thinking_level=thinking,
            timezone=os.getenv("HELZER_TIMEZONE", "Asia/Colombo").strip() or "Asia/Colombo",
            owner_ids=_csv_ints(os.getenv("HELZER_OWNER_IDS", "")),
            allowed_role_ids=_csv_ints(os.getenv("HELZER_ALLOWED_ROLE_IDS", "")),
            database_path=os.getenv("HELZER_DATABASE", "data/helzer.db").strip() or "data/helzer.db",
            max_memory_messages=max(10, int(os.getenv("HELZER_MEMORY_MESSAGES", "40"))),
            max_tool_rounds=max(1, int(os.getenv("HELZER_MAX_TOOL_ROUNDS", "5"))),
            dm_only=os.getenv("HELZER_DM_ONLY", "false").lower() in {"1", "true", "yes"},
        )
