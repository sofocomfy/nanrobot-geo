# NANROBOT free cloud scheduler

This repository uses standard GitHub-hosted Ubuntu runners in a public repository. It does not depend on the owner's computer or ChatGPT desktop staying online.

## Active scope

- At approximately 09:07 and 21:07 Asia/Shanghai, call the site's normal WordPress cron endpoint and verify all due IDs in queue.json against publicly published posts.
- Preserve a public workflow summary of actual publication state, missing due posts, and queue exhaustion. An HTTP 200 from wp-cron.php alone is not treated as proof that an article published.
- Support weekly Saturday-morning email once SMTP Secrets are configured. The recipient is configured privately through REPORT_EMAIL; no address or password is committed.
- Support manual test runs. Pushes to the scheduler code also run the checks once.

The first two reviewed articles already reside in WordPress's scheduled queue for November 15, 2026 at 09:00 and 21:00 UTC+8. queue.json tracks these articles. This is currently a finite queue, NOT a perpetual two-new-articles-per-day writing service. Replenish with reviewed, fact-checked, distinct articles scheduled in WordPress and update queue.json. Never republish old material merely to meet a numeric target.

## Free-service boundary

GitHub Models was retired on July 30, 2026, including its inference API. This setup does not call a retired endpoint or silently substitute a paid AI API. There is no chargeable model service in this code. Standard GitHub-hosted runners in public repositories remain free under GitHub's published Actions billing rules; artifact/cache storage is a separate concern, so this workflow uses no caches, artifacts, larger runners, or paid integrations.

References:
- https://docs.github.com/en/github-models
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://developer.wordpress.org/plugins/cron/

## Email Secrets

In Settings → Secrets and variables → Actions, configure SMTP_HOST, SMTP_PORT (STARTTLS, normally 587), SMTP_USER, SMTP_PASSWORD, MAIL_FROM, and REPORT_EMAIL. Use an authorized SMTP account/application password. Never commit secrets or reuse a WordPress admin password as an SMTP password. The program does not create accounts or credentials.

SMTP acceptance does not prove inbox delivery. Until the recipient confirms receipt, delivery remains unverified. Unconfigured email is explicitly reported as not_configured.

## Missing measurements

Google Search Console, Bing AI Performance and identifiable AI-referral analytics are not connected to this public-only runner. Missing data is never represented as zero traffic. Do not add private exports or search reports to this public repository or its logs.

## Operational limits

GitHub schedules can be delayed. Default WordPress cron is page-load driven; these external calls improve triggering but do not guarantee an exact publication minute or uptime. Future runs depend on Actions remaining enabled; public repositories may have scheduled workflows disabled after prolonged inactivity under GitHub's policy. A scheduled workflow is not a guarantee of indefinite unattended service.

Inspect Actions → NANROBOT offline publishing → latest run summary. A successful run before articles are due only validates cloud triggering/reporting; publication still requires checking after their scheduled times.
