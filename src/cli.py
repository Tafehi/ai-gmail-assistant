from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from src.gmail.auth import get_credentials
from src.gmail.client import GmailClient
from src.gmail.config import load_config, parse_date_input
from src.gmail.delete import build_delete_query, find_deletable_messages, execute_deletion
from src.gmail.keep import label_latest_as_keep

console = Console()


def _get_client():
    config = load_config()
    creds = get_credentials(config.credentials_path, config.token_path)
    return GmailClient(creds), config


@click.group()
def cli():
    """AI Gmail Cleaner - Bulk delete old emails and preserve recent ones."""
    pass


@cli.command()
def auth():
    """Authenticate with Google (run OAuth flow)."""
    config = load_config()
    get_credentials(config.credentials_path, config.token_path)
    console.print(
        f"[green]Authenticated successfully.[/green] Token saved to {config.token_path}"
    )


@cli.command()
def status():
    """Show current email counts and configuration."""
    client, config = _get_client()

    console.print("Counting emails (this may take a moment)...")

    total = client.count_messages("")
    query = build_delete_query(config.delete_before_date)
    deletable = client.count_messages(query)
    keep_count = client.count_messages("label:Keep")

    console.print("\n[bold]Gmail Status[/bold]")
    console.print(f"  Total emails:          {total:,}")
    console.print(f"  Before {config.delete_before_date}:  {deletable:,}")
    console.print(f"  Labeled 'Keep':        {keep_count:,}")
    console.print(
        f"\n[dim]Config: delete before {config.delete_before_date}, keep latest {config.keep_latest_count}[/dim]"
    )


@cli.command()
@click.option(
    "--count", type=int, help="Number of latest emails to keep (overrides .env)"
)
def keep(count: int | None):
    """Label the latest N emails with 'Keep' label."""
    client, config = _get_client()
    n = count or config.keep_latest_count

    console.print(f"Labeling latest {n:,} emails as 'Keep'...")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}")
    ) as progress:
        progress.add_task(description="Applying labels...", total=None)
        labeled = label_latest_as_keep(client, n, batch_size=config.batch_size)

    console.print(f"[green]Done.[/green] Labeled {labeled:,} emails as 'Keep'.")


@cli.command()
@click.option(
    "--dry-run/--no-dry-run",
    default=None,
    help="Preview without deleting (overrides .env)",
)
@click.option("--before", type=str, help="Delete before date (overrides .env)")
@click.option(
    "--exclude-keep/--no-exclude-keep",
    default=True,
    help="Exclude emails labeled 'Keep'",
)
def delete(dry_run: bool | None, before: str | None, exclude_keep: bool):
    """Permanently delete all emails before the configured date."""
    client, config = _get_client()

    target_date = parse_date_input(before) if before else config.delete_before_date
    is_dry_run = dry_run if dry_run is not None else config.dry_run

    query = build_delete_query(target_date, exclude_keep)
    console.print(f"Query: [cyan]{query}[/cyan]")
    console.print("Scanning emails...")

    message_ids = find_deletable_messages(client, target_date, exclude_keep)
    total = len(message_ids)

    if total == 0:
        console.print("[green]No emails found matching criteria.[/green]")
        return

    console.print(
        f"\n[bold red]Found {total:,} emails to permanently delete.[/bold red]"
    )

    if is_dry_run:
        console.print("[yellow]DRY RUN — no emails were deleted.[/yellow]")
        console.print("Run with --no-dry-run to actually delete.")
        return

    if not click.confirm(
        f"\nPermanently delete {total:,} emails? This cannot be undone"
    ):
        console.print("Cancelled.")
        return

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
    ) as progress:
        task = progress.add_task("Deleting...", total=total)

        def on_progress(deleted, _total):
            progress.update(task, completed=deleted)

        deleted = execute_deletion(client, message_ids, config.batch_size, on_progress)

    console.print(f"\n[green]Done.[/green] Permanently deleted {deleted:,} emails.")


