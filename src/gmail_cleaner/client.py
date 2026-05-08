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

    def get_estimated_count(self, query: str) -> int:
        response = self.service.users().messages().list(
            userId="me", q=query, maxResults=1
        ).execute()
        return response.get("resultSizeEstimate", 0)

    def batch_delete(self, message_ids: list[str]) -> None:
        self.service.users().messages().batchDelete(
            userId="me", body={"ids": message_ids}
        ).execute()

    def batch_modify(self, message_ids: list[str], add_label_ids: list[str]) -> None:
        self.service.users().messages().batchModify(
            userId="me",
            body={"ids": message_ids, "addLabelIds": add_label_ids},
        ).execute()

    def get_or_create_label(self, label_name: str) -> str:
        results = self.service.users().labels().list(userId="me").execute()
        for label in results.get("labels", []):
            if label["name"] == label_name:
                return label["id"]

        created = self.service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        return created["id"]
