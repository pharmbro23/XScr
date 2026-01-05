"""Telegram Bot API client for sending notifications."""

import logging
import time
from typing import Optional
import httpx

from ..config import settings
from ..summarizer.schemas import TweetSummary

logger = logging.getLogger(__name__)

# Telegram message size limit
MAX_MESSAGE_LENGTH = 4096


def send_telegram_alert(
    handle: str,
    tweet_text: str,
    tweet_url: str,
    summary: Optional[TweetSummary] = None,
    fallback_tickers: Optional[list] = None,
    fallback_actions: Optional[list] = None,
    max_retries: int = 3
) -> bool:
    """
    Send a formatted tweet alert to Telegram.
    
    Args:
        handle: Twitter handle
        tweet_text: Full tweet text
        tweet_url: URL to the tweet
        summary: LLM-generated summary (optional)
        fallback_tickers: Regex-extracted tickers (fallback)
        fallback_actions: Regex-extracted actions (fallback)
        max_retries: Number of retry attempts
        
    Returns:
        True if message was sent successfully
    """
    message = format_tweet_message(
        handle=handle,
        tweet_text=tweet_text,
        tweet_url=tweet_url,
        summary=summary,
        fallback_tickers=fallback_tickers,
        fallback_actions=fallback_actions
    )
    
    # Split message if too long
    messages = _split_message(message)
    
    for attempt in range(max_retries):
        try:
            for msg in messages:
                _send_message(msg)
                time.sleep(0.5)  # Rate limit protection
            
            logger.info(f"✅ Sent Telegram alert for @{handle}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send Telegram message (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    logger.error(f"Failed to send Telegram alert after {max_retries} attempts")
    return False


def format_tweet_message(
    handle: str,
    tweet_text: str,
    tweet_url: str,
    summary: Optional[TweetSummary] = None,
    fallback_tickers: Optional[list] = None,
    fallback_actions: Optional[list] = None
) -> str:
    """
    Format a tweet into a structured Telegram message.
    
    Args:
        handle: Twitter handle
        tweet_text: Tweet text
        tweet_url: Tweet URL
        summary: Optional LLM summary
        fallback_tickers: Fallback ticker list
        fallback_actions: Fallback action list
        
    Returns:
        Formatted message string
    """
    # Truncate tweet text if too long
    max_tweet_length = 500
    display_text = tweet_text
    if len(tweet_text) > max_tweet_length:
        display_text = tweet_text[:max_tweet_length] + "..."
    
    # Build message
    lines = [
        f"🚨 *New Tweet from @{handle}*",
        f"🔗 [View Tweet]({tweet_url})",
        "",
        f"📝 *Raw Tweet:*",
        display_text,
        ""
    ]
    
    # Add LLM summary if available
    if summary:
        lines.append("🤖 *AI Summary:*")
        for bullet in summary.summary_bullets:
            lines.append(f"• {bullet}")
        lines.append("")
        
        # Tickers
        if summary.tickers:
            ticker_str = ", ".join([f"${t}" for t in summary.tickers])
            lines.append(f"📊 *Tickers:* {ticker_str}")
        
        # Action
        if summary.action and summary.action != "unknown":
            lines.append(f"⚡ *Action:* {summary.action.upper()}")
        
        # Time horizon
        if summary.time_horizon and summary.time_horizon != "unknown":
            lines.append(f"⏱️ *Horizon:* {summary.time_horizon}")
        
        # Confidence
        confidence_emoji = {"low": "🟡", "medium": "🟠", "high": "🟢"}
        emoji = confidence_emoji.get(summary.confidence, "⚪")
        lines.append(f"{emoji} *Confidence:* {summary.confidence}")
        lines.append("")
        
        # Risks and verification
        if summary.risks_or_unknowns:
            lines.append("⚠️ *Risks:*")
            for risk in summary.risks_or_unknowns[:3]:  # Limit to 3
                lines.append(f"• {risk}")
            lines.append("")
        
        if summary.what_to_verify:
            lines.append("✅ *Verify:*")
            for item in summary.what_to_verify[:3]:  # Limit to 3
                lines.append(f"• {item}")
    
    else:
        # Fallback to regex extraction
        lines.append("⚠️ *AI summary unavailable - using fallback extraction*")
        
        if fallback_tickers:
            ticker_str = ", ".join([f"${t}" for t in fallback_tickers])
            lines.append(f"📊 *Detected Tickers:* {ticker_str}")
        
        if fallback_actions:
            action_str = ", ".join(fallback_actions)
            lines.append(f"⚡ *Detected Actions:* {action_str}")
    
    return "\n".join(lines)


def _send_message(text: str) -> None:
    """Send a single message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    
    response = httpx.post(url, json=payload, timeout=10.0)
    response.raise_for_status()


def _split_message(message: str) -> list[str]:
    """Split message into chunks if it exceeds Telegram's limit."""
    if len(message) <= MAX_MESSAGE_LENGTH:
        return [message]
    
    # Simple split by lines
    lines = message.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for line in lines:
        line_length = len(line) + 1  # +1 for newline
        
        if current_length + line_length > MAX_MESSAGE_LENGTH:
            # Save current chunk and start new one
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length
    
    # Add remaining chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks
