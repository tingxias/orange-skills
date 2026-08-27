import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SiyuanWorkflowSkillTests(unittest.TestCase):
    def test_skill_uses_direct_note_storage_instead_of_relay_service(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("思源", skill)
        self.assertIn("严格按日期", skill)
        self.assertIn("Asia/Shanghai", skill)
        self.assertNotIn("Producer Key", skill)
        self.assertNotIn("Consumer Key", skill)
        self.assertNotIn("leaseToken", skill)
        self.assertNotIn("daily_report 服务", skill)
        self.assertNotIn("python3", skill)

    def test_skill_models_same_or_separate_execution_tools(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("同一运行端", skill)
        self.assertIn("分开的运行端", skill)
        self.assertIn("same_runtime", skill)
        self.assertIn("separate_runtimes", skill)
        self.assertIn("日报存储端", skill)
        self.assertIn("公司系统写入端", skill)
        self.assertIn("最终提交端", skill)
        self.assertIn("same_tool", skill)
        self.assertIn("separate_tools", skill)
        self.assertIn("company_writer", schema)
        self.assertIn("company_submitter", schema)
        self.assertIn("auto_submit_after_write", schema)
        self.assertIn("write_success_evidence", schema)
        self.assertIn("submit_success_evidence", schema)

    def test_missing_user_decisions_are_asked_and_persisted(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("只询问缺失", skill)
        self.assertIn("用户明确回答", skill)
        self.assertIn("立即持久化", skill)
        self.assertIn("后续不再重复询问", skill)
        self.assertIn("DAILY_REPORT_CONFIG", skill)
        self.assertIn("workflow_mode", schema)
        self.assertIn("project_scope", schema)
        self.assertIn("report_store", schema)
        self.assertIn("company_writer", schema)
        self.assertIn("company_submitter", schema)
        self.assertIn("field_mapping", schema)
        self.assertIn("success_evidence", schema)
        self.assertIn("authorization", schema)
        self.assertIn("credential_ref", schema)
        self.assertNotIn("credential\"", schema)

    def test_exact_date_and_submission_receipt_rules_are_explicit(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("不得搜索或选择最新日报", skill)
        self.assertIn("YYYY-MM-DD", skill)
        self.assertIn("项目名称", skill)
        self.assertIn("1.", skill)
        self.assertIn("成功凭证", skill)
        self.assertIn("已提交", skill)
        self.assertIn("结果不确定", skill)
        self.assertIn("不得重复提交", skill)
        self.assertIn("写入成功不等于最终提交成功", skill)
        self.assertIn("只有最终提交成功", skill)

    def test_fixed_report_fields_are_mandatory(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("固定必填字段", skill)
        self.assertIn("编号", skill)
        self.assertIn("日期", skill)
        self.assertIn("完成进度", skill)
        self.assertIn("客户/项目名称", skill)
        self.assertIn("缺一不可", skill)
        self.assertIn("report_format", schema)
        self.assertIn("required_fields", schema)
        self.assertIn("progress_format", schema)
        self.assertIn("不能通过配置取消", skill)

    def test_report_items_use_spaced_blocks_not_compact_inline_text(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("每条事项独立成块", skill)
        self.assertIn("字段分行", skill)
        self.assertIn("不要使用 `｜`", skill)
        self.assertIn('"layout": "block"', schema)
        self.assertIn('"item_separator": "blank_line"', schema)

    def test_target_report_date_is_separate_from_source_window(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("目标日报日期", skill)
        self.assertIn("统计范围", skill)
        self.assertIn("截至昨天的本周总结", skill)
        self.assertIn("写入昨天", skill)
        self.assertIn("执行当天", skill)

    def test_project_conversations_are_default_source_instead_of_git(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("项目对话记录和任务记录", skill)
        self.assertIn("用户明确要求读取 Git", skill)
        self.assertIn("不得自行改用 Git", skill)

    def test_append_and_modify_preserve_unrelated_content(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("完整读取并保存原文快照", skill)
        self.assertIn("保留全部原有内容", skill)
        self.assertIn("只修改用户指定的项目或事项", skill)
        self.assertIn("原有非目标内容没有减少", skill)
        self.assertIn("明确要求“覆盖”“重写”或“清空”", skill)

    def test_project_name_is_title_and_same_project_is_grouped(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("同一项目的多条工作合并为一个项目块", skill)
        self.assertIn("工作内容在项目块内按序号列出", skill)
        self.assertIn('"item_template": "### {number}. {customer_or_project}', schema)
        self.assertNotIn('"item_template": "### {number}. 日报事项', schema)

    def test_source_window_is_not_written_as_report_heading(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("统计范围只用于筛选数据和结果回执", skill)
        self.assertIn("不得写入日报正文或标题", skill)
        self.assertIn("对话记录补充", skill)

    def test_all_report_operations_route_through_siyuan_mcp(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("推送（创建/写入）、追加、修改、查询和获取", skill)
        self.assertIn("全部通过思源笔记 MCP", skill)
        self.assertIn("report_store.transport", schema)
        self.assertIn("siyuan_mcp", schema)
        self.assertIn("思源 MCP 是唯一日报存储入口", skill)
        self.assertNotIn("中间服务作为日报读写入口", skill)

    def test_push_means_siyuan_write_without_company_tools(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("用户只说“推送”", skill)
        self.assertIn("只执行思源日报存储阶段", skill)
        self.assertIn("不得要求公司系统工具", skill)
        self.assertIn("精确回读一致后即可报告推送成功", skill)
        self.assertIn("只有用户明确要求写入或提交公司系统", skill)
        self.assertIn('"company_delivery_enabled": false', schema)
        self.assertIn("公司系统配置不是思源推送的前置条件", schema)
        self.assertIn("明确要求公司系统", metadata)

    def test_legacy_relay_configuration_is_removed_not_ignored(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "workflow-config.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("立即删除", skill)
        self.assertIn("不读取、不迁移、不回退", skill)
        self.assertIn("不得保留旧配置文件", schema)

    def test_mcp_discovery_precedes_workflow_config_check(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("先发现并初始化思源 MCP", skill)
        self.assertIn("`workflow` 配置缺失不等于思源 MCP 不可用", skill)
        self.assertIn("区分配置缺失、未初始化、鉴权失败和连接失败", skill)

    def test_ui_metadata_matches_direct_workflow(self):
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("思源日报", metadata)
        self.assertIn("公司系统", metadata)
        self.assertIn("明确要求公司系统", metadata)
        self.assertNotIn("完整 Key", metadata)
        self.assertNotIn("结构化日报服务", metadata)


if __name__ == "__main__":
    unittest.main()
