"""Test deduplication logic."""

import pytest
import tempfile
import os

from app.database.models import init_database, get_connection
from app.database.operations import is_tweet_processed, save_processed_tweet


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    
    # Temporarily override settings
    os.environ["DATABASE_PATH"] = db_path
    
    # Force reload of settings
    from app import config
    config.settings = config.Settings()
    
    init_database()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_is_tweet_processed_returns_false_for_new_tweet(temp_db):
    """Test that a new tweet is not marked as processed."""
    assert is_tweet_processed("123456789") is False


def test_is_tweet_processed_returns_true_after_saving(temp_db):
    """Test that a tweet is marked as processed after saving."""
    tweet_id = "123456789"
    
    # Save the tweet
    save_processed_tweet(
        tweet_id=tweet_id,
        handle="testuser",
        tweet_text="Test tweet",
        tweet_url="https://twitter.com/testuser/status/123456789"
    )
    
    # Check it's marked as processed
    assert is_tweet_processed(tweet_id) is True


def test_duplicate_tweet_id_prevents_reprocessing(temp_db):
    """Test that the same tweet cannot be saved twice."""
    tweet_id = "123456789"
    
    # Save once
    save_processed_tweet(
        tweet_id=tweet_id,
        handle="testuser",
        tweet_text="Test tweet",
        tweet_url="https://twitter.com/testuser/status/123456789"
    )
    
    # Try to save again (should raise sqlite3.IntegrityError)
    with pytest.raises(Exception):  # SQLite will raise IntegrityError
        save_processed_tweet(
            tweet_id=tweet_id,
            handle="testuser",
            tweet_text="Different text",
            tweet_url="https://twitter.com/testuser/status/123456789"
        )


def test_multiple_different_tweets_can_be_saved(temp_db):
    """Test that multiple different tweets can be saved."""
    for i in range(5):
        tweet_id = f"12345678{i}"
        save_processed_tweet(
            tweet_id=tweet_id,
            handle="testuser",
            tweet_text=f"Test tweet {i}",
            tweet_url=f"https://twitter.com/testuser/status/{tweet_id}"
        )
        assert is_tweet_processed(tweet_id) is True
