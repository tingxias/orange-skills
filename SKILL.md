---
name: daily-report
description: 当用户需要通过 daily_report 服务发送或获取结构化日报、查询日报状态，或回传下游处理结果时使用。
---

# 日报发送与获取

发送者和获取者可以由同一软件执行，也可以分开部署。发送者以生产者（Producer）身份提交日报；获取者以消费者（Consumer）身份领取日报、填写公司系统或完成其他下游处理，并回传成功或失败结果。两端共用同一个日报服务，但不必运行在同一环境。

## 使用前确认

首次使用时，必须由用户明确输入本次角色对应的完整 Key（即 Bearer 密钥）。后续使用已保存凭据或更换运行环境时，也必须由用户明确授权读取对应配置。不能因为本地配置文件存在、上次会话使用过，或服务地址有默认值，就默默读取凭据并继续调用接口。

- 发送或查询日报：需要用户明确提供发送端的 `Producer Key`。
- 获取、完成或失败回执：需要用户明确提供获取端的 `Consumer Key`。
- 同一软件同时承担两种角色：必须分别确认两把 Key；发送者和获取者分开时，各自只配置本角色的 Key。
- 服务使用完整的 `drp_...`（Producer）或 `drc_...`（Consumer）字符串作为 Bearer 密钥，没有可拆开的用户名和密码字段。完整字符串必须按密钥处理，不要写入日志、日报正文或 Git。

未确认前，不执行 `push`、`get`、`fetch`、`complete` 或 `fail`。如果用户只是在询问配置方式，可以只说明所需字段，不发起网络请求。

## 配置

凭据保存在运行端的 `~/.config/daily-report/config.json`，文件权限设置为 `0600`。发送端可以只配置 Producer Key：

```json
{
  "base_url": "https://report.lehuicheng.top",
  "producer_key": "<完整的 Producer Key>"
}
```

获取端可以只配置 Consumer Key：

```json
{
  "base_url": "https://report.lehuicheng.top",
  "consumer_key": "<完整的 Consumer Key>",
  "state_file": "~/.config/daily-report/claim.json"
}
```

同一运行端需要两种角色时，才在同一个配置中同时填写两把 Key。也可以用环境变量覆盖配置：`DAILY_REPORT_BASE_URL`、`DAILY_REPORT_PRODUCER_KEY`、`DAILY_REPORT_CONSUMER_KEY`、`DAILY_REPORT_STATE_FILE`。不要在配置中保存管理员 Token、公司系统凭据或不属于当前角色的密钥。

按以下方式调用客户端：

```bash
CLIENT="${CODEX_HOME:-$HOME/.codex}/skills/daily-report/scripts/daily_report.py"
python3 "$CLIENT" <命令>
```

客户端会绕过系统 HTTP 代理，直接访问日报服务。`health` 不需要角色 Key；其他命令会在发送对应请求前检查本命令所需的 Key。

## 发送日报

确认用户已提供 Producer Key 后，先执行 `health` 检查服务状态，再生成固定的 JSON 请求。确定幂等键后，重试时必须复用完全相同的请求正文和 `generatedAt`，不要重新生成时间。

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

使用 `get <日报 ID>` 从发送端查询状态；它不会领取日报，也不会创建获取端租约。

## 获取与回执

确认用户已提供 Consumer Key 后，只执行一次 `fetch`：

```bash
python3 "$CLIENT" fetch
```

HTTP `204` 表示当前没有待处理日报，属于正常结果。HTTP `200` 会返回日报、`submissionKey` 和一次性 `leaseToken`；客户端同时将租约保存到权限为 `0600` 的 `claim.json`。本地存在租约状态时不要再次执行 `fetch`，下游系统未明确确认成功前也不要执行回执。

下游处理成功后执行：

```bash
python3 "$CLIENT" complete
```

下游处理失败时，明确指定是否允许重试：

```bash
python3 "$CLIENT" fail \
  --error-code DOWNSTREAM_UNAVAILABLE \
  --error-message '下游系统暂时不可用' \
  --retryable
```

确定性数据错误或业务错误使用 `--no-retryable`。`complete` 或 `fail` 成功后，客户端会删除本地租约状态。不要记录 Producer Key、Consumer Key 或 `leaseToken`，租约只传递给下游调用和本客户端。

发送者和获取者分开时，获取端也可以直接调用以下 HTTP 契约，不要求使用本客户端：

- `POST /api/v1/reports/claim`：使用 `Authorization: Bearer <Consumer Key>` 领取一条日报。`204` 表示暂无任务；`200` 返回日报、`submissionKey` 和一次性 `leaseToken`。
- 下游系统填写成功后，调用 `POST /api/v1/reports/{id}/complete`，请求体只包含 `leaseToken`。
- 下游系统填写失败后，调用 `POST /api/v1/reports/{id}/fail`，提交 `leaseToken`、`errorCode`、`errorMessage` 和 `retryable`。

## 错误处理

- `AUTHENTICATION_REQUIRED` 或 `ROLE_FORBIDDEN`：确认用户已明确提供正确角色的 Key，不要替换成管理员 Token，也不要用 Producer Key 调获取接口或反过来使用。
- `REPORT_CONFLICT`：保留原始请求正文和幂等键，再调查冲突原因。
- 获取接口返回 `204`：正常结束，不发送任何回执。
- `INVALID_LEASE` 或 `INVALID_REPORT_STATE`：停止当前任务并调查状态，不要继续领取新任务。
- 传输错误：使用完全相同的正文和幂等键重试，不要重新生成时间戳。

实现与测试分别位于 `scripts/daily_report.py`、`scripts/test_daily_report.py` 和 `scripts/test_skill_locale.py`。
