"""
LLM adapter with automatic failover: NVIDIA NIM primary -> Groq fallback. Both are free-
tier, OpenAI-compatible chat-completions APIs, so a single adapter interface covers both --
no OpenAI dependency anywhere in this codebase.

This directly implements the JD line "debug, test, deploy, and monitor reliable production
systems": a provider outage or free-tier rate-limit on NVIDIA NIM does not take the whole
agent down.
"""
import httpx
from app.config import settings


class LLMProviderError(Exception):
    pass


def _call_provider(base_url: str, api_key: str, model: str, messages: list[dict],
                    tools: list[dict] | None, timeout: float = 30.0) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body: dict = {"model": model, "messages": messages, "temperature": 0.1}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    resp = httpx.post(f"{base_url}/chat/completions", headers=headers, json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def chat_completion(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Tries the primary provider first; on ANY failure (timeout, rate limit, 5xx, network
    error) falls back to the secondary provider. Raises LLMProviderError only if both fail,
    which the orchestrator treats as an escalation trigger (never a silent wrong answer)."""
    providers = {
        "nvidia": (settings.nvidia_nim_base_url, settings.nvidia_nim_api_key, settings.nvidia_nim_model),
        "groq": (settings.groq_base_url, settings.groq_api_key, settings.groq_model),
    }
    order = [settings.llm_primary_provider, settings.llm_fallback_provider]

    last_error = None
    for provider_name in order:
        base_url, api_key, model = providers[provider_name]
        if not api_key:
            last_error = f"{provider_name}: no API key configured"
            continue
        try:
            return _call_provider(base_url, api_key, model, messages, tools)
        except Exception as e:
            last_error = f"{provider_name}: {e}"
            continue

    raise LLMProviderError(f"All LLM providers failed. Last error: {last_error}")
