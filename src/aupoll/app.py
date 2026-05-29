from __future__ import annotations

import html
import os
from typing import Any

from flask import Flask, Response, redirect, render_template, request, url_for

from . import db
from .stats import histogram, summarize


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.globals["format_number"] = format_number

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> str | tuple[str, int]:
        with db.connect() as connection:
            if not db.is_initialized(connection):
                return render_message("AUpoll is not initialized yet.", 503)
            poll = db.poll(connection)
            questions = db.questions(connection)
        return render_template("poll.html", poll=poll, questions=questions, error=None)

    @app.post("/submit")
    def submit() -> Response | tuple[str, int]:
        with db.connect() as connection:
            if not db.is_initialized(connection):
                return render_message("AUpoll is not initialized yet.", 503)
            poll = db.poll(connection)
            questions = db.questions(connection)
            parsed, error = parse_answers(request.form, questions)
            if error:
                return render_template("poll.html", poll=poll, questions=questions, error=error), 400
            db.insert_response(connection, parsed)
        return redirect(url_for("results", submitted="1"))

    @app.get("/results")
    def results() -> str | tuple[str, int]:
        with db.connect() as connection:
            if not db.is_initialized(connection):
                return render_message("AUpoll is not initialized yet.", 503)
            poll = db.poll(connection)
            questions = db.questions(connection)
            answers = db.answers_by_question(connection)

        figures = []
        for question in questions:
            values = answers.get(question["id"], [])
            buckets = histogram(values, question["minimum"], question["maximum"], question["step"])
            figures.append(
                {
                    "question": question,
                    "summary": summarize(values),
                    "buckets": buckets,
                    "max_count": max([int(bucket["count"]) for bucket in buckets] or [0]),
                }
            )
        return render_template(
            "results.html",
            poll=poll,
            figures=figures,
            submitted=request.args.get("submitted") == "1",
        )

    return app


def parse_answers(form: Any, questions: list[Any]) -> tuple[dict[str, float], str | None]:
    answers: dict[str, float] = {}
    for question in questions:
        raw_value = form.get(question["id"])
        if raw_value is None:
            return {}, "Please answer every question."
        try:
            value = float(raw_value)
        except ValueError:
            return {}, "One of the answers was not a number."
        if value < question["minimum"] or value > question["maximum"]:
            return {}, "One of the answers was outside the allowed range."
        offset = (value - question["minimum"]) / question["step"]
        if abs(offset - round(offset)) > 0.000001:
            return {}, "One of the answers did not match the configured scale."
        answers[question["id"]] = value
    return answers, None


def format_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    if abs(value - round(value)) < 0.005:
        return str(int(round(value)))
    return f"{value:.1f}"


def render_message(message: str, status: int) -> tuple[str, int]:
    return (
        f"<!doctype html><title>AUpoll</title><body><main><h1>{html.escape(message)}</h1></main></body>",
        status,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    create_app().run(host="0.0.0.0", port=port)

