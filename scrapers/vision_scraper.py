"""
Vision Scraper

This module scrapes events from images and PDFs using Anthropic Claude API.
Suitable for sites where event information is contained in images or PDF files.
"""

from typing import List, Dict
import requests
import base64
import json
import os
from anthropic import Anthropic
from .base_scraper import BaseScraper


class VisionScraper(BaseScraper):
    """
    Scraper for image-based and PDF event sources using Claude's vision capabilities.

    Uses Anthropic's Claude API to extract structured event information
    from images or PDF pages.
    """

    def __init__(self, site_config: Dict):
        """
        Initialize the vision scraper.

        Args:
            site_config: Site configuration dictionary
        """
        super().__init__(site_config)

        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for VisionScraper")

        self.client = Anthropic(api_key=api_key)

    def scrape(self) -> List[Dict]:
        """
        Scrape events from images or PDFs using Claude vision.

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Get image/PDF URLs from config
            image_urls = self.config.get('image_urls', [])

            # If no image URLs specified, try to fetch from a page
            if not image_urls:
                image_urls = self._discover_image_urls()

            self.logger.info(f"Processing {len(image_urls)} images/PDFs")

            # Process each image
            for url in image_urls:
                try:
                    self.logger.info(f"Processing image: {url}")
                    image_events = self._process_image(url)
                    events.extend(image_events)

                    # Rate limit between API calls
                    self.rate_limit()

                except Exception as e:
                    self.logger.error(f"Error processing image {url}: {str(e)}")
                    continue

            self.logger.info(f"Extracted {len(events)} events from vision parsing")

        except Exception as e:
            self.logger.error(f"Error in vision scraping: {str(e)}")
            raise

        return events

    def _discover_image_urls(self) -> List[str]:
        """
        Discover image URLs from the configured website.

        Returns:
            List of image URLs
        """
        image_urls = []

        try:
            # Fetch the page
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse with BeautifulSoup to find images
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Get image selector from config
            image_selector = self.config.get('image_selector', 'img')

            # Find all images
            images = soup.select(image_selector)

            for img in images:
                src = img.get('src', '')
                if src:
                    # Make absolute URL
                    from urllib.parse import urljoin
                    absolute_url = urljoin(self.url, src)
                    image_urls.append(absolute_url)

            self.logger.info(f"Discovered {len(image_urls)} image URLs")

        except Exception as e:
            self.logger.error(f"Error discovering image URLs: {str(e)}")

        return image_urls

    def _process_image(self, image_url: str) -> List[Dict]:
        """
        Process a single image/PDF to extract events.

        Args:
            image_url: URL of the image or PDF

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Fetch the image
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Determine media type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type.lower():
                media_type = 'application/pdf'
            elif 'png' in content_type.lower():
                media_type = 'image/png'
            elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
                media_type = 'image/jpeg'
            elif 'webp' in content_type.lower():
                media_type = 'image/webp'
            elif 'gif' in content_type.lower():
                media_type = 'image/gif'
            else:
                # Default to PNG
                media_type = 'image/png'

            # Encode image to base64
            image_data = base64.standard_b64encode(response.content).decode('utf-8')

            # Create prompt for Claude
            prompt = self._create_extraction_prompt()

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response
            events = self._parse_claude_response(response_text)

            self.logger.info(f"Extracted {len(events)} events from image")

        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")

        return events

    def _create_extraction_prompt(self) -> str:
        """
        Create the prompt for Claude to extract event information.

        Returns:
            Prompt string
        """
        prompt = """
Please analyze this image and extract all event information you can find.

For each event, extract the following details:
- title: Event title/name
- description: Event description or details
- when_date: Event date in YYYY-MM-DD format
- when_time: Event time (e.g., "2:00 PM" or "14:00")
- location: Event location/venue
- registration_url: Registration or event URL if visible
- target_age: Target age group if specified
- image_url: Leave empty

Return the data as a JSON array of events. Example format:
```json
[
  {
    "title": "Summer Reading Program",
    "description": "Join us for our annual summer reading program...",
    "when_date": "2025-07-15",
    "when_time": "10:00 AM",
    "location": "Main Library",
    "registration_url": "",
    "target_age": "Ages 6-12",
    "image_url": ""
  }
]
```

If there are no events in the image, return an empty array: []

Important:
- Extract ALL events you can find in the image
- Convert dates to YYYY-MM-DD format
- If date/time is unclear, leave it empty
- Be thorough and extract all relevant details
"""
        return prompt

    def _parse_claude_response(self, response_text: str) -> List[Dict]:
        """
        Parse Claude's response and extract event dictionaries.

        Args:
            response_text: Response text from Claude

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            # Try to find JSON in the response
            # Look for JSON array or object
            import re

            # Find JSON code blocks
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON array
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    self.logger.warning("No JSON found in Claude response")
                    return events

            # Parse JSON
            parsed_events = json.loads(json_str)

            # Convert to standardized event dictionaries
            for event_data in parsed_events:
                event = self.create_event_dict(
                    title=event_data.get('title', ''),
                    description=event_data.get('description', ''),
                    when_date=event_data.get('when_date', ''),
                    when_time=event_data.get('when_time', ''),
                    location=event_data.get('location', ''),
                    registration_url=event_data.get('registration_url', ''),
                    target_age=event_data.get('target_age', ''),
                    event_url=event_data.get('registration_url', '')
                )
                events.append(event)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from Claude response: {str(e)}")
            self.logger.debug(f"Response text: {response_text}")

        except Exception as e:
            self.logger.error(f"Error parsing Claude response: {str(e)}")

        return events
