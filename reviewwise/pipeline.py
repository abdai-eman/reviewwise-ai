"""The only AI step is extraction; Python validates and counts its results."""

import csv
import hashlib
import io
import json
import time
import os
from dataclasses import dataclass, field
from typing import Literal

import httpx
from ollama import Client, ResponseError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from reviewwise.config import (
    CATEGORIES, MAX_REVIEW_LENGTH, MAX_REVIEWS, MODEL, OLLAMA_URL, REQUEST_TIMEOUT,
)
from reviewwise.prompts import COMPACT_PROMPT
from reviewwise.evidence import Packet, decode_packet, review_groups, response_schema, wire_reviews


EXTRACTION_OPTIONS = {"temperature": 0, "num_ctx": 2048, "num_predict": 512, "num_threads": min(2, os.cpu_count() or 1)}


class ReviewWiseError(Exception):
    """A problem that can be explained directly to the user."""

    def __init__(self, message, kind="general"):
        super().__init__(message)
        self.kind = kind


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
class FailedReview:
    review: Review
    reason: str


@dataclass(frozen=True)
class BatchResult:
    analyses: list[Analysis]
    elapsed_seconds: float
    model_digest: str
    reused_reviews: int = 0
    failures: list[FailedReview] = field(default_factory=list)
    pending: list[Review] = field(default_factory=list)
    running: bool = False
    stop_reason: str = ""
    ai_requests: int = 0

    @property
    def total_reviews(self):
        return len(self.analyses) + len(self.failures) + len(self.pending)

    @property
    def complete(self):
        return not self.running and not self.failures and not self.pending


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
    return Client(host=OLLAMA_URL, timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=3), trust_env=False)


def require_model(client):
    try:
        for model in client.list().models:
            if model.model == MODEL:
                return model.digest or "unknown"
    except (ConnectionError, httpx.HTTPError, ResponseError) as exc:
        raise ReviewWiseError(
            "Ollama is unavailable. Open Ollama, then retry. If it is not installed, "
            "install it from ollama.com/download and run setup again."
            , kind="unavailable"
        ) from exc
    raise ReviewWiseError(
        f"The {MODEL} model is missing. Restart START_REVIEWWISE.bat (Windows) or run bash setup.sh "
        f"with internet access, or run: ollama pull {MODEL}", kind="model_missing"
    )


def validate_extraction(content, review):
    extracted = Extraction.model_validate_json(content, strict=True)
    quotes = extracted.positives + [item.quote for item in extracted.complaints]
    if any(not quote.strip() or quote not in review.text for quote in quotes):
        raise ValueError("Every evidence quote must occur verbatim in the original review.")
    return extracted


def generation_options(reviews):
    options = dict(EXTRACTION_OPTIONS)
    if any(len(review.text.encode("utf-8")) > 1000 for review in reviews):
        options.update(num_ctx=4096, num_predict=768)
    return options


def extract_group(client, reviews, should_stop=None, stats=None):
    if should_stop and should_stop():
        raise ReviewWiseError("Stopped by you.", kind="cancelled")
    if stats is not None:
        stats["requests"] += 1
    stream = None
    try:
        stream = client.chat(
            model=MODEL,
            messages=[{"role": "system", "content": COMPACT_PROMPT},
                      {"role": "user", "content": json.dumps({"reviews": wire_reviews(reviews)}, ensure_ascii=False)}],
            format=response_schema(reviews), options=generation_options(reviews),
            keep_alive="1m", stream=True,
        )
        pieces = []
        for chunk in stream:
            if should_stop and should_stop():
                raise ReviewWiseError("Stopped by you.", kind="cancelled")
            pieces.append(chunk.message.content or "")
        decoded = decode_packet("".join(pieces), reviews)
        return {review.number: validate_extraction(json.dumps(decoded[review.number], ensure_ascii=False), review) for review in reviews}
    except httpx.TimeoutException as exc:
        raise ReviewWiseError("Ollama timed out. Completed results are retained; close memory-heavy applications before resuming.", kind="timeout") from exc
    except (ConnectionError, httpx.HTTPError, ResponseError) as exc:
        raise ReviewWiseError(f"Ollama could not analyse this group. Check that it is running and {MODEL} is installed. A load failure can mean insufficient memory. Details: {str(exc)[:300]}", kind="unavailable") from exc
    except (ValidationError, ValueError) as exc:
        raise ReviewWiseError(f"The AI labels failed validation: {str(exc)[:500]}", kind="validation") from exc
    finally:
        close = getattr(stream, "close", None)
        if close:
            close()


