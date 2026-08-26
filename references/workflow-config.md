# 日报工作流持久化配置

默认文件为 `~/.config/daily-report/config.json`，可用 `DAILY_REPORT_CONFIG` 指定其他位置。目录权限 `0700`，文件权限 `0600`。配置只保存流程决定和凭据引用，不保存密钥、密码、令牌、租约或公司系统登录信息。

```json
{
  "workflow": {
    "workflow_mode": "same_runtime",
    "local_roles": ["report_store", "company_writer", "company_submitter"],
    "company_action_mode": "same_tool",
    "timezone": "Asia/Shanghai",
    "auto_submit_after_write": true,
    "report_format": {
      "required_fields": ["number", "date", "progress", "customer_or_project"],
      "progress_format": "status_or_percentage",
      "item_template": "{number}. 日期：{date}｜客户/项目名称：{customer_or_project}｜完成进度：{progress}｜工作内容：{summary}"
    },
    "report_store": {
      "tool_ref": "逻辑工具标识",
      "credential_ref": "工具连接配置中的凭据引用，可省略",
      "transport": "siyuan_mcp",
      "read_enabled": true,
      "write_enabled": true,
      "notebook": "工作",
      "path_template": "/工作/daily note/YYYY/MM/YYYY-MM-DD"
    },
    "company_writer": {
      "tool_ref": "逻辑工具标识",
      "credential_ref": "工具连接配置中的凭据引用，可省略",
      "target_name": "用户确认的系统和表单",
      "template_name": "用户确认的日报模板",
      "readback_enabled": true,
      "write_success_evidence": ["record_id", "saved_status"]
    },
    "company_submitter": {
      "tool_ref": "逻辑工具标识",
      "credential_ref": "工具连接配置中的凭据引用，可省略",
      "readback_enabled": true,
      "submit_success_evidence": ["submission_id", "submitted_status"],
      "auto_mark_submitted": true
    },
    "handoff_mode": {
      "report_to_writer": "shared_report_store",
      "writer_to_submitter": "record_reference"
    },
    "field_mapping": {
      "completed": "用户确认的完成事项字段",
      "in_progress": "用户确认的进行中字段",
      "risks": "用户确认的问题或风险字段",
      "next_steps": "用户确认的后续计划字段"
    },
    "authorization": {
      "read_projects": true,
      "read_report": true,
      "write_report": true,
      "write_company_system": true,
      "submit_company_system": true,
      "write_status_marker": true
    },
    "project_scope": {
      "mode": "all",
      "project_roots": []
    }
  }
}
```

## 角色与布局

- `workflow_mode`：`same_runtime` 或 `separate_runtimes`。
- `local_roles`：从 `report_store`、`company_writer`、`company_submitter` 中选择一个或多个。分开的运行端只执行自己已保存的角色。
- `company_action_mode`：公司系统写入端与最终提交端使用同一工具时为 `same_tool`，使用不同工具时为 `separate_tools`。
- `report_format.required_fields` 固定必须包含 `number`、`date`、`progress`、`customer_or_project`，不能通过配置删除、替换或设为可选。`progress_format` 可为状态、百分比或二者并用，但不能省略完成进度。
- `report_store.transport` 固定为 `siyuan_mcp`。创建、追加、修改、查询和获取个人日报均通过思源笔记 MCP 完成；旧中间服务配置不改变此规则。
- `handoff_mode.report_to_writer`：`shared_report_store` 或 `explicit_payload`。后者必须传递明确日期和本次日报正文，不能传递“最新日报”。
- `handoff_mode.writer_to_submitter`：优先使用 `record_reference`；若只能使用 `explicit_payload`，必须包含目标日期、目标系统和已验证的写入结果，不能包含秘密。

## 能力与成功凭证

- `report_store` 必须声明可读、可写能力。只有读取能力时可以查询，不能创建、追加、修改或回写状态。
- `company_writer` 必须保存目标系统、表单或模板、字段映射，以及至少一种 `write_success_evidence`。写入成功只表示内容已填入或保存，不表示已最终提交。
- `company_submitter` 必须保存至少一种 `submit_success_evidence`。只有该凭证验证通过才允许写“已提交”。
- `auto_submit_after_write=true` 仅在写入验证成功、最终提交端可用且 `submit_company_system=true` 时生效。
- `auto_mark_submitted=true` 仅在最终提交成功后生效；不授权删除、移动、批量修改或权限变更。
- `credential_ref` 只指向环境变量、工具连接或安全凭据管理器，不得包含实际凭据值。

## 需要用户明确决定的字段

当前操作用到且尚未配置时才询问：角色布局、当前运行端角色、写入/提交是否同工具、具体工具和目标、日报模板、字段映射、两个阶段的成功凭证、自动提交、状态回写、持久授权以及首次项目范围。用户没有明确回答的字段保持缺失，不能猜测后写入配置。

## 更新与迁移

用户修改某一项时只更新该项，保留其它已确认字段和未知字段。旧配置中的 `base_url`、Producer/Consumer Key 或租约字段不参与当前思源直连流程，但不得未经用户要求自动删除。采用临时文件和原子替换写入，随后检查 `0600` 权限并回读 JSON；写入失败或结果不确定时先重新读取状态，不能盲目覆盖。
