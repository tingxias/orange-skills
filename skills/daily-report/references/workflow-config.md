# 日报工作流持久化配置

默认文件为 `~/.config/daily-report/config.json`，可用 `DAILY_REPORT_CONFIG` 指定其他位置。目录权限 `0700`，文件权限 `0600`。配置只保存流程决定和凭据引用，不保存密钥、密码、令牌、租约或公司系统登录信息。

```json
{
  "workflow": {
    "workflow_mode": "same_runtime",
    "local_roles": ["report_store"],
    "company_delivery_enabled": false,
    "timezone": "Asia/Shanghai",
    "report_format": {
      "required_fields": ["number", "date", "progress", "customer_or_project"],
      "progress_format": "status_or_percentage",
      "layout": "block",
      "item_separator": "blank_line",
      "grouping": "one_block_per_project",
      "content_numbering": "nested_ordered_list",
      "item_template": "### {number}. {customer_or_project}\n\n- 日期：{date}\n- 客户/项目名称：{customer_or_project}\n- 完成进度：{progress}\n- 工作内容：\n{numbered_summaries}"
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
    "authorization": {
      "read_projects": true,
      "read_report": true,
      "write_report": true
    },
    "project_scope": {
      "mode": "all",
      "project_roots": []
    }
  }
}
```

只有用户明确要求公司系统操作时，才在 `workflow` 中增加以下可选配置：

```json
{
  "company_delivery_enabled": true,
  "company_delivery": {
    "company_action_mode": "same_tool",
    "auto_submit_after_write": true,
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
      "write_company_system": true,
      "submit_company_system": true,
      "write_status_marker": true
    }
  }
}
```

## 角色与布局

- `company_delivery_enabled` 默认为 `false`。公司系统配置不是思源推送的前置条件；普通“推送日报”在思源写入并精确回读成功后即完成。
- `workflow_mode`：`same_runtime` 或 `separate_runtimes`。
- `local_roles`：从 `report_store`、`company_writer`、`company_submitter` 中选择一个或多个。分开的运行端只执行自己已保存的角色。
- `company_delivery.company_action_mode`：公司系统写入端与最终提交端使用同一工具时为 `same_tool`，使用不同工具时为 `separate_tools`。
- `report_format.required_fields` 固定必须包含 `number`、`date`、`progress`、`customer_or_project`，不能通过配置删除、替换或设为可选。`progress_format` 可为状态、百分比或二者并用，但不能省略完成进度。`layout` 固定为 `block`，`item_separator` 固定为 `blank_line`；字段必须分行，禁止使用 `｜` 拼成单行。`grouping` 固定为 `one_block_per_project`，项目名作为块标题；同一项目的多条工作放入块内有序列表，不重复创建同名项目块。
- `report_store.transport` 固定为 `siyuan_mcp`。创建、追加、修改、查询和获取个人日报均通过思源笔记 MCP 完成；思源 MCP 是唯一日报存储入口。
- `company_delivery.handoff_mode.report_to_writer`：`shared_report_store` 或 `explicit_payload`。后者必须传递明确日期和本次日报正文，不能传递“最新日报”。
- `company_delivery.handoff_mode.writer_to_submitter`：优先使用 `record_reference`；若只能使用 `explicit_payload`，必须包含目标日期、目标系统和已验证的写入结果，不能包含秘密。

## 能力与成功凭证

- `report_store` 必须声明可读、可写能力。只有读取能力时可以查询，不能创建、追加、修改或回写状态。
- `company_delivery.company_writer` 只在用户明确要求写入公司系统时需要，必须保存目标系统、表单或模板、字段映射，以及至少一种 `write_success_evidence`。
- `company_delivery.company_submitter` 只在用户明确要求最终提交时需要，必须保存至少一种 `submit_success_evidence`。只有该凭证验证通过才允许写“已提交”。
- `company_delivery.auto_submit_after_write=true` 仅在当前请求已明确进入公司系统流程、写入验证成功、最终提交端可用且 `submit_company_system=true` 时生效；普通思源推送不得触发。
- `auto_mark_submitted=true` 仅在最终提交成功后生效；不授权删除、移动、批量修改或权限变更。
- `credential_ref` 只指向环境变量、工具连接或安全凭据管理器，不得包含实际凭据值。

## 需要用户明确决定的字段

普通思源推送只询问当前操作缺少的日期、思源目标、读写能力、授权和必填日报字段。只有用户明确要求公司系统操作时，才询问角色布局、写入/提交是否同工具、具体工具和目标、日报模板、字段映射、两个阶段的成功凭证、自动提交和状态回写。用户没有明确回答的字段保持缺失，不能猜测后写入配置。

目标日报日期与项目记录的统计范围必须分别计算：相对日期按 `Asia/Shanghai` 解析，“截至昨天的本周总结”以昨天为目标日报日期、以本周一至昨天为统计范围。默认读取当前工具的项目对话记录和任务记录；只有用户明确要求时才读取 Git。统计范围和数据来源只出现在执行回执中，不写入日报正文或标题。

创建、追加和修改采用保留式写入：先完整读取原文，追加时按项目合并，修改时只变更目标项目，写入前后确认非目标内容未减少。全文覆盖、重写或清空只能由用户明确提出，不能作为普通推送、追加或修改的实现方式。

## 更新与迁移

用户修改某一项时只更新该项，保留其它已确认字段和未知字段。旧版服务地址、角色密钥、租约状态和客户端配置已经停用；发现旧配置文件或这些字段时必须删除，不读取、不迁移、不回退。采用临时文件和原子替换写入，随后检查 `0600` 权限并回读 JSON；写入失败或结果不确定时先重新读取状态，不能盲目覆盖。

不得保留旧配置文件。删除后如需继续使用日报，只能按本文件的 `workflow` 结构重新建立思源 MCP 配置。
