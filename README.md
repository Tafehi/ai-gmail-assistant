# AI Gmail Assistant

Talk to your Gmail using AI. Search, read, label, and manage your inbox through natural language via Claude Code skills and Google's official Gmail MCP server — plus bulk delete old emails, clean categories, and free up storage without touching the Gmail UI.

## Features

- **Bulk delete by date** — permanently remove all emails before a specific date across all labels
- **Clean categories** — delete all Promotions, Social, Updates, or Forums emails except the current month
- **Keep label** — protect your latest N emails from deletion
- **Dry-run by default** — always preview before deleting
- **Date formats** — supports `2024`, `03.2024`, `15.03.2024`, `2024-03`, `2024-03-15`

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

## Usage

### Authenticate

```bash
gmail-cleaner auth
```

Opens your browser for Google OAuth consent. Token is cached in `token.json`.

### Check Status

```bash
gmail-cleaner status
```

Shows total emails, count before your target date, and how many have the "Keep" label.

### Protect Recent Emails

```bash
gmail-cleaner keep
gmail-cleaner keep --count 2000
```

Labels your latest N emails with "Keep" so they're excluded from bulk deletion.

### Delete Old Emails

```bash
# Preview what would be deleted (dry-run, default)
gmail-cleaner delete

# Override date from CLI
gmail-cleaner delete --before 03.2024

# Actually delete (requires confirmation)
gmail-cleaner delete --before 03.2024 --no-dry-run
```

Permanently deletes all emails before the configured date, excluding those labeled "Keep". Searches across all categories.

### Clean a Category

```bash
# Delete all promotions except current month
gmail-cleaner clean promotions

# Delete all promotions except a specific month
gmail-cleaner clean promotions --keep-month 05.2026

# Actually delete
gmail-cleaner clean promotions --no-dry-run

# Also works for: social, updates, forums
gmail-cleaner clean social
gmail-cleaner clean updates --keep-month 04.2026 --no-dry-run
```

Deletes all emails in a Gmail category while keeping only the specified month (defaults to current month).

## Recommended Workflow

```bash
gmail-cleaner auth                                  # 1. Authenticate
gmail-cleaner status                                # 2. Check counts
gmail-cleaner keep --count 1000                     # 3. Protect latest emails
gmail-cleaner delete --before 03.2024               # 4. Preview deletion
gmail-cleaner delete --before 03.2024 --no-dry-run  # 5. Delete old emails
gmail-cleaner clean promotions --no-dry-run         # 6. Clean promotions
```

## MCP Setup (Claude Code / Claude Desktop)

The Gmail MCP server config is in `.claude/settings.json`. Replace `<YOUR_CLIENT_ID>` and `<YOUR_CLIENT_SECRET>` with your OAuth credentials to enable interactive email management through Claude.

The MCP server supports searching, reading, and labeling emails. Permanent deletion is only available via the CLI.

## Safety

- **Dry-run by default** — requires explicit `--no-dry-run` to delete anything
- **Confirmation prompt** — asks before executing deletion
- **Keep label exclusion** — emails labeled "Keep" are never deleted by the `delete` command
- **Irreversible** — `batchDelete` permanently removes emails with no recovery

## Project Structure

```
src/gmail_cleaner/
├── __main__.py   # CLI entry point (auth, status, keep, delete, clean)
├── auth.py       # OAuth2 flow + token caching
├── client.py     # Gmail API wrapper
├── config.py     # .env loading + date parsing
├── delete.py     # Bulk deletion logic
└── keep.py       # "Keep" label logic
```
