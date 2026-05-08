# AI Gmail Cleaner

Bulk delete old Gmail emails and preserve recent ones. Free up storage by permanently removing emails before a given date, while protecting your latest emails with a "Keep" label.

## Prerequisites

- Python 3.10+
- A Google Cloud project

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Navigate to **APIs & Services > Library**
4. Search for and enable **Gmail API**
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials > OAuth client ID**
7. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Add your email as a test user
   - Add scope: `https://mail.google.com/`
8. Select **Desktop app** as application type
9. Download the JSON file and save as `credentials.json` in the project root

## Installation

```bash
git clone https://github.com/Tafehi/ai-gmail-cleaner.git
cd ai-gmail-cleaner
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `.env` with your settings:

```env
DELETE_BEFORE_DATE=2024
KEEP_LATEST_COUNT=1000
DRY_RUN=true
```

## Usage

### 1. Authenticate

```bash
gmail-cleaner auth
```

Opens your browser for Google OAuth consent. Token is cached locally in `token.json`.

### 2. Check Status

```bash
gmail-cleaner status
```

Shows total emails, count before your target date, and how many have the "Keep" label.

### 3. Protect Recent Emails

```bash
gmail-cleaner keep
gmail-cleaner keep --count 2000
```

Labels your latest N emails with "Keep" so they're excluded from deletion.

### 4. Delete Old Emails

```bash
# Preview (dry-run, default)
gmail-cleaner delete

# Actually delete
gmail-cleaner delete --no-dry-run

# Override date
gmail-cleaner delete --before 2020 --no-dry-run
```

Permanently deletes all emails before the configured date, excluding those labeled "Keep". Searches across all categories (Inbox, Social, Promotions, Updates, Forums).

## Recommended Workflow

1. `gmail-cleaner auth` — authenticate
2. `gmail-cleaner keep --count 1000` — protect latest 1000 emails
3. `gmail-cleaner delete` — preview what would be deleted
4. `gmail-cleaner delete --no-dry-run` — permanently delete

## MCP Setup (Claude Desktop)

For interactive email management through Claude, add the Gmail MCP server to your Claude Desktop config.

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

See `claude_desktop_config.json` in this repo for the configuration template. Replace `<YOUR_CLIENT_ID>` and `<YOUR_CLIENT_SECRET>` with your OAuth credentials from Google Cloud Console.

The MCP server enables Claude to search, read, and label your emails interactively. It does not support permanent deletion (use the CLI for that).

## Safety

- **Dry-run by default** — deletion requires explicit `--no-dry-run`
- **Confirmation prompt** — asks before executing deletion
- **Keep label exclusion** — emails labeled "Keep" are never deleted
- **Irreversible** — `batchDelete` permanently removes emails with no recovery
