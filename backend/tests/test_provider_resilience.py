"""
Unit tests for LLM provider resilience, alias normalization, and failover.
"""

from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.agent.llm_client import (
    LLMProviderError,
    _normalize_provider_name,
    _call_provider,
    chat_completion,
    ProviderConfig,
)


def test_provider_alias_normalization():
    assert _normalize_provider_name("groq") == "groq"
    assert _normalize_provider_name("GROQ") == "groq"
    assert _normalize_provider_name("nvidia") == "nvidia"
    assert _normalize_provider_name("nvidia_nim") == "nvidia"
    assert _normalize_provider_name("nim") == "nvidia"
    assert _normalize_provider_name("NVIDIA_NIM") == "nvidia"


def test_unsupported_provider_raises_informative_error():
    with pytest.raises(LLMProviderError) as exc_info:
        _normalize_provider_name("openai_paid")
    assert "Unsupported LLM provider" in str(exc_info.value)
    assert "Supported names" in str(exc_info.value)


@patch("httpx.post")
def test_provider_bounded_429_retry(mock_post):
    # Mock first call returning 429 and second succeeding
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.1"}
    resp_429.text = "Rate limited"

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Success!"}}]
    }

    mock_post.side_effect = [resp_429, resp_200]

    provider = ProviderConfig(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key="test_key",
        model="openai/gpt-oss-20b",
    )

    res = _call_provider(provider, [{"role": "user", "content": "hi"}], tools=None)
    assert res["choices"][0]["message"]["content"] == "Success!"
    assert mock_post.call_count == 2


@patch("app.agent.llm_client._call_provider")
def test_chat_completion_failover(mock_call):
    # Make first provider fail, second succeed
    mock_call.side_effect = [
        LLMProviderError("Primary provider quota exceeded (429)"),
        {"choices": [{"message": {"role": "assistant", "content": "Fallback answer"}}]},
    ]

    res = chat_completion([{"role": "user", "content": "test"}])
    assert res["choices"][0]["message"]["content"] == "Fallback answer"
