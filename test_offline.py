import datetime as dt
import unittest
from unittest.mock import patch
import offline


class OfflineTests(unittest.TestCase):
    def test_future_queue_is_not_claimed_published(self):
        now = dt.datetime.fromisoformat('2026-11-14T12:00:00+08:00')
        r = offline.assess([{'id':199,'publish_at':'2026-11-15T09:00:00+08:00'}], [], now)
        self.assertEqual(r['remaining_queued_count'], 1)
        self.assertEqual(r['due_checks'], [])

    def test_missing_due_article_is_failure_evidence(self):
        now = dt.datetime.fromisoformat('2026-11-15T09:10:00+08:00')
        r = offline.assess([{'id':199,'publish_at':'2026-11-15T09:00:00+08:00'}], [], now)
        self.assertEqual(r['due_checks'][0]['status'], 'overdue_or_unavailable')

    def test_empty_queue_is_explicit(self):
        r = offline.assess([], [], dt.datetime.now(dt.timezone.utc))
        self.assertTrue(r['queue_exhausted'])

    def test_email_not_configured_is_not_sent(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(offline.email_report({}), 'not_configured')


if __name__ == '__main__':
    unittest.main()
