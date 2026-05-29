"""YAML configuration parsing and validation for AUpoll polls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PollConfig:
    """Top-level poll settings and ordered question definitions.

    Attributes:
        title: Poll page title.
        subtitle: Supporting text shown under the title.
        submit_label: Label for the submit button.
        results_title: Heading for the results page.
        questions: Ordered questions rendered in the poll.
    """

    title: str
    subtitle: str
    submit_label: str
    results_title: str
    questions: list["QuestionConfig"]


@dataclass(frozen=True)
class QuestionConfig:
    """Validated configuration for one poll question.

    Attributes:
        id: Stable identifier used in form fields and answer rows.
        prompt: Question text shown to respondents.
        help: Optional helper text for the question.
        minimum: Lowest accepted numeric answer.
        maximum: Highest accepted numeric answer.
        step: Required increment between accepted answers.
        min_label: Display label for the low end of the scale.
        max_label: Display label for the high end of the scale.
    """

    id: str
    prompt: str
    help: str
    minimum: float
    maximum: float
    step: float
    min_label: str
    max_label: str


def load_config(path: str | Path) -> PollConfig:
    """Load and parse a poll YAML file.

    Args:
        path: Filesystem path to the YAML configuration.

    Returns:
        Parsed poll configuration.

    Raises:
        ValueError: If the YAML content does not describe a valid poll.
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> PollConfig:
    """Parse raw configuration data into validated poll settings.

    Args:
        raw: Mapping loaded from a YAML configuration file.

    Returns:
        Parsed poll configuration with defaults applied.

    Raises:
        ValueError: If required poll or question settings are invalid.
    """
    poll = raw.get("poll") or {}
    questions = raw.get("questions") or []
    if not isinstance(questions, list) or not questions:
        raise ValueError("config must include at least one question")

    parsed_questions = [_parse_question(item, index) for index, item in enumerate(questions)]
    ids = [question.id for question in parsed_questions]
    if len(ids) != len(set(ids)):
        raise ValueError("question ids must be unique")

    return PollConfig(
        title=str(poll.get("title") or "AUpoll"),
        subtitle=str(poll.get("subtitle") or ""),
        submit_label=str(poll.get("submit_label") or "Submit"),
        results_title=str(poll.get("results_title") or "Results"),
        questions=parsed_questions,
    )


def _parse_question(raw: Any, index: int) -> QuestionConfig:
    """Validate and parse a single question mapping from configuration data."""
    if not isinstance(raw, dict):
        raise ValueError(f"question {index + 1} must be a mapping")

    question_id = str(raw.get("id") or "").strip()
    prompt = str(raw.get("prompt") or "").strip()
    scale = raw.get("scale") or {}

    if not question_id:
        raise ValueError(f"question {index + 1} is missing id")
    if not question_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"question id {question_id!r} must use letters, numbers, dashes, or underscores")
    if not prompt:
        raise ValueError(f"question {question_id!r} is missing prompt")
    if not isinstance(scale, dict):
        raise ValueError(f"question {question_id!r} scale must be a mapping")

    minimum = _number(scale.get("min"), f"{question_id}.scale.min")
    maximum = _number(scale.get("max"), f"{question_id}.scale.max")
    step = _number(scale.get("step", 1), f"{question_id}.scale.step")
    if maximum <= minimum:
        raise ValueError(f"question {question_id!r} scale.max must be greater than scale.min")
    if step <= 0:
        raise ValueError(f"question {question_id!r} scale.step must be positive")

    return QuestionConfig(
        id=question_id,
        prompt=prompt,
        help=str(raw.get("help") or ""),
        minimum=minimum,
        maximum=maximum,
        step=step,
        min_label=str(scale.get("min_label") or str(minimum)),
        max_label=str(scale.get("max_label") or str(maximum)),
    )


def _number(value: Any, label: str) -> float:
    """Coerce a required numeric configuration value to ``float``."""
    if value is None:
        raise ValueError(f"{label} is required")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
