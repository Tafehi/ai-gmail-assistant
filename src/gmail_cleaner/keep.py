from .client import GmailClient


def label_latest_as_keep(
    client: GmailClient,
    count: int,
    label_name: str = "Keep",
    batch_size: int = 1000,
) -> int:
    label_id = client.get_or_create_label(label_name)
    message_ids = client.list_message_ids(query="", max_results=count)

    labeled = 0
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i : i + batch_size]
        client.batch_modify(batch, add_label_ids=[label_id])
        labeled += len(batch)

    return labeled
