"""
Playwright Scraper

This module scrapes events from JavaScript-heavy sites using Playwright.
Suitable for sites that require JavaScript rendering or have complex interactions.
"""

from typing import List, Dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class PlaywrightScraper(BaseScraper):
    """
    Scraper for JavaScript-heavy sites using Playwright.

    Renders JavaScript and waits for dynamic content before scraping.
    Uses same selector configuration as HTMLScraper but with browser rendering.
    """

    def scrape(self) -> List[Dict]:
        """
        Scrape events from a JavaScript-heavy site using Playwright.

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            with sync_playwright() as p:
                # Launch browser
                self.logger.info("Launching browser...")
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                # Create context with user agent
                context = browser.new_context(
                    user_agent=self.get_random_user_agent()
                )

                # Create page
                page = context.new_page()

                # Set timeout from config (default 30 seconds)
                timeout = self.config.get('timeout', 30000)
                page.set_default_timeout(timeout)

                # Navigate to URL
                self.logger.info(f"Navigating to {self.url}")
                page.goto(self.url, wait_until='networkidle')

                # Wait for specific selector if configured
                wait_selector = self.config.get('wait_selector')
                if wait_selector:
                    self.logger.info(f"Waiting for selector: {wait_selector}")
                    try:
                        page.wait_for_selector(wait_selector, timeout=timeout)
                    except PlaywrightTimeoutError:
                        self.logger.warning(f"Timeout waiting for selector: {wait_selector}")

                # Additional wait time if configured (in milliseconds)
                additional_wait = self.config.get('additional_wait', 2000)
                if additional_wait > 0:
                    self.logger.info(f"Additional wait: {additional_wait}ms")
                    page.wait_for_timeout(additional_wait)

                # Execute any custom JavaScript if configured
                custom_js = self.config.get('execute_js')
                if custom_js:
                    self.logger.info("Executing custom JavaScript")
                    page.evaluate(custom_js)
                    page.wait_for_timeout(1000)  # Wait after JS execution

                # Get page content
                content = page.content()

                # Close browser
                browser.close()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                events = self._parse_html(soup)

                self.logger.info(f"Parsed {len(events)} events from Playwright")

        except Exception as e:
            self.logger.error(f"Error in Playwright scraping: {str(e)}")
            raise

        return events

    def _parse_html(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse HTML and extract events using CSS selectors.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Get selectors from config
            selectors = self.config.get('selectors', {})

            # Get the container selector for event items
            container_selector = selectors.get('container', 'div.event')

            # Find all event containers
            event_elements = soup.select(container_selector)
            self.logger.info(f"Found {len(event_elements)} event elements")

            # Parse each event
            for element in event_elements:
                event = self._parse_event_element(element, selectors)
                if event:
                    events.append(event)

        except Exception as e:
            self.logger.error(f"Error parsing HTML events: {str(e)}")

        return events

    def _parse_event_element(self, element, selectors: Dict) -> Dict:
        """
        Parse a single event element.

        Args:
            element: BeautifulSoup element containing event data
            selectors: Dictionary of CSS selectors

        Returns:
            Event dictionary or None if parsing fails
        """
        try:
            # Helper function to extract text from selector
            def get_text(selector, attr=None):
                """Extract text from element using selector."""
                if not selector:
                    return ""
                found = element.select_one(selector)
                if not found:
                    return ""
                if attr:
                    return found.get(attr, "")
                return found.get_text(strip=True)

            # Extract fields using selectors
            title = get_text(selectors.get('title', '.title'))
            description = get_text(selectors.get('description', '.description'))
            when_date = get_text(selectors.get('date', '.date'))
            when_time = get_text(selectors.get('time', '.time'))
            location = get_text(selectors.get('location', '.location'))

            # Extract URLs (may be in href attributes)
            event_url = get_text(selectors.get('url', 'a.event-link'), attr='href')
            registration_url = get_text(selectors.get('registration_url', 'a.register'), attr='href')
            image_url = get_text(selectors.get('image', 'img'), attr='src')

            target_age = get_text(selectors.get('age', '.age'))

            # Make URLs absolute if they're relative
            event_url = self._make_absolute_url(event_url)
            registration_url = self._make_absolute_url(registration_url)
            image_url = self._make_absolute_url(image_url)

            # If no registration URL, use event URL
            if not registration_url:
                registration_url = event_url

            # Create event dictionary
            event = self.create_event_dict(
                title=title,
                description=description,
                when_date=when_date,
                when_time=when_time,
                location=location,
                event_url=event_url,
                registration_url=registration_url,
                image_url=image_url,
                target_age=target_age
            )

            # Only return events with at least a title
            if event['title']:
                return event
            else:
                return None

        except Exception as e:
            self.logger.warning(f"Failed to parse event element: {str(e)}")
            return None

    def _make_absolute_url(self, url: str) -> str:
        """
        Convert relative URL to absolute URL.

        Args:
            url: URL string (may be relative or absolute)

        Returns:
            Absolute URL
        """
        if not url:
            return ""

        # If already absolute, return as is
        if url.startswith('http://') or url.startswith('https://'):
            return url

        # If protocol-relative, add https
        if url.startswith('//'):
            return 'https:' + url

        # If relative path, combine with base URL
        from urllib.parse import urljoin
        return urljoin(self.url, url)
