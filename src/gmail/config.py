import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    delete_before_date: date
    keep_latest_count: int
    credentials_path: Path
    token_path: Path
    dry_run: bool
    batch_size: int


def parse_date_input(value: str) -> date:
    value = value.strip()
    if len(value) == 4 and value.isdigit():
        return date(int(value), 1, 1)
    # Handle dot format: MM.YYYY or DD.MM.YYYY
    if "." in value:
        parts = value.split(".")
        if len(parts) == 2:
            return date(int(parts[1]), int(parts[0]), 1)
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    # Handle dash/slash format: YYYY-MM or YYYY-MM-DD
    parts = value.replace("/", "-").split("-")
    if len(parts) == 2:
        return date(int(parts[0]), int(parts[1]), 1)
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    raise ValueError(f"Cannot parse date: '{value}'. Use YYYY, MM.YYYY, or YYYY-MM-DD.")


def load_config(env_path: Path | None = None) -> Config:
    load_dotenv(env_path or Path(".env"))

    delete_before = os.getenv("DELETE_BEFORE_DATE")
    if not delete_before:
        raise ValueError("DELETE_BEFORE_DATE is required in .env")

    keep_count = int(os.getenv("KEEP_LATEST_COUNT", "1000"))
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json"))
    batch_size = min(int(os.getenv("BATCH_SIZE", "1000")), 1000)
    dry_run = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

    return Config(
        delete_before_date=parse_date_input(delete_before),
        keep_latest_count=keep_count,
        credentials_path=credentials_path,
        token_path=token_path,
        dry_run=dry_run,
        batch_size=batch_size,
    )
