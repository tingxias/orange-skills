---
name: daily-report
description: 当用户需要在 Codex 中生成并通过 daily_report 服务推送结构化日报，或查询已推送日报状态时使用。
---

# Codex 日报推送

Codex 只负责从当前开发上下文生成结构化日报，并以生产者（Producer）身份推送到日报服务。YonClaw 是独立的软件，负责以消费者（Consumer）身份获取日报、填写公司系统，并回传成功或失败结果；Codex 不执行这些消费操作。

## 职责边界

- **Codex**：整理开发进展，检查服务健康状态，调用 `push` 推送日报；需要时使用 `get` 查询自己推送的日报状态。
- **YonClaw**：使用 Consumer Key 调用领取接口，读取 `submissionKey` 和租约，填写公司系统，之后调用成功或失败回执接口。
- **不要混用凭据**：Codex 只配置 Producer Key，不配置 Consumer Key；Consumer Key 和一次性租约只保存在 YonClaw 运行环境。

## 配置

Codex 从 `~/.config/daily-report/config.json` 读取服务地址和 Producer Key，配置格式如下：

```json
{
  "base_url": "https://report.lehuicheng.top",
  "producer_key": "<生产者 Key>"
}
```

将配置文件权限设置为 `0600`，不要在其中保存管理员 Token 或 Consumer Key。环境变量 `DAILY_REPORT_BASE_URL` 和 `DAILY_REPORT_PRODUCER_KEY` 优先于配置文件。客户端代码保留 Consumer Key 参数仅用于 YonClaw 侧复用 API 契约，不要在 Codex 配置中设置它。

按以下方式调用客户端：

```bash
CLIENT="${CODEX_HOME:-$HOME/.codex}/skills/daily-report/scripts/daily_report.py"
python3 "$CLIENT" <命令>
```

客户端会绕过系统 HTTP 代理，直接访问日报服务。`health` 不需要凭据，`push` 和 `get` 只需要 Producer Key。

## 推送日报

推送前先执行 `health` 检查服务状态，再生成一份固定的 JSON 请求。确定幂等键后，重试时必须复用完全相同的请求正文和 `generatedAt`，不要重新生成时间。

```bash
echo '{
  "reportDate": "2026-07-22",
  "timezone": "Asia/Shanghai",
  "templateKey": "daily",
  "scope": {"mode": "all", "projectRoots": []},
  "completed": ["完成事项"],
  "inProgress": ["进行中事项"],
  "risks": [],
  "nextSteps": [],
  "evidence": [],
  "generatedAt": "2026-07-22T10:00:00Z"
}' | python3 "$CLIENT" push \
  --idempotency-key 'wish-2026-07-22-daily'
```

HTTP `201` 表示新建成功，`200` 表示相同内容的幂等重放。遇到 `409 REPORT_CONFLICT` 时不要盲目重试，应对比原请求正文和幂等键。`completed` 或 `inProgress` 至少包含一项，`timezone` 必须使用 IANA 时区名称。

## YonClaw 接口契约

以下操作由 YonClaw 在独立运行环境执行，Codex 不调用这些命令，也不保存 Consumer Key 或租约文件：

- `POST /api/v1/reports/claim`：使用 `Authorization: Bearer <Consumer Key>` 领取一条日报。`204` 表示暂无任务；`200` 返回日报、`submissionKey` 和一次性 `leaseToken`。YonClaw 必须持久化租约，避免重复领取。
- 公司系统填写成功后，调用 `POST /api/v1/reports/{id}/complete`，请求体只包含 `leaseToken`。
- 公司系统填写失败后，调用 `POST /api/v1/reports/{id}/fail`，提交 `leaseToken`、`errorCode`、`errorMessage` 和 `retryable`。
- 回执成功后才能丢弃租约；`INVALID_LEASE` 或 `INVALID_REPORT_STATE` 时停止当前任务并调查状态，不要继续领取新任务。

使用 `get <日报 ID>` 从生产者侧查询状态；它不会领取日报，也不会创建 YonClaw 租约。

## 错误处理

- `AUTHENTICATION_REQUIRED` 或 `ROLE_FORBIDDEN`：确认 Codex 使用 Producer Key、YonClaw 使用 Consumer Key，不要替换成管理员 Token。
- `REPORT_CONFLICT`：保留原始请求正文和幂等键，再调查冲突原因。
- YonClaw 的领取接口返回 `204`：正常结束，不发送任何回执。
- YonClaw 遇到 `INVALID_LEASE` 或 `INVALID_REPORT_STATE`：停止当前任务，不要继续领取新任务。
- 传输错误：使用完全相同的正文和幂等键重试，不要重新生成时间戳。

实现与测试分别位于 `scripts/daily_report.py`、`scripts/test_daily_report.py` 和 `scripts/test_skill_locale.py`。
