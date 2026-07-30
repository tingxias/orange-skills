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
        self.assertIn("首次使用或对应角色 Key 未配置时", skill)
        self.assertIn("直接读取并使用", skill)
        self.assertIn("不再要求逐次授权", skill)
        self.assertNotIn("未确认前，不执行", skill)
        self.assertNotIn("Codex", skill)
        self.assertNotIn("YonClaw", skill)
        self.assertIn("填写公司系统", skill)
        self.assertIn("追加", skill)
        self.assertIn("修改", skill)
        self.assertIn("查询本人日报", skill)
        self.assertIn("不能传入或拼接 `userId`", skill)
        self.assertIn("已提交", skill)
        self.assertIn("整理本周工作内容", skill)
        self.assertIn("本周一 `00:00` 到当前时间", skill)
        self.assertNotIn("使用默认范围（本周全部项目），还是指定项目？", skill)
        self.assertIn("默认读取当前工具可见的全部项目", skill)
        self.assertIn("不询问目录范围", skill)
        self.assertIn("执行这些命令时不得询问同步目录或项目范围", skill)
        self.assertIn("按项目归并", skill)
        self.assertIn("不逐条复制任务标题", skill)
        self.assertIn("当前工具不能提供项目或任务列表时，说明缺失来源并请用户补充，不猜测工作内容。", skill)
        self.assertIn("scope.mode=all", skill)
        self.assertIn("scope.mode=whitelist", skill)
        self.assertIn("当前工具", skill)
        self.assertNotIn("NC", skill)
        self.assertNotIn("## Configuration", skill)
        self.assertNotIn("## Push", skill)
        self.assertIn("发送、查询和获取结构化日报", metadata)
        self.assertIn("本周项目和任务", metadata)
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