@cli.command()
@click.argument(
    "category", type=click.Choice(["promotions", "social", "updates", "forums"])
)
@click.option(
    "--keep-month",
    type=str,
    help="Month to keep (e.g. 05.2026). Defaults to current month.",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=None,
    help="Preview without deleting (overrides .env)",
)
def clean(category: str, keep_month: str | None, dry_run: bool | None):
    """Delete all emails in a category except the specified month.

    Example: gmail-cleaner clean promotions --keep-month 05.2026
    """
    client, config = _get_client()
    is_dry_run = dry_run if dry_run is not None else config.dry_run

    if keep_month:
        keep_date = parse_date_input(keep_month)
    else:
        today = date.today()
        keep_date = date(today.year, today.month, 1)

    query = f"category:{category} before:{keep_date.year}/{keep_date.month:02d}/{keep_date.day:02d}"
    console.print(f"Query: [cyan]{query}[/cyan]")
    console.print(
        f"Keeping {category} emails from {keep_date.strftime('%B %Y')} onwards."
    )
    console.print("Scanning emails...")

    message_ids = client.list_message_ids(query)
    total = len(message_ids)

    if total == 0:
        console.print(f"[green]No {category} emails found to delete.[/green]")
        return

    console.print(
        f"\n[bold red]Found {total:,} {category} emails to permanently delete.[/bold red]"
    )

    if is_dry_run:
        console.print("[yellow]DRY RUN — no emails were deleted.[/yellow]")
        console.print("Run with --no-dry-run to actually delete.")
        return

    if not click.confirm(
        f"\nPermanently delete {total:,} {category} emails? This cannot be undone"
    ):
        console.print("Cancelled.")
        return

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
    ) as progress:
        task = progress.add_task("Deleting...", total=total)

        def on_progress(deleted, _total):
            progress.update(task, completed=deleted)

        deleted = execute_deletion(client, message_ids, config.batch_size, on_progress)

    console.print(
        f"\n[green]Done.[/green] Permanently deleted {deleted:,} {category} emails."
    )


@cli.command()
@click.argument("label_name")
@click.option("--query", "-q", required=True, help="Gmail search query to match emails")
@click.option(
    "--color",
    type=str,
    default=None,
    help="Label color (e.g. red, blue, green, yellow, purple, orange)",
)
@click.option(
    "--max", "max_results", type=int, default=None, help="Max emails to label"
)
def label(label_name: str, query: str, color: str | None, max_results: int | None):
    """Apply a label to emails matching a query.

    Example: gmail-cleaner label "Receipts" -q "subject:receipt"
    """
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

    client, config = _get_client()

    bg_color, text_color = None, None
    if color:
        if color.lower() in COLOR_MAP:
            bg_color, text_color = COLOR_MAP[color.lower()]
        else:
            console.print(
                f"[yellow]Unknown color '{color}'. Available: {', '.join(COLOR_MAP.keys())}[/yellow]"
            )
            return

    label_id = client.get_or_create_label(label_name, bg_color, text_color)

    console.print(f"Query: [cyan]{query}[/cyan]")
    console.print("Finding emails...")

    message_ids = client.list_message_ids(query, max_results)
    total = len(message_ids)

    if total == 0:
        console.print("[green]No emails found matching query.[/green]")
        return

    console.print(f"Labeling {total:,} emails as '{label_name}'...")

    for i in range(0, total, config.batch_size):
        batch = message_ids[i : i + config.batch_size]
        client.batch_modify(batch, add_label_ids=[label_id])

    console.print(f"[green]Done.[/green] Labeled {total:,} emails as '{label_name}'.")


@cli.command()
def chat():
    """Launch the web chat UI for natural language Gmail management."""
    import uvicorn
    console.print("[bold]Starting AI Gmail Assistant...[/bold]")
    console.print("Open [cyan]http://localhost:8000[/cyan] in your browser.\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    cli()
