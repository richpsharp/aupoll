# AUpoll

Actually useful polls, configured from a small YAML file and backed by SQLite.

## Run locally with Docker Compose

The initializer is a one-shot container. It reads `config/poll.yaml`, creates the
SQLite database in the `aupoll_data` volume, and exits. If the database is
already initialized, it exits successfully without changing it.

```sh
docker compose run --rm init
docker compose up app
```

Open http://localhost:8000.

To reset the poll database during development:

```sh
docker compose down -v
```

Run the Python test suite locally with:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Configuration

Edit `config/poll.yaml` before running the initializer.

```yaml
poll:
  title: "AUpoll"
  subtitle: "A small poll with useful results."
questions:
  - id: clarity
    prompt: "How clear was the proposal?"
    scale:
      min: 1
      max: 7
      step: 1
      min_label: "Not clear"
      max_label: "Very clear"
```

The current app supports numeric scale questions so it can compute histograms,
mean, median, standard deviation, and 5th/95th percentiles.
