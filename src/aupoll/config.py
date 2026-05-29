from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PollConfig:
    title: str
    subtitle: str
    submit_label: str
    results_title: str
    questions: list["QuestionConfig"]


@dataclass(frozen=True)
class QuestionConfig:
    id: str
    prompt: str
    help: str
    minimum: float
    maximum: float
    step: float
    min_label: str
    max_label: str


def load_config(path: str | Path) -> PollConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle) or {}
    return parse_config(raw_config)


def parse_config(raw_config: dict[str, Any]) -> PollConfig:
    poll = raw_config.get("poll") or {}
    questions = raw_config.get("questions") or []
    if not isinstance(questions, list) or not questions:
        raise ValueError("config must include at least one question")

    parsed_questions = [_parse_question(question_data, index) for index, question_data in enumerate(questions)]
    question_ids = [question.id for question in parsed_questions]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("question ids must be unique")

    return PollConfig(
        title=str(poll.get("title") or "AUpoll"),
        subtitle=str(poll.get("subtitle") or ""),
        submit_label=str(poll.get("submit_label") or "Submit"),
        results_title=str(poll.get("results_title") or "Results"),
        questions=parsed_questions,
    )


def _parse_question(raw_question: Any, index: int) -> QuestionConfig:
    if not isinstance(raw_question, dict):
        raise ValueError(f"question {index + 1} must be a mapping")

    question_id = str(raw_question.get("id") or "").strip()
    prompt = str(raw_question.get("prompt") or "").strip()
    scale = raw_question.get("scale") or {}

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
        help=str(raw_question.get("help") or ""),
        minimum=minimum,
        maximum=maximum,
        step=step,
        min_label=str(scale.get("min_label") or str(minimum)),
        max_label=str(scale.get("max_label") or str(maximum)),
    )


def _number(value: Any, label: str) -> float:
    if value is None:
        raise ValueError(f"{label} is required")
    try:
        return float(value)
    except (TypeError, ValueError) as parse_error:
        raise ValueError(f"{label} must be a number") from parse_error

