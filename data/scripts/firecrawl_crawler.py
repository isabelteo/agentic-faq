from firecrawl import Firecrawl
from pathlib import Path
import json
import os
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
import hashlib
from datetime import datetime
import argparse
import time

load_dotenv()

# Setup logging
log_dir = Path('data/scripts/logs')
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"firecrawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY not found in .env file")

app = Firecrawl(api_key=FIRECRAWL_API_KEY)

LINKS_DIR = Path('data/scripts/output')
OUTPUT_BASE_DIR = Path('data/scripts/output/firecrawl')


def get_already_crawled_urls():
    """Scan output directory and extract URLs that have already been crawled."""
    crawled_urls = set()

    if not OUTPUT_BASE_DIR.exists():
        return crawled_urls

    for json_file in OUTPUT_BASE_DIR.rglob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'source_url' in data:
                    crawled_urls.add(data['source_url'])
        except Exception as e:
            logger.warning(f"Could not read {json_file}: {e}")

    return crawled_urls

def extract_folder_name(url):
    """Extract folder name from URL based on domain and first path segment."""
    parsed = urlparse(url)
    domain = parsed.netloc
    path_parts = [p for p in parsed.path.split('/') if p]

    if path_parts:
        first_segment = path_parts[0]
        folder_name = f"{domain}-{first_segment}"
    else:
        folder_name = domain

    return folder_name

def get_output_filename(url):
    """Generate a unique filename based on URL hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{url_hash}.json"

def crawl_url(url):
    """Crawl a single URL using Firecrawl."""
    try:
        logger.info(f"Crawling: {url}")
        data = app.scrape(
            url,
            only_main_content=True,
            max_age=172800000,
            formats=["links", "markdown"]
        )
        logger.debug(f"Successfully crawled: {url}")
        return data
    except Exception as e:
        error_msg = str(e)

        # Check if it's a rate limit error
        if "Rate Limit Exceeded" in error_msg or "rate limit" in error_msg.lower():
            logger.error(f"Rate limit exceeded. Stopping crawl.")
            raise  # Re-raise to signal caller to stop

        logger.error(f"Error crawling {url}: {e}")
        return None

def save_data(url, data):
    """Save crawled data to organized folder structure."""
    if not data:
        return False

    folder_name = extract_folder_name(url)
    output_dir = OUTPUT_BASE_DIR / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = get_output_filename(url)
    output_path = output_dir / filename

    # Use Pydantic's built-in serialization for the Document model
    if hasattr(data, 'model_dump'):
        # Pydantic v2
        data_to_save = data.model_dump(exclude_none=True)
    else:
        data_to_save = data

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "source_url": url,
            "data": data_to_save
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved to: {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Firecrawl crawler for scraping URLs")
    parser.add_argument('--batch-size', type=int, default=None, help='Maximum number of URLs to process per run (default: process all)')
    args = parser.parse_args()

    logger.info("Starting Firecrawl crawler...")
    all_urls = []

    # Read URLs from both files
    link_files = [
        #LINKS_DIR / 'ask-links.txt',
        LINKS_DIR / 'supportgowhere-links.txt'
    ]

    for link_file in link_files:
        if link_file.exists():
            with open(link_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                all_urls.extend(urls)
            logger.info(f"Loaded {len(urls)} URLs from {link_file.name}")
        else:
            logger.warning(f"Link file not found: {link_file}")

    logger.info(f"Total URLs available: {len(all_urls)}")

    # Get already crawled URLs
    crawled_urls = get_already_crawled_urls()
    logger.info(f"Already crawled: {len(crawled_urls)}")

    # Filter to only new URLs
    urls_to_crawl = [url for url in all_urls if url not in crawled_urls]
    logger.info(f"New URLs to crawl: {len(urls_to_crawl)}")

    # Apply batch size limit if specified
    if args.batch_size:
        urls_to_crawl = urls_to_crawl[:args.batch_size]
        logger.info(f"Batch size limit: {args.batch_size}, processing {len(urls_to_crawl)} URLs")

    if not urls_to_crawl:
        logger.info("No new URLs to crawl. All URLs have been processed!")
        return

    logger.info("Starting crawl...")

    successful = 0
    failed = 0

    try:
        for i, url in enumerate(urls_to_crawl, 1):
            logger.info(f"[{i}/{len(urls_to_crawl)}] Processing URL")
            data = crawl_url(url)
            if save_data(url, data):
                successful += 1
            else:
                failed += 1

            # Add 4-second delay between requests to stay under rate limit (15 req/min)
            if i < len(urls_to_crawl):
                time.sleep(4)
    except Exception as e:
        if "Rate Limit Exceeded" in str(e) or "rate limit" in str(e).lower():
            logger.error(f"Rate limit hit. Stopping crawl. Processed: {successful} successful, {failed} failed")
            return

    logger.info(f"Crawl complete! Successful: {successful}, Failed: {failed}")

if __name__ == "__main__":
    main()
