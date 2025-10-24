"""
Base Scraper Abstract Class

This module defines the abstract base class for all scrapers.
All specific scraper implementations must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
import time
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.

    Provides common functionality like rate limiting, error handling,
    and logging. All scraper implementations must inherit from this class
    and implement the scrape() method.
    """

    def __init__(self, site_config: Dict):
        """
        Initialize the scraper with site configuration.

        Args:
            site_config: Dictionary containing site configuration including
                        name, url, method, selectors, etc.
        """
        self.config = site_config
        self.name = site_config.get('name', 'Unknown')
        self.url = site_config.get('url', '')
        self.logger = logging.getLogger(f"Scraper.{self.name}")

        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]

    def get_random_user_agent(self) -> str:
        """Get a random user agent for requests."""
        return random.choice(self.user_agents)

    def rate_limit(self, min_delay: float = 2.0, max_delay: float = 3.0):
        """
        Apply rate limiting between requests.

        Args:
            min_delay: Minimum delay in seconds (default: 2.0)
            max_delay: Maximum delay in seconds (default: 3.0)
        """
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Rate limiting: sleeping for {delay:.2f} seconds")
        time.sleep(delay)

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Scrape events from the website.

        This method must be implemented by all scraper subclasses.

        Returns:
            List of event dictionaries with standardized fields:
            - title (str): Event title
            - description (str): Event description
            - when_date (str): Event date in ISO format (YYYY-MM-DD)
            - when_time (str): Event time (HH:MM AM/PM)
            - location (str): Event location
            - registration_url (str): URL for registration
            - image_url (str): URL of event image
            - target_age (str): Target age group
            - event_url (str): URL to event details
            - source_organization (str): Name of the organization
            - scraped_at (str): Timestamp when scraped
        """
        pass

    def scrape_with_retry(self, max_retries: int = 1, retry_delay: int = 30) -> List[Dict]:
        """
        Scrape with retry logic.

        Args:
            max_retries: Maximum number of retry attempts (default: 1)
            retry_delay: Delay between retries in seconds (default: 30)

        Returns:
            List of event dictionaries
        """
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Starting scrape for {self.name} (attempt {attempt + 1}/{max_retries + 1})")
                events = self.scrape()
                self.logger.info(f"Successfully scraped {len(events)} events from {self.name}")
                return events

            except Exception as e:
                self.logger.error(f"Error scraping {self.name}: {str(e)}", exc_info=True)

                if attempt < max_retries:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Failed to scrape {self.name} after {max_retries + 1} attempts")
                    return []

        return []

    def create_event_dict(
        self,
        title: str = "",
        description: str = "",
        when_date: str = "",
        when_time: str = "",
        location: str = "",
        registration_url: str = "",
        image_url: str = "",
        target_age: str = "",
        event_url: str = ""
    ) -> Dict:
        """
        Create a standardized event dictionary with default values.

        Args:
            Various event fields (all optional with defaults)

        Returns:
            Standardized event dictionary
        """
        return {
            'title': title.strip() if title else "",
            'description': description.strip() if description else "",
            'when_date': when_date.strip() if when_date else "",
            'when_time': when_time.strip() if when_time else "",
            'location': location.strip() if location else "",
            'registration_url': registration_url.strip() if registration_url else "",
            'image_url': image_url.strip() if image_url else "",
            'target_age': target_age.strip() if target_age else "",
            'event_url': event_url.strip() if event_url else "",
            'source_organization': self.name,
            'scraped_at': datetime.now().isoformat()
        }
