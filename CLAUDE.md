# AI Gmail Assistant

## Overview

AI-powered Gmail management via Claude Code skills. Talk to your Gmail in natural language — search, label, categorize, clean, and bulk-delete emails without touching the Gmail UI.

## Setup

- Python 3.10+, dependencies in `pyproject.toml`
- Requires Google Cloud project with Gmail API enabled + OAuth Desktop credentials
- OAuth credentials go in `credentials.json` (gitignored), token auto-saved to `token.json`
- Configuration via `.env` (copy from `.env.example`)

## Commands

```bash
source .venv/bin/activate

gmail-cleaner auth                              # OAuth flow
gmail-cleaner status                            # Email counts
gmail-cleaner keep --count 1000                 # Label latest N as "Keep"
gmail-cleaner delete --before 03.2024           # Dry-run delete before date
gmail-cleaner delete --before 03.2024 --no-dry-run  # Actually delete
gmail-cleaner clean promotions                  # Delete all promotions except current month
gmail-cleaner clean social --keep-month 05.2026 # Delete social, keep specific month
gmail-cleaner label "Finance" -q "subject:invoice" --color green  # Label emails by query
gmail-cleaner label "Shopping" -q "from:amazon" --color orange --max 100
```

## Label Colors

Available: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `teal`, `gray`, `pink`

## Date Formats

`2024`, `03.2024`, `15.03.2024`, `2024-03`, `2024-03-15`

## Skills

- `.claude/skills/gmail.md` — General Gmail management (status, delete, clean, keep)
- `.claude/skills/gmail-auto-label.md` — AI-powered auto-labeling by reading email subjects

## Architecture

```
src/gmail_cleaner/
├── __main__.py   # Click CLI entry point (auth, status, keep, delete, clean, label)
├── auth.py       # OAuth2 flow + token caching
├── client.py     # Gmail API wrapper (list, batchDelete, batchModify, labels, subjects)
├── config.py     # .env loading + date parsing
├── delete.py     # Bulk deletion logic
└── keep.py       # "Keep" label logic
```

## Key Details

- Uses `https://mail.google.com/` scope (full access for deletion)
- `messages.batchDelete` permanently deletes up to 1000 per call — irreversible
- `category:promotions` query targets the Promotions tab without affecting other labels
- Dry-run mode is ON by default; requires explicit `--no-dry-run` to delete
- Gmail MCP server config is in `.claude/settings.json` for interactive use via Claude
- `client.list_messages_with_subjects()` fetches message IDs + subjects for AI categorization
