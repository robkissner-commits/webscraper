"""
Google Sheets Exporter Utility

This module provides functionality to export event data to Google Sheets.
"""

from typing import List, Dict
import logging
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SheetsExporter:
    """
    Export event data to Google Sheets using the Google Sheets API.
    """

    # Scopes required for Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Column headers for the sheet
    HEADERS = [
        'Title',
        'Description',
        'Date',
        'Time',
        'Location',
        'Registration URL',
        'Image URL',
        'Target Age',
        'Event URL',
        'Source Organization',
        'Scraped At'
    ]

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Initialize the Google Sheets exporter.

        Args:
            credentials_path: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.service = None

        # Initialize the service
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Google Sheets API service."""
        try:
            # Load credentials
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )

            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            raise

    def export_events(
        self,
        events: List[Dict],
        sheet_name: str = "Events",
        clear_existing: bool = True
    ) -> bool:
        """
        Export events to Google Sheets.

        Args:
            events: List of event dictionaries
            sheet_name: Name of the sheet (tab) to write to
            clear_existing: Whether to clear existing data before writing

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Exporting {len(events)} events to Google Sheets")

            # Clear existing data if requested
            if clear_existing:
                self._clear_sheet(sheet_name)

            # Prepare data for export
            rows = self._prepare_data(events)

            # Write to sheet
            self._write_to_sheet(sheet_name, rows)

            # Format the sheet
            self._format_sheet(sheet_name)

            logger.info(f"Successfully exported {len(events)} events to Google Sheets")
            return True

        except Exception as e:
            logger.error(f"Failed to export events to Google Sheets: {str(e)}")
            return False

    def _prepare_data(self, events: List[Dict]) -> List[List[str]]:
        """
        Prepare event data for export.

        Args:
            events: List of event dictionaries

        Returns:
            List of rows (each row is a list of cell values)
        """
        # Start with headers
        rows = [self.HEADERS]

        # Add event data
        for event in events:
            row = [
                event.get('title', ''),
                event.get('description', ''),
                event.get('when_date', ''),
                event.get('when_time', ''),
                event.get('location', ''),
                event.get('registration_url', ''),
                event.get('image_url', ''),
                event.get('target_age', ''),
                event.get('event_url', ''),
                event.get('source_organization', ''),
                event.get('scraped_at', '')
            ]
            rows.append(row)

        return rows

    def _clear_sheet(self, sheet_name: str):
        """
        Clear all data from the sheet.

        Args:
            sheet_name: Name of the sheet to clear
        """
        try:
            # Clear all data
            range_name = f"{sheet_name}!A1:Z10000"

            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                body={}
            ).execute()

            logger.info(f"Cleared existing data from sheet '{sheet_name}'")

        except HttpError as e:
            if e.resp.status == 400:
                # Sheet doesn't exist, create it
                logger.info(f"Sheet '{sheet_name}' doesn't exist, will be created")
            else:
                raise

    def _write_to_sheet(self, sheet_name: str, rows: List[List[str]]):
        """
        Write data to the sheet.

        Args:
            sheet_name: Name of the sheet
            rows: List of rows to write
        """
        range_name = f"{sheet_name}!A1"

        body = {
            'values': rows
        }

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        logger.info(f"Wrote {len(rows)} rows to sheet '{sheet_name}'")

    def _format_sheet(self, sheet_name: str):
        """
        Apply formatting to the sheet.

        Args:
            sheet_name: Name of the sheet to format
        """
        try:
            # Get the sheet ID
            sheet_id = self._get_sheet_id(sheet_name)

            if sheet_id is None:
                logger.warning(f"Could not find sheet ID for '{sheet_name}', skipping formatting")
                return

            # Prepare formatting requests
            requests = []

            # Format header row (bold, background color)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.2,
                                'blue': 0.2
                            },
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                },
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            })

            # Auto-resize columns
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': len(self.HEADERS)
                    }
                }
            })

            # Freeze header row
            requests.append({
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            })

            # Execute formatting requests
            body = {'requests': requests}

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()

            logger.info(f"Applied formatting to sheet '{sheet_name}'")

        except Exception as e:
            logger.warning(f"Failed to format sheet: {str(e)}")

    def _get_sheet_id(self, sheet_name: str) -> int:
        """
        Get the sheet ID for a given sheet name.

        Args:
            sheet_name: Name of the sheet

        Returns:
            Sheet ID or None if not found
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']

            return None

        except Exception as e:
            logger.error(f"Error getting sheet ID: {str(e)}")
            return None

    def add_summary_sheet(self, stats: Dict):
        """
        Add a summary sheet with scraping statistics.

        Args:
            stats: Dictionary containing scraping statistics
        """
        try:
            sheet_name = "Summary"

            # Prepare summary data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            rows = [
                ['Event Scraper Summary'],
                [''],
                ['Last Run', timestamp],
                ['Total Events Scraped', str(stats.get('total_events', 0))],
                ['Unique Events', str(stats.get('unique_events', 0))],
                ['Duplicates Removed', str(stats.get('duplicates_removed', 0))],
                ['Sites Scraped Successfully', str(stats.get('successful_sites', 0))],
                ['Sites Failed', str(stats.get('failed_sites', 0))],
                [''],
                ['Source Breakdown'],
            ]

            # Add source breakdown
            sources = stats.get('sources', {})
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                rows.append([source, str(count)])

            # Write to summary sheet
            self._write_to_sheet(sheet_name, rows)

            logger.info("Added summary sheet")

        except Exception as e:
            logger.error(f"Failed to create summary sheet: {str(e)}")
