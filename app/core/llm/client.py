from __future__ import annotations

import re

import httpx

from app.core.llm.config import LlmConfig, get_llm_config


class LlmNotConfiguredError(RuntimeError):
    pass


def _build_chat_completions_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def _extract_message_content(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("LLM response payload was not a JSON object")

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("LLM response did not contain any choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("LLM choice payload was malformed")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("LLM response choice did not contain a message")

    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text" and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        if text_parts:
            return "\n".join(text_parts)

    raise ValueError("LLM response message content was empty")


def _strip_markdown_code_fences(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_api_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001
        payload = None

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()

    text = response.text.strip()
    if text:
        return text

    return f"HTTP {response.status_code}"


def request_chat_completion_content(
    *,
    system_prompt: str,
    user_prompt: str,
    config: LlmConfig | None = None,
) -> str:
    llm_config = config or get_llm_config()
    if not llm_config.is_configured:
        raise LlmNotConfiguredError("LLM provider is not configured")

    payload = {
        "model": llm_config.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "authorization": f"Bearer {llm_config.api_key}",
        "content-type": "application/json",
    }
    url = _build_chat_completions_url(llm_config.base_url or "")

    last_error: Exception | None = None
    for _attempt in range(llm_config.retry_count + 1):
        try:
            with httpx.Client(timeout=llm_config.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.is_error:
                    raise RuntimeError(_extract_api_error_message(response))
                content = _extract_message_content(response.json())
                return _strip_markdown_code_fences(content)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is None:
        raise RuntimeError("LLM request failed without returning an error")
    raise last_error
