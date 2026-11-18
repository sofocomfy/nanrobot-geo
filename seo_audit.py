"""Public, read-only SEO checks. No traffic estimates or automatic content edits."""
import concurrent.futures
import datetime as dt
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, urlopen

SITE = 'https://blog.nanrobot.com'
CORE = [22, 39, 67, 96, 137, 187]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.description = ''
        self.robots = ''
        self.canonical = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            name = a.get('name', '').lower()
            if name == 'description':
                self.description = a.get('content', '')
            if name in ('robots', 'googlebot', 'bingbot'):
                self.robots += ',' + a.get('content', '').lower()
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonical = a.get('href', '')


def fetch(url):
    req = Request(url, headers={'User-Agent': 'NANROBOT-SEO-Audit/1.0 (owner scheduled check)'})
    with urlopen(req, timeout=30) as r:
        return r.status, r.geturl(), r.read().decode('utf-8', errors='replace'), r.headers.get('X-Robots-Tag', '')


def check(url):
    try:
        status, final, body, header_robots = fetch(url)
        p = Page()
        p.feed(body)
        issues = []
        if p.h1 != 1:
            issues.append('h1_count')
        if not p.description.strip():
            issues.append('missing_description')
        if p.canonical.rstrip('/') != final.rstrip('/'):
            issues.append('canonical_review')
        if 'noindex' in p.robots + header_robots.lower():
            issues.append('noindex')
        return {'url': url, 'http': status, 'final_url': final, 'h1': p.h1,
                'canonical': p.canonical, 'issues': issues}
    except Exception as exc:
        return {'url': url, 'issues': ['request_failed'], 'error': type(exc).__name__}


def main():
    report = {'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'Public technical checks only; no automatic edits or backlink submissions',
              'traffic': {'gsc': 'not_connected', 'ga4': 'not_connected', 'bing_ai': 'not_connected'}}
    failed = False
    try:
        urls = [SITE + '/']
        page = 1
        while True:
            _, _, body, _ = fetch(f'{SITE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=link')
            batch = json.loads(body)
            for post in batch:
                link = post['link']
                if urlsplit(link).hostname != 'blog.nanrobot.com':
                    raise ValueError('Unexpected post host')
                urls.append(link)
            if len(batch) < 100:
                break
            page += 1
            if page > 50:
                raise ValueError('Pagination safety limit exceeded')
        report['checked_page_count'] = len(urls)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            report['pages'] = list(pool.map(check, urls))
        report['discovery'] = []
        for path in ['/robots.txt', '/sitemap_index.xml']:
            status, final, body, _ = fetch(SITE + path)
            report['discovery'].append({'url': final, 'http': status})
        failed = any(p['issues'] for p in report['pages'])
    except Exception as exc:
        report['collection_error'] = type(exc).__name__
        failed = True
    report['result'] = 'needs_review' if failed else 'checks_passed'
    Path('seo-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    text = '# NANROBOT SEO/GEO technical report\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n'
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(text)
    print(json.dumps(report, indent=2))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())