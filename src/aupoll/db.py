"""SQLite persistence helpers for AUpoll."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import PollConfig


DEFAULT_DB_PATH = "/data/aupoll.sqlite3"


def database_path() -> str:
    """Return the configured SQLite database path."""
    return os.environ.get("AUPOLL_DB_PATH", DEFAULT_DB_PATH)


@contextmanager
def connect(path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Open a transactional SQLite connection with AUpoll defaults.

    Args:
        path: Optional database path. When omitted, ``AUPOLL_DB_PATH`` or the
            default container path is used.

    Yields:
        A SQLite connection with row objects and foreign keys enabled.

    Raises:
        Exception: Re-raises any exception from the managed block after rolling
            back the transaction.
    """
    db_path = path or database_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def is_initialized(connection: sqlite3.Connection) -> bool:
    """Return whether the database has the AUpoll schema and metadata."""
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'meta'"
    ).fetchone()
    if row is None:
        return False
    configured = connection.execute("SELECT value FROM meta WHERE key = 'configured_at'").fetchone()
    return configured is not None


def initialize(connection: sqlite3.Connection, config: PollConfig) -> None:
    """Create the AUpoll schema and seed it from configuration.

    Args:
        connection: Open SQLite connection to initialize.
        config: Validated poll configuration to store.
    """
    connection.executescript(
        """
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE poll (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            submit_label TEXT NOT NULL,
            results_title TEXT NOT NULL
        );

        CREATE TABLE questions (
            id TEXT PRIMARY KEY,
            position INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            help TEXT NOT NULL,
            minimum REAL NOT NULL,
            maximum REAL NOT NULL,
            step REAL NOT NULL,
            min_label TEXT NOT NULL,
            max_label TEXT NOT NULL
        );

        CREATE TABLE responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        CREATE TABLE answers (
            response_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            value REAL NOT NULL,
            PRIMARY KEY (response_id, question_id),
            FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        """
    )
    connection.execute(
        """
        INSERT INTO poll (id, title, subtitle, submit_label, results_title)
        VALUES (1, ?, ?, ?, ?)
        """,
        (config.title, config.subtitle, config.submit_label, config.results_title),
    )
    connection.executemany(
        """
        INSERT INTO questions (
            id, position, prompt, help, minimum, maximum, step, min_label, max_label
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                question.id,
                position,
                question.prompt,
                question.help,
                question.minimum,
                question.maximum,
                question.step,
                question.min_label,
                question.max_label,
            )
            for position, question in enumerate(config.questions)
        ],
    )
    connection.execute(
        "INSERT INTO meta (key, value) VALUES ('configured_at', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    )


def poll(connection: sqlite3.Connection) -> sqlite3.Row:
    """Fetch the single configured poll row."""
    return connection.execute("SELECT * FROM poll WHERE id = 1").fetchone()


def questions(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Fetch configured questions in display order."""
    return list(connection.execute("SELECT * FROM questions ORDER BY position"))


def insert_response(connection: sqlite3.Connection, answers: dict[str, float]) -> int:
    """Persist a respondent's answers.

    Args:
        connection: Open SQLite connection.
        answers: Numeric answer values keyed by question id.

    Returns:
        The inserted response id.
    """
    cursor = connection.execute("INSERT INTO responses DEFAULT VALUES")
    response_id = int(cursor.lastrowid)
    connection.executemany(
        "INSERT INTO answers (response_id, question_id, value) VALUES (?, ?, ?)",
        [(response_id, question_id, value) for question_id, value in answers.items()],
    )
    return response_id


def answers_by_question(connection: sqlite3.Connection) -> dict[str, list[float]]:
    """Fetch submitted answer values grouped by question id."""
    rows = connection.execute("SELECT question_id, value FROM answers ORDER BY question_id, value").fetchall()
    values: dict[str, list[float]] = {}
    for row in rows:
        values.setdefault(row["question_id"], []).append(float(row["value"]))
    return values

