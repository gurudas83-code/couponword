"""Offline regression tests for fail-visible CI reliability protections."""
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.actions_health_monitor import latest_main_result, issue_body, WORKFLOWS

ROOT = Path(__file__).resolve().parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def run(ident, conclusion, *, event="push", branch="main",
        created="2026-11-20T08:00:00Z", status="completed"):
    return {
        "id": ident, "event": event, "head_branch": branch,
        "conclusion": conclusion, "status": status,
        "created_at": created, "run_attempt": 1,
        "html_url": "https://github.com/gurudas83-code/couponword/actions/runs/" + str(ident),
    }


class ActionsHealthTests(unittest.TestCase):
    def test_recent_success_overrides_old_main_failure(self):
        item = latest_main_result("Pages", [
            run(10, "failure", created="2026-11-19T08:00:00Z"),
            run(11, "success"),
        ], NOW)
        self.assertEqual(item["result"], "PASS")
        self.assertEqual(item["run_id"], 11)

    def test_development_failures_never_masquerade_as_main_incidents(self):
        item = latest_main_result("SEO", [
            run(20, "failure", event="pull_request", branch="feature/seo"),
            run(21, "success", created="2026-11-19T08:00:00Z"),
        ], NOW)
        self.assertEqual(item["result"], "PASS")
        self.assertEqual(item["run_id"], 21)

    def test_failed_latest_main_run_alerts(self):
        self.assertEqual(
            latest_main_result("Pages", [run(22, "failure")], NOW)["result"], "FAIL"
        )
        self.assertEqual(
            latest_main_result("Pages", [run(23, "timed_out")], NOW)["result"], "FAIL"
        )

    def test_missed_scheduled_checks_are_visible(self):
        item = latest_main_result("Source monitor", [
            run(1, "success", event="schedule", created="2026-11-17T08:00:00Z")
        ], NOW, max_age_hours=30)
        self.assertEqual(item["result"], "STALE")

    def test_unknown_is_never_counted_as_pass(self):
        self.assertEqual(latest_main_result("Pages", [], NOW)["result"], "UNKNOWN")
        item = latest_main_result("Pages", [
            run(1, None, status="in_progress")
        ], NOW)
        self.assertEqual(item["result"], "UNKNOWN")

    def test_health_report_contains_source_not_secret(self):
        item = latest_main_result("Pages", [run(23, "failure")], NOW)
        report = {
            "checks": [item], "checked_at_utc": NOW.isoformat(),
        }
        body = issue_body(report)
        self.assertIn("/actions/runs/23", body)
        self.assertIn("main-branch", body)
        self.assertNotIn("GITHUB_TOKEN", body)

    def test_only_expected_workflows_are_monitored(self):
        self.assertEqual(len(WORKFLOWS), 6)
        self.assertNotIn("quickcommerce-comparison.yml", WORKFLOWS)
        self.assertNotIn("quickcommerce-private-smoke.yml", WORKFLOWS)

    def test_coupon_bot_cannot_commit_unreviewed_or_unverified_deals(self):
        workflow = (WORKFLOWS_DIR / "bot.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("python -m json.tool coupons.json", workflow)
        self.assertIn("coupon-review", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("|| exit 0", workflow)

    def test_critical_workflows_have_fixed_runner(self):
        for name in (
            "static-seo-quality.yml", "research-quality.yml",
            "mobile-integrity-6h.yml", "amazon-catalog-sync.yml",
            "six-hour-research-monitor.yml", "quickcommerce-comparison.yml",
        ):
            with self.subTest(workflow=name):
                content = (WORKFLOWS_DIR / name).read_text(encoding="utf-8")
                self.assertIn("runs-on: ubuntu-24.04", content)
                self.assertNotIn("runs-on: ubuntu-latest", content)


if __name__ == "__main__":
    unittest.main()
