"""CLI commands for managing tracked handles."""

import sys
import logging
from pathlib import Path

import typer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import (
    init_database,
    add_tracked_handle,
    remove_tracked_handle,
    list_tracked_handles,
)
from app.scheduler import poll_tweets_once

app = typer.Typer(help="Twitter Signal Monitor CLI")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@app.command()
def add(handle: str):
    """Add a Twitter handle to track."""
    init_database()
    try:
        result = add_tracked_handle(handle)
        typer.echo(f"✅ Added @{result.handle}")
    except ValueError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def remove(handle: str):
    """Remove a tracked Twitter handle."""
    init_database()
    removed = remove_tracked_handle(handle)
    if removed:
        typer.echo(f"✅ Removed @{handle}")
    else:
        typer.echo(f"❌ Handle @{handle} not found", err=True)
        raise typer.Exit(1)


@app.command()
def list():
    """List all tracked handles."""
    init_database()
    handles = list_tracked_handles()
    
    if not handles:
        typer.echo("No handles being tracked")
        return
    
    typer.echo(f"\n📋 Tracking {len(handles)} handle(s):\n")
    for h in handles:
        last_seen = h.last_seen_tweet_id or "None"
        typer.echo(f"  @{h.handle}")
        typer.echo(f"    Last seen tweet: {last_seen}")
        typer.echo(f"    Added: {h.created_at}\n")


@app.command()
def poll():
    """Manually trigger a poll cycle."""
    init_database()
    typer.echo("🔄 Starting manual poll...")
    
    stats = poll_tweets_once()
    
    typer.echo(f"\n📊 Poll Results:")
    typer.echo(f"  Tweets fetched: {stats['tweets_fetched']}")
    typer.echo(f"  Tweets processed: {stats['tweets_processed']}")
    typer.echo(f"  Duplicates skipped: {stats['tweets_skipped_duplicate']}")
    typer.echo(f"  Alerts sent: {stats['alerts_sent']}")
    typer.echo(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    app()
