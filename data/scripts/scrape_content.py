#!/usr/bin/env python3
"""
Scraper for ask.gov.sg and life.gov.sg using Playwright - handles JavaScript-rendered content.

Supports:
- ask.gov.sg: Extracts questions and answers from article-based structure
- life.gov.sg/guides: Extracts content from <section role="main">

Outputs formatted markdown with links preserved.
"""

import asyncio
from urllib.parse import urljoin

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, NavigableString


def html_to_markdown(element, base_url, links=None):
    """Recursively convert a BeautifulSoup element's inline content to markdown,
    preserving links as [text](url). Tracks all links in the links list."""
    if links is None:
        links = []
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).replace("\xa0", " ")
            if text.strip():
                parts.append(text)
        elif child.name == "a":
            href = child.get("href", "")
            link_text = child.get_text(strip=True).replace("\xa0", " ")
            if not link_text:
                # icon-only link (no visible text) - skip to avoid duplicate empty links
                continue
            full_url = urljoin(base_url, href) if href else href
            links.append({"text": link_text, "url": full_url})
            parts.append(f"[{link_text}]({full_url})")
        elif child.name in ("b", "strong"):
            parts.append(f"**{child.get_text(strip=True)}**")
        elif child.name in ("i", "em"):
            parts.append(f"*{child.get_text(strip=True)}*")
        elif child.name == "sup":
            # footnote marker - not rendered as a distinct footnote list, so drop it
            continue
        elif child.name == "br":
            parts.append("\n")
        elif child.name in ("p", "div"):
            text_only = child.get_text(strip=True).replace("\xa0", " ")
            if not text_only:
                # spacer element (e.g. <div>&nbsp;</div>) - skip, blocks already get spacing
                continue
            if "italic" in (child.get("class") or []):
                # citation/attribution footer ("This information is sourced from...")
                continue
            inner = html_to_markdown(child, base_url, links)
            if inner.strip():
                parts.append(inner.strip() + "\n\n")
        elif child.name in ("ul", "ol"):
            for i, li in enumerate(child.find_all("li", recursive=False)):
                bullet = "-" if child.name == "ul" else f"{i + 1}."
                parts.append(f"{bullet} {html_to_markdown(li, base_url, links).strip()}\n")
        else:
            parts.append(html_to_markdown(child, base_url, links))
    return "".join(parts)


async def extract_life_gov_sg_data(page):
    """Extract data from life.gov.sg pages."""
    return await page.evaluate(
        r"""
        () => {
            // life.gov.sg: extract from <section role="main"> or fallback to other section locations
            let mainSection = document.querySelector('section[role="main"]');

            // Fallback: try alternative XPath location
            if (!mainSection) {
                const xpath = '//*[@id="__next"]/div/main/section/div/section';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                mainSection = result.singleNodeValue;
            }

            // Additional fallback: try just main > section
            if (!mainSection) {
                const main = document.querySelector('main');
                if (main) {
                    mainSection = main.querySelector('section');
                }
            }

            if (!mainSection) {
                const alternatives = document.querySelector('article') ||
                                    document.querySelector('div[role="main"]') ||
                                    document.querySelector('div.main-content') ||
                                    document.querySelector('main');
                return { mainSectionFound: false, alternatives: !!alternatives };
            }

            // Extract title from h1 or h2
            const titleEl = mainSection.querySelector('h1') || mainSection.querySelector('h2');
            const title = titleEl ? titleEl.textContent.trim() : null;

            // Extract description using XPath or fallback selectors
            let description = null;
            try {
                // Try specific XPath: //*[@id="__next"]/div/main/section[3]/div/div/h5
                const xpath = '//*[@id="__next"]/div/main/section[3]/div/div/h5';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const descEl = result.singleNodeValue;
                if (descEl) {
                    description = descEl.textContent.trim();
                }
            } catch (e) {
                // Fallback: look for h5 in various common locations
                const fallbackSelectors = [
                    'h5[class*="sidebar-description__Subtitle"]',
                    'div.sidebar_description__Subtitle h5',
                    'div.sidebar-description h5',
                    'main section h5'
                ];
                for (const selector of fallbackSelectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        description = el.textContent.trim();
                        break;
                    }
                }
            }

            // Extract content from paragraph using alternative XPath - handles multiple paragraphs
            let contentFromParagraph = null;
            try {
                // Try to extract all paragraphs from the content container
                const xpaths = [
                    '//*[@id="__next"]/div/main/section[2]/div/div/div[1]/p',
                    '//*[@id="__next"]/div/main/section/div/div/div/p'
                ];
                for (const xpath of xpaths) {
                    const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (result.snapshotLength > 0) {
                        const paragraphs = [];
                        for (let i = 0; i < result.snapshotLength; i++) {
                            const p = result.snapshotItem(i);
                            const text = p.textContent ? p.textContent.trim() : '';
                            if (text) {
                                paragraphs.push(text);
                            }
                        }
                        if (paragraphs.length > 0) {
                            contentFromParagraph = paragraphs.join('\n\n');
                            break;
                        }
                    }
                }
            } catch (e) {
                // If XPath extraction fails, continue without it
            }

            // Extract sidebar title if available
            const sidebarTitle = document.querySelector('div.sidebar-description__TItle');

            const sidebarMetadata = {
                title: sidebarTitle ? sidebarTitle.textContent.trim() : null,
                description: description
            };

            // Get all content from main section
            const contentHtml = mainSection.innerHTML;

            // Additional extraction: check for articles with multiple paragraphs in specific structure
            let contentByParagraphs = null;
            try {
                const xpath = '//*[@id="__next"]/div/main/section[2]/div/div/div[1]';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const container = result.singleNodeValue;

                if (container) {
                    // Extract all paragraph elements from this container
                    const paragraphs = container.querySelectorAll('p');
                    if (paragraphs.length > 1) {
                        // Join multiple paragraphs with proper spacing
                        const texts = Array.from(paragraphs)
                            .map(p => (p.textContent || '').trim())
                            .filter(text => text.length > 0);
                        if (texts.length > 0) {
                            contentByParagraphs = texts.join('\n\n');
                        }
                    }
                }
            } catch (e) {
                // Continue without it
            }

            return { title, contentHtml, sidebarMetadata, contentFromParagraph, contentByParagraphs };
        }
        """
    )


