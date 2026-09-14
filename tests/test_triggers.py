from helzer.triggers import should_respond, strip_trigger


class Bot:
    user = type("User", (), {"id": 42})()


class Author:
    bot = False
    id = 7


class Message:
    def __init__(self, content, *, dm=False, mentions=None, reply_to_bot=False):
        self.content = content
        self.author = Author()
        self.guild = None if dm else object()
        self.mentions = mentions or []
        self.reference = type("Ref", (), {"resolved": type("M", (), {"author": Bot.user})()})() if reply_to_bot else None


def test_dm_always_responds():
    assert should_respond(Message("hello", dm=True), Bot())


def test_name_trigger_is_case_insensitive():
    assert should_respond(Message("hey HELZER help me"), Bot())


def test_bot_mention_triggers():
    assert should_respond(Message("<@42> help", mentions=[Bot.user]), Bot())


def test_reply_to_bot_triggers():
    assert should_respond(Message("continue", reply_to_bot=True), Bot())


def test_strip_trigger_preserves_request():
    assert strip_trigger("Helzer, help me", Bot()) == "help me"
