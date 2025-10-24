# Community Event Scraper

A comprehensive Python web scraper for extracting community events from 48+ organization websites. Supports multiple scraping methods (iCal, JSON/API, HTML, JavaScript-heavy sites via Playwright, and image/PDF parsing via AI) with automatic export to Google Sheets.

## Features

- **Multiple Scraping Methods:**
  - iCal (.ics) calendar feeds
  - JSON/API endpoints
  - Static HTML pages (BeautifulSoup)
  - JavaScript-heavy sites (Playwright)
  - Image/PDF parsing (Anthropic Claude Vision API)

- **Configuration-Driven:** Add new sites via YAML configuration without code changes

- **Robust Error Handling:**
  - Graceful failure handling
  - Automatic retries for failed sites
  - Comprehensive logging

- **Data Quality:**
  - Automatic date/time normalization
  - Deduplication
  - Data validation
  - Clean, standardized output

- **Google Sheets Integration:**
  - Automatic export with formatting
  - Summary statistics
  - Easy downstream automation

## Project Structure

```
event_scraper/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py          # Abstract base class
│   ├── ical_scraper.py           # iCal feed parser
│   ├── json_scraper.py           # JSON API parser
│   ├── html_scraper.py           # Static HTML scraper
│   ├── playwright_scraper.py     # JavaScript renderer
│   └── vision_scraper.py         # AI image/PDF parser
├── config/
│   ├── sites.yaml                # Site configurations
│   └── credentials.json          # Google credentials (gitignored)
├── utils/
│   ├── normalizer.py             # Data normalization
│   ├── date_parser.py            # Date/time parsing
│   ├── deduplicator.py           # Duplicate removal
│   └── sheets_exporter.py        # Google Sheets export
├── logs/                         # Log files
├── main.py                       # Main orchestrator
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud account (for Sheets export)
- Anthropic API key (for vision scraping)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd event_scraper
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Set Up Google Sheets API

#### a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Sheets API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

#### b. Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the details and click "Create"
4. Grant it the "Editor" role
5. Click "Done"

#### c. Generate Credentials

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON" format
5. Download the file
6. Save it as `config/credentials.json`

#### d. Share Your Google Sheet

1. Open your Google Sheet
2. Click "Share"
3. Add the service account email (found in credentials.json)
4. Give it "Editor" permissions

### 6. Get Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Save it for the next step

### 7. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_SHEETS_CREDENTIALS=config/credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id_here
```

**Finding your Google Sheet ID:**
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
- Copy the `{SHEET_ID}` part

## Configuration

### Adding Sites

Edit `config/sites.yaml` to add or modify sites:

#### iCal Example

```yaml
- name: "Village of Mamaroneck"
  url: "https://www.villageofmamaroneck.org"
  ical_url: "https://www.villageofmamaroneck.org/calendar.ics"
  method: "ical"
  status: "good"
  notes: "Has iCal feed with event data"
```

#### HTML Example

```yaml
- name: "Emelin Theater"
  url: "https://www.emelin.org/events"
  method: "html"
  status: "good"
  selectors:
    container: "div.event-item"
    title: "h3.event-title"
    description: "div.event-description"
    date: "span.event-date"
    time: "span.event-time"
    location: "span.event-location"
    url: "a.event-link"
    image: "img.event-image"
```

#### JSON API Example

```yaml
- name: "Mamaroneck Library"
  url: "https://mamaronecklibrary.org"
  api_url: "https://mamaronecklibrary.org/events.json"
  method: "json"
  status: "ok"
  field_map:
    title: "title"
    description: "description"
    when_date: "start_date"
    when_time: "start_time"
    event_url: "url"
```

#### Playwright Example

```yaml
- name: "Town of Larchmont"
  url: "https://www.townlarchmont.gov/calendar"
  method: "playwright"
  timeout: 60000
  wait_selector: "div.calendar-event"
  additional_wait: 3000
  selectors:
    container: "div.calendar-event"
    title: "h3"
    date: "span.date"
    time: "span.time"
```

#### Vision (Image/PDF) Example

```yaml
- name: "At Home on the Sound"
  url: "https://www.athomeonthesound.org/calendar"
  method: "vision"
  image_selector: "a[href*='.pdf']"
```

