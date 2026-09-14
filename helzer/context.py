from __future__ import annotations


def actor(message):
    return getattr(message, "author", None) or getattr(message, "user", None)


def scope_for(message) -> str:
    user = actor(message)
    guild = getattr(message, "guild", None)
    channel = getattr(message, "channel", None)
    if guild is None:
        return f"dm:{getattr(user, 'id', 0)}"
    return f"guild:{guild.id}:channel:{getattr(channel, 'id', 0)}:user:{getattr(user, 'id', 0)}"


def discord_context(message) -> str:
    user = actor(message)
    guild = getattr(message, "guild", None)
    channel = getattr(message, "channel", None)
    parts = [
        f"requester_id={str(getattr(user, 'id', 0))}",
        f"channel_id={str(getattr(channel, 'id', 0))}",
        f"guild_id={str(getattr(guild, 'id', 0))}",
    ]
    if guild:
        parts.append(f"guild_name={guild.name!r}")
    if getattr(message, "mentions", None):
        parts.append("mentioned_user_ids=" + repr([str(u.id) for u in message.mentions]))
    if getattr(message, "channel_mentions", None):
        parts.append("mentioned_channel_ids=" + repr([str(c.id) for c in message.channel_mentions]))
    reference = getattr(message, "reference", None)
    resolved = getattr(reference, "resolved", None)
    if resolved is not None and getattr(resolved, "content", None):
        author = getattr(resolved, "author", None)
        parts.append(f"replied_message={getattr(author, 'display_name', 'user')!r}: {resolved.content!r}")
    return "Discord context: " + "; ".join(parts)
