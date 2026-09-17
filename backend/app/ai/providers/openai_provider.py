"""OpenAI Live AI Provider Implementation.

Implements secure, tenant-scoped external LLM invocation for OpenAI models
(e.g., gpt-4o-mini, gpt-4o, gpt-3.5-turbo) via direct HTTPS API calls
with timeout, bounded retry, response normalization, and zero credential leakage.
"""
from __future__ import annotations

import json
import time
from typing import Any
import httpx

from app.ai.providers.base_provider import BaseAIProvider, AIProviderException, AIProviderTimeoutException
from app.ai.schemas.provider import AIRequest, AIResponse
from app.ai.security.ssrf_validator import validate_provider_endpoint
from app.common.logger.logger import get_logger

logger = get_logger(__name__)

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 2

# Rates per 1,000,000 tokens (in USD)
OPENAI_COST_RATES: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}


class OpenAIAIProvider(BaseAIProvider):
    """
    Production-ready OpenAI API provider.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        if not api_key or not api_key.strip():
            raise AIProviderException("OpenAI API key is required and cannot be empty.")

        self._api_key = api_key.strip()
        self._model_name = model_name or DEFAULT_OPENAI_MODEL
        self._base_url = validate_provider_endpoint(base_url) or DEFAULT_BASE_URL
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    @property
    def provider_type(self) -> str:
        return "OPENAI"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_payload(self, request: AIRequest) -> dict[str, Any]:
        """
        Converts generic AIRequest to OpenAI chat completions REST payload.
        """
        messages: list[dict[str, Any]] = []

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt,
            })

        user_content = request.prompt
        if request.context:
            user_content = f"Context: {json.dumps(request.context)}\n\n{user_content}"

        messages.append({
            "role": "user",
            "content": user_content,
        })

        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.tools:
            formatted_tools = []
            for tool in request.tools:
                if "type" in tool and "function" in tool:
                    formatted_tools.append(tool)
                elif "name" in tool:
                    formatted_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.get("name"),
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {}),
                        },
                    })
            if formatted_tools:
                payload["tools"] = formatted_tools

        return payload

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        input_rate, output_rate = OPENAI_COST_RATES.get(
            self._model_name, OPENAI_COST_RATES[DEFAULT_OPENAI_MODEL]
        )
        cost = (prompt_tokens * input_rate / 1_000_000.0) + (completion_tokens * output_rate / 1_000_000.0)
        return round(cost, 6)

    def execute(self, request: AIRequest) -> AIResponse:
        """
        Executes a prompt against the OpenAI REST API with bounded retries and timeouts.
        """
        if request.simulate_failure:
            raise AIProviderException("OpenAI simulated failure for test.")
        if request.simulate_timeout:
            raise AIProviderTimeoutException("OpenAI simulated timeout for test.")

        endpoint = f"{self._base_url.rstrip('/')}/chat/completions"
        payload = self._build_payload(request)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        t0 = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout, follow_redirects=False) as client:
                    resp = client.post(endpoint, json=payload, headers=headers)

                status_code = resp.status_code

                if status_code == 200:
                    data = resp.json()
                    return self._parse_success_response(data, t0)

                # Client errors (400, 401, 403, 404) should fail immediately without retry
                if status_code in (400, 401, 403, 404):
                    err_detail = "Authentication failure or invalid request to OpenAI API."
                    if status_code == 401:
                        err_detail = "Invalid or expired OpenAI API key."
                    elif status_code == 404:
                        err_detail = f"OpenAI model '{self._model_name}' not found."
                    raise AIProviderException(f"OpenAI API Error [{status_code}]: {err_detail}")

                # Transient errors (429 Rate Limit, 500/502/503/504 Service Unavailable) -> bounded retry
                if status_code in (429, 500, 502, 503, 504):
                    last_error = AIProviderException(f"OpenAI API transient error [{status_code}].")
                    if attempt < self._max_retries:
                        time.sleep(0.3 * (2 ** attempt))
                        continue
                    raise last_error

                raise AIProviderException(f"OpenAI API returned unexpected status code [{status_code}].")

            except httpx.TimeoutException as exc:
                last_error = AIProviderTimeoutException("OpenAI API request timed out.")
                if attempt < self._max_retries:
                    time.sleep(0.3 * (2 ** attempt))
                    continue
                raise last_error from None

            except httpx.RequestError as exc:
                last_error = AIProviderException("Failed to connect to OpenAI API.")
                if attempt < self._max_retries:
                    time.sleep(0.3 * (2 ** attempt))
                    continue
                raise last_error from None

        if last_error:
            raise last_error
        raise AIProviderException("OpenAI API request failed after retries.")

    def _parse_success_response(self, data: dict[str, Any], t0: float) -> AIResponse:
        latency_ms = int((time.perf_counter() - t0) * 1000)

        choices = data.get("choices", [])
        if not choices:
            raise AIProviderException("OpenAI API returned empty choices.")

        message = choices[0].get("message", {})
        content_text = message.get("content") or ""

        tool_calls: list[dict[str, Any]] = []
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            raw_args = fn.get("arguments", "{}")
            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except Exception:
                parsed_args = {"raw": raw_args}

            tool_calls.append({
                "name": fn.get("name"),
                "arguments": parsed_args,
            })

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        cost = self._estimate_cost(prompt_tokens, completion_tokens)

        return AIResponse(
            provider_type="OPENAI",
            model_name=self._model_name,
            content=content_text,
            tool_calls=tool_calls if tool_calls else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            raw_metadata={"finish_reason": choices[0].get("finish_reason")},
        )
