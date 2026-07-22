import unittest
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillLocaleTests(unittest.TestCase):
    def test_skill_guidance_and_ui_metadata_are_chinese(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("日报发送与获取", skill)
        self.assertIn("## 配置", skill)
        self.assertIn("发送者", skill)
        self.assertIn("获取者", skill)
        self.assertIn("可以由同一软件执行，也可以分开", skill)
        self.assertIn("首次使用时，必须由用户明确输入", skill)
        self.assertIn("后续使用已保存凭据", skill)
        self.assertIn("未确认前", skill)
        self.assertNotIn("Codex", skill)
        self.assertNotIn("YonClaw", skill)
        self.assertIn("填写公司系统", skill)
        self.assertIn("追加", skill)
        self.assertIn("修改", skill)
        self.assertIn("查询本人日报", skill)
        self.assertIn("不能传入或拼接 `userId`", skill)
        self.assertIn("已提交", skill)
        self.assertNotIn("## Configuration", skill)
        self.assertNotIn("## Push", skill)
        self.assertIn("发送、查询和获取结构化日报", metadata)
        self.assertNotIn("Codex", metadata)
        self.assertNotIn("YonClaw", metadata)
        self.assertIn("首次使用请先提供当前角色的完整 Key", metadata)
        self.assertIn("使用 $daily-report", metadata)

    def test_cli_help_is_chinese(self):
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "daily_report.py"), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("日报发送与获取客户端", result.stdout)
        self.assertIn("提交日报", result.stdout)
        self.assertIn("追加日报内容", result.stdout)
        self.assertIn("修改日报内容", result.stdout)
        self.assertIn("查询本人日报列表", result.stdout)
        self.assertNotIn("submit a report", result.stdout)
        self.assertNotIn("usage:", result.stdout)
        self.assertNotIn("positional arguments:", result.stdout)
        self.assertNotIn("show this help message", result.stdout)


if __name__ == "__main__":
    unittest.main()
