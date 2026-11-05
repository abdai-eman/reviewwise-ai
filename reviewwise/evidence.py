"""Compact AI labels refer to numbered pieces of the original text."""
import json
import re

from pydantic import BaseModel, ConfigDict, Field

from reviewwise.config import CATEGORIES


class Tag(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit: int = Field(ge=0)
    category: str = Field(json_schema_extra={"enum": list(CATEGORIES)})


class Labels(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(ge=1)
    positive: list[int] = Field(max_length=20)
    complaints: list[Tag] = Field(max_length=20)


class Packet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[Labels]


def evidence_units(text):
    # Every unit remains an exact substring; the original review supplies context.
    return [part.strip() for part in re.split(
        r"(?<=[.!?;])\s+|\n+|\s+(?:but|mais|aber|mee)\s+", text, flags=re.IGNORECASE,
    ) if part.strip()]


def wire_reviews(reviews):
    return [{"id": review.number, "review": review.text, "units": evidence_units(review.text)} for review in reviews]


def response_schema(reviews):
    schema = Packet.model_json_schema()
    schema["$defs"]["Labels"]["properties"]["id"]["enum"] = [review.number for review in reviews]
    limit = max(len(evidence_units(review.text)) for review in reviews) - 1
    schema["$defs"]["Tag"]["properties"]["unit"]["maximum"] = limit
    schema["$defs"]["Labels"]["properties"]["positive"]["items"].update({"minimum": 0, "maximum": limit})
    schema["properties"]["results"].update({"minItems": len(reviews), "maxItems": len(reviews)})
    return schema


def decode_packet(content, reviews):
    packet = Packet.model_validate_json(content, strict=True)
    expected = {review.number for review in reviews}
    ids = [item.id for item in packet.results]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("The response must include every supplied review ID exactly once.")
    texts = {review.number: evidence_units(review.text) for review in reviews}
    output = {}
    for item in packet.results:
        units = texts[item.id]
        indexes = item.positive + [tag.unit for tag in item.complaints]
        if any(index < 0 or index >= len(units) for index in indexes):
            raise ValueError(f"Review {item.id}: an evidence unit does not exist.")
        if any(tag.category not in CATEGORIES for tag in item.complaints):
            raise ValueError(f"Review {item.id}: an unknown complaint category was returned.")
        output[item.id] = {
            "positives": [units[index] for index in dict.fromkeys(item.positive)],
            "complaints": [{"category": tag.category, "quote": units[tag.unit]} for tag in item.complaints],
        }
    return output


def review_groups(reviews):
    group = []
    for review in reviews:
        candidate = group + [review]
        size = len(json.dumps(wire_reviews(candidate), ensure_ascii=False).encode("utf-8"))
        if group and (len(candidate) > 4 or size > 1500):
            yield group
            group = []
        group.append(review)
    if group:
        yield group
