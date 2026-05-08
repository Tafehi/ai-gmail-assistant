---
name: gmail
description: Manage Gmail - delete old emails, clean categories (promotions/social), label recent ones, check status
---

# Gmail Cleaner Skill

Run Gmail management commands from the project's Python CLI tool.

## Available Commands

### Status - Check email counts
```bash
source .venv/bin/activate && gmail-cleaner status
```

### Keep - Label latest N emails with "Keep" label
```bash
source .venv/bin/activate && gmail-cleaner keep
source .venv/bin/activate && gmail-cleaner keep --count 2000
```

### Delete - Permanently delete old emails
```bash
# Dry run (preview only)
source .venv/bin/activate && gmail-cleaner delete

# Override date
source .venv/bin/activate && gmail-cleaner delete --before 03.2024

# Actually delete (with confirmation)
source .venv/bin/activate && gmail-cleaner delete --no-dry-run
```

### Clean - Delete all emails in a category, keeping only a specific month
```bash
# Delete all promotions except current month (default)
source .venv/bin/activate && gmail-cleaner clean promotions

# Delete all promotions except a specific month
source .venv/bin/activate && gmail-cleaner clean promotions --keep-month 05.2026

# Works for: promotions, social, updates, forums
source .venv/bin/activate && gmail-cleaner clean social
source .venv/bin/activate && gmail-cleaner clean updates
source .venv/bin/activate && gmail-cleaner clean forums

# Actually delete (with confirmation)
source .venv/bin/activate && gmail-cleaner clean promotions --no-dry-run
```

### Auth - Re-authenticate
```bash
source .venv/bin/activate && gmail-cleaner auth
```

## Configuration

Edit `.env` to configure:
- `DELETE_BEFORE_DATE` - Date formats: `2024`, `03.2024`, `15.03.2024`, `2024-03`, `2024-03-15`
- `KEEP_LATEST_COUNT` - Number of latest emails to protect (default: 1000)
- `DRY_RUN` - Set to `false` to enable deletion (default: `true`)

## Workflow

1. Run `status` to see email counts
2. Run `keep` to protect your latest emails with a "Keep" label
3. Run `delete` (dry-run) to preview what would be removed
4. Run `delete --no-dry-run` to permanently delete old emails
5. Run `clean promotions` to clear out a specific category
