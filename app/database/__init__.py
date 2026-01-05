"""Database layer for Twitter Signal Monitor."""

from .models import init_database, TrackedHandle, ProcessedTweet, TwitterSession
from .operations import (
    add_tracked_handle,
    remove_tracked_handle,
    list_tracked_handles,
    update_last_seen_tweet,
    is_tweet_processed,
    save_processed_tweet,
    get_session_cookies,
    save_session_cookies,
)

__all__ = [
    "init_database",
    "TrackedHandle",
    "ProcessedTweet",
    "TwitterSession",
    "add_tracked_handle",
    "remove_tracked_handle",
    "list_tracked_handles",
    "update_last_seen_tweet",
    "is_tweet_processed",
    "save_processed_tweet",
    "get_session_cookies",
    "save_session_cookies",
]
