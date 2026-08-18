"""The only file that knows how to talk to Gemini."""

import threading
import time

from google import genai
from google.genai import errors, types

from app.config import (
    GEMINI_API_KEY,
    GEMINI_EMBED_FALLBACK,
    GEMINI_EMBED_MODEL,
    GEMINI_FALLBACKS,
    GEMINI_MODEL,
)

_client: genai.Client | None = None
_lock = threading.Lock()

# a long extraction is a lot of JSON, and a prototype is a whole HTML file; the default
# cap would truncate either and we would silently lose the tail
MAX_OUTPUT_TOKENS = 65536


def client() -> genai.Client:
    """Built on first use — importing this module must not require a key.

    The lock is not optional: extractors run in parallel threads, and without it two
    of them build a client each, the second overwrites the first, and the orphan gets
    collected — closing the httpx session the first thread is still sending on.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                if not GEMINI_API_KEY:
                    raise RuntimeError(
                        "GEMINI_API_KEY missing — copy backend/.env.example to .env"
                    )
                _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _generate(contents: list, config: dict, attempts: int):
    """One request, with the model chain walked on 503 (busy) and 429 (daily quota).

    Each model in the chain has its own free-tier allowance, so the fallback list is a
    budget measure as much as a reliability one.
    """
    models = [GEMINI_MODEL, *GEMINI_FALLBACKS]
    last_error: Exception | None = None

    for model in models:
        delay = 2.0
        for attempt in range(1, attempts + 1):
            try:
                response = client().models.generate_content(
                    model=model, contents=contents, config=config
                )

                # truncation must be loud. Half a findings array is not fewer findings,
                # it is a broken result that looks like a smaller one.
                finish = response.candidates[0].finish_reason if response.candidates else None
                if finish and str(getattr(finish, "name", finish)) not in (
                    "STOP",
                    "FINISH_REASON_UNSPECIFIED",
                ):
                    raise ValueError(f"{model} stopped early: {finish}")

                if model != GEMINI_MODEL:
                    print(f"  (served by {model} — {GEMINI_MODEL} was unavailable)")
                return response

            except errors.ServerError as overloaded:  # 5xx — busy, worth retrying
                last_error = overloaded
                if attempt < attempts:
                    time.sleep(delay)
                    delay *= 2
            except errors.ClientError as refused:
                if refused.code != 429:
                    raise
                # Free tier is 20 requests/day PER MODEL. A daily quota will not clear in
                # two seconds, so don't retry this model — spend the next one's allowance.
                last_error = refused
                print(f"  ({model} daily quota exhausted)")
                break

    raise RuntimeError(f"no model could serve the request: {models}") from last_error


def _base_config(thinking: str) -> dict:
    return {
        # `thinking` is MINIMAL | LOW | MEDIUM | HIGH, set per agent at the call site.
        # (thinking_budget is gone on Gemini 3.5+ — thinking_level replaces it.)
        "thinking_config": {"thinking_level": thinking},
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        # we never pass tools; disabling stops the SDK's AFC warning
        "automatic_function_calling": {"disable": True},
    }


def generate_json(
    prompt: str,
    schema,
    *,
    images: list[tuple[bytes, str]] | None = None,
    thinking: str = "MEDIUM",
    attempts: int = 2,
):
    """Call Gemini and get back `schema`-shaped data.

    The schema is enforced by the API, so a malformed response fails here rather than
    three nodes downstream.
    """
    contents: list = [prompt]
    for data, mime_type in images or []:
        contents.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    config = _base_config(thinking) | {
        "response_mime_type": "application/json",
        "response_schema": schema,
    }
    response = _generate(contents, config, attempts)

    if response.parsed is None:
        raise ValueError(f"unparseable output: {response.text!r:.200}")
    return response.parsed


def generate_text(prompt: str, *, thinking: str = "MEDIUM", attempts: int = 2) -> str:
    """Plain text out — used for the prototype, which is a file rather than a record."""
    response = _generate([prompt], _base_config(thinking), attempts)
    return response.text or ""


# The API caps a batch at 100, and each item in it counts separately against a
# 100-per-minute free-tier limit — so a normal run of ~150 findings will hit the
# ceiling once and has to wait it out.
EMBED_BATCH = 100
EMBED_DIMENSIONS = 768


def embed(texts: list[str]) -> list[list[float]] | None:
    """Vectors for comparing meaning. Returns None if the service will not serve us —
    the merger falls back to word overlap rather than failing the whole run."""
    if not texts:
        return []

    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = texts[start : start + EMBED_BATCH]
        got = _embed_batch(batch)
        if got is None:
            return None
        vectors.extend(got)
    return vectors


def _embed_batch(batch: list[str]) -> list[list[float]] | None:
    for model in (GEMINI_EMBED_MODEL, GEMINI_EMBED_FALLBACK):
        for attempt in range(2):
            try:
                response = client().models.embed_content(
                    model=model,
                    # a flat list of strings is read as ONE multi-part document and
                    # returns a single vector; nesting each string batches them
                    contents=[[text] for text in batch],
                    config={
                        "task_type": "SEMANTIC_SIMILARITY",
                        "output_dimensionality": EMBED_DIMENSIONS,
                    },
                )
                return [e.values for e in response.embeddings]
            except errors.ClientError as refused:
                if refused.code != 429:
                    raise
                if attempt == 0:
                    print("  (embedding rate limit — waiting 25s)", flush=True)
                    time.sleep(25)
            except errors.ServerError:
                time.sleep(2)
    print("  (embeddings unavailable — merging on word overlap instead)", flush=True)
    return None
