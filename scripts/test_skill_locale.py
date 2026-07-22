import unittest
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillLocaleTests(unittest.TestCase):
    def test_skill_guidance_and_ui_metadata_are_chinese(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("Codex 日报推送", skill)
        self.assertIn("## 配置", skill)
        self.assertIn("Codex 只负责", skill)
        self.assertIn("YonClaw", skill)
        self.assertIn("填写公司系统", skill)
        self.assertNotIn('python3 "$CLIENT" fetch', skill)
        self.assertNotIn("## Configuration", skill)
        self.assertNotIn("## Push", skill)
        self.assertIn("推送结构化日报", metadata)
        self.assertIn("使用 $daily-report", metadata)

    def test_cli_help_is_chinese(self):
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "daily_report.py"), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Codex 日报推送客户端", result.stdout)
        self.assertIn("提交日报", result.stdout)
        self.assertNotIn("submit a report", result.stdout)
        self.assertNotIn("usage:", result.stdout)
        self.assertNotIn("positional arguments:", result.stdout)
        self.assertNotIn("show this help message", result.stdout)


if __name__ == "__main__":
    unittest.main()
