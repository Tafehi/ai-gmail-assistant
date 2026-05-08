import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from .auth import get_credentials
from .client import GmailClient
from .config import load_config, parse_date_input
from .delete import build_delete_query, find_deletable_messages, execute_deletion
from .keep import label_latest_as_keep

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
    creds = get_credentials(config.credentials_path, config.token_path)
    console.print(f"[green]Authenticated successfully.[/green] Token saved to {config.token_path}")


@cli.command()
def status():
    """Show current email counts and configuration."""
    client, config = _get_client()

    total = client.get_estimated_count("")
    query = build_delete_query(config.delete_before_date)
    deletable = client.get_estimated_count(query)
    keep_count = client.get_estimated_count("label:Keep")

    console.print(f"\n[bold]Gmail Status[/bold]")
    console.print(f"  Total emails:          {total:,}")
    console.print(f"  Before {config.delete_before_date}:  {deletable:,}")
    console.print(f"  Labeled 'Keep':        {keep_count:,}")
    console.print(f"\n[dim]Config: delete before {config.delete_before_date}, keep latest {config.keep_latest_count}[/dim]")


@cli.command()
@click.option("--count", type=int, help="Number of latest emails to keep (overrides .env)")
def keep(count: int | None):
    """Label the latest N emails with 'Keep' label."""
    client, config = _get_client()
    n = count or config.keep_latest_count

    console.print(f"Labeling latest {n:,} emails as 'Keep'...")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="Applying labels...", total=None)
        labeled = label_latest_as_keep(client, n, batch_size=config.batch_size)

    console.print(f"[green]Done.[/green] Labeled {labeled:,} emails as 'Keep'.")


@cli.command()
@click.option("--dry-run/--no-dry-run", default=None, help="Preview without deleting (overrides .env)")
@click.option("--before", type=str, help="Delete before date (overrides .env)")
@click.option("--exclude-keep/--no-exclude-keep", default=True, help="Exclude emails labeled 'Keep'")
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

    console.print(f"\n[bold red]Found {total:,} emails to permanently delete.[/bold red]")

    if is_dry_run:
        console.print("[yellow]DRY RUN — no emails were deleted.[/yellow]")
        console.print("Run with --no-dry-run to actually delete.")
        return

    if not click.confirm(f"\nPermanently delete {total:,} emails? This cannot be undone"):
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


if __name__ == "__main__":
    cli()
