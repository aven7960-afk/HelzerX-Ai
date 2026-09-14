from google.genai import types

from helzer.gemini import GeminiProvider


def test_function_result_is_wrapped_in_content():
    content = GeminiProvider.function_result("server_info", {"ok": True})

    assert isinstance(content, types.Content)
    assert content.role == "user"
    assert len(content.parts) == 1
    assert content.parts[0].function_response.name == "server_info"
    assert content.parts[0].function_response.response == {"ok": True}
