# Agentic FAQ

## Ask.gov.sg Scraper

A web scraper for ask.gov.sg that extracts Q&A content from JavaScript-rendered pages using Playwright and converts it to markdown.

### Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

### Setup

Create and activate a virtual environment:

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

### Get Sitemaps

Get the sitemaps from ask.gov.sg into /data/scripts/sitemaps

Run 
```bash
python data/scripts/scrape_sitemap.py
```

### Running the Scraper

The scraper can process a single URL or a list of URLs in multiple formats:


#### Text file with URLs (one per line)
Create `urls.txt`:
```
https://ask.gov.sg/aic/questions/cls1kszwg00em1codqhq5jgx3
https://ask.gov.sg/aic/questions/another-question-id
https://ask.gov.sg/aic/questions/yet-another-id
```

Then run:
```bash
python data/scripts/scrape_content.py data/urls.txt
```


### Run the firecrawl crawler

Pass the txt file with the urls you want to process in the script
```bash
python data/scripts/firecrawl_crawler.py
```

To add batch size
```bash
python data/scripts/firecrawl_crawler.py --batch-size 5
```