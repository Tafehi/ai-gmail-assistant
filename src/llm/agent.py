from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool

from src.gmail.auth import get_credentials
from src.gmail.client import GmailClient
from src.gmail.config import load_config, parse_date_input
from src.gmail.delete import build_delete_query, execute_deletion
from src.gmail.keep import label_latest_as_keep

PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "env_keys": ["OPENAI_API_KEY"],
    },
    "Azure OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "env_keys": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
    },
    "AWS Bedrock": {
        "models": [
            "anthropic.claude-sonnet-4-20250514-v1:0",
            "anthropic.claude-haiku-4-20250414-v1:0",
            "amazon.titan-text-premier-v1:0",
        ],
        "env_keys": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    },
    "Anthropic": {
        "models": ["claude-sonnet-4-20250514", "claude-haiku-4-20250414"],
        "env_keys": ["ANTHROPIC_API_KEY"],
    },
}

COLOR_MAP = {
    "red": ("#cc3a21", "#ffffff"),
    "blue": ("#285bac", "#ffffff"),
    "green": ("#076239", "#ffffff"),
    "yellow": ("#f2c960", "#000000"),
    "purple": ("#653e9b", "#ffffff"),
    "orange": ("#fa903e", "#ffffff"),
    "teal": ("#2da2bb", "#ffffff"),
    "gray": ("#666666", "#ffffff"),
    "pink": ("#b65775", "#ffffff"),
}


def _get_project_root() -> Path:
    path = Path(__file__).resolve().parent.parent.parent
    if (path / ".claude" / "skills").exists():
        return path
    cwd = Path.cwd()
    if (cwd / ".claude" / "skills").exists():
        return cwd
    return path


def _get_gmail_client() -> tuple[GmailClient, object]:
    config = load_config()
    creds = get_credentials(config.credentials_path, config.token_path)
    return GmailClient(creds), config


def load_skills_as_system_prompt() -> str:
    skills_dir = _get_project_root() / ".claude" / "skills"
    parts = []
    for md_file in sorted(skills_dir.glob("*.md")):
        content = md_file.read_text()
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                content = content[end + 3:].strip()
        parts.append(content)

    skills_content = "\n\n---\n\n".join(parts)
    return (
        "You are an AI Gmail assistant. You have access to tools that interact with "
        "the user's Gmail account.\n\n"
        "## Operational Knowledge\n\n"
        "The following instructions describe available Gmail operations:\n\n"
        f"{skills_content}\n\n"
        "## Instructions\n\n"
        "- Always confirm before deleting emails (use dry-run first)\n"
        "- Show counts before destructive operations\n"
        "- Use Gmail search query syntax for precise matching\n"
        "- Default to dry-run mode for deletions\n"
        "- Available label colors: red, blue, green, yellow, purple, orange, teal, gray, pink\n"
        "- Use gmail_read (not gmail_search) when the user asks about email content, sender, or date\n"
        "- Use gmail_label_by_id when labeling specific emails you already have IDs for\n"
        "- IMPORTANT: After every action, provide a brief human-readable summary of what was done. "
        "For labeling, list each email subject with the label applied. "
        "For reading, show sender, date, and content. "
        "For deletion, confirm how many were deleted. Never respond with just a symbol or empty message.\n"
    )


def get_llm(provider: str, model: str):
    load_dotenv()

    if provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=os.getenv("OPENAI_API_KEY"))

    elif provider == "Azure OpenAI":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", model),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        )

    elif provider == "AWS Bedrock":
        from langchain_aws import ChatBedrock
        return ChatBedrock(
            model_id=model,
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )

    elif provider == "Anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=os.getenv("ANTHROPIC_API_KEY"))

    raise ValueError(f"Unknown provider: {provider}")


def check_provider_credentials(provider: str) -> str | None:
    load_dotenv()
    info = PROVIDERS.get(provider)
    if not info:
        return f"Unknown provider: {provider}"
    missing = [k for k in info["env_keys"] if not os.getenv(k)]
    if missing:
        return f"Missing credentials in .env: {', '.join(missing)}"
    return None


# --- LangChain Tools ---


