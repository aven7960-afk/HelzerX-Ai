from __future__ import annotations


def should_respond(message, bot) -> bool:
    if getattr(message.author, "bot", False):
        return False
    if message.guild is None:
        return True
    if getattr(bot, "user", None) and any(u.id == bot.user.id for u in getattr(message, "mentions", [])):
        return True
    if "helzer" in (message.content or "").lower():
        return True
    reference = getattr(message, "reference", None)
    resolved = getattr(reference, "resolved", None)
    bot_user = getattr(bot, "user", None)
    return bool(bot_user and resolved and getattr(getattr(resolved, "author", None), "id", None) == bot_user.id)


def strip_trigger(content: str, bot) -> str:
    text = content or ""
    user = getattr(bot, "user", None)
    if user:
        text = text.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "")
    import re
    text = re.sub(r"\bhelzer\b", "", text, flags=re.IGNORECASE)
    return " ".join(text.replace(",", " ").split()).strip()
