"""Prevent repeated GitHub Pages artifact deployment failures on reruns."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
WORKFLOW = ROOT / ".github" / "workflows" / "public-pages-artifact.yml"
ARTIFACT = "github-pages-${{ github.run_id }}-${{ github.run_attempt }}"


class PagesArtifactRetryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_upload_and_deploy_use_same_attempt_scoped_artifact(self):
        text = self.workflow
        self.assertIn("name: " + ARTIFACT, text)
        self.assertIn("artifact_name: " + ARTIFACT, text)
        self.assertEqual(text.count("name: " + ARTIFACT), 2)

    def test_visibility_poll_runs_between_upload_and_deploy(self):
        text = self.workflow
        upload = text.index("- name: Upload Pages artifact")
        poll = text.index("- name: Confirm Pages artifact is visible")
        deploy = text.index("- name: Deploy to GitHub Pages")
        self.assertLess(upload, poll)
        self.assertLess(poll, deploy)
        self.assertIn("actions: read", text)
        self.assertIn('gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100"', text)
        self.assertIn("matches", text)
        self.assertIn("exit 1", text)


if __name__ == "__main__":
    unittest.main()
