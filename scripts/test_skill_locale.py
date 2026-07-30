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
        self.assertIn('首次生成周报时，询问：“使用本周全部项目，还是指定项目？”', skill)
        self.assertIn("`weekly_summary_scope`", skill)
        self.assertIn("后续生成周报自动使用已保存的范围偏好", skill)
        self.assertIn("只覆盖本次，不改写已保存的范围偏好", skill)
        self.assertNotIn("默认读取当前工具可见的全部项目及其本周任务，不询问目录范围", skill)
        self.assertIn("执行这些命令时不得询问同步目录或项目范围", skill)
        self.assertIn("用户未明确目标日期时，先询问要领取哪一天的日报", skill)
        self.assertIn("不得默认当天、最近日期、最早日期或本地租约中的日期", skill)
        self.assertIn("下游系统确认日报写入成功后，立即自动执行 `complete`", skill)
        self.assertIn("不再询问用户是否回执", skill)
        self.assertIn("日报日期必须写入 `reportDate`", skill)
        self.assertIn("每条内容必须以项目名称开头", skill)
        self.assertIn("同一栏目包含多条内容时，按 `1.`、`2.`", skill)
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