## Usage

### Run the Scraper

```bash
python main.py
```

The scraper will:
1. Load site configurations
2. Scrape all enabled sites
3. Normalize and clean the data
4. Remove duplicates
5. Export to Google Sheets
6. Generate a summary report in `logs/`

### Output

#### Google Sheets
- **Events sheet:** All scraped events with formatted columns
- **Summary sheet:** Statistics and source breakdown

#### Log Files
- `logs/scraper.log` - Detailed execution log
- `logs/report_TIMESTAMP.txt` - Summary report

### Event Data Format

Each event contains:
- `title` - Event title
- `description` - Event description
- `when_date` - Date (YYYY-MM-DD format)
- `when_time` - Time (HH:MM AM/PM format)
- `location` - Event location
- `registration_url` - Registration link
- `image_url` - Event image URL
- `target_age` - Target age group
- `event_url` - Event details URL
- `source_organization` - Source organization name
- `scraped_at` - Timestamp of scraping

## Troubleshooting

### Common Issues

#### "Google Sheets credentials not found"
- Ensure `config/credentials.json` exists
- Verify the path in `.env` is correct
- Check file permissions

#### "Failed to scrape [site]"
- Check the site's URL is accessible
- Verify CSS selectors in `sites.yaml`
- Review logs for specific error messages
- Try increasing timeout for Playwright sites

#### "Playwright browser not found"
- Run: `playwright install chromium`

#### "Rate limiting errors"
- Increase delays in `.env`:
  ```
  MIN_DELAY=3.0
  MAX_DELAY=5.0
  ```

#### "No events found"
- Verify the site structure hasn't changed
- Check CSS selectors using browser DevTools
- Enable DEBUG logging in `.env`:
  ```
  LOG_LEVEL=DEBUG
  ```

### Debugging

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG
```

Check individual scrapers:

```python
# Test a single site
from scrapers import HTMLScraper

config = {
    'name': 'Test Site',
    'url': 'https://example.com/events',
    'selectors': {
        'container': 'div.event',
        'title': 'h2'
    }
}

scraper = HTMLScraper(config)
events = scraper.scrape()
print(f"Found {len(events)} events")
```

## Customization

### Adding a New Scraper Type

1. Create a new file in `scrapers/` (e.g., `rss_scraper.py`)
2. Inherit from `BaseScraper`
3. Implement the `scrape()` method
4. Add to `scrapers/__init__.py`
5. Add to `SCRAPER_MAP` in `main.py`

### Custom Data Processing

Edit `utils/normalizer.py` to add custom normalization logic:

```python
def normalize_event(event: Dict) -> Dict:
    # Add custom processing here
    # ...
    return normalized
```

## Performance

- **Expected runtime:** 5-10 minutes for 48 sites
- **Rate limiting:** 2-3 seconds between requests (configurable)
- **Retries:** 1 automatic retry after 30 seconds (configurable)

### Optimization Tips

1. **Disable unused sites:** Set `enabled: false` in `sites.yaml`
2. **Parallel scraping:** Consider using threading for independent sites
3. **Cache results:** Add caching for frequently accessed sites

## Maintenance

### Regular Updates

1. **Check site structure changes:**
   - Review failed scrapes in logs
   - Update CSS selectors as needed

2. **Update dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Clean old logs:**
   ```bash
   rm logs/report_*.txt
   rm logs/scraper.log
   ```

### Adding New Sites

1. Inspect the site's structure
2. Determine the best scraping method
3. Add configuration to `sites.yaml`
4. Test with a single run
5. Adjust selectors/settings as needed

## API Rate Limits

### Anthropic Claude API
- Standard rate limits apply
- Vision calls count toward API quota
- Monitor usage in [Anthropic Console](https://console.anthropic.com/)

### Google Sheets API
- 100 requests per 100 seconds per user
- 500 requests per 100 seconds per project
- Usually not an issue for daily scraping

## Security

- **Never commit `.env` or credentials files**
- Keep API keys secure
- Regularly rotate credentials
- Use service accounts with minimal permissions

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `logs/`
3. Open an issue on GitHub

## Acknowledgments

Built with:
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Playwright](https://playwright.dev/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Google Sheets API](https://developers.google.com/sheets/api)
