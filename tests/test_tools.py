from helzer.tools import tool_specs


LARGE_DISCORD_ID = "1548945777513201694"


def test_discord_id_tool_schema_uses_strings():
    specs = {tool["name"]: tool for tool in tool_specs()}
    for name, parameter in (
        ("member_info", "user_id"),
        ("send_message", "channel_id"),
        ("send_dm", "user_id"),
        ("timeout_member", "user_id"),
        ("ban_member", "user_id"),
        ("kick_member", "user_id"),
        ("unban_member", "user_id"),
        ("add_role", "user_id"),
        ("remove_role", "role_id"),
        ("delete_channel", "channel_id"),
        ("rename_channel", "channel_id"),
        ("lock_channel", "channel_id"),
        ("unlock_channel", "channel_id"),
        ("set_slowmode", "channel_id"),
        ("purge_messages", "channel_id"),
    ):
        assert specs[name]["parameters"]["properties"][parameter]["type"] == "string"


def test_large_discord_id_stays_exact_as_string():
    specs = {tool["name"]: tool for tool in tool_specs()}
    schema = specs["send_dm"]["parameters"]["properties"]["user_id"]
    assert schema["type"] == "string"
    assert LARGE_DISCORD_ID == str(LARGE_DISCORD_ID)
