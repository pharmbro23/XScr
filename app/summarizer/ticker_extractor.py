"""Regex-based ticker and action keyword extraction."""

import re
from typing import List, Set


# Common stock ticker patterns
TICKER_PATTERNS = [
    r'\$([A-Z]{1,5})\b',  # $TSLA format
    r'\(([A-Z]{1,5})\)',  # (AAPL) format
    r'\b([A-Z]{2,5})\b',  # Standalone tickers (risky, has false positives)
]

# Crypto ticker patterns
CRYPTO_TICKERS = {
    'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK',
    'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'BNB', 'USDT', 'USDC'
}

# Common false positive words to exclude
FALSE_POSITIVES = {
    'IT', 'IS', 'IN', 'ON', 'AT', 'TO', 'BE', 'OR', 'AND', 'THE',
    'FOR', 'ARE', 'WAS', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER',
    'HIS', 'ITS', 'OUR', 'OUT', 'MAY', 'SEE', 'GET', 'HAS', 'HAD',
    'DAY', 'WAY', 'NEW', 'NOW', 'OLD', 'TOP', 'BIG', 'BAD', 'HOT',
    'PM', 'AM', 'US', 'UK', 'CEO', 'CFO', 'CTO', 'IPO', 'API', 'AI',
    'ML', 'VC', 'PE', 'RE', 'PR', 'HR', 'IR', 'DD', 'YTD', 'QoQ',
}

# Action keywords
ACTION_KEYWORDS = {
    'buy': ['buy', 'buying', 'bought', 'long', 'bullish'],
    'sell': ['sell', 'selling', 'sold', 'bearish'],
    'add': ['add', 'adding', 'added', 'accumulate', 'accumulating'],
    'trim': ['trim', 'trimming', 'trimmed', 'reduce', 'reducing', 'reduced'],
    'short': ['short', 'shorting', 'shorted'],
    'cover': ['cover', 'covering', 'covered', 'closing'],
    'watch': ['watch', 'watching', 'monitor', 'monitoring', 'eyeing', 'tracking'],
}


def extract_tickers(text: str) -> List[str]:
    """
    Extract ticker symbols from text using regex patterns.
    
    Args:
        text: Tweet text to extract tickers from
        
    Returns:
        List of unique ticker symbols (uppercase)
    """
    tickers: Set[str] = set()
    
    # Extract using patterns
    for pattern in TICKER_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            ticker = match.upper()
            
            # Filter out false positives
            if ticker not in FALSE_POSITIVES:
                tickers.add(ticker)
    
    # Check for crypto tickers (case-insensitive)
    words = text.upper().split()
    for word in words:
        # Remove common punctuation
        clean_word = word.strip('.,!?;:()[]{}"\\'')
        if clean_word in CRYPTO_TICKERS:
            tickers.add(clean_word)
    
    return sorted(list(tickers))


def extract_action_keywords(text: str) -> List[str]:
    """
    Extract investment action keywords from text.
    
    Args:
        text: Tweet text to extract actions from
        
    Returns:
        List of detected actions (e.g., ['buy', 'watch'])
    """
    text_lower = text.lower()
    detected_actions = []
    
    for action, keywords in ACTION_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                detected_actions.append(action)
                break  # Only add action once
    
    return detected_actions
