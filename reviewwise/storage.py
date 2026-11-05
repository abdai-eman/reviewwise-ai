"""Explicit local report saves. Imported counts are recomputed from validated evidence."""
from dataclasses import asdict, replace
from datetime import date, datetime
import math
import json
import os
from pathlib import Path
import platform
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from reviewwise.config import MAX_REVIEWS, MAX_REVIEW_LENGTH
from reviewwise.pipeline import BatchResult, validate_extraction

MAX_REPORT_BYTES = 20 * 1024 * 1024


class SavedReport(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    schema_version: Literal[1] = 1
    recorded_at: datetime
    reporting_day: date
    title: str = Field(min_length=1, max_length=160)
    provenance: str = Field(default="Saved on this device", max_length=500)
    result: BatchResult

    @model_validator(mode="after")
    def validate_evidence_and_coverage(self):
        result = self.result
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("The saved report timestamp must include its timezone.")
        reviews = [item.review for item in result.analyses] + [item.review for item in result.failures] + result.pending
        if not 1 <= len(reviews) <= MAX_REVIEWS:
            raise ValueError("The report contains an unsupported number of reviews.")
        ids = [item.number for item in reviews]
        if len(ids) != len(set(ids)) or set(ids) != set(range(1, len(reviews) + 1)):
            raise ValueError("Each submitted review must appear exactly once in the report coverage.")
        if any(not item.text.strip() or len(item.text) > MAX_REVIEW_LENGTH for item in reviews):
            raise ValueError("The report contains an empty or oversized review.")
        if not math.isfinite(result.elapsed_seconds) or result.elapsed_seconds < 0:
            raise ValueError("The report has an invalid elapsed time.")
        if not 0 <= result.reused_reviews <= len(result.analyses) or result.ai_requests < 0:
            raise ValueError("The report has invalid reuse/request metadata.")
        for item in result.analyses:
            validate_extraction(item.extraction.model_dump_json(), item.review)
        self.result = replace(result, running=False)
        return self


def report_document(result, reporting_day):
    # JSON round-trip applies the same strict validation used for imported files.
    document = {
        "schema_version": 1, "recorded_at": datetime.now().astimezone().isoformat(),
        "reporting_day": reporting_day.isoformat(), "title": f"Weekly report · {reporting_day.isoformat()}",
        "provenance": "Saved from ReviewWise on this device",
        "result": asdict(result),
    }
    encoded = json.dumps(document, default=lambda value: value.model_dump())
    return SavedReport.model_validate_json(encoded)


def load_report(data):
    if len(data) > MAX_REPORT_BYTES:
        raise ValueError("Use a saved report smaller than 20 MB.")
    return SavedReport.model_validate_json(data)


def reports_directory(project):
    if platform.system() == "Windows" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "ReviewWise/reports"
    return Path(project) / ".reviewwise/reports"


class ReportStore:
    def __init__(self, folder):
        self.folder = Path(folder)

    def save(self, document):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{document.reporting_day.isoformat()}-{uuid4().hex[:12]}.json"
        temporary = path.with_suffix('.tmp')
        temporary.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
        return path.name

    def list(self):
        entries = []
        if self.folder.exists():
            for path in self.folder.glob('*.json'):
                try:
                    if path.stat().st_size <= MAX_REPORT_BYTES:
                        document = load_report(path.read_bytes())
                        entries.append((path.name, document))
                except (ValueError, OSError):
                    continue
        return sorted(entries, key=lambda entry: entry[1].recorded_at, reverse=True)

    def delete(self, name):
        path = (self.folder / name).resolve()
        if path.parent != self.folder.resolve() or path.suffix != '.json':
            raise ValueError("Choose a report saved by this application.")
        path.unlink()
