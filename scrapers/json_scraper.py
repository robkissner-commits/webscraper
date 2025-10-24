"""
JSON/API Scraper

This module scrapes events from JSON API endpoints.
Suitable for sites that provide JSON-formatted event data.
"""

from typing import List, Dict, Any
import requests
from .base_scraper import BaseScraper


class JSONScraper(BaseScraper):
    """
    Scraper for JSON API endpoints.

    Fetches and parses JSON data from API endpoints.
    Supports custom field mappings via configuration.
    """

    def scrape(self) -> List[Dict]:
        """
        Scrape events from a JSON API endpoint.

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Get the API endpoint URL
            api_url = self.config.get('api_url', self.url)

            # Get optional headers from config
            custom_headers = self.config.get('headers', {})

            # Prepare headers
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'application/json'
            }
            headers.update(custom_headers)

            # Fetch JSON data
            self.logger.info(f"Fetching JSON from {api_url}")
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract events based on configuration
            events = self._parse_json_data(data)

            self.logger.info(f"Parsed {len(events)} events from JSON endpoint")

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch JSON data: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"Error parsing JSON data: {str(e)}")
            raise

        return events

    def _parse_json_data(self, data: Any) -> List[Dict]:
        """
        Parse JSON data and extract events.

        Args:
            data: JSON data (dict or list)

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Get the path to the events array in the JSON structure
            events_path = self.config.get('events_path', None)

            # Navigate to the events array if path is specified
            if events_path:
                for key in events_path.split('.'):
                    data = data.get(key, data)

            # If data is not a list, wrap it
            if not isinstance(data, list):
                data = [data]

            # Get field mappings from config
            field_map = self.config.get('field_map', {})

            # Parse each event
            for item in data:
                event = self._parse_json_event(item, field_map)
                if event:
                    events.append(event)

        except Exception as e:
            self.logger.error(f"Error parsing JSON events: {str(e)}")

        return events

    def _parse_json_event(self, item: Dict, field_map: Dict) -> Dict:
        """
        Parse a single event from JSON data.

        Args:
            item: Single event JSON object
            field_map: Mapping of JSON fields to event fields

        Returns:
            Event dictionary or None if parsing fails
        """
        try:
            # Helper function to get nested fields
            def get_nested_field(obj, path):
                """Get a nested field from object using dot notation."""
                keys = path.split('.')
                value = obj
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key, '')
                    else:
                        return ''
                return value if value else ''

            # Extract fields using field map
            title = get_nested_field(item, field_map.get('title', 'title'))
            description = get_nested_field(item, field_map.get('description', 'description'))
            when_date = get_nested_field(item, field_map.get('when_date', 'date'))
            when_time = get_nested_field(item, field_map.get('when_time', 'time'))
            location = get_nested_field(item, field_map.get('location', 'location'))
            event_url = get_nested_field(item, field_map.get('event_url', 'url'))
            registration_url = get_nested_field(item, field_map.get('registration_url', 'registration_url'))
            image_url = get_nested_field(item, field_map.get('image_url', 'image'))
            target_age = get_nested_field(item, field_map.get('target_age', 'age'))

            # Create event dictionary
            event = self.create_event_dict(
                title=str(title),
                description=str(description),
                when_date=str(when_date),
                when_time=str(when_time),
                location=str(location),
                event_url=str(event_url),
                registration_url=str(registration_url) if registration_url else str(event_url),
                image_url=str(image_url),
                target_age=str(target_age)
            )

            return event

        except Exception as e:
            self.logger.warning(f"Failed to parse JSON event: {str(e)}")
            return None
