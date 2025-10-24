"""
Deduplicator Utility

This module provides functions to deduplicate events based on
title, date, and location.
"""

from typing import Dict, List, Set
import hashlib
import logging

logger = logging.getLogger(__name__)


def create_event_hash(event: Dict) -> str:
    """
    Create a hash for an event based on title, date, and location.

    This hash is used to identify duplicate events.

    Args:
        event: Event dictionary

    Returns:
        Hash string (SHA256)
    """
    # Normalize fields for hashing
    title = event.get('title', '').strip().lower()
    date = event.get('when_date', '').strip().lower()
    location = event.get('location', '').strip().lower()

    # Create a unique string from key fields
    unique_string = f"{title}|{date}|{location}"

    # Generate hash
    hash_object = hashlib.sha256(unique_string.encode())
    return hash_object.hexdigest()


def deduplicate_events(events: List[Dict]) -> List[Dict]:
    """
    Remove duplicate events from a list.

    Duplicates are identified by matching title, date, and location.
    When duplicates are found, the first occurrence is kept.

    Args:
        events: List of event dictionaries

    Returns:
        List of unique event dictionaries
    """
    seen_hashes: Set[str] = set()
    unique_events: List[Dict] = []
    duplicate_count = 0

    for event in events:
        # Create hash for this event
        event_hash = create_event_hash(event)

        # Check if we've seen this hash before
        if event_hash not in seen_hashes:
            # New unique event
            seen_hashes.add(event_hash)
            unique_events.append(event)
        else:
            # Duplicate event
            duplicate_count += 1
            logger.debug(f"Duplicate event found: {event.get('title')} on {event.get('when_date')}")

    if duplicate_count > 0:
        logger.info(f"Removed {duplicate_count} duplicate events")

    logger.info(f"Kept {len(unique_events)} unique events out of {len(events)} total")

    return unique_events


def deduplicate_by_url(events: List[Dict]) -> List[Dict]:
    """
    Remove duplicate events based on event_url.

    This is useful when the same event appears on multiple pages
    but has the same detail page URL.

    Args:
        events: List of event dictionaries

    Returns:
        List of unique event dictionaries
    """
    seen_urls: Set[str] = set()
    unique_events: List[Dict] = []
    duplicate_count = 0

    for event in events:
        event_url = event.get('event_url', '').strip()

        # Skip events without URLs
        if not event_url:
            unique_events.append(event)
            continue

        # Check if we've seen this URL before
        if event_url not in seen_urls:
            # New unique event
            seen_urls.add(event_url)
            unique_events.append(event)
        else:
            # Duplicate event
            duplicate_count += 1
            logger.debug(f"Duplicate event URL found: {event_url}")

    if duplicate_count > 0:
        logger.info(f"Removed {duplicate_count} duplicate events by URL")

    return unique_events


def merge_events(event1: Dict, event2: Dict) -> Dict:
    """
    Merge two event dictionaries, preferring non-empty values.

    This is useful when the same event appears from multiple sources
    with different levels of detail.

    Args:
        event1: First event dictionary
        event2: Second event dictionary

    Returns:
        Merged event dictionary
    """
    merged = event1.copy()

    # For each field, prefer non-empty value
    for key, value in event2.items():
        if value and not merged.get(key):
            merged[key] = value

    return merged


def find_similar_events(events: List[Dict], similarity_threshold: float = 0.8) -> List[List[Dict]]:
    """
    Find groups of similar events based on title similarity.

    This is useful for identifying events that might be duplicates
    but have slight variations in title.

    Args:
        events: List of event dictionaries
        similarity_threshold: Minimum similarity score (0-1) to consider events similar

    Returns:
        List of groups of similar events
    """
    from difflib import SequenceMatcher

    similar_groups = []
    processed_indices = set()

    def calculate_similarity(str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    for i, event1 in enumerate(events):
        if i in processed_indices:
            continue

        # Start a new group with this event
        group = [event1]
        processed_indices.add(i)

        title1 = event1.get('title', '')
        date1 = event1.get('when_date', '')

        # Look for similar events
        for j, event2 in enumerate(events):
            if j <= i or j in processed_indices:
                continue

            title2 = event2.get('title', '')
            date2 = event2.get('when_date', '')

            # Only compare events on the same date
            if date1 != date2:
                continue

            # Calculate title similarity
            similarity = calculate_similarity(title1, title2)

            if similarity >= similarity_threshold:
                group.append(event2)
                processed_indices.add(j)

        # Only add groups with more than one event
        if len(group) > 1:
            similar_groups.append(group)

    if similar_groups:
        logger.info(f"Found {len(similar_groups)} groups of similar events")

    return similar_groups
