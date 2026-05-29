"""Flask application routes and presentation helpers for AUpoll."""

from __future__ import annotations

import html
import os
from math import ceil
from typing import Any

from flask import Flask, Response, redirect, render_template, request, url_for

from . import db as database
from .stats import histogram, summarize


def create_app() -> Flask:
    """Create the Flask application and register poll routes.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)
    app.jinja_env.globals["format_number"] = format_number

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> str | tuple[str, int]:
        with database.connect() as connection:
            context = poll_context(connection)
            if context is None:
                return render_message("AUpoll is not initialized yet.", 503)
            poll, questions = context
        return render_template("poll.html", poll=poll, questions=questions, error=None)

    @app.post("/submit")
    def submit() -> Response | tuple[str, int]:
        with database.connect() as connection:
            context = poll_context(connection)
            if context is None:
                return render_message("AUpoll is not initialized yet.", 503)
            poll, questions = context
            parsed, error = parse_answers(request.form, questions)
            if error:
                return render_template("poll.html", poll=poll, questions=questions, error=error), 400
            database.insert_response(connection, parsed)
        return redirect(url_for("results", submitted="1"))

    @app.get("/results")
    def results() -> str | tuple[str, int]:
        with database.connect() as connection:
            context = poll_context(connection)
            if context is None:
                return render_message("AUpoll is not initialized yet.", 503)
            poll, questions = context
            answers = database.answers_by_question(connection)

        figures = []
        for question in questions:
            values = answers.get(question["id"], [])
            buckets = histogram(values, question["minimum"], question["maximum"], question["step"])
            max_count = max([int(bucket["count"]) for bucket in buckets] or [0])
            y_max, y_ticks = count_axis(max_count)
            figures.append(
                {
                    "question": question,
                    "summary": summarize(values),
                    "buckets": buckets,
                    "y_max": y_max,
                    "y_ticks": y_ticks,
                }
            )
        return render_template(
            "results.html",
            poll=poll,
            figures=figures,
            submitted=request.args.get("submitted") == "1",
        )

    return app


def poll_context(connection: Any) -> tuple[Any, list[Any]] | None:
    if not database.is_initialized(connection):
        return None
    return database.poll(connection), database.questions(connection)


def parse_answers(form: Any, questions: list[Any]) -> tuple[dict[str, float], str | None]:
    """Validate submitted form values against configured poll questions.

    Args:
        form: Request form data with one value per question id.
        questions: Question records containing id, minimum, maximum, and step fields.

    Returns:
        A tuple of parsed answers by question id and an error message. The error
        message is ``None`` when all answers are valid.
    """
    answers: dict[str, float] = {}
    for question in questions:
        submitted_value = form.get(question["id"])
        if submitted_value is None:
            return {}, "Please answer every question."
        try:
            value = float(submitted_value)
        except ValueError:
            return {}, "One of the answers was not a number."
        if value < question["minimum"] or value > question["maximum"]:
            return {}, "One of the answers was outside the allowed range."
        scale_step_offset = (value - question["minimum"]) / question["step"]
        if abs(scale_step_offset - round(scale_step_offset)) > 0.000001:
            return {}, "One of the answers did not match the configured scale."
        answers[question["id"]] = value
    return answers, None


def format_number(value: float | None) -> str:
    """Format optional numeric values for result templates.

    Args:
        value: Number to display, or ``None`` when the value is unavailable.

    Returns:
        ``"n/a"`` for missing values, an integer string for whole numbers, or a
        one-decimal string otherwise.
    """
    if value is None:
        return "n/a"
    if abs(value - round(value)) < 0.005:
        return str(int(round(value)))
    return f"{value:.1f}"


def count_axis(max_count: int) -> tuple[int, list[dict[str, int | float]]]:
    """Build a compact y-axis scale for histogram counts.

    Args:
        max_count: Largest bucket count in the histogram.

    Returns:
        The axis maximum and ticks containing count values plus template-ready
        percentage offsets.
    """
    if max_count <= 0:
        return 1, [{"value": 0, "percent": 0}, {"value": 1, "percent": 100}]

    if max_count <= 5:
        axis_maximum = max_count
        step = 1
    else:
        step = _nice_step(ceil(max_count / 4))
        axis_maximum = ceil(max_count / step) * step

    ticks = [
        {"value": value, "percent": value / axis_maximum * 100}
        for value in range(0, axis_maximum + step, step)
    ]
    return axis_maximum, ticks


def _nice_step(minimum: int) -> int:
    """Return a 1/2/5-based tick step that is at least ``minimum``."""
    magnitude = 1
    while magnitude * 10 <= minimum:
        magnitude *= 10
    for multiplier in (1, 2, 5, 10):
        step = multiplier * magnitude
        if step >= minimum:
            return step
    return 10 * magnitude


def render_message(message: str, status: int) -> tuple[str, int]:
    """Render a minimal HTML status page.

    Args:
        message: User-facing message to display.
        status: HTTP status code to return with the page.

    Returns:
        HTML body and status code suitable for Flask route returns.
    """
    return (
        f"<!doctype html><title>AUpoll</title><body><main><h1>{html.escape(message)}</h1></main></body>",
        status,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    create_app().run(host="0.0.0.0", port=port)
