"""
iCal Scraper

This module scrapes events from iCal (.ics) calendar feeds.
Suitable for sites that provide iCalendar format event feeds.
"""

from typing import List, Dict
import requests
from icalendar import Calendar
from datetime import datetime
from .base_scraper import BaseScraper


class ICalScraper(BaseScraper):
    """
    Scraper for iCal (.ics) calendar feeds.

    Parses iCalendar format files and extracts event information.
    """

    def scrape(self) -> List[Dict]:
        """
        Scrape events from an iCal feed.

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Get the iCal feed URL from config
            ical_url = self.config.get('ical_url', self.url)

            # Fetch the iCal data
            self.logger.info(f"Fetching iCal feed from {ical_url}")
            headers = {'User-Agent': self.get_random_user_agent()}

            response = requests.get(ical_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse the iCal data
            cal = Calendar.from_ical(response.content)

            # Extract events
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = self._parse_ical_event(component)
                    if event:
                        events.append(event)

            self.logger.info(f"Parsed {len(events)} events from iCal feed")

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch iCal feed: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"Error parsing iCal feed: {str(e)}")
            raise

        return events

    def _parse_ical_event(self, component) -> Dict:
        """
        Parse a single VEVENT component from iCal.

        Args:
            component: iCalendar VEVENT component

        Returns:
            Event dictionary or None if parsing fails
        """
        try:
            # Extract basic fields
            title = str(component.get('summary', ''))
            description = str(component.get('description', ''))
            location = str(component.get('location', ''))
            url = str(component.get('url', ''))

            # Parse date and time
            dtstart = component.get('dtstart')
            if dtstart:
                dt = dtstart.dt

                # Handle both date and datetime objects
                if isinstance(dt, datetime):
                    when_date = dt.strftime('%Y-%m-%d')
                    when_time = dt.strftime('%I:%M %p')
                else:
                    # It's a date object (all-day event)
                    when_date = dt.strftime('%Y-%m-%d')
                    when_time = "All Day"
            else:
                when_date = ""
                when_time = ""

            # Create event dictionary
            event = self.create_event_dict(
                title=title,
                description=description,
                when_date=when_date,
                when_time=when_time,
                location=location,
                event_url=url,
                registration_url=url  # Use same URL for registration if available
            )

            return event

        except Exception as e:
            self.logger.warning(f"Failed to parse iCal event: {str(e)}")
            return None
