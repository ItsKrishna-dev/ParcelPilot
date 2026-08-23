"""
LLM provider adapter with failover.

Supported providers:
- NVIDIA NIM
- Groq

Both providers expose OpenAI-compatible chat-completions APIs. The adapter
normalizes provider aliases so values such as "nvidia", "nvidia_nim", or
"nim" resolve consistently.
"""

from dataclasses import dataclass

import httpx

from app.config import settings


class LLMProviderError(Exception):
    """Raised when all configured LLM providers fail."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str


PROVIDER_ALIASES = {
    "nvidia": "nvidia",
    "nvidia_nim": "nvidia",
    "nim": "nvidia",
    "groq": "groq",
}


def _normalize_provider_name(provider_name: str) -> str:
    normalized = (provider_name or "").strip().lower()
    resolved = PROVIDER_ALIASES.get(normalized)

    if resolved is None:
        supported = ", ".join(sorted(PROVIDER_ALIASES))
        raise LLMProviderError(
            f"Unsupported LLM provider '{provider_name}'. "
            f"Supported names: {supported}."
        )

    return resolved


def _provider_configs() -> dict[str, ProviderConfig]:
    return {
        "nvidia": ProviderConfig(
            name="nvidia",
            base_url=settings.nvidia_nim_base_url.rstrip("/"),
            api_key=settings.nvidia_nim_api_key.strip(),
            model=settings.nvidia_nim_model.strip(),
        ),
        "groq": ProviderConfig(
            name="groq",
            base_url=settings.groq_base_url.rstrip("/"),
            api_key=settings.groq_api_key.strip(),
            model=settings.groq_model.strip(),
        ),
    }


def _build_request_body(
    model: str,
    messages: list[dict],
    tools: list[dict] | None,
) -> dict:
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": settings.groq_max_tokens,
    }

    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    return body


def _call_provider(
    provider: ProviderConfig,
    messages: list[dict],
    tools: list[dict] | None,
    timeout_seconds: float = 15.0,
) -> dict:
    import time

    if not provider.api_key:
        raise LLMProviderError(
            f"No API key configured for provider '{provider.name}'."
        )

    if not provider.base_url:
        raise LLMProviderError(
            f"No base URL configured for provider '{provider.name}'."
        )

    if not provider.model:
        raise LLMProviderError(
            f"No model configured for provider '{provider.name}'."
        )

    endpoint = f"{provider.base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }

    body = _build_request_body(
        model=provider.model,
        messages=messages,
        tools=tools,
    )

    max_attempts = max(1, settings.llm_retry_max_attempts + 1)
    last_response = None

    for attempt in range(max_attempts):
        try:
            response = httpx.post(
                endpoint,
                headers=headers,
                json=body,
                timeout=httpx.Timeout(
                    timeout_seconds,
                    connect=5.0,
                ),
            )
            last_response = response
        except httpx.TimeoutException as error:
            raise LLMProviderError(
                f"Provider '{provider.name}' timed out."
            ) from error
        except httpx.RequestError as error:
            raise LLMProviderError(
                f"Provider '{provider.name}' request failed: {error}"
            ) from error

        if response.status_code == 429 and attempt < max_attempts - 1:
            retry_after = response.headers.get("Retry-After")
            wait_time = 1.0
            if retry_after:
                try:
                    wait_time = min(float(retry_after), 5.0)
                except ValueError:
                    wait_time = 1.0
            time.sleep(wait_time)
            continue

        break

    if last_response is None:
        raise LLMProviderError(f"Provider '{provider.name}' returned no response.")

    if last_response.status_code >= 400:
        detail = last_response.text[:1000]
        raise LLMProviderError(
            f"Provider '{provider.name}' returned HTTP "
            f"{last_response.status_code}: {detail}"
        )

    try:
        payload = last_response.json()
    except ValueError as error:
        raise LLMProviderError(
            f"Provider '{provider.name}' returned invalid JSON."
        ) from error

    if not isinstance(payload, dict):
        raise LLMProviderError(
            f"Provider '{provider.name}' returned an invalid response object."
        )

    if "choices" not in payload or not payload["choices"]:
        raise LLMProviderError(
            f"Provider '{provider.name}' response has no choices."
        )

    return payload


def _provider_order() -> list[str]:
    primary = _normalize_provider_name(
        settings.llm_primary_provider
    )

    fallback = _normalize_provider_name(
        settings.llm_fallback_provider
    )

    # Avoid calling the same provider twice if both environment variables
    # resolve to the same canonical provider.
    return list(dict.fromkeys([primary, fallback]))


def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    """
    Call the configured primary provider and fall back to the secondary provider.

    Any provider failure is isolated. The function raises only if every
    configured provider fails, allowing the orchestrator to return a controlled
    escalation instead of a 500 response.
    """
    configs = _provider_configs()
    errors: list[str] = []

    for provider_name in _provider_order():
        provider = configs[provider_name]

        try:
            return _call_provider(
                provider=provider,
                messages=messages,
                tools=tools,
            )
        except LLMProviderError as error:
            errors.append(str(error))

    error_summary = " | ".join(errors)

    raise LLMProviderError(
        "All configured LLM providers failed. "
        f"Details: {error_summary}"
    )