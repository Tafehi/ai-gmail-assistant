# AI Gmail Assistant

## Overview

AI-powered Gmail management via web chat UI and Claude Code skills. Talk to your Gmail in natural language — search, label, categorize, clean, and bulk-delete emails without touching the Gmail UI.

## Setup

```bash
pip install -r requirements.txt
# Or: pip install -e .
gmail-cleaner auth                              # First-time OAuth
```

- Python 3.10+, dependencies in `requirements.txt` / `pyproject.toml`
- Requires Google Cloud project with Gmail API enabled + OAuth Desktop credentials
- OAuth credentials go in `credentials.json` (gitignored), token auto-saved to `token.json`
- Configuration via `.env` (copy from `.env.example`)

## Commands

```bash
gmail-cleaner auth                              # OAuth flow
gmail-cleaner status                            # Email counts
gmail-cleaner keep --count 1000                 # Label latest N as "Keep"
gmail-cleaner delete --before 03.2024           # Dry-run delete before date
gmail-cleaner delete --before 03.2024 --no-dry-run  # Actually delete
gmail-cleaner clean promotions                  # Delete all promotions except current month
gmail-cleaner clean social --keep-month 05.2026 # Delete social, keep specific month
gmail-cleaner label "Finance" -q "subject:invoice" --color green  # Label emails by query
gmail-cleaner label "Shopping" -q "from:amazon" --color orange --max 100
gmail-cleaner chat                              # Launch web chat UI
```

## Web Chat UI

Run the app:

```bash
python main.py
# Or: gmail-cleaner chat
# Opens at http://localhost:8000
```

### Supported Providers

Configure credentials in `.env`:

| Provider | Required .env Keys |
|----------|-------------------|
| Anthropic (default) | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |

### How It Works

- FastAPI serves `static/index.html` (dark chat UI) and exposes `/api/chat` endpoint
- LangGraph agent wraps `GmailClient` methods as tools (status, search, delete, label, clean, keep)
- `.claude/skills/*.md` files are loaded as system prompts — any LLM gets the same operational knowledge
- Provider and model selection via header dropdowns

## Label Colors

Available: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `teal`, `gray`, `pink`

## Date Formats

`2024`, `03.2024`, `15.03.2024`, `2024-03`, `2024-03-15`

## Skills

- `.claude/skills/gmail.md` — General Gmail management (status, delete, clean, keep)
- `.claude/skills/gmail-auto-label.md` — AI-powered auto-labeling by reading email subjects

## Architecture

```
main.py              # FastAPI app entry point (serves UI + API)
static/
└── index.html       # Chat UI (HTML/CSS/JS — modern dark theme)
src/
├── gmail/
│   ├── auth.py      # OAuth2 flow + token caching
│   ├── client.py    # Gmail API wrapper (list, batchDelete, batchModify, labels, subjects)
│   ├── config.py    # .env loading + date parsing
│   ├── delete.py    # Bulk deletion logic
│   └── keep.py      # "Keep" label logic
├── llm/
│   └── agent.py     # LangGraph agent: provider switching, Gmail tools, skills loading
└── cli.py           # Click CLI entry point (auth, status, keep, delete, clean, label, chat)
```

## Key Details

- Uses `https://mail.google.com/` scope (full access for deletion)
- `messages.batchDelete` permanently deletes up to 1000 per call — irreversible
- `category:promotions` query targets the Promotions tab without affecting other labels
- Dry-run mode is ON by default; requires explicit `--no-dry-run` to delete
- Gmail MCP server config is in `.claude/settings.json` for interactive use via Claude
- `client.list_messages_with_subjects()` fetches message IDs + subjects for AI categorization
- `client.get_message_detail()` fetches full email info (from, date, subject, snippet)

## LangGraph Agent Tools

| Tool | Purpose |
|------|---------|
| `gmail_status` | Email counts (total, deletable, kept) |
| `gmail_search` | Search by query, returns subjects + IDs only |
| `gmail_read` | Read full email details (sender, date, content snippet) |
| `gmail_delete` | Delete emails by query (requires confirm=True) |
| `gmail_label` | Label emails by Gmail search query |
| `gmail_label_by_id` | Label specific emails by message ID (comma-separated) |
| `gmail_clean_category` | Delete all in a category except specified month |
| `gmail_keep` | Protect latest N emails with Keep label |

## Lessons Learned / Dev Notes

- **LangChain 1.x moved agents to LangGraph** — use `from langgraph.prebuilt import create_react_agent`, NOT `from langchain.agents import AgentExecutor`
- **`recursion_limit` goes in `invoke()` config**, not in `create_react_agent()` — e.g. `agent.invoke({...}, config={"recursion_limit": 50})`
- **Don't name a folder `langchain/`** — conflicts with the installed package. Used `src/llm/` instead
- **Agent response extraction** — the last message may be a ToolMessage, not AIMessage. Loop backwards through `result["messages"]` to find the last AIMessage with content
- **API key errors appear as empty errors** — always include `type(e).__name__` in error responses for debugging
- **LLM tool descriptions drive behavior** — be very explicit about when to use each tool (e.g. "ALWAYS use gmail_read when user asks about content/sender/date")
- **Anthropic API requires billing** — `ANTHROPIC_API_KEY` needs credits loaded at console.anthropic.com. Switch to OpenAI if no Anthropic credits available
