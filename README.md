# AI Gmail Assistant — Talk to Your Gmail Using LLM & Skills

Talk to your Gmail using AI. Manage your inbox through natural language — search, read, label, auto-categorize, clean categories, and bulk-delete old emails using Claude Code skills and Google's official Gmail MCP server. No need to touch the Gmail UI.

## Features

- **Natural language control** — ask Claude to manage your email in plain English
- **AI auto-labeling** — reads email subjects and auto-categorizes with colored labels
- **Smart labeling** — apply labels with colors to emails matching any Gmail query
- **Bulk delete by date** — permanently remove all emails before a specific date across all labels
- **Clean categories** — delete all Promotions, Social, Updates, or Forums emails except the current month
- **Keep label** — protect your latest N emails from deletion
- **Dry-run by default** — always preview before deleting
- **CI/CD** — GitHub Actions with security scanning, linting, and functional tests
- **Date formats** — supports `2024`, `03.2024`, `15.03.2024`, `2024-03`, `2024-03-15`

## How It Works

This project combines:
1. **Claude Code Skills** (`.claude/skills/`) — teach Claude how to manage your Gmail
2. **Gmail MCP Server** — lets Claude search and read your emails directly
3. **Python CLI** — powers the actual Gmail API operations (delete, label, clean)

Just open Claude Code in this project and ask:
- *"Check my gmail status"*
- *"Delete all emails before March 2024"*
- *"Clean my promotions tab"*
- *"Label my latest 50 emails based on their subject"*
- *"Label all emails from Amazon as Shopping with orange color"*

## Prerequisites

- Python 3.10+
- A Google Cloud project with Gmail API enabled

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
pip install -e .
cp .env.example .env
```

Edit `.env` with your settings:

```env
DELETE_BEFORE_DATE=03.2024
KEEP_LATEST_COUNT=1000
DRY_RUN=true
```

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

## MCP Integration

The Gmail MCP server config is in `.claude/settings.json`. Add your OAuth credentials to enable Claude to search, read, and label emails interactively via Google's official MCP endpoint.

## Safety

- **Dry-run by default** — requires explicit `--no-dry-run` to delete anything
- **Confirmation prompt** — asks before executing deletion
- **Keep label exclusion** — emails labeled "Keep" are never deleted
- **Irreversible** — `batchDelete` permanently removes emails with no recovery
- **Security scans** — Bandit + Safety run on every push via GitHub Actions

## CI/CD

GitHub Actions runs on every push and PR:
- **Security** — Bandit static analysis + dependency vulnerability scan
- **Tests** — pytest functional tests for config parsing and query building
- **Lint** — Ruff linting + formatting + mypy type checking

## Project Structure

```
├── .claude/
│   ├── settings.json           # Gmail MCP server config
│   └── skills/
│       ├── gmail.md            # General Gmail management skill
│       └── gmail-auto-label.md # AI auto-labeling skill
├── .github/workflows/ci.yml    # Security + tests + lint
├── src/gmail_cleaner/
│   ├── __main__.py             # CLI (auth, status, keep, delete, clean, label)
│   ├── auth.py                 # OAuth2 flow + token caching
│   ├── client.py               # Gmail API wrapper
│   ├── config.py               # .env loading + date parsing
│   ├── delete.py               # Bulk deletion logic
│   └── keep.py                 # "Keep" label logic
└── tests/                      # Functional tests
```
