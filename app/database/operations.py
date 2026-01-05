"""Database CRUD operations."""

import json
import logging
from typing import List, Optional

from .models import (
    get_connection,
    get_current_timestamp,
    TrackedHandle,
    ProcessedTweet,
    TwitterSession,
)

logger = logging.getLogger(__name__)


def add_tracked_handle(handle: str, user_id: Optional[str] = None) -> TrackedHandle:
    """
    Add a new tracked handle to the database.
    
    Args:
        handle: Twitter handle (without @)
        user_id: Optional Twitter user ID
        
    Returns:
        TrackedHandle object
        
    Raises:
        ValueError: If handle already exists
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Normalize handle (remove @ if present)
    handle = handle.lstrip("@").lower()
    
    timestamp = get_current_timestamp()
    
    try:
        cursor.execute("""
            INSERT INTO tracked_handles (handle, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (handle, user_id, timestamp, timestamp))
        
        conn.commit()
        
        # Fetch the created record
        cursor.execute("""
            SELECT * FROM tracked_handles WHERE handle = ?
        """, (handle,))
        
        row = cursor.fetchone()
        return TrackedHandle(**dict(row))
        
    except sqlite3.IntegrityError:
        raise ValueError(f"Handle '{handle}' is already being tracked")
    finally:
        conn.close()


def remove_tracked_handle(handle: str) -> bool:
    """
    Remove a tracked handle from the database.
    
    Args:
        handle: Twitter handle (without @)
        
    Returns:
        True if handle was removed, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    handle = handle.lstrip("@").lower()
    
    cursor.execute("""
        DELETE FROM tracked_handles WHERE handle = ?
    """, (handle,))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected_rows > 0


def list_tracked_handles() -> List[TrackedHandle]:
    """
    List all tracked handles.
    
    Returns:
        List of TrackedHandle objects
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM tracked_handles ORDER BY handle ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [TrackedHandle(**dict(row)) for row in rows]


def update_last_seen_tweet(handle: str, tweet_id: str) -> None:
    """
    Update the last seen tweet ID for a handle.
    
    Args:
        handle: Twitter handle
        tweet_id: Tweet ID to store as last seen
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    handle = handle.lstrip("@").lower()
    timestamp = get_current_timestamp()
    
    cursor.execute("""
        UPDATE tracked_handles 
        SET last_seen_tweet_id = ?, updated_at = ?
        WHERE handle = ?
    """, (tweet_id, timestamp, handle))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"Updated last_seen_tweet_id for @{handle} to {tweet_id}")


def is_tweet_processed(tweet_id: str) -> bool:
    """
    Check if a tweet has already been processed.
    
    Args:
        tweet_id: Tweet ID to check
        
    Returns:
        True if tweet exists in processed_tweets table
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 FROM processed_tweets WHERE tweet_id = ?
    """, (tweet_id,))
    
    result = cursor.fetchone() is not None
    conn.close()
    
    return result


def save_processed_tweet(
    tweet_id: str,
    handle: str,
    tweet_text: str,
    tweet_url: str,
    summary_json: Optional[dict] = None
) -> ProcessedTweet:
    """
    Save a processed tweet to the database.
    
    Args:
        tweet_id: Tweet ID
        handle: Twitter handle
        tweet_text: Full tweet text
        tweet_url: URL to the tweet
        summary_json: Optional LLM summary as dict
        
    Returns:
        ProcessedTweet object
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    handle = handle.lstrip("@").lower()
    timestamp = get_current_timestamp()
    summary_str = json.dumps(summary_json) if summary_json else None
    
    cursor.execute("""
        INSERT INTO processed_tweets 
        (tweet_id, handle, tweet_text, tweet_url, processed_at, summary_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tweet_id, handle, tweet_text, tweet_url, timestamp, summary_str))
    
    conn.commit()
    
    # Fetch the created record
    cursor.execute("""
        SELECT * FROM processed_tweets WHERE tweet_id = ?
    """, (tweet_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return ProcessedTweet(**dict(row))


def get_session_cookies() -> Optional[dict]:
    """
    Get stored Twitter session cookies.
    
    Returns:
        Dictionary of cookies or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cookies_json FROM twitter_session WHERE id = 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row["cookies_json"]:
        return json.loads(row["cookies_json"])
    return None


def save_session_cookies(cookies: dict) -> None:
    """
    Save Twitter session cookies to database.
    
    Args:
        cookies: Dictionary of cookies to store
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = get_current_timestamp()
    cookies_str = json.dumps(cookies)
    
    cursor.execute("""
        INSERT OR REPLACE INTO twitter_session (id, cookies_json, last_refreshed)
        VALUES (1, ?, ?)
    """, (cookies_str, timestamp))
    
    conn.commit()
    conn.close()
    
    logger.info("Saved Twitter session cookies to database")