async def extract_ask_gov_sg_data(page):
    """Extract data from ask.gov.sg pages."""
    return await page.evaluate(
        """
        () => {
            // ask.gov.sg: extract from nested articles
            const articles = Array.from(document.querySelectorAll('article'));
            const questionArticle = articles.find(a => a.querySelector('header'));
            if (!questionArticle) return null;

            const h1 = questionArticle.querySelector('header h1');
            const question = h1 ? h1.textContent.trim() : null;

            const answerArticle = questionArticle.querySelector('article');
            const answerHtml = answerArticle ? answerArticle.innerHTML : null;

            return { question, answerHtml };
        }
        """
    )


async def scrape_life_gov_sg(url):
    """Scrape a single page from life.gov.sg and return structured data."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            print(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector("section[role='main']", timeout=30000)
            except Exception:
                pass

            data = await extract_life_gov_sg_data(page)
            await browser.close()
    except Exception as e:
        print(f"Browser error: {type(e).__name__}: {e}")
        return None

    if not data:
        print("Could not find content on the page.")
        return None

    title = data.get("title")
    content_html = data.get("contentHtml")

    # Fallback to URL slug if no title found
    if not title:
        guide_name = url.split("/")[-1] or "guide"
        title = guide_name.replace("-", " ").title()
        print(f"Using URL slug as title: {title}")

    md = []
    md.append(f"# {title}")
    md.append("")

    links_with_text = []

    # Primary parsing: use existing html_to_markdown logic
    if content_html:
        content_soup = BeautifulSoup(content_html, "html.parser")
        content_md = html_to_markdown(content_soup, url, links_with_text).strip()
        md.append(content_md)
        md.append("")

    # Secondary parsing: for articles with paragraph-based content
    content_by_paras = data.get("contentByParagraphs")
    if content_by_paras and content_by_paras.strip():
        md.append(content_by_paras)
        md.append("")

    # Convert links to flat array of URLs (removing duplicates while preserving order)
    seen_urls = set()
    flat_links = []
    for link in links_with_text:
        url_str = link["url"]
        if url_str not in seen_urls:
            seen_urls.add(url_str)
            flat_links.append(url_str)

    # Build metadata
    metadata = {"title": title}

    # Add sidebar metadata if available
    if data.get("sidebarMetadata"):
        sidebar = data["sidebarMetadata"]
        if sidebar.get("description"):
            metadata["description"] = sidebar["description"]

    # Return structured data
    return {
        "source_url": url,
        "data": {
            "markdown": "\n".join(md),
            "metadata": metadata,
            "links": flat_links
        }
    }


async def scrape_ask_gov_sg(url):
    """Scrape a single page from ask.gov.sg and return structured data."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            print(f"Loading {url}...")
            await page.goto(url, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector("article header h1", timeout=30000)
            except Exception:
                pass

            data = await extract_ask_gov_sg_data(page)
            await browser.close()
    except Exception as e:
        print(f"Browser error: {type(e).__name__}: {e}")
        return None

    if not data:
        print("Could not find content on the page.")
        return None

    title = data.get("question")
    content_html = data.get("answerHtml")

    # Fallback to URL slug if no title found
    if not title:
        guide_name = url.split("/")[-1] or "question"
        title = guide_name.replace("-", " ").title()
        print(f"Using URL slug as title: {title}")

    md = []
    md.append(f"# {title}")
    md.append("")

    links_with_text = []
    if content_html:
        content_soup = BeautifulSoup(content_html, "html.parser")
        content_md = html_to_markdown(content_soup, url, links_with_text).strip()
        md.append("## Answer")
        md.append("")
        md.append(content_md)
        md.append("")

    # Convert links to flat array of URLs (removing duplicates while preserving order)
    seen_urls = set()
    flat_links = []
    for link in links_with_text:
        url_str = link["url"]
        if url_str not in seen_urls:
            seen_urls.add(url_str)
            flat_links.append(url_str)

    # Build metadata
    metadata = {"title": title}

    # Return structured data
    return {
        "source_url": url,
        "data": {
            "markdown": "\n".join(md),
            "metadata": metadata,
            "links": flat_links
        }
    }


def load_processed_urls(output_base_dir):
    """Load all source_url values from existing JSON files in output directories."""
    from pathlib import Path
    import json

    processed_urls = set()
    output_path = Path(output_base_dir)

    if not output_path.exists():
        return processed_urls

    # Scan all subdirectories and JSON files
    for json_file in output_path.rglob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "source_url" in data:
                    processed_urls.add(data["source_url"])
        except (json.JSONDecodeError, IOError):
            # Skip files that can't be read or parsed
            pass

    return processed_urls


async def main():
    import sys
    import json
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python scrape_content.py <url_or_json_file>")
        print("  - url_or_json_file: A single URL or path to a JSON file with a list of URLs")
        print("  - Supports: ask.gov.sg, life.gov.sg/guides")
        print("  - JSON format: {\"urls\": [\"url1\", \"url2\", ...]}")
        sys.exit(1)

    input_arg = sys.argv[1]
    urls = []

    # Check if input is a JSON file
    if input_arg.endswith('.json') and Path(input_arg).exists():
        with open(input_arg, 'r', encoding='utf-8') as f:
            data = json.load(f)
            urls = data.get('urls', [])
        print(f"Loaded {len(urls)} URLs from {input_arg}")
    # Check if input is a file with URLs (one per line)
    elif Path(input_arg).exists() and not input_arg.endswith('.json'):
        with open(input_arg, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(urls)} URLs from {input_arg}")
    # Otherwise treat it as a single URL
    else:
        urls = [input_arg]

    if not urls:
        print("No URLs to process")
        sys.exit(1)

    # Create output directories if they don't exist
    Path("data/scripts/output").mkdir(parents=True, exist_ok=True)
    Path("data/scripts/output/web-scraper").mkdir(parents=True, exist_ok=True)
    Path("data/scripts/output/web-scraper/lifesg-guides").mkdir(parents=True, exist_ok=True)

    # Load already-processed URLs and filter
    output_base_dir = Path("data/scripts/output/web-scraper")
    processed_urls = load_processed_urls(output_base_dir)

    original_count = len(urls)
    urls = [url for url in urls if url not in processed_urls]

    # Filter out life.gov.sg URLs containing /guides/pe
    urls = [url for url in urls if not (url.startswith("https://www.life.gov.sg") and "/guides/pe" in url)]

    skipped_count = original_count - len(urls)

    if skipped_count > 0:
        print(f"Skipping {skipped_count} already-processed or filtered URL(s)")

    if not urls:
        print("All URLs have already been processed")
        sys.exit(0)

    print(f"\nRemaining URLs to process ({len(urls)}):")
    for url in urls:
        print(f"  - {url}")

    # Process URLs and save results immediately
    saved_count = 0
    failed_count = 0
    failed_urls = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing {url}...")
        try:
            # Call appropriate scraper based on site type
            if "life.gov.sg" in url:
                content = await scrape_life_gov_sg(url)
            else:
                content = await scrape_ask_gov_sg(url)

            if content:
                # Determine output path based on site type
                if "life.gov.sg" in url:
                    output_dir = Path("data/scripts/output/web-scraper/lifesg-guides")
                else:
                    output_dir = Path("data/scripts/output/web-scraper")

                output_dir.mkdir(parents=True, exist_ok=True)

                # Generate filename from URL
                if "life.gov.sg" in url:
                    # Extract guide name from URL (e.g., "active-ageing" from life.gov.sg/guides/active-ageing)
                    guide_name = url.split("/")[-1] or "guide"
                    filename = f"{guide_name}.json"
                else:
                    # For ask.gov.sg, use question slug or generic name
                    filename = f"question-{saved_count + 1}.json"

                output_path = output_dir / filename

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

                saved_count += 1
                print(f"Saved to {output_path}")
            else:
                print(f"Failed to scrape {url}")
                failed_urls.append(url)
                failed_count += 1
        except Exception as e:
            print(f"Error processing {url}: {type(e).__name__}: {e}")
            failed_urls.append(url)
            failed_count += 1
            continue

    print(f"\nSaved {saved_count}/{original_count} results as JSON (skipped {skipped_count} already-processed, failed {failed_count})")

    if failed_urls:
        print("\nFailed URLs (for debugging):")
        for url in failed_urls:
            print(f"  - {url}")


if __name__ == "__main__":
    asyncio.run(main())
