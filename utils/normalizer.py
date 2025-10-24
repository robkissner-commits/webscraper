"""
Data Normalizer Utility

This module provides functions to normalize and clean event data.
Ensures all events have standardized formats and valid data.
"""

from typing import Dict, List
import logging
from .date_parser import parse_date, parse_time

logger = logging.getLogger(__name__)


def normalize_event(event: Dict) -> Dict:
    """
    Normalize a single event dictionary.

    - Trims all string fields
    - Standardizes dates to ISO format
    - Standardizes times to HH:MM AM/PM format
    - Validates required fields
    - Sets default values for missing fields

    Args:
        event: Event dictionary

    Returns:
        Normalized event dictionary
    """
    try:
        # Create a copy to avoid modifying original
        normalized = event.copy()

        # Clean and trim text fields
        text_fields = [
            'title', 'description', 'location',
            'registration_url', 'image_url', 'target_age',
            'event_url', 'source_organization'
        ]

        for field in text_fields:
            value = normalized.get(field, '')
            if value and isinstance(value, str):
                normalized[field] = value.strip()
            else:
                normalized[field] = ''

        # Normalize date
        date_value = normalized.get('when_date', '')
        if date_value:
            parsed_date = parse_date(str(date_value))
            normalized['when_date'] = parsed_date
        else:
            normalized['when_date'] = ''

        # Normalize time
        time_value = normalized.get('when_time', '')
        if time_value:
            parsed_time = parse_time(str(time_value))
            normalized['when_time'] = parsed_time
        else:
            normalized['when_time'] = ''

        # Ensure scraped_at timestamp exists
        if 'scraped_at' not in normalized or not normalized['scraped_at']:
            from datetime import datetime
            normalized['scraped_at'] = datetime.now().isoformat()

        # Validate required fields
        if not normalized.get('title'):
            logger.warning("Event missing title field")
            return None

        if not normalized.get('when_date'):
            logger.debug(f"Event '{normalized.get('title')}' missing date")

        return normalized

    except Exception as e:
        logger.error(f"Error normalizing event: {str(e)}")
        return None


def normalize_events(events: List[Dict]) -> List[Dict]:
    """
    Normalize a list of events.

    Filters out invalid events (e.g., missing required fields).

    Args:
        events: List of event dictionaries

    Returns:
        List of normalized event dictionaries
    """
    normalized_events = []

    for event in events:
        normalized = normalize_event(event)
        if normalized:
            normalized_events.append(normalized)

    logger.info(f"Normalized {len(normalized_events)} out of {len(events)} events")

    return normalized_events


def validate_event(event: Dict) -> bool:
    """
    Validate that an event has required fields.

    Required fields:
    - title (non-empty)
    - when_date (valid date)

    Args:
        event: Event dictionary

    Returns:
        True if valid, False otherwise
    """
    # Check title
    if not event.get('title') or not event['title'].strip():
        return False

    # Check date (should be non-empty, date parsing will happen in normalize)
    if not event.get('when_date'):
        return False

    return True


def clean_html_text(text: str) -> str:
    """
    Clean HTML tags and extra whitespace from text.

    Args:
        text: Text potentially containing HTML

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    import re
    from html import unescape

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Unescape HTML entities
    text = unescape(text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 1000)

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Truncate and add ellipsis
    return text[:max_length - 3] + "..."


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize and validate URL.

    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs

    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""

    url = url.strip()

    # If already absolute, return as is
    if url.startswith('http://') or url.startswith('https://'):
        return url

    # If protocol-relative, add https
    if url.startswith('//'):
        return 'https:' + url

    # If relative and base_url provided, make absolute
    if base_url:
        from urllib.parse import urljoin
        return urljoin(base_url, url)

    return url
