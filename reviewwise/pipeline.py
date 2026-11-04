"""The only AI step is extraction; Python validates and counts its results."""

import csv
import hashlib
import io
import json
import time
from dataclasses import dataclass
from typing import Literal

import httpx
from ollama import Client, ResponseError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from reviewwise.config import (
    CATEGORIES, MAX_REVIEW_LENGTH, MAX_REVIEWS, MODEL, OLLAMA_URL, REQUEST_TIMEOUT,
)
from reviewwise.prompts import EXTRACTION_PROMPT


EXTRACTION_OPTIONS = {"temperature": 0, "num_ctx": 4096, "num_predict": 1024}


class ReviewWiseError(Exception):
    """A problem that can be explained directly to the user."""


@dataclass(frozen=True)
class Review:
    number: int
    text: str


class Complaint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal[
        "slow_service", "cold_coffee", "high_prices", "dirty_tables",
        "incorrect_order", "unfriendly_staff", "other",
    ]
    quote: str = Field(min_length=1, max_length=MAX_REVIEW_LENGTH)


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    positives: list[str] = Field(max_length=20)
    complaints: list[Complaint] = Field(max_length=20)


@dataclass(frozen=True)
class Analysis:
    review: Review
    extraction: Extraction


@dataclass(frozen=True)
class BatchResult:
    analyses: list[Analysis]
    elapsed_seconds: float
    model_digest: str
    reused_reviews: int = 0


def make_reviews(texts):
    texts = [text.strip() for text in texts if text.strip()]
    if not texts:
        raise ReviewWiseError("Enter at least one nonempty review.")
    if len(texts) > MAX_REVIEWS:
        raise ReviewWiseError(f"Use at most {MAX_REVIEWS:,} reviews per report.")
    for number, text in enumerate(texts, 1):
        if len(text) > MAX_REVIEW_LENGTH:
            raise ReviewWiseError(
                f"Review {number} exceeds {MAX_REVIEW_LENGTH} characters. Shorten it and try again."
            )
    return [Review(number, text) for number, text in enumerate(texts, 1)]


def reviews_from_text(text):
    return make_reviews(text.splitlines())


def reviews_from_csv(data):
    if len(data) > 1_000_000:
        raise ReviewWiseError("The CSV must be smaller than 1 MB.")
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), strict=True)
        if not reader.fieldnames or reader.fieldnames.count("review") != 1:
            raise ReviewWiseError("Use a UTF-8 CSV with exactly one column named 'review'.")
        texts = []
        for row in reader:
            if None in row or row.get("review") is None:
                raise ReviewWiseError("A CSV row is malformed. Check its columns and quotation marks.")
            texts.append(row["review"])
        return make_reviews(texts)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ReviewWiseError("Could not read the CSV. Save it as UTF-8 with a 'review' column.") from exc


def local_client():
    # Fixed loopback destination: OLLAMA_HOST and system proxies cannot redirect reviews.
    return Client(host=OLLAMA_URL, timeout=REQUEST_TIMEOUT, trust_env=False)


def require_model(client):
    try:
        for model in client.list().models:
            if model.model == MODEL:
                return model.digest or "unknown"
    except (ConnectionError, httpx.HTTPError, ResponseError) as exc:
        raise ReviewWiseError(
            "Ollama is unavailable. Open Ollama, then retry. If it is not installed, "
            "install it from ollama.com/download and run setup again."
        ) from exc
    raise ReviewWiseError(
        f"The {MODEL} model is missing. Restart START_REVIEWWISE.bat (Windows) or run bash setup.sh "
        f"with internet access, or run: ollama pull {MODEL}"
    )


def validate_extraction(content, review):
    extracted = Extraction.model_validate_json(content, strict=True)
    quotes = extracted.positives + [item.quote for item in extracted.complaints]
    if any(not quote.strip() or quote not in review.text for quote in quotes):
        raise ValueError("Every evidence quote must occur verbatim in the original review.")
    return extracted


def extract_review(client, review):
    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": json.dumps({"review": review.text}, ensure_ascii=False)},
    ]
    for attempt in range(2):
        try:
            response = client.chat(
                model=MODEL,
                messages=messages,
                format=Extraction.model_json_schema(),
                options=dict(EXTRACTION_OPTIONS),
                keep_alive="5m",
            )
        except httpx.TimeoutException as exc:
            raise ReviewWiseError(
                f"Review {review.number} timed out after waiting for Ollama. "
                "Close memory-heavy applications and retry with fewer or shorter reviews."
            ) from exc
        except (ConnectionError, httpx.HTTPError, ResponseError) as exc:
            raise ReviewWiseError(
                f"Ollama could not analyze review {review.number}. Check that Ollama is running "
                f"and {MODEL} is installed. A model-load failure can mean insufficient memory."
            ) from exc
        content = response.message.content or ""
        try:
            return validate_extraction(content, review)
        except (ValidationError, ValueError) as exc:
            if attempt == 1:
                raise ReviewWiseError(
                    f"Review {review.number} could not be validated after two AI attempts. "
                    "No complete report was generated. Try that review separately."
                ) from exc
            messages.extend([
                {"role": "assistant", "content": content},
                {"role": "user", "content": (
                    "The JSON failed validation. Use exactly the requested keys and allowed "
                    "categories. Every quote must be a nonempty verbatim substring of the "
                    "original review, not a translation. Return corrected JSON only."
                )},
            ])


def extraction_cache_key(review, digest):
    """Reuse only identical input, model weights, prompt, schema and settings."""
    payload = {
        "review": review.text, "model": MODEL, "digest": digest, "host": OLLAMA_URL,
        "prompt": EXTRACTION_PROMPT, "schema": Extraction.model_json_schema(),
        "options": EXTRACTION_OPTIONS,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def analyze_reviews(reviews, progress=None, cache=None):
    # Validate again at the boundary, including callers other than the UI.
    reviews = make_reviews([review.text for review in reviews])
    start = time.perf_counter()
    with local_client() as client:
        digest = require_model(client)
        analyses = []
        reused = 0
        for review in reviews:
            key = extraction_cache_key(review, digest) if cache is not None and digest != "unknown" else None
            extraction = None
            if key is not None and key in cache:
                try:
                    extraction = validate_extraction(cache[key], review)
                    reused += 1
                except (ValueError, TypeError):
                    cache.pop(key, None)
            if extraction is None:
                extraction = extract_review(client, review)
                if key is not None:
                    # The caller owns this temporary session cache; no review files are written.
                    while len(cache) >= MAX_REVIEWS:
                        cache.pop(next(iter(cache)))
                    cache[key] = extraction.model_dump_json()
            analyses.append(Analysis(review, extraction))
            if progress:
                progress(len(analyses), len(reviews))
    return BatchResult(analyses, time.perf_counter() - start, digest, reused)


def complaint_rows(analyses):
    ids = {category: set() for category in CATEGORIES}
    for analysis in analyses:
        for complaint in analysis.extraction.complaints:
            ids[complaint.category].add(analysis.review.number)
    rows = [
        {"category": category, "Complaint": CATEGORIES[category],
         "Reviews": len(numbers), "Review numbers": ", ".join(map(str, sorted(numbers)))}
        for category, numbers in ids.items() if numbers
    ]
    return sorted(rows, key=lambda row: (-row["Reviews"], row["category"]))
