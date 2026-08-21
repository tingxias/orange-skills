import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillLocaleTests(unittest.TestCase):
    def test_skill_guidance_and_ui_metadata_are_chinese_and_direct(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("日报编排", skill)
        self.assertIn("日报存储", skill)
        self.assertIn("最终提交", skill)
        self.assertIn("公司系统写入端", skill)
        self.assertIn("最终提交端", skill)
        self.assertIn("same_tool", skill)
        self.assertIn("separate_tools", skill)
        self.assertIn("只询问缺失", skill)
        self.assertIn("立即持久化", skill)
        self.assertIn("后续不再重复询问", skill)
        self.assertIn("严格按日期", skill)
        self.assertIn("不得搜索或选择最新日报", skill)
        self.assertIn("Asia/Shanghai", skill)
        self.assertIn("项目名称", skill)
        self.assertIn("1.", skill)
        self.assertIn("成功凭证", skill)
        self.assertIn("已提交", skill)
        self.assertIn("结果不确定", skill)
        self.assertNotIn("Producer Key", skill)
        self.assertNotIn("Consumer Key", skill)
        self.assertNotIn("leaseToken", skill)
        self.assertNotIn("daily_report 服务", skill)
        self.assertNotIn("python3", skill)
        self.assertIn("思源日报编排", metadata)
        self.assertIn("公司系统写入端", metadata)
        self.assertIn("最终提交端", metadata)
        self.assertNotIn("完整 Key", metadata)


if __name__ == "__main__":
    unittest.main()
