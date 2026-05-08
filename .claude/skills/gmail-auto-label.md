---
name: gmail-auto-label
description: Read email subjects and auto-label them with appropriate categories and colors based on content
---

# Gmail Auto-Label Skill

Automatically categorize and label emails by reading their subjects. Uses AI judgment to pick appropriate label names and colors.

## How to Use

When the user asks to auto-label their emails, follow this process:

### Step 1: Fetch email subjects

```bash
source .venv/bin/activate && python3 -c "
from gmail_cleaner.config import load_config
from gmail_cleaner.auth import get_credentials
from gmail_cleaner.client import GmailClient

config = load_config()
creds = get_credentials(config.credentials_path, config.token_path)
client = GmailClient(creds)

messages = client.list_messages_with_subjects('', max_results=50)
for m in messages:
    print(f\"{m['id']} | {m['subject']}\")
"
```

Adjust `max_results` and the query based on what the user asks (e.g., `'is:unread'`, `'after:2026/05/01'`).

### Step 2: Analyze subjects and decide labels

Read the subjects and group them into categories. Common categories:
- **Finance** — invoices, receipts, bank statements, payment confirmations
- **Shopping** — order confirmations, shipping updates, delivery notifications
- **Social** — social media notifications, friend requests, messages
- **Work** — meeting invites, project updates, team notifications
- **Travel** — flight confirmations, hotel bookings, travel updates
- **Newsletter** — weekly digests, blog updates, subscriptions
- **Security** — password resets, login alerts, 2FA codes
- **Personal** — personal correspondence

### Step 3: Apply labels with colors

Use the CLI to apply labels. Available colors: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `teal`, `gray`, `pink`.

Suggested color mapping:
- Finance → green
- Shopping → orange
- Social → blue
- Work → purple
- Travel → teal
- Newsletter → gray
- Security → red
- Personal → pink

```bash
# Apply labels by querying for specific patterns found in subjects
source .venv/bin/activate && gmail-cleaner label "Finance" -q "subject:(invoice OR receipt OR payment OR bank statement)" --color green
source .venv/bin/activate && gmail-cleaner label "Shopping" -q "subject:(order confirmed OR shipped OR delivery)" --color orange
source .venv/bin/activate && gmail-cleaner label "Newsletter" -q "subject:(weekly OR digest OR unsubscribe)" --color gray
```

### Step 4: For individual emails that don't match patterns

For emails that need individual labeling (subjects don't share patterns), use Python directly:

```bash
source .venv/bin/activate && python3 -c "
from gmail_cleaner.config import load_config
from gmail_cleaner.auth import get_credentials
from gmail_cleaner.client import GmailClient

config = load_config()
creds = get_credentials(config.credentials_path, config.token_path)
client = GmailClient(creds)

# Create label and apply to specific message IDs
label_id = client.get_or_create_label('Finance', '#076239', '#ffffff')
client.batch_modify(['MESSAGE_ID_1', 'MESSAGE_ID_2'], add_label_ids=[label_id])
"
```

## Notes

- Always show the user what labels you plan to apply before doing it
- Ask confirmation before labeling large batches
- The user can customize category names and colors
- Use Gmail search operators in queries for precision: `from:`, `subject:`, `has:`, `after:`, `before:`
