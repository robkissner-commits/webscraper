# Quick Start Guide

Get up and running with the Event Scraper in 5 minutes!

## Prerequisites Check

- [ ] Python 3.8+ installed
- [ ] Google Cloud account
- [ ] Anthropic API account

## Installation (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install Playwright
playwright install chromium
```

### 2. Set Up Google Sheets

**Quick Steps:**
1. Go to https://console.cloud.google.com/
2. Create project → Enable "Google Sheets API"
3. Create Service Account → Download JSON
4. Save as `config/credentials.json`
5. Share your Google Sheet with the service account email

**Find service account email:**
```bash
cat config/credentials.json | grep client_email
```

### 3. Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit .env and add:
# - Your Anthropic API key
# - Your Google Sheet ID (from the URL)
```

### 4. Add Your Sites

Edit `config/sites.yaml` and configure your 48 sites. Examples are already provided for each scraper type.

### 5. Run!

```bash
python main.py
```

## Testing Individual Sites

Before running all sites, test individual ones:

```python
# Test an iCal site
python -c "
from scrapers import ICalScraper
config = {
    'name': 'Test',
    'url': 'https://example.com',
    'ical_url': 'https://example.com/calendar.ics'
}
scraper = ICalScraper(config)
events = scraper.scrape()
print(f'Found {len(events)} events')
"
```

## Common First-Run Issues

### "Module not found"
```bash
# Activate virtual environment
source venv/bin/activate
```

### "Playwright not found"
```bash
playwright install chromium
```

### "Google Sheets authentication failed"
- Check `config/credentials.json` exists
- Verify service account email has access to your sheet
- Confirm GOOGLE_SHEET_ID in .env is correct

### "Anthropic API error"
- Verify ANTHROPIC_API_KEY in .env
- Check you have API credits

## What Gets Created

After running, you'll have:
- `logs/scraper.log` - Detailed log
- `logs/report_*.txt` - Summary report
- Google Sheet with two tabs:
  - **Events** - All scraped events
  - **Summary** - Statistics

## Next Steps

1. **Review the output** - Check Google Sheets for data quality
2. **Adjust configurations** - Update CSS selectors for failed sites
3. **Add remaining sites** - Configure all 48 sites in `sites.yaml`
4. **Automate** - Set up a cron job or scheduled task

## Cron Job Example

Run daily at 7 AM:

```bash
# Edit crontab
crontab -e

# Add line:
0 7 * * * cd /path/to/webscraper && /path/to/venv/bin/python main.py
```

## Debugging

```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env

# Run again
python main.py

# Check logs
tail -f logs/scraper.log
```

## Getting Help

- Check `README.md` for full documentation
- Review `logs/` for error details
- Inspect site structure with browser DevTools
- Test scrapers individually (see above)

## Tips for Adding Sites

1. **Find the right method:**
   - Look for `.ics` files → use `ical`
   - Look for `/api/` or `.json` → use `json`
   - Simple HTML → use `html`
   - Lots of JavaScript → use `playwright`
   - Events in images/PDFs → use `vision`

2. **Find CSS selectors:**
   - Open browser DevTools (F12)
   - Right-click event → Inspect
   - Copy selector
   - Test in DevTools console: `document.querySelector('your-selector')`

3. **Start simple:**
   - Enable one site at a time
   - Get it working
   - Move to the next

Good luck! 🚀
