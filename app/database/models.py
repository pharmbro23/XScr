"""SQLite database models and schema."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from ..config import settings


@dataclass
class TrackedHandle:
    """Represents a tracked Twitter handle."""
    id: int
    handle: str
    user_id: Optional[str]
    last_seen_tweet_id: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class ProcessedTweet:
    """Represents a processed tweet."""
    id: int
    tweet_id: str
    handle: str
    tweet_text: str
    tweet_url: str
    processed_at: str
    summary_json: Optional[str]


@dataclass
class TwitterSession:
    """Represents Twitter session cookies."""
    id: int
    cookies_json: str
    last_refreshed: str


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create tracked_handles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_handles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT UNIQUE NOT NULL,
            user_id TEXT,
            last_seen_tweet_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create processed_tweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT UNIQUE NOT NULL,
            handle TEXT NOT NULL,
            tweet_text TEXT,
            tweet_url TEXT,
            processed_at TEXT NOT NULL,
            summary_json TEXT
        )
    """)
    
    # Create twitter_session table (single row)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twitter_session (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cookies_json TEXT,
            last_refreshed TEXT
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_processed_tweets_tweet_id 
        ON processed_tweets(tweet_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_processed_tweets_handle 
        ON processed_tweets(handle)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tracked_handles_handle 
        ON tracked_handles(handle)
    """)
    
    conn.commit()
    conn.close()


def get_current_timestamp() -> str:
    """Get current UTC timestamp as ISO format string."""
    return datetime.now(timezone.utc).isoformat()
