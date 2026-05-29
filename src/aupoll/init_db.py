from __future__ import annotations

import os

from .config import load_config
from .db import connect, initialize, is_initialized


def main() -> int:
    config_path = os.environ.get("AUPOLL_CONFIG_PATH", "/config/poll.yaml")
    with connect() as connection:
        if is_initialized(connection):
            print("AUpoll database already initialized; nothing to do.")
            return 0
        config = load_config(config_path)
        initialize(connection, config)
        print(f"AUpoll database initialized from {config_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

