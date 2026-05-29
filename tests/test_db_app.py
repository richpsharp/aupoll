from pathlib import Path

from aupoll.app import create_app
from aupoll.config import parse_config
from aupoll.db import connect, initialize, is_initialized


def sample_config():
    return parse_config(
        {
            "poll": {"title": "Test Poll", "results_title": "Test Results"},
            "questions": [
                {
                    "id": "q1",
                    "prompt": "How useful?",
                    "scale": {"min": 1, "max": 3, "step": 1, "min_label": "Low", "max_label": "High"},
                }
            ],
        }
    )


def test_initialize_creates_configured_database(tmp_path: Path):
    database_file_path = tmp_path / "poll.sqlite3"

    with connect(str(database_file_path)) as connection:
        assert not is_initialized(connection)
        initialize(connection, sample_config())
        assert is_initialized(connection)
        question_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    assert question_count == 1


def test_app_accepts_response_and_renders_results(tmp_path: Path, monkeypatch):
    database_file_path = tmp_path / "poll.sqlite3"
    monkeypatch.setenv("AUPOLL_DB_PATH", str(database_file_path))
    with connect(str(database_file_path)) as connection:
        initialize(connection, sample_config())

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    submit_response = client.post("/submit", data={"q1": "3"})
    assert submit_response.status_code == 302

    results_response = client.get("/results")
    assert results_response.status_code == 200
    body = results_response.get_data(as_text=True)
    assert "Test Results" in body
    assert "Mean" in body
    assert "3" in body

