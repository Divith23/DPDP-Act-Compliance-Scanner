import asyncio
import json
import re
import httpx

from app.config import settings


_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


def _get_config(role: str) -> tuple[str, str]:
    """Return API key and model for the requested LLM role."""
    if role == "evidence":
        return (
            settings.GEMINI_EVIDENCE_API_KEY,
            settings.GEMINI_EVIDENCE_MODEL,
        )

    if role == "analysis":
        return (
            settings.GEMINI_ANALYSIS_API_KEY,
            settings.GEMINI_ANALYSIS_MODEL,
        )

    raise ValueError(f"Unknown Gemini role: {role}")


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Use Google's retry hint when available, otherwise exponential backoff."""
    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return min(max(float(retry_after), 1.0), 60.0)
        except ValueError:
            pass

    try:
        body = response.json()
        details = body.get("error", {}).get("details", [])

        for detail in details:
            if detail.get("@type", "").endswith("RetryInfo"):
                delay = detail.get("retryDelay", "")
                match = re.match(r"(\d+(?:\.\d+)?)s", str(delay))

                if match:
                    return min(max(float(match.group(1)), 1.0), 60.0)

    except (ValueError, TypeError):
        pass

    return min(2 ** attempt, 60.0)


def _extract_json_object(text: str) -> dict:
    """Extract one JSON object from an LLM response.

    Gemini normally returns valid JSON when responseMimeType is JSON, but
    models can occasionally append another JSON object, markdown fences, or
    explanatory text. This parser tolerates those formatting errors while
    still requiring the extracted object to be valid JSON.
    """
    text = str(text or "").strip()

    if not text:
        raise json.JSONDecodeError("Empty LLM response", "", 0)

    # Remove common Markdown JSON fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    # First try the entire response.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Find the first balanced JSON object while respecting quoted strings.
    start = text.find("{")

    while start != -1:
        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1

                if depth == 0:
                    candidate = text[start:index + 1]

                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        break

        start = text.find("{", start + 1)

    raise json.JSONDecodeError(
        "Could not extract a valid JSON object from LLM response",
        text,
        0,
    )


async def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    *,
    role: str,
) -> dict:
    api_key, model = _get_config(role)

    if not api_key:
        raise RuntimeError(f"Gemini {role} API key is not configured.")

    if not model:
        raise RuntimeError(f"Gemini {role} model is not configured.")

    url = _GEMINI_URL.format(model=model, key=api_key)

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
    }

    timeout = httpx.Timeout(120.0, connect=20.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error = None

        for attempt in range(3):
            try:
                response = await client.post(url, json=payload)

                if response.status_code in {429, 503}:
                    if attempt < 2:
                        delay = _retry_delay(response, attempt)
                        print(
                            f"Gemini {role}: HTTP {response.status_code}; "
                            f"retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                response.raise_for_status()

                data = response.json()

                content = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )

                return _extract_json_object(content)

            except httpx.HTTPStatusError as exc:
                last_error = exc

                if (
                    exc.response.status_code in {429, 503}
                    and attempt < 2
                ):
                    delay = _retry_delay(exc.response, attempt)
                    await asyncio.sleep(delay)
                    continue

                raise RuntimeError(
                    f"Gemini {role} API error "
                    f"{exc.response.status_code}: "
                    f"{exc.response.text}"
                ) from exc

            except (httpx.ReadError, httpx.TimeoutException) as exc:
                last_error = exc

                if attempt < 2:
                    await asyncio.sleep(min(2 ** attempt, 10))
                    continue

                raise RuntimeError(
                    f"Gemini {role} request failed: {exc}"
                ) from exc

            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError(
                    f"Gemini {role} returned an unexpected response: {exc}"
                ) from exc

            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Gemini {role} returned invalid JSON: {exc}"
                ) from exc

        raise RuntimeError(
            f"Gemini {role} request failed after retries: {last_error}"
        )


async def call_evidence_llm(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """LLM #1: semantic evidence discovery."""
    return await _call_gemini(
        system_prompt,
        user_prompt,
        role="evidence",
    )


async def call_analysis_llm(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """LLM #2: legal compliance analysis."""
    return await _call_gemini(
        system_prompt,
        user_prompt,
        role="analysis",
    )


async def call_llm(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """Backward-compatible alias using the analysis model."""
    return await call_analysis_llm(
        system_prompt,
        user_prompt,
    )