def extract_review(client, review):
    for attempt in range(2):
        try:
            return extract_group(client, [review])[review.number]
        except ReviewWiseError as exc:
            if exc.kind != "validation" or attempt == 1:
                raise


def extraction_cache_key(review, digest):
    """Reuse only identical input, model weights, prompt, schema and settings."""
    payload = {
        "review": review.text, "model": MODEL, "digest": digest, "host": OLLAMA_URL,
        "prompt": COMPACT_PROMPT, "schema": Packet.model_json_schema(), "units_version": 1,
        "options": generation_options([review]),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def analyze_reviews(reviews, progress=None, cache=None, on_update=None, should_stop=None):
    # Validate again at the boundary, including callers other than the UI.
    reviews = make_reviews([review.text for review in reviews])
    start = time.perf_counter()
    with local_client() as client:
        digest = require_model(client)
        analyses, failures = {}, {}
        reused = 0
        stats = {"requests": 0}

        def snapshot(running=True, reason=""):
            result = BatchResult(
                [analyses[number] for number in sorted(analyses)], time.perf_counter() - start, digest, reused,
                [failures[number] for number in sorted(failures)],
                [review for review in reviews if review.number not in analyses and review.number not in failures],
                running, reason, stats["requests"],
            )
            if on_update:
                on_update(result)
            return result

        def save(review, extraction, is_reused=False):
            nonlocal reused
            analyses[review.number] = Analysis(review, extraction)
            reused += int(is_reused)
            if cache is not None and digest != "unknown" and not is_reused:
                while len(cache) >= MAX_REVIEWS:
                    cache.pop(next(iter(cache)))
                cache[extraction_cache_key(review, digest)] = extraction.model_dump_json()
            if progress:
                progress(len(analyses) + len(failures), len(reviews))
            snapshot()

        uncached = []
        for review in reviews:
            key = extraction_cache_key(review, digest) if cache is not None and digest != "unknown" else None
            extraction = None
            if key is not None and key in cache:
                try:
                    extraction = validate_extraction(cache[key], review)
                except (ValueError, TypeError):
                    cache.pop(key, None)
            if extraction is not None:
                save(review, extraction, is_reused=True)
            else:
                uncached.append(review)
        aliases = {}
        for review in uncached:
            aliases.setdefault(review.text, []).append(review)

        def save_aliases(review, extraction):
            for index, original in enumerate(aliases[review.text]):
                save(original, extraction, is_reused=index > 0)

        unique_reviews = [items[0] for items in aliases.values()]
        snapshot()
        try:
            for group in review_groups(unique_reviews):
                try:
                    extracted = extract_group(client, group, should_stop, stats)
                except ReviewWiseError as exc:
                    if exc.kind != "validation":
                        raise
                    # Isolate invalid responses. Good reviews survive a bad neighbour.
                    for review in group:
                        try:
                            item = extract_group(client, [review], should_stop, stats)[review.number]
                            save_aliases(review, item)
                        except ReviewWiseError as individual_error:
                            if individual_error.kind != "validation":
                                raise
                            for original in aliases[review.text]:
                                failures[original.number] = FailedReview(original, str(individual_error))
                            if progress:
                                progress(len(analyses) + len(failures), len(reviews))
                            snapshot()
                else:
                    for review in group:
                        save_aliases(review, extracted[review.number])
        except ReviewWiseError as exc:
            return snapshot(running=False, reason=str(exc))
    return snapshot(running=False)


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
