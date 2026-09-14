from __future__ import annotations


def scope_for(message) -> str:
    if message.guild is None:
        return f"dm:{message.author.id}"
    return f"guild:{message.guild.id}:channel:{message.channel.id}:user:{message.author.id}"


def discord_context(message) -> str:
    guild = getattr(message, "guild", None)
    channel = getattr(message, "channel", None)
    parts = [
        f"requester_id={getattr(message.author, 'id', 0)}",
        f"channel_id={getattr(channel, 'id', 0)}",
        f"guild_id={getattr(guild, 'id', 0)}",
    ]
    if guild:
        parts.append(f"guild_name={guild.name!r}")
    if getattr(message, "mentions", None):
        parts.append("mentioned_user_ids=" + repr([u.id for u in message.mentions]))
    if getattr(message, "channel_mentions", None):
        parts.append("mentioned_channel_ids=" + repr([c.id for c in message.channel_mentions]))
    reference = getattr(message, "reference", None)
    resolved = getattr(reference, "resolved", None)
    if resolved is not None and getattr(resolved, "content", None):
        author = getattr(resolved, "author", None)
        parts.append(f"replied_message={getattr(author, 'display_name', 'user')!r}: {resolved.content!r}")
    return "Discord context: " + "; ".join(parts)
