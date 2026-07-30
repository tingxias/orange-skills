---
name: daily-report
description: 当用户需要通过 daily_report 服务生成本周工作总结，发送、追加、修改或获取结构化日报，查询日报状态，或回传下游处理结果时使用。
---

# 日报发送与获取

发送者和获取者可以由同一软件执行，也可以分开部署。发送者以生产者（Producer）身份提交日报；获取者以消费者（Consumer）身份领取日报、填写公司系统或完成其他下游处理，并回传成功或失败结果。两端共用同一个日报服务，但不必运行在同一环境。

## 凭据使用

首次使用或对应角色 Key 未配置时，要求用户输入本次角色对应的完整 Key（即 Bearer 密钥）。配置文件或环境变量已有当前命令所需角色 Key 时，直接读取并使用，不再要求逐次授权。

- 发送、查询、追加或修改日报：使用已配置的 `Producer Key`；缺失、失效或角色不匹配时，请用户更新发送端 Key。
- 获取、完成或失败回执：使用已配置的 `Consumer Key`；缺失、失效或角色不匹配时，请用户更新获取端 Key。
- 同一软件同时承担两种角色时，分别使用已配置的两把 Key；发送者和获取者分开时，各自只配置本角色的 Key。
- 服务使用完整的 `drp_...`（Producer）或 `drc_...`（Consumer）字符串作为 Bearer 密钥，没有可拆开的用户名和密码字段。完整字符串必须按密钥处理，不要写入日志、日报正文或 Git。

如果用户只是在询问配置方式，可以只说明所需字段，不发起网络请求。

## 配置

凭据和周报范围偏好保存在运行端的 `~/.config/daily-report/config.json`，文件权限设置为 `0600`。发送端可以配置 Producer Key 和已确认的周报范围：

```json
{
  "base_url": "https://report.lehuicheng.top",
  "producer_key": "<完整的 Producer Key>",
  "weekly_summary_scope": {"mode": "all", "project_roots": []}
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

## 整理本周工作内容

当用户要求根据当前工具中的项目和任务生成日报时，使用已配置的 Producer Key。配置中没有 `weekly_summary_scope` 时，首次生成周报时，询问：“使用本周全部项目，还是指定项目？”。

- 用户选择全部项目时，保存 `{"mode":"all","project_roots":[]}` 到 `weekly_summary_scope`，并读取当前工具可见的全部项目及其本周任务。
- 用户选择指定项目时，继续询问项目名称或路径，保存 `{"mode":"whitelist","project_roots":[...]}` 到 `weekly_summary_scope`，并读取匹配项目。
- 保存时保留配置中已有的服务地址、角色 Key 和 `state_file`，文件权限保持 `0600`。
- 后续生成周报自动使用已保存的范围偏好，不再询问目录。
- 用户在当前请求中主动指定项目名称或路径时，使用该范围只覆盖本次，不改写已保存的范围偏好。

“本周”按运行端本地时区计算，只包含本周一 `00:00` 到当前时间。当前工具不能提供项目或任务列表时，说明缺失来源并请用户补充，不猜测工作内容。

将任务按项目归并，再按状态形成简明的结果性总结。同一项目、同一状态的多个任务合并成一条；每条 `completed`、`inProgress`、`risks` 或 `nextSteps` 条目都必须以简明项目名称或已确认路径前缀保留项目归属，不得只按状态汇总为跨项目全局列表。只保留关键结果、当前进展、明确风险和已经确定的下一步；不逐条复制任务标题、聊天记录或操作步骤。同一事项从多个来源出现时只保留一份，没有可靠状态或时间的信息不自行归类。

- 已完成结果写入 `completed`。
- 正在推进的工作写入 `inProgress`。
- 明确阻塞或风险写入 `risks`。
- 已确定的后续动作写入 `nextSteps`。
- 支撑总结的项目、任务、提交或文件引用可写入 `evidence`，不得包含凭据、租约或敏感配置。

保持默认范围时使用 `scope.mode=all`，即 `scope: {"mode":"all","projectRoots":[]}`；指定项目时使用 `scope.mode=whitelist`，并把确认后的项目名称或路径写入 `projectRoots`。

## 发送日报

使用已配置的 Producer Key 后，先执行 `health` 检查服务状态，再生成固定的 JSON 请求。Key 缺失、失效或角色不匹配时停止并请求更新。确定幂等键后，重试时必须复用完全相同的请求正文和 `generatedAt`，不要重新生成时间。

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

## 查询本人日报

使用已配置的 Producer Key 查询该 Key 所属用户的日报。用户身份只由服务端认证结果确定，不能传入或拼接 `userId`；即使发送端与获取端分开，查询也只需要 Producer Key。Key 缺失、失效或角色不匹配时停止并请求更新。

```bash
python3 "$CLIENT" list \
  --report-date 2026-07-22 \
  --template-key daily \
  --status received \
  --limit 20
