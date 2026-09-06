from lxml import etree
import re
from pathlib import Path

SITEMAPS_DIR = Path('data/scripts/sitemaps')

ask_pattern = re.compile(r'^https://ask\.gov\.sg/\w+/questions/\w+$')
supportgowhere_pattern = re.compile(r'^https://supportgowhere\.life\.gov\.sg/(schemes|services)/.+$')
lifesg_guides_pattern = re.compile(r'^https://www\.life\.gov\.sg/guides/.+$')
ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

urls_by_domain = {
    'ask': set(),
    'supportgowhere': set(),
    'lifesg_guides': set()
}
failed_prefixes = []

print("Reading sitemaps from local folder...")
sitemap_files = sorted(SITEMAPS_DIR.glob('*.xml'))

if not sitemap_files:
    print(f"No XML files found in {SITEMAPS_DIR}")
else:
    for sitemap_file in sitemap_files:
        prefix = sitemap_file.stem
        try:
            with open(sitemap_file, 'rb') as f:
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(f.read(), parser)

            urls = [loc.text for loc in root.findall(f".//{ns}loc")]

            ask_urls = [url for url in urls if ask_pattern.match(url)]
            supportgowhere_urls = [url for url in urls if supportgowhere_pattern.match(url)]
            lifesg_guides_urls = [url for url in urls if lifesg_guides_pattern.match(url)]

            urls_by_domain['ask'].update(ask_urls)
            urls_by_domain['supportgowhere'].update(supportgowhere_urls)
            urls_by_domain['lifesg_guides'].update(lifesg_guides_urls)

            total_found = len(ask_urls) + len(supportgowhere_urls) + len(lifesg_guides_urls)
            print(f"  {prefix}: {total_found} URLs found ({len(ask_urls)} ask, {len(supportgowhere_urls)} supportgowhere, {len(lifesg_guides_urls)} lifesg_guides)")
        except Exception as e:
            print(f"  {prefix}: Error - {e}")
            failed_prefixes.append(prefix)

output_dir = Path('data/scripts/output')
output_dir.mkdir(parents=True, exist_ok=True)

domain_files = {
    'ask': output_dir / 'ask-links.txt',
    'supportgowhere': output_dir / 'supportgowhere-links.txt',
    'lifesg_guides': output_dir / 'lifesg-guides-links.txt'
}

print("\nWriting URLs to files...")
for domain, urls in urls_by_domain.items():
    output_path = domain_files[domain]
    with open(output_path, 'w', encoding='utf-8') as f:
        for url in sorted(urls):
            f.write(url + '\n')
    print(f"  {domain}: {len(urls)} URLs saved to {output_path}")

total_urls = sum(len(urls) for urls in urls_by_domain.values())
print(f"\nTotal: {total_urls} question URLs saved")
if failed_prefixes:
    print(f"Failed prefixes: {', '.join(failed_prefixes)}")
