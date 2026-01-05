"""Twitter timeline scraper using httpx and BeautifulSoup."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Set
import httpx
from bs4 import BeautifulSoup

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Represents a tweet from the timeline."""
    tweet_id: str
    handle: str
    text: str
    url: str
    created_at: datetime
    is_retweet: bool = False
    is_reply: bool = False


def fetch_timeline_tweets(
    cookies: dict,
    tracked_handles: Set[str],
    max_tweets: int = 50
) -> List[Tweet]:
    """
    Fetch tweets from the Following timeline using authenticated session.
    
    Args:
        cookies: Session cookies dictionary
        tracked_handles: Set of handles to filter for (lowercase, no @)
        max_tweets: Maximum number of tweets to fetch
        
    Returns:
        List of Tweet objects from tracked handles
    """
    logger.info(f"Fetching timeline tweets (tracking {len(tracked_handles)} handles)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://twitter.com/",
    }
    
    tweets = []
    
    try:
        with httpx.Client(cookies=cookies, headers=headers, timeout=30.0, follow_redirects=True) as client:
            # Fetch the Following timeline
            response = client.get("https://twitter.com/home")
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch timeline: HTTP {response.status_code}")
                if response.status_code == 401:
                    logger.error("Session appears to be invalid (401 Unauthorized)")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")
            
            # Twitter's HTML structure detection (this is fragile and may need updates)
            # We'll look for article elements which typically contain tweets
            articles = soup.find_all("article", {"data-testid": "tweet"})
            
            if not articles:
                # Fallback: try to find tweets by common patterns
                logger.warning("No tweets found with standard selectors, trying fallback...")
                # This is a simplified approach - real scraping would need more robust selectors
                # For MVP, we'll log this and return empty
                logger.warning("Unable to parse timeline. Twitter's HTML structure may have changed.")
                return []
            
            logger.info(f"Found {len(articles)} potential tweet elements")
            
            for article in articles[:max_tweets]:
                try:
                    tweet = _parse_tweet_element(article, tracked_handles)
                    if tweet:
                        tweets.append(tweet)
                except Exception as e:
                    logger.debug(f"Failed to parse tweet element: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(tweets)} tweets from tracked handles")
            
    except httpx.TimeoutException:
        logger.error("Request to Twitter timed out")
    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
    
    return tweets


def _parse_tweet_element(article, tracked_handles: Set[str]) -> Tweet | None:
    """
    Parse a tweet from an article element.
    
    NOTE: This is a simplified parser for MVP. Twitter's HTML structure is complex
    and changes frequently. For production, consider using the official API or
    a more robust scraping solution.
    """
    try:
        # Extract handle from the tweet
        # Look for links like /username/status/123456
        status_link = article.find("a", href=re.compile(r"/\w+/status/\d+"))
        if not status_link:
            return None
        
        href = status_link.get("href", "")
        match = re.search(r"/(\w+)/status/(\d+)", href)
        if not match:
            return None
        
        handle = match.group(1).lower()
        tweet_id = match.group(2)
        
        # Filter to only tracked handles
        if handle not in tracked_handles:
            return None
        
        # Extract tweet text
        tweet_text_elem = article.find("div", {"data-testid": "tweetText"})
        tweet_text = tweet_text_elem.get_text(strip=True) if tweet_text_elem else ""
        
        if not tweet_text:
            # Try alternative selector
            tweet_text_elem = article.find("div", {"lang": True})
            tweet_text = tweet_text_elem.get_text(strip=True) if tweet_text_elem else "[No text found]"
        
        # Check if it's a retweet or reply
        is_retweet = bool(article.find("span", string=re.compile(r"Retweeted", re.I)))
        is_reply = bool(article.find("div", string=re.compile(r"Replying to", re.I)))
        
        # Construct tweet URL
        tweet_url = f"https://twitter.com/{handle}/status/{tweet_id}"
        
        # For timestamp, we'll use current time as approximation
        # Real implementation would parse the timestamp from the HTML
        created_at = datetime.now(timezone.utc)
        
        return Tweet(
            tweet_id=tweet_id,
            handle=handle,
            text=tweet_text,
            url=tweet_url,
            created_at=created_at,
            is_retweet=is_retweet,
            is_reply=is_reply
        )
        
    except Exception as e:
        logger.debug(f"Error parsing tweet element: {e}")
        return None