def _safe_gmail_call(func):
    """Wrap Gmail API calls to catch errors and return readable messages."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_detail = str(e) or repr(e)
            if hasattr(e, 'content'):
                error_detail = e.content.decode() if isinstance(e.content, bytes) else str(e.content)
            elif hasattr(e, 'reason'):
                error_detail = e.reason
            return f"Gmail API error: {error_detail}"
    return wrapper


@tool
def gmail_status() -> str:
    """Get current email counts: total emails, deletable (before configured date), and emails labeled Keep."""
    return _safe_gmail_call(_gmail_status_impl)()

def _gmail_status_impl():
    client, config = _get_gmail_client()
    total = client.count_messages("")
    query = build_delete_query(config.delete_before_date)
    deletable = client.count_messages(query)
    keep_count = client.count_messages("label:Keep")
    return (
        f"Total emails: {total:,}\n"
        f"Before {config.delete_before_date}: {deletable:,}\n"
        f"Labeled 'Keep': {keep_count:,}"
    )


@tool
def gmail_search(query: str, max_results: int = 20) -> str:
    """Search Gmail and return email subjects and IDs. Only returns subjects — use gmail_read to get full content, sender, and date. Use Gmail search operators like from:, subject:, after:, before:, is:unread."""
    return _safe_gmail_call(_gmail_search_impl)(query, max_results)

def _gmail_search_impl(query, max_results):
    client, _ = _get_gmail_client()
    messages = client.list_messages_with_subjects(query, max_results)
    if not messages:
        return "No emails found matching that query."
    lines = [f"- {m['subject']} (id: {m['id']})" for m in messages]
    return f"Found {len(messages)} emails:\n" + "\n".join(lines)


@tool
def gmail_read(message_id: str = "", query: str = "", max_results: int = 5) -> str:
    """Read full email details: subject, sender (from), date, and content snippet. ALWAYS use this tool when the user asks about email content, who sent it, or when it was received. Pass query='' for latest emails, or a specific query to filter."""
    return _safe_gmail_call(_gmail_read_impl)(message_id, query, max_results)

def _gmail_read_impl(message_id, query, max_results):
    client, _ = _get_gmail_client()

    if message_id:
        detail = client.get_message_detail(message_id)
        return (
            f"Subject: {detail['subject']}\n"
            f"From: {detail['from']}\n"
            f"To: {detail['to']}\n"
            f"Date: {detail['date']}\n"
            f"Content: {detail['snippet']}"
        )

    if not query:
        query = ""

    message_ids = client.list_message_ids(query, max_results)
    if not message_ids:
        return "No emails found."

    results = []
    for mid in message_ids:
        detail = client.get_message_detail(mid)
        results.append(
            f"---\n"
            f"Subject: {detail['subject']}\n"
            f"From: {detail['from']}\n"
            f"Date: {detail['date']}\n"
            f"Content: {detail['snippet']}\n"
        )
    return f"Found {len(results)} emails:\n" + "\n".join(results)


@tool
def gmail_delete(query: str, confirm: bool = False) -> str:
    """Delete emails matching a Gmail query. First call with confirm=False to see the count, then confirm=True to actually delete. This is IRREVERSIBLE."""
    return _safe_gmail_call(_gmail_delete_impl)(query, confirm)

def _gmail_delete_impl(query, confirm):
    client, config = _get_gmail_client()
    message_ids = client.list_message_ids(query)
    if not message_ids:
        return "No emails found matching that query."
    if not confirm:
        return (
            f"Found {len(message_ids):,} emails matching '{query}'. "
            f"Call again with confirm=True to permanently delete them."
        )
    execute_deletion(client, message_ids, config.batch_size)
    return f"Permanently deleted {len(message_ids):,} emails."


@tool
def gmail_label(label_name: str, query: str, color: str = "", max_results: int = 500) -> str:
    """Apply a label to emails matching a Gmail search query. Use this for bulk labeling by pattern. Optional color: red, blue, green, yellow, purple, orange, teal, gray, pink."""
    return _safe_gmail_call(_gmail_label_impl)(label_name, query, color, max_results)

def _gmail_label_impl(label_name, query, color, max_results):
    client, config = _get_gmail_client()

    bg_color, text_color = None, None
    if color:
        if color.lower() in COLOR_MAP:
            bg_color, text_color = COLOR_MAP[color.lower()]
        else:
            return f"Unknown color '{color}'. Available: {', '.join(COLOR_MAP.keys())}"

    label_id = client.get_or_create_label(label_name, bg_color, text_color)
    message_ids = client.list_message_ids(query, max_results)

    if not message_ids:
        return "No emails found matching that query."

    for i in range(0, len(message_ids), config.batch_size):
        batch = message_ids[i : i + config.batch_size]
        client.batch_modify(batch, add_label_ids=[label_id])

    return f"Labeled {len(message_ids):,} emails as '{label_name}'."


@tool
def gmail_label_by_id(label_name: str, message_ids: str, color: str = "") -> str:
    """Apply a label to specific emails by their message IDs. Use this when you know the exact email IDs (from gmail_search or gmail_read). Pass message_ids as comma-separated IDs. Optional color: red, blue, green, yellow, purple, orange, teal, gray, pink."""
    return _safe_gmail_call(_gmail_label_by_id_impl)(label_name, message_ids, color)

def _gmail_label_by_id_impl(label_name, message_ids, color):
    client, _ = _get_gmail_client()

    bg_color, text_color = None, None
    if color:
        if color.lower() in COLOR_MAP:
            bg_color, text_color = COLOR_MAP[color.lower()]
        else:
            return f"Unknown color '{color}'. Available: {', '.join(COLOR_MAP.keys())}"

    label_id = client.get_or_create_label(label_name, bg_color, text_color)
    ids = [mid.strip() for mid in message_ids.split(",") if mid.strip()]

    if not ids:
        return "No message IDs provided."

    client.batch_modify(ids, add_label_ids=[label_id])
    return f"Successfully labeled {len(ids)} emails as '{label_name}' (color: {color or 'default'}). Message IDs: {', '.join(ids[:5])}"


@tool
def gmail_clean_category(category: str, keep_month: str = "", confirm: bool = False) -> str:
    """Delete all emails in a category (promotions, social, updates, or forums) except the specified month. Use keep_month format: MM.YYYY (e.g. '05.2026'). Defaults to current month if not specified."""
    return _safe_gmail_call(_gmail_clean_category_impl)(category, keep_month, confirm)

def _gmail_clean_category_impl(category, keep_month, confirm):
    valid = ("promotions", "social", "updates", "forums")
    if category.lower() not in valid:
        return f"Invalid category. Choose from: {', '.join(valid)}"

    client, config = _get_gmail_client()

    if keep_month:
        keep_date = parse_date_input(keep_month)
    else:
        today = date.today()
        keep_date = date(today.year, today.month, 1)

    query = f"category:{category} before:{keep_date.year}/{keep_date.month:02d}/{keep_date.day:02d}"
    message_ids = client.list_message_ids(query)

    if not message_ids:
        return f"No {category} emails found to delete."

    if not confirm:
        return (
            f"Found {len(message_ids):,} {category} emails before {keep_date.strftime('%B %Y')}. "
            f"Call again with confirm=True to permanently delete them."
        )

    execute_deletion(client, message_ids, config.batch_size)
    return f"Permanently deleted {len(message_ids):,} {category} emails."


@tool
def gmail_keep(count: int = 1000) -> str:
    """Label the latest N emails with 'Keep' to protect them from deletion."""
    return _safe_gmail_call(_gmail_keep_impl)(count)

def _gmail_keep_impl(count):
    client, config = _get_gmail_client()
    labeled = label_latest_as_keep(client, count, batch_size=config.batch_size)
    return f"Labeled {labeled:,} emails as 'Keep'."


GMAIL_TOOLS = [gmail_status, gmail_search, gmail_read, gmail_delete, gmail_label, gmail_label_by_id, gmail_clean_category, gmail_keep]


def create_agent(provider: str, model: str):
    llm = get_llm(provider, model)
    if llm is None:
        return None

    from langgraph.prebuilt import create_react_agent

    system_prompt = load_skills_as_system_prompt()
    agent = create_react_agent(llm, GMAIL_TOOLS, prompt=system_prompt)
    return agent
