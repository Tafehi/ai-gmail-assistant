# AI Gmail Assistant — Talk to Your Gmail

Talk to your Gmail — literally. Use your voice or type natural language to manage your inbox. Search, read, label, categorize, clean, and bulk-delete emails without ever opening Gmail.

![Demo](pics/demo.gif)

## Features

- **Voice input** — click the mic and speak your commands (Chrome/Edge)
- **Multi-LLM chat** — Anthropic Claude, OpenAI GPT-4o, Azure OpenAI, AWS Bedrock
- **Read emails** — ask who sent your latest email, when, and what it says
- **Auto-label** — "label my 5 latest emails based on content" — AI picks categories and colors
- **Bulk delete** — "delete all emails before 2023" with dry-run safety
- **Clean categories** — wipe Promotions, Social, or Updates tabs in one command
- **Animated UI** — dark theme with particle network background and typing indicators
- **CLI + Web** — use the chat UI or the `gmail-cleaner` command-line tool
- **Skills as prompts** — `.claude/skills/*.md` loaded as system context for any LLM
- **CI/CD** — GitHub Actions with security scanning, linting, type checking, and tests

## Quick Start

```bash
git clone https://github.com/Tafehi/ai-gmail-cleaner.git
cd ai-gmail-cleaner
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # Add your LLM API key
gmail-cleaner auth           # Authenticate with Gmail
python main.py               # Open http://localhost:8000
```

## How It Works

```
Voice/Text → Browser → FastAPI → LangGraph Agent → Gmail API
                                      ↓
                              LLM (OpenAI/Claude/Bedrock)
                                      ↓
                              Gmail Tools (read, label, delete, search)
```

1. You speak or type a command in the browser
2. FastAPI passes it to a LangGraph ReAct agent with your chosen LLM
3. The agent decides which Gmail tools to call (read, search, label, delete)
4. Tools execute against the Gmail API and return results
5. The agent summarizes what happened and responds

## Voice Input

Click the **microphone button** next to the input field:
- Button turns red and pulses while listening
- Speak your command naturally ("what is my latest email")
- When you stop talking, the message auto-sends
- Works in **Chrome** and **Edge** (uses Web Speech API)

## Supported LLM Providers

Configure your API key in `.env`:

| Provider | Key | Models |
|----------|-----|--------|
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4, claude-haiku-4 |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` + endpoint | gpt-4o, gpt-4o-mini |
| AWS Bedrock | `AWS_ACCESS_KEY_ID` + secret | claude-sonnet-4, titan |

Switch providers and models from the sidebar dropdown — no restart needed.

## Example Commands

Say or type any of these:

| Command | What it does |
|---------|-------------|
| "How many emails do I have?" | Shows total, deletable, and protected counts |
| "What is my latest email?" | Reads subject, sender, date, and content |
| "Search for emails from Amazon" | Lists matching email subjects |
| "Label my 5 latest emails based on content" | AI categorizes and applies colored labels |
| "Clean my promotions tab" | Deletes all promotions except current month |
| "Delete emails before March 2024" | Dry-run preview of deletion |

## CLI Commands

```bash
gmail-cleaner auth                              # OAuth flow
gmail-cleaner status                            # Email counts
gmail-cleaner keep --count 1000                 # Protect latest N emails
gmail-cleaner delete --before 03.2024           # Dry-run delete
gmail-cleaner delete --before 03.2024 --no-dry-run  # Actually delete
gmail-cleaner clean promotions                  # Clean a category
gmail-cleaner label "Finance" -q "subject:invoice" --color green
gmail-cleaner chat                              # Launch web UI
```

**Label colors:** `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `teal`, `gray`, `pink`

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Gmail API**
3. Create **OAuth client ID** (Desktop app type)
4. Add your email as a test user in the consent screen
5. Download the JSON → save as `credentials.json` in project root

## Safety

- **Dry-run by default** — requires explicit confirmation to delete
- **Keep label** — protected emails are never deleted
- **Irreversible deletion** — `batchDelete` permanently removes (no trash)
- **Security scanning** — Bandit + dependency checks on every push

## Architecture

```
main.py                     # FastAPI app (serves UI + API)
static/index.html           # Chat UI with voice, particles, dark theme
src/
├── gmail/                  # Gmail API layer
│   ├── auth.py             # OAuth2 flow + token caching
│   ├── client.py           # API wrapper (list, delete, modify, labels, read)
│   ├── config.py           # .env loading + date parsing
│   ├── delete.py           # Bulk deletion logic
│   └── keep.py             # "Keep" label protection
├── llm/
│   └── agent.py            # LangGraph agent, 8 Gmail tools, provider switching
└── cli.py                  # Click CLI (auth, status, keep, delete, clean, label, chat)
```

## Claude Code Skills

| Skill | Description |
|-------|-------------|
| `gmail` | General Gmail management — status, delete, clean, keep, label |
| `gmail-auto-label` | AI reads subjects and auto-categorizes with colored labels |

Skills double as system prompts for the LangGraph agent — any LLM gets the same operational knowledge that Claude Code uses.

## CI/CD

GitHub Actions on every push:
- **Security** — Bandit static analysis
- **Tests** — pytest (config parsing + FastAPI endpoints)
- **Lint** — Ruff lint + format + mypy type checking
