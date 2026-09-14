import asyncio

from google.genai import types

from helzer.gemini import GeminiProvider, GeminiQuotaError


def test_function_result_is_wrapped_in_content():
    content = GeminiProvider.function_result("server_info", {"ok": True})

    assert isinstance(content, types.Content)
    assert content.role == "user"
    assert len(content.parts) == 1
    assert content.parts[0].function_response.name == "server_info"
    assert content.parts[0].function_response.response == {"ok": True}


def test_minimal_thinking_level_is_preserved():
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.model = "gemini-3.5-flash-lite"
    provider.thinking_level = "minimal"

    assert provider.thinking_level == "minimal"


def test_quota_messages_are_detected():
    assert GeminiProvider._is_quota_exhausted(RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded"))
    assert GeminiProvider._is_quota_exhausted(RuntimeError("generate_content_free_tier_requests"))
    assert not GeminiProvider._is_quota_exhausted(RuntimeError("temporarily unavailable"))


def test_quota_error_is_not_retried(monkeypatch):
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.model = "gemini-3.5-flash-lite"
    provider.thinking_level = "minimal"

    class FakeModels:
        calls = 0

        async def generate_content(self, **kwargs):
            self.calls += 1
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded for requests per day")

    fake_models = FakeModels()

    class FakeAio:
        models = fake_models

    class FakeClient:
        aio = FakeAio()

    provider.client = FakeClient()

    async def run():
        try:
            await provider.generate([], "test")
        except GeminiQuotaError:
            return
        raise AssertionError("expected GeminiQuotaError")

    asyncio.run(run())
    assert fake_models.calls == 1
