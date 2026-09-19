"""Multi-provider LLM abstraction for Planck AI.

Every provider speaks the OpenAI chat-completions format, so one request/response
shape flows through the agent loop no matter which provider answers.
"""
import copy
from typing import Dict, Any, List, Optional

import httpx


class RateLimitError(Exception):
    """Raised on HTTP 429 so the caller can switch providers instead of waiting."""

    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMProvider:
    """OpenAI-compatible chat-completions provider. Subclasses set the endpoint and default model."""

    api_url: str = ""
    default_model: str = ""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()

    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Adapt the shared message history to this provider's quirks."""
        return messages

    async def generate(
                      self,
                      messages: List[Dict[str, Any]],
                      tools: Optional[List[Dict[str, Any]]] = None,
                      max_tokens: int = 1500,
                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        Make a single request. No retries or sleeping here: on any failure we raise
        immediately so the agent can fall through to the next provider.
        """
        payload = {
            "model": self.model,
            "messages": self._prepare_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            # Report only the error type: some httpx errors echo the request headers,
            # which would put the API key in logs and in the error shown to users
            raise Exception(f"{self.provider_name} request failed ({type(e).__name__})") from None

        if response.status_code == 429:
            raise RateLimitError(
                f"{self.provider_name} rate limit: {response.text[:300]}",
                retry_after=_parse_retry_after(response.headers.get("Retry-After"))
            )
        if response.status_code != 200:
            raise Exception(f"{self.provider_name} API error: {response.status_code} - {response.text[:500]}")
        return response.json()


class GroqProvider(LLMProvider):
    """Groq API provider"""
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    default_model = "openai/gpt-oss-120b"


class GeminiProvider(LLMProvider):
    """Google Gemini via its OpenAI-compatible endpoint"""
    api_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    default_model = "gemini-3.5-flash-lite"

    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Gemini rejects tool calls that lack a thought_signature. Calls made earlier in the
        # run by another provider get Google's documented placeholder so Gemini can take over.
        messages = copy.deepcopy(messages)
        for message in messages:
            for tool_call in message.get("tool_calls") or []:
                google = tool_call.setdefault("extra_content", {}).setdefault("google", {})
                google.setdefault("thought_signature", "skip_thought_signature_validator")
        return messages


class NVIDIAProvider(LLMProvider):
    """NVIDIA API catalog provider (OpenAI-compatible)"""
    api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    default_model = "openai/gpt-oss-20b"


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def create_provider(provider_name: str, api_key: str, model: Optional[str] = None) -> LLMProvider:
    """Factory function to create LLM provider instances"""
    providers = {
        "groq": GroqProvider,
        "gemini": GeminiProvider,
        "nvidia": NVIDIAProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_name}. Supported providers: {list(providers.keys())}")

    return provider_class(api_key=api_key, model=model)


def get_available_providers() -> List[str]:
    """Get list of available provider names"""
    return ["groq", "gemini", "nvidia"]
