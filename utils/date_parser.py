"""
Date Parser Utility

This module provides functions to parse various date and time formats
and standardize them to ISO format.
"""

from datetime import datetime
from dateutil import parser as dateutil_parser
import re
import logging

logger = logging.getLogger(__name__)


def parse_date(date_string: str) -> str:
    """
    Parse various date formats and return ISO format (YYYY-MM-DD).

    Args:
        date_string: Date string in various formats

    Returns:
        Date in ISO format (YYYY-MM-DD) or empty string if parsing fails
    """
    if not date_string or not isinstance(date_string, str):
        return ""

    date_string = date_string.strip()

    try:
        # Try to parse with dateutil (handles most formats)
        dt = dateutil_parser.parse(date_string, fuzzy=True)
        return dt.strftime('%Y-%m-%d')

    except Exception as e:
        logger.debug(f"Failed to parse date '{date_string}': {str(e)}")
        return ""


def parse_time(time_string: str) -> str:
    """
    Parse various time formats and return standardized format (HH:MM AM/PM).

    Args:
        time_string: Time string in various formats

    Returns:
        Time in format "HH:MM AM/PM" or original string if parsing fails
    """
    if not time_string or not isinstance(time_string, str):
        return ""

    time_string = time_string.strip()

    # Handle common special cases
    if time_string.lower() in ['all day', 'all-day', 'allday']:
        return "All Day"

    try:
        # Try to parse with dateutil
        dt = dateutil_parser.parse(time_string, fuzzy=True)
        return dt.strftime('%I:%M %p')

    except Exception:
        # Try regex patterns for common time formats
        patterns = [
            # 2:30pm, 2:30 pm, 2:30PM
            (r'(\d{1,2}):(\d{2})\s*([ap]m)', lambda m: f"{int(m.group(1)):02d}:{m.group(2)} {m.group(3).upper()}"),

            # 2pm, 2 pm, 2PM
            (r'(\d{1,2})\s*([ap]m)', lambda m: f"{int(m.group(1)):02d}:00 {m.group(2).upper()}"),

            # 14:30 (24-hour format)
            (r'(\d{1,2}):(\d{2})(?!\s*[ap]m)', lambda m: _convert_24h_to_12h(int(m.group(1)), int(m.group(2)))),
        ]

        for pattern, formatter in patterns:
            match = re.search(pattern, time_string, re.IGNORECASE)
            if match:
                return formatter(match)

        # If all parsing fails, return original
        logger.debug(f"Could not parse time '{time_string}', returning original")
        return time_string


def _convert_24h_to_12h(hour: int, minute: int) -> str:
    """
    Convert 24-hour time to 12-hour format with AM/PM.

    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)

    Returns:
        Time string in "HH:MM AM/PM" format
    """
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{hour_12:02d}:{minute:02d} {period}"


def standardize_date(date_string: str) -> str:
    """
    Standardize date string to ISO format.

    This is an alias for parse_date() for consistency.

    Args:
        date_string: Date string in any format

    Returns:
        Date in ISO format (YYYY-MM-DD)
    """
    return parse_date(date_string)


def parse_datetime(datetime_string: str) -> tuple:
    """
    Parse a combined datetime string and return separate date and time.

    Args:
        datetime_string: Combined date and time string

    Returns:
        Tuple of (date_str, time_str) in standardized formats
    """
    if not datetime_string or not isinstance(datetime_string, str):
        return ("", "")

    try:
        dt = dateutil_parser.parse(datetime_string, fuzzy=True)
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%I:%M %p')
        return (date_str, time_str)

    except Exception as e:
        logger.debug(f"Failed to parse datetime '{datetime_string}': {str(e)}")
        return ("", "")


def validate_date(date_string: str) -> bool:
    """
    Validate if a string is a valid date.

    Args:
        date_string: Date string to validate

    Returns:
        True if valid date, False otherwise
    """
    parsed = parse_date(date_string)
    return bool(parsed)


def validate_time(time_string: str) -> bool:
    """
    Validate if a string is a valid time.

    Args:
        time_string: Time string to validate

    Returns:
        True if valid time, False otherwise
    """
    parsed = parse_time(time_string)
    return bool(parsed)
