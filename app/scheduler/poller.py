"""APScheduler polling job for checking Twitter timeline."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import settings
from ..database import (
    list_tracked_handles,
    is_tweet_processed,
    save_processed_tweet,
    update_last_seen_tweet,
)
from ..twitter import ensure_session, fetch_timeline_tweets
from ..summarizer import summarize_tweet, extract_tickers, extract_action_keywords
from ..telegram import send_telegram_alert

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def start_background_poller() -> BackgroundScheduler:
    """
    Start the background polling job.
    
    Returns:
        BackgroundScheduler instance
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return _scheduler
    
    logger.info(f"Starting background poller (interval: {settings.poll_interval_seconds}s)...")
    
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        func=poll_tweets_once,
        trigger=IntervalTrigger(seconds=settings.poll_interval_seconds),
        id="poll_tweets",
        name="Poll Twitter for new tweets",
        replace_existing=True,
    )
    
    _scheduler.start()
    logger.info("✅ Background poller started")
    
    return _scheduler


def poll_tweets_once() -> dict:
    """
    Execute one polling cycle: fetch timeline, process new tweets, send alerts.
    
    Returns:
        Dictionary with polling stats
    """
    logger.info("=== Starting poll cycle ===")
    
    stats = {
        "tweets_fetched": 0,
        "tweets_processed": 0,
        "tweets_skipped_duplicate": 0,
        "alerts_sent": 0,
        "errors": 0,
    }
    
    try:
        # Get tracked handles
        handles = list_tracked_handles()
        if not handles:
            logger.info("No tracked handles configured")
            return stats
        
        logger.info(f"Tracking {len(handles)} handles")
        
        # Ensure we have a valid Twitter session
        try:
            cookies = ensure_session()
        except Exception as e:
            logger.error(f"Failed to ensure Twitter session: {e}")
            stats["errors"] += 1
            return stats
        
        # Build set of tracked handles for filtering
        tracked_handle_set = {h.handle.lower() for h in handles}
        
        # Fetch timeline tweets
        try:
            tweets = fetch_timeline_tweets(
                cookies=cookies,
                tracked_handles=tracked_handle_set,
                max_tweets=50
            )
            stats["tweets_fetched"] = len(tweets)
            logger.info(f"Fetched {len(tweets)} tweets from tracked handles")
        except Exception as e:
            logger.error(f"Failed to fetch timeline: {e}")
            stats["errors"] += 1
            return stats
        
        # Process each tweet
        for tweet in tweets:
            try:
                # Check if already processed (deduplication)
                if is_tweet_processed(tweet.tweet_id):
                    logger.debug(f"Skipping duplicate tweet {tweet.tweet_id}")
                    stats["tweets_skipped_duplicate"] += 1
                    continue
                
                logger.info(f"Processing new tweet from @{tweet.handle}: {tweet.tweet_id}")
                
                # Extract tickers and actions as fallback
                fallback_tickers = extract_tickers(tweet.text)
                fallback_actions = extract_action_keywords(tweet.text)
                
                # Summarize with LLM
                summary = None
                try:
                    summary = summarize_tweet(tweet.text, tweet.handle)
                except Exception as e:
                    logger.error(f"LLM summarization failed: {e}")
                
                # Send Telegram alert
                try:
                    sent = send_telegram_alert(
                        handle=tweet.handle,
                        tweet_text=tweet.text,
                        tweet_url=tweet.url,
                        summary=summary,
                        fallback_tickers=fallback_tickers,
                        fallback_actions=fallback_actions,
                    )
                    if sent:
                        stats["alerts_sent"] += 1
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert: {e}")
                    stats["errors"] += 1
                
                # Save to database
                try:
                    save_processed_tweet(
                        tweet_id=tweet.tweet_id,
                        handle=tweet.handle,
                        tweet_text=tweet.text,
                        tweet_url=tweet.url,
                        summary_json=summary.model_dump() if summary else None,
                    )
                    stats["tweets_processed"] += 1
                    
                    # Update last_seen_tweet_id
                    update_last_seen_tweet(tweet.handle, tweet.tweet_id)
                    
                except Exception as e:
                    logger.error(f"Failed to save processed tweet: {e}")
                    stats["errors"] += 1
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet.tweet_id}: {e}")
                stats["errors"] += 1
                continue
        
        logger.info(f"=== Poll cycle complete: {stats} ===")
        
    except Exception as e:
        logger.error(f"Fatal error in poll cycle: {e}")
        stats["errors"] += 1
    
    return stats


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Background poller stopped")
