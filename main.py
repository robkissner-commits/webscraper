#!/usr/bin/env python3
"""
Event Scraper - Main Orchestrator

This script orchestrates the scraping of community events from multiple websites,
normalizes the data, removes duplicates, and exports to Google Sheets.
"""

import os
import sys
import yaml
import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import scrapers
from scrapers import (
    ICalScraper,
    JSONScraper,
    HTMLScraper,
    PlaywrightScraper,
    VisionScraper
)

# Import utilities
from utils import (
    normalize_events,
    deduplicate_events,
    SheetsExporter
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class EventScraperOrchestrator:
    """
    Main orchestrator for the event scraping system.

    Coordinates scraping from multiple sites, data processing, and export.
    """

    # Map method names to scraper classes
    SCRAPER_MAP = {
        'ical': ICalScraper,
        'json': JSONScraper,
        'html': HTMLScraper,
        'playwright': PlaywrightScraper,
        'vision': VisionScraper
    }

    def __init__(self, config_path: str = 'config/sites.yaml'):
        """
        Initialize the orchestrator.

        Args:
            config_path: Path to sites configuration file
        """
        self.config_path = config_path
        self.sites = []
        self.all_events = []
        self.stats = {
            'total_events': 0,
            'unique_events': 0,
            'duplicates_removed': 0,
            'successful_sites': 0,
            'failed_sites': 0,
            'sources': {}
        }

        # Load environment variables
        load_dotenv()

        # Load site configuration
        self._load_config()

    def _load_config(self):
        """Load site configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.sites = config.get('sites', [])

            # Filter out disabled sites
            self.sites = [s for s in self.sites if s.get('enabled', True)]

            logger.info(f"Loaded configuration for {len(self.sites)} sites")

        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)

    def run(self):
        """
        Run the complete scraping pipeline.

        1. Scrape all sites
        2. Normalize data
        3. Remove duplicates
        4. Export to Google Sheets
        5. Generate report
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting Event Scraper")
            logger.info("=" * 80)

            start_time = datetime.now()

            # Step 1: Scrape all sites
            logger.info("\n[Step 1/5] Scraping sites...")
            self._scrape_all_sites()

            # Step 2: Normalize events
            logger.info(f"\n[Step 2/5] Normalizing {len(self.all_events)} events...")
            self.all_events = normalize_events(self.all_events)
            logger.info(f"Normalized to {len(self.all_events)} valid events")

            # Step 3: Remove duplicates
            logger.info(f"\n[Step 3/5] Removing duplicates...")
            original_count = len(self.all_events)
            self.all_events = deduplicate_events(self.all_events)
            duplicates = original_count - len(self.all_events)
            self.stats['duplicates_removed'] = duplicates
            self.stats['unique_events'] = len(self.all_events)
            logger.info(f"Removed {duplicates} duplicates, {len(self.all_events)} unique events remain")

            # Step 4: Export to Google Sheets
            logger.info(f"\n[Step 4/5] Exporting to Google Sheets...")
            self._export_to_sheets()

            # Step 5: Generate report
            logger.info(f"\n[Step 5/5] Generating report...")
            self._generate_report()

            # Calculate total time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("=" * 80)
            logger.info(f"Scraping completed in {duration:.1f} seconds")
            logger.info(f"Total events: {self.stats['unique_events']}")
            logger.info(f"Successful sites: {self.stats['successful_sites']}")
            logger.info(f"Failed sites: {self.stats['failed_sites']}")
            logger.info("=" * 80)

        except KeyboardInterrupt:
            logger.warning("\nScraping interrupted by user")
            sys.exit(1)

        except Exception as e:
            logger.error(f"Fatal error in scraping pipeline: {str(e)}", exc_info=True)
            sys.exit(1)

    def _scrape_all_sites(self):
        """Scrape all configured sites."""
        for i, site_config in enumerate(self.sites, 1):
            site_name = site_config.get('name', 'Unknown')
            method = site_config.get('method', '')

            logger.info(f"\n[{i}/{len(self.sites)}] Scraping {site_name} (method: {method})...")

            try:
                # Get the appropriate scraper class
                scraper_class = self.SCRAPER_MAP.get(method)

                if not scraper_class:
                    logger.error(f"Unknown scraping method: {method}")
                    self.stats['failed_sites'] += 1
                    continue

                # Create scraper instance
                scraper = scraper_class(site_config)

                # Scrape with retry
                events = scraper.scrape_with_retry()

                if events:
                    self.all_events.extend(events)
                    self.stats['successful_sites'] += 1
                    self.stats['total_events'] += len(events)

                    # Track events per source
                    self.stats['sources'][site_name] = len(events)

                    logger.info(f"✓ Successfully scraped {len(events)} events from {site_name}")
                else:
                    self.stats['failed_sites'] += 1
                    logger.warning(f"✗ No events found for {site_name}")

            except Exception as e:
                self.stats['failed_sites'] += 1
                logger.error(f"✗ Failed to scrape {site_name}: {str(e)}")
                continue

    def _export_to_sheets(self):
        """Export events to Google Sheets."""
        try:
            # Get credentials and sheet ID from environment
            credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')

            if not credentials_path or not spreadsheet_id:
                logger.warning("Google Sheets credentials not configured, skipping export")
                logger.info("Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEET_ID in .env file")
                return

            # Create exporter
            exporter = SheetsExporter(credentials_path, spreadsheet_id)

            # Export events
            success = exporter.export_events(self.all_events)

            if success:
                # Add summary sheet
                exporter.add_summary_sheet(self.stats)
                logger.info("✓ Successfully exported to Google Sheets")
            else:
                logger.error("✗ Failed to export to Google Sheets")

        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {str(e)}")

    def _generate_report(self):
        """Generate a summary report."""
        report_path = f"logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        try:
            with open(report_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("EVENT SCRAPER REPORT\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total events scraped: {self.stats['total_events']}\n")
                f.write(f"Unique events: {self.stats['unique_events']}\n")
                f.write(f"Duplicates removed: {self.stats['duplicates_removed']}\n")
                f.write(f"Successful sites: {self.stats['successful_sites']}\n")
                f.write(f"Failed sites: {self.stats['failed_sites']}\n\n")

                f.write("EVENTS BY SOURCE\n")
                f.write("-" * 80 + "\n")

                # Sort sources by event count
                sorted_sources = sorted(
                    self.stats['sources'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                for source, count in sorted_sources:
                    f.write(f"{source:.<50} {count:>5} events\n")

                f.write("\n" + "=" * 80 + "\n")

            logger.info(f"Report saved to: {report_path}")

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")


def main():
    """Main entry point."""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Create orchestrator and run
    orchestrator = EventScraperOrchestrator()
    orchestrator.run()


if __name__ == '__main__':
    main()
