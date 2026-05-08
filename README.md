# AI Gmail Assistant — Talk to Your Gmail Using LLM & Skills

Talk to your Gmail using AI. Manage your inbox through natural language — search, read, label, auto-categorize, clean categories, and bulk-delete old emails. Use the **web chat UI** with any LLM provider (Anthropic, OpenAI, Azure, AWS Bedrock) or **Claude Code skills** directly.

## Features

- **Modern dark chat UI** — FastAPI + vanilla HTML/CSS/JS with animations and typing indicators
- **Multi-LLM support** — Anthropic Claude, OpenAI GPT, Azure OpenAI, AWS Bedrock via LangChain
- **Natural language control** — ask the AI to manage your email in plain English
- **AI auto-labeling** — reads email subjects and auto-categorizes with colored labels
- **Smart labeling** — apply labels with colors to emails matching any Gmail query
- **Bulk delete by date** — permanently remove all emails before a specific date
- **Clean categories** — delete all Promotions, Social, Updates, or Forums emails except the current month
- **Keep label** — protect your latest N emails from deletion
- **Dry-run by default** — always preview before deleting
- **Skills as prompts** — `.claude/skills/*.md` are loaded as system context for any LLM
- **CI/CD** — GitHub Actions with security scanning, linting, and functional tests

## How It Works

```
Browser (static/index.html) ←→ FastAPI (main.py) ←→ LangGraph Agent (src/llm/) ←→ Gmail API (src/gmail/)
```

1. **FastAPI backend** (`main.py`) — serves the chat page and API endpoints
2. **LangChain + LangGraph** (`src/llm/`) — ReAct agent with Gmail tools and provider switching
3. **Gmail API wrapper** (`src/gmail/`) — powers the actual operations (delete, label, clean)
4. **Claude Code Skills** (`.claude/skills/`) — operational knowledge loaded as system prompts
5. **Gmail MCP Server** — lets Claude search and read your emails directly

### Request Flow

1. User opens `http://localhost:8000` → FastAPI serves `static/index.html`
2. JS fetches `GET /api/providers` → populates provider/model dropdowns
3. JS fetches `GET /api/status` → shows green dot if Gmail is authenticated
4. User types a message → JS `POST /api/chat` with `{message, provider, model, history}`
5. FastAPI creates (or retrieves cached) LangGraph agent for that provider/model
6. Agent reads skills system prompt, binds Gmail tools, processes the message
7. Agent may call tools (`gmail_search`, `gmail_status`, etc.) which hit the Gmail API
8. Final response returned as JSON → JS renders it with typing animation

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the chat HTML page |
| GET | `/api/providers` | Lists available LLM providers and models |
| GET | `/api/status` | Checks Gmail authentication status |
| POST | `/api/chat` | Main chat endpoint — sends message to LLM agent |
| POST | `/api/auth` | Triggers Gmail OAuth flow |

## Prerequisites

- Python 3.10+
- A Google Cloud project with Gmail API enabled
- At least one LLM provider API key (Anthropic, OpenAI, Azure, or AWS)

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. **APIs & Services > Library** — search and enable **Gmail API**
4. **APIs & Services > Credentials** — click **Create Credentials > OAuth client ID**
5. Configure the OAuth consent screen:
   - Choose "External" user type
   - Add your email as a **test user**
6. Create OAuth client ID:
   - Application type: **Desktop app**
   - Download the JSON and save as `credentials.json` in the project root

## Installation

```bash
git clone https://github.com/Tafehi/ai-gmail-cleaner.git
cd ai-gmail-cleaner
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your settings:

```env
DELETE_BEFORE_DATE=03.2024
KEEP_LATEST_COUNT=1000
DRY_RUN=true

# Add at least one LLM provider key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
```

## Web Chat UI

Launch the chat interface:

```bash
python main.py
```

Or via CLI:

```bash
gmail-cleaner chat
```

Then open **http://localhost:8000** in your browser.

### Provider Selection

Select your LLM provider and model from the header dropdowns:

| Provider | Required .env Keys |
|----------|-------------------|
| **Anthropic** (default) | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |

### Gmail Authentication

Run `gmail-cleaner auth` from the terminal on first use — it opens a browser for Google OAuth consent.

### Example Prompts

- *"How many emails do I have?"*
- *"Search for emails from Amazon"*
- *"Label all emails from Netflix as Entertainment with orange color"*
- *"Clean my promotions tab"*
- *"Delete emails before 2023"*

## CLI Commands

### Authenticate

```bash
gmail-cleaner auth
```

### Check Status

```bash
gmail-cleaner status
```

### Protect Recent Emails

```bash
gmail-cleaner keep
gmail-cleaner keep --count 2000
```

### Delete Old Emails

```bash
gmail-cleaner delete                              # Dry-run preview
gmail-cleaner delete --before 03.2024             # Override date
gmail-cleaner delete --before 03.2024 --no-dry-run  # Actually delete
```

### Clean a Category

```bash
gmail-cleaner clean promotions                    # Keep current month only
gmail-cleaner clean promotions --keep-month 05.2026
gmail-cleaner clean social --no-dry-run
gmail-cleaner clean updates
gmail-cleaner clean forums
```

### Label Emails

```bash
gmail-cleaner label "Finance" -q "subject:invoice" --color green
gmail-cleaner label "Shopping" -q "from:amazon" --color orange
gmail-cleaner label "Work" -q "from:@company.com" --color purple --max 200
```

**Available colors:** `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `teal`, `gray`, `pink`

## Claude Code Skills

| Skill | Description |
|-------|-------------|
| `gmail` | General Gmail management — status, delete, clean, keep, label |
| `gmail-auto-label` | AI reads email subjects and auto-categorizes with colored labels |

Skills are also loaded as system prompts for the LangGraph agent — any LLM gets the same operational knowledge.

## MCP Integration

The Gmail MCP server config is in `.claude/settings.json`. Add your OAuth credentials to enable Claude to search, read, and label emails interactively via Google's official MCP endpoint.

## Safety

- **Dry-run by default** — requires explicit `--no-dry-run` or `confirm=True` to delete
- **Confirmation prompt** — asks before executing deletion
- **Keep label exclusion** — emails labeled "Keep" are never deleted
- **Irreversible** — `batchDelete` permanently removes emails with no recovery
- **Security scans** — Bandit + Safety run on every push via GitHub Actions

## CI/CD

GitHub Actions runs on every push and PR:
- **Security** — Bandit static analysis + dependency vulnerability scan
- **Tests** — pytest functional tests for config parsing, query building, and FastAPI endpoints
- **Lint** — Ruff linting + formatting + mypy type checking

## Project Structure

```
├── main.py                     # FastAPI app entry point
├── requirements.txt            # All dependencies
├── static/
│   └── index.html              # Chat UI (HTML/CSS/JS)
├── .claude/
│   ├── settings.json           # Gmail MCP server config
│   └── skills/
│       ├── gmail.md            # General Gmail management skill
│       └── gmail-auto-label.md # AI auto-labeling skill
├── .github/workflows/ci.yml    # Security + tests + lint
├── src/
│   ├── gmail/
│   │   ├── auth.py             # OAuth2 flow + token caching
│   │   ├── client.py           # Gmail API wrapper
│   │   ├── config.py           # .env loading + date parsing
│   │   ├── delete.py           # Bulk deletion logic
│   │   └── keep.py             # "Keep" label logic
│   ├── llm/
│   │   └── agent.py            # LangGraph agent, provider switching, Gmail tools
│   └── cli.py                  # Click CLI (auth, status, keep, delete, clean, label, chat)
└── tests/                      # Functional + API tests
```
