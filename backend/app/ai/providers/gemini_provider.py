"""Google Gemini Live AI Provider Implementation.

Implements secure, tenant-scoped external LLM invocation for Gemini models
(e.g., gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash) via direct HTTPS API calls
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

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 2

# Rates per 1,000,000 tokens (in USD)
GEMINI_COST_RATES: dict[str, tuple[float, float]] = {
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-2.0-flash": (0.10, 0.40),
}


class GeminiAIProvider(BaseAIProvider):
    """
    Production-ready Google Gemini API provider.
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
            raise AIProviderException("Gemini API key is required and cannot be empty.")

        self._api_key = api_key.strip()
        self._model_name = model_name or DEFAULT_GEMINI_MODEL
        self._base_url = validate_provider_endpoint(base_url) or DEFAULT_BASE_URL
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    @property
    def provider_type(self) -> str:
        return "GEMINI"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_payload(self, request: AIRequest) -> dict[str, Any]:
        """
        Converts generic AIRequest to Gemini generateContent REST payload.
        """
        user_text = request.prompt
        if request.context:
            user_text = f"Context: {json.dumps(request.context)}\n\n{user_text}"

        contents: list[dict[str, Any]] = [
            {
                "role": "user",
                "parts": [{"text": user_text}],
            }
        ]

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }

        if request.system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": request.system_prompt}]
            }

        if request.tools:
            function_declarations = []
            for tool in request.tools:
                if "function" in tool:
                    fn = tool["function"]
                    function_declarations.append({
                        "name": fn.get("name"),
                        "description": fn.get("description", ""),
                        "parameters": fn.get("parameters", {}),
                    })
                elif "name" in tool:
                    function_declarations.append({
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    })
            if function_declarations:
                payload["tools"] = [{"functionDeclarations": function_declarations}]

        return payload

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        input_rate, output_rate = GEMINI_COST_RATES.get(
            self._model_name, GEMINI_COST_RATES[DEFAULT_GEMINI_MODEL]
        )
        cost = (prompt_tokens * input_rate / 1_000_000.0) + (completion_tokens * output_rate / 1_000_000.0)
        return round(cost, 6)

    def execute(self, request: AIRequest) -> AIResponse:
        """
        Executes a prompt against the Gemini REST API with bounded retries and timeouts.
        """
        if request.simulate_failure:
            raise AIProviderException("Gemini simulated failure for test.")
        if request.simulate_timeout:
            raise AIProviderTimeoutException("Gemini simulated timeout for test.")

        endpoint = f"{self._base_url.rstrip('/')}/models/{self._model_name}:generateContent"
        payload = self._build_payload(request)
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
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
                    err_detail = "Authentication failure or invalid request to Gemini API."
                    if status_code == 401 or status_code == 403:
                        err_detail = "Invalid or unauthorized Gemini API key."
                    elif status_code == 404:
                        err_detail = f"Gemini model '{self._model_name}' not found."
                    raise AIProviderException(f"Gemini API Error [{status_code}]: {err_detail}")

                # Transient errors (429 Rate Limit, 500/503 Service Unavailable) -> bounded retry
                if status_code in (429, 500, 502, 503, 504):
                    last_error = AIProviderException(f"Gemini API transient error [{status_code}].")
                    if attempt < self._max_retries:
                        time.sleep(0.3 * (2 ** attempt))
                        continue
                    raise last_error

                # Unexpected status code
                raise AIProviderException(f"Gemini API returned unexpected status code [{status_code}].")

            except httpx.TimeoutException as exc:
                last_error = AIProviderTimeoutException("Gemini API request timed out.")
                if attempt < self._max_retries:
                    time.sleep(0.3 * (2 ** attempt))
                    continue
                raise last_error from None

            except httpx.RequestError as exc:
                last_error = AIProviderException("Failed to connect to Gemini API.")
                if attempt < self._max_retries:
                    time.sleep(0.3 * (2 ** attempt))
                    continue
                raise last_error from None

        if last_error:
            raise last_error
        raise AIProviderException("Gemini API request failed after retries.")

    def _parse_success_response(self, data: dict[str, Any], t0: float) -> AIResponse:
        latency_ms = int((time.perf_counter() - t0) * 1000)

        candidates = data.get("candidates", [])
        if not candidates:
            raise AIProviderException("Gemini API returned an empty candidate list.")

        candidate = candidates[0]
        content_obj = candidate.get("content", {})
        parts = content_obj.get("parts", [])

        content_text = ""
        tool_calls: list[dict[str, Any]] = []

        for part in parts:
            if "text" in part:
                content_text += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "name": fc.get("name"),
                    "arguments": fc.get("args", {}),
                })

        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)
        total_tokens = usage_meta.get("totalTokenCount", prompt_tokens + completion_tokens)
        cost = self._estimate_cost(prompt_tokens, completion_tokens)

        return AIResponse(
            provider_type="GEMINI",
            model_name=self._model_name,
            content=content_text,
            tool_calls=tool_calls if tool_calls else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            raw_metadata={"finish_reason": candidate.get("finishReason")},
        )
