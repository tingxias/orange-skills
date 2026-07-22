---
name: daily-report
description: 当用户需要通过 daily_report 服务提交结构化日报、领取待处理日报、查询日报状态，或回传下游处理成功与失败结果时使用。
---

# 日报推送与获取

使用技能内置的纯标准库客户端，以生产者（Producer）身份推送日报，以消费者（Consumer）身份领取并回执日报。将凭据保存在 Skill 目录之外，并持续保留一次性领取租约，直到下游系统明确处理成功或失败。

## 配置

从 `~/.config/daily-report/config.json` 读取凭据，配置格式如下：

```json
{
  "base_url": "https://report.lehuicheng.top",
  "producer_key": "<生产者 Key>",
  "consumer_key": "<消费者 Key>",
  "state_file": "~/.config/daily-report/claim.json"
}
```

将配置文件权限设置为 `0600`，不要在其中保存管理员 Token。以下环境变量优先于配置文件：`DAILY_REPORT_BASE_URL`、`DAILY_REPORT_PRODUCER_KEY`、`DAILY_REPORT_CONSUMER_KEY`、`DAILY_REPORT_STATE_FILE`。

按以下方式调用客户端：

```bash
CLIENT="${CODEX_HOME:-$HOME/.codex}/skills/daily-report/scripts/daily_report.py"
python3 "$CLIENT" <命令>
```

客户端会绕过系统 HTTP 代理，直接访问日报服务。

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

## 获取并回执

只执行一次 `fetch`：

```bash
python3 "$CLIENT" fetch
```

HTTP `204` 表示当前没有待处理日报，属于正常结果。HTTP `200` 会返回日报、`submissionKey` 和一次性 `leaseToken`；客户端同时将租约保存到权限为 `0600` 的 `claim.json`。本地存在租约状态时不要再次执行 `fetch`，下游公司系统未明确确认成功前也不要执行 `complete`。

下游处理成功后执行：

```bash
python3 "$CLIENT" complete
```

下游处理失败时，明确指定是否允许重试：

```bash
python3 "$CLIENT" fail \
  --error-code DOWNSTREAM_UNAVAILABLE \
  --error-message '公司系统暂时不可用' \
  --retryable
```

确定性数据错误或业务错误使用 `--no-retryable`。`complete` 或 `fail` 成功后，客户端会删除本地租约状态。不要记录生产者 Key、消费者 Key 或 `leaseToken`，租约只传递给下游调用和本客户端。

使用 `get <日报 ID>` 从生产者侧查询状态。`INVALID_LEASE` 表示已保存的租约不能继续使用，应停止当前流程并检查日报状态，不要反复重试。

## 错误处理

- `AUTHENTICATION_REQUIRED` 或 `ROLE_FORBIDDEN`：确认使用同一用户下正确角色的生产者/消费者 Key，不要替换成管理员 Token。
- `REPORT_CONFLICT`：保留原始请求正文和幂等键，再调查冲突原因。
- `fetch` 返回 `204`：正常结束，不发送任何回执。
- `INVALID_LEASE` 或 `INVALID_REPORT_STATE`：停止当前流程，不要继续领取新任务。
- 传输错误：使用完全相同的正文和幂等键重试，不要重新生成时间戳。

实现与测试分别位于 `scripts/daily_report.py`、`scripts/test_daily_report.py` 和 `scripts/test_skill_locale.py`。
