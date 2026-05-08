from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GmailClient:
    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials)

    def list_message_ids(self, query: str, max_results: int | None = None) -> list[str]:
        message_ids = []
        page_token = None

        while True:
            kwargs = {"userId": "me", "q": query, "maxResults": 500}
            if page_token:
                kwargs["pageToken"] = page_token

            response = self.service.users().messages().list(**kwargs).execute()
            messages = response.get("messages", [])
            message_ids.extend(msg["id"] for msg in messages)

            if max_results and len(message_ids) >= max_results:
                return message_ids[:max_results]

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return message_ids

    def count_messages(self, query: str) -> int:
        count = 0
        page_token = None

        while True:
            kwargs = {"userId": "me", "q": query, "maxResults": 500}
            if page_token:
                kwargs["pageToken"] = page_token

            response = self.service.users().messages().list(**kwargs).execute()
            messages = response.get("messages", [])
            count += len(messages)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return count

    def batch_delete(self, message_ids: list[str]) -> None:
        self.service.users().messages().batchDelete(
            userId="me", body={"ids": message_ids}
        ).execute()

    def batch_modify(self, message_ids: list[str], add_label_ids: list[str]) -> None:
        self.service.users().messages().batchModify(
            userId="me",
            body={"ids": message_ids, "addLabelIds": add_label_ids},
        ).execute()

    def get_or_create_label(self, label_name: str, bg_color: str | None = None, text_color: str | None = None) -> str:
        results = self.service.users().labels().list(userId="me").execute()
        for label in results.get("labels", []):
            if label["name"] == label_name:
                return label["id"]

        body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        if bg_color and text_color:
            body["color"] = {"backgroundColor": bg_color, "textColor": text_color}

        created = self.service.users().labels().create(userId="me", body=body).execute()
        return created["id"]

    def get_message_subject(self, message_id: str) -> str:
        msg = self.service.users().messages().get(
            userId="me", id=message_id, format="metadata", metadataHeaders=["Subject"]
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])
        for h in headers:
            if h["name"] == "Subject":
                return h["value"]
        return "(no subject)"

    def list_messages_with_subjects(self, query: str, max_results: int | None = None) -> list[dict]:
        message_ids = self.list_message_ids(query, max_results)
        results = []
        for mid in message_ids:
            subject = self.get_message_subject(mid)
            results.append({"id": mid, "subject": subject})
        return results

    def list_labels(self) -> list[dict]:
        results = self.service.users().labels().list(userId="me").execute()
        return results.get("labels", [])