```

`--report-date`、`--template-key` 和 `--status` 均可省略；`--limit` 默认 20，范围为 1 到 100。结果按日报日期、创建时间和 ID 倒序返回在 `reports` 数组中，空数组表示本人没有符合条件的日报。查询是只读操作，不会领取日报或改变状态。使用 Consumer Key 会返回 `403 ROLE_FORBIDDEN`。

## 追加或修改日报

使用已配置的 Producer Key 后，先使用 `get <日报 ID>` 确认当前内容和状态。追加与修改都更新原日报 ID，不要生成新的幂等键或重新调用 `push`。这些操作不读取项目任务，也不询问同步目录或项目范围。

追加内容时，仅发送需要新增的数组项；服务保留原内容并自动去重：

```bash
echo '{
  "completed": ["补充完成事项"],
  "evidence": [{"kind": "commit", "value": "abc123"}]
}' | python3 "$CLIENT" append '<日报 ID>'
```

修改内容时，仅发送需要替换的字段，未提供的字段保持不变：

```bash
echo '{
  "inProgress": ["调整后的进行中事项"],
  "risks": []
}' | python3 "$CLIENT" modify '<日报 ID>'
```

追加模式会合并 `completed`、`inProgress`、`risks`、`nextSteps` 和 `evidence`。修改模式会整体替换请求中出现的字段。`received`、`retry_wait`、`dead_letter` 可以更新；`processing` 已被获取端领取，`submitted` 已提交，两种状态都禁止更新。修改 `dead_letter` 后，需要单独执行重入操作才能再次投递。

## 获取与回执

使用已配置的 Consumer Key 后，只执行一次 `fetch`。`fetch`、`complete`、`fail`、`get`、`list`、`append` 和 `modify` 不读取项目任务；执行这些命令时不得询问同步目录或项目范围。Key 缺失、失效或角色不匹配时停止并请求更新：

```bash
python3 "$CLIENT" fetch --report-date 2026-07-30
```

`fetch` 必须明确提供目标日期。用户未明确目标日期时，先询问要领取哪一天的日报；不得默认当天、最近日期、最早日期或本地租约中的日期。HTTP `204` 表示该日期没有待处理日报，属于正常结果；客户端不会改为领取其他日期。HTTP `200` 会返回日报、`submissionKey` 和一次性 `leaseToken`；客户端同时将租约保存到权限为 `0600` 的 `claim.json`。本地存在租约状态时不要再次执行 `fetch`，下游系统未明确确认成功前也不要执行回执。

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

- `POST /api/v1/reports/claim`：使用 `Authorization: Bearer <Consumer Key>` 和 `{"reportDate":"YYYY-MM-DD"}` 请求体领取指定日期的日报。`204` 表示该日期暂无任务；`200` 返回日报、`submissionKey` 和一次性 `leaseToken`。
- 下游系统填写成功后，调用 `POST /api/v1/reports/{id}/complete`，请求体只包含 `leaseToken`。
- 下游系统填写失败后，调用 `POST /api/v1/reports/{id}/fail`，提交 `leaseToken`、`errorCode`、`errorMessage` 和 `retryable`。

## 错误处理

- `AUTHENTICATION_REQUIRED` 或 `ROLE_FORBIDDEN`：确认已配置正确角色的 Key；缺失、失效或角色不匹配时请用户更新，不要替换成管理员 Token，也不要用 Producer Key 调获取接口或反过来使用。
- `REPORT_CONFLICT`：保留原始请求正文和幂等键，再调查冲突原因。
- 追加或修改返回 `INVALID_REPORT_STATE`：日报正在处理或已经提交，不要绕过状态限制创建重复日报。
- 获取接口返回 `204`：正常结束，不发送任何回执。
- `INVALID_LEASE` 或 `INVALID_REPORT_STATE`：停止当前任务并调查状态，不要继续领取新任务。
- 传输错误：使用完全相同的正文和幂等键重试，不要重新生成时间戳。

实现与测试分别位于 `scripts/daily_report.py`、`scripts/test_daily_report.py` 和 `scripts/test_skill_locale.py`。
