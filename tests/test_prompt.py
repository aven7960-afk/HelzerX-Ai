from helzer.prompts import build_system_prompt


def test_prompt_covers_language_and_behavior():
    prompt = build_system_prompt("Asia/Colombo", "Test Server")
    assert "Sinhala" in prompt
    assert "Singlish" in prompt
    assert "Recent conversation" in prompt
    assert "never invent" in prompt.lower()


def test_prompt_contains_server_context():
    prompt = build_system_prompt("Asia/Colombo", "My Server")
    assert "My Server" in prompt
    assert "Asia/Colombo" in prompt
