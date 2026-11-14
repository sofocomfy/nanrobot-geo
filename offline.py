"""Free GitHub-hosted trigger and public report. Never generates filler articles."""
import datetime as dt
from email.message import EmailMessage
import json
import os
from pathlib import Path
import smtplib
import ssl
import sys
from urllib.request import Request, urlopen

SITE = 'https://blog.nanrobot.com'
TZ = dt.timezone(dt.timedelta(hours=8))


def get(url):
    req = Request(url, headers={'User-Agent': 'NANROBOT-Cloud-Publisher/1.0 (site-owner scheduler)'})
    with urlopen(req, timeout=35) as r:
        return r.status, r.read().decode('utf-8')


def load_posts():
    posts = []
    page = 1
    while True:
        _, body = get(f'{SITE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,slug,link,date,title')
        batch = json.loads(body)
        posts.extend(batch)
        if len(batch) < 100:
            return posts
        page += 1


def assess(queue, posts, now):
    by_id = {p['id']: p for p in posts}
    due = [p for p in queue if dt.datetime.fromisoformat(p['publish_at']) <= now]
    pending = [p for p in queue if dt.datetime.fromisoformat(p['publish_at']) > now]
    checks = [{'id': p['id'], 'publish_at': p['publish_at'],
               'status': 'published' if p['id'] in by_id else 'overdue_or_unavailable'} for p in due]
    local_day = now.astimezone(TZ).date().isoformat()
    today = [p for p in posts if p['date'].startswith(local_day)]
    hour = now.astimezone(TZ).hour
    expected = 2 if hour >= 21 else (1 if hour >= 9 else 0)
    return {'due_checks': checks, 'remaining_queued_count': len(pending),
            'queue_exhausted': not pending, 'site_date': local_day,
            'today_published_count': len(today),
            'today_urls': [p['link'] for p in today],
            'expected_published_by_now': expected,
            'daily_publication_shortfall': len(today) < expected,
            'daily_target': 2, 'target_is_not_guaranteed': True}


def email_report(report):
    needed = ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'MAIL_FROM', 'REPORT_EMAIL']
    if not all(os.getenv(k) for k in needed):
        return 'not_configured'
    message = EmailMessage()
    message['Subject'] = 'NANROBOT 云端发布与巡检报告'
    message['From'] = os.environ['MAIL_FROM']
    message['To'] = os.environ['REPORT_EMAIL']
    message.set_content(json.dumps(report, ensure_ascii=False, indent=2))
    with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.getenv('SMTP_PORT', '587')), timeout=35) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(message)
    return 'smtp_accepted_not_inbox_verified'


def main():
    now = dt.datetime.now(dt.timezone.utc)
    report = {'generated_utc': now.isoformat(), 'site': SITE,
              'execution': 'GitHub-hosted runner, independent of local computer',
              'content_generation': 'unavailable: GitHub Models retired; reviewed queue only',
              'gsc': 'not_connected', 'bing_ai': 'not_connected', 'ai_referrals': 'not_connected'}
    failed = False
    try:
        code, _ = get(SITE + '/wp-cron.php')
        report['cron_endpoint_status'] = code
        # WordPress can dispatch cron asynchronously. Re-read after a short bounded wait.
        import time
        time.sleep(5)
        queue = json.loads(Path('queue.json').read_text(encoding='utf-8'))
        report.update(assess(queue, load_posts(), now))
        failed = report['daily_publication_shortfall'] or any(c['status'] != 'published' for c in report['due_checks'])
    except Exception as exc:
        report['collection_error'] = type(exc).__name__
        failed = True
    local = now.astimezone(TZ)
    should_email = os.getenv('SEND_EMAIL') == 'true' or (local.weekday() == 5 and local.hour < 12)
    if should_email:
        try:
            report['email_delivery'] = email_report(report)
        except Exception as exc:
            report['email_delivery'] = 'error:' + type(exc).__name__
            failed = True
    else:
        report['email_delivery'] = 'not_due'
    # Only public site state enters logs and the public workflow summary.
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write('# NANROBOT cloud publication report\n\n```json\n')
            f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n```\n')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
