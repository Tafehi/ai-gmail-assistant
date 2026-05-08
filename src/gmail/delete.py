from datetime import date

from .client import GmailClient


def build_delete_query(before_date: date, exclude_keep: bool = True) -> str:
    query = f"before:{before_date.year}/{before_date.month:02d}/{before_date.day:02d}"
    if exclude_keep:
        query += " -label:Keep"
    return query


def find_deletable_messages(
    client: GmailClient,
    before_date: date,
    exclude_keep: bool = True,
) -> list[str]:
    query = build_delete_query(before_date, exclude_keep)
    return client.list_message_ids(query)


def execute_deletion(
    client: GmailClient,
    message_ids: list[str],
    batch_size: int = 1000,
    progress_callback=None,
) -> int:
    total = len(message_ids)
    deleted = 0

    for i in range(0, total, batch_size):
        batch = message_ids[i : i + batch_size]
        client.batch_delete(batch)
        deleted += len(batch)
        if progress_callback:
            progress_callback(deleted, total)

    return deleted
