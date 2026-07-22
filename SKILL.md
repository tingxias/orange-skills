---
name: daily-report
description: Use when the user needs to submit a structured daily report, claim a pending report, inspect report status, or acknowledge downstream success or failure through the daily_report service.
---

# Daily Report

Use the bundled standard-library client to push reports as a Producer and claim or acknowledge reports as a Consumer. Keep credentials outside the skill directory and preserve the one-time claim lease until the downstream system has explicitly succeeded or failed.

## Configuration

Read credentials from `~/.config/daily-report/config.json` or these environment overrides:

```json
{
  "base_url": "https://report.lehuicheng.top",
  "producer_key": "<Producer Key>",
  "consumer_key": "<Consumer Key>",
  "state_file": "~/.config/daily-report/claim.json"
}
```

Use `0600` permissions for this file and never put an admin token in it. Environment variables take precedence: `DAILY_REPORT_BASE_URL`, `DAILY_REPORT_PRODUCER_KEY`, `DAILY_REPORT_CONSUMER_KEY`, and `DAILY_REPORT_STATE_FILE`.

Run the client as:

```bash
CLIENT="${CODEX_HOME:-$HOME/.codex}/skills/daily-report/scripts/daily_report.py"
python3 "$CLIENT" <command>
```

The client bypasses ambient HTTP proxies because the service is an internal address.

## Push

Before pushing, check `health` and build one fixed JSON payload. Keep the same `generatedAt` and body when retrying; change neither after choosing the idempotency key.

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

Treat HTTP `201` as a new report and `200` as an identical replay. Do not blindly retry `409 REPORT_CONFLICT`; compare the original body and idempotency key. The payload must contain at least one item in `completed` or `inProgress`, and `timezone` must be an IANA name.

## Fetch And Acknowledge

Run `fetch` once:

```bash
python3 "$CLIENT" fetch
```

HTTP `204` is a normal “no pending report” result. HTTP `200` returns the report, `submissionKey`, and one-time `leaseToken`; the client stores the lease in `claim.json` with mode `0600`. Do not call `fetch` again while that state exists, and do not complete a report before the downstream company system confirms success.

After downstream success:

```bash
python3 "$CLIENT" complete
```

After downstream failure, choose retryability explicitly:

```bash
python3 "$CLIENT" fail \
  --error-code DOWNSTREAM_UNAVAILABLE \
  --error-message 'company system temporarily unavailable' \
  --retryable
```

Use `--no-retryable` for deterministic data or business errors. A successful `complete` or `fail` removes the local lease state. Never log Producer/Consumer Keys or `leaseToken`; pass the lease only to the downstream call and this client.

Use `get <report-id>` for a Producer-side status check. `INVALID_LEASE` means the saved lease cannot be reused; stop and inspect the report rather than repeatedly retrying it.

## Error Handling

- `AUTHENTICATION_REQUIRED` or `ROLE_FORBIDDEN`: verify the correct same-user Producer/Consumer Key; never substitute the admin token.
- `REPORT_CONFLICT`: preserve the original payload and idempotency key, then investigate.
- `204` from `fetch`: finish normally without a callback.
- `INVALID_LEASE` or `INVALID_REPORT_STATE`: stop the current workflow; do not issue another claim.
- Transport errors: retry the exact same push body and idempotency key, not a regenerated timestamp.

The implementation and tests live in `scripts/daily_report.py` and `scripts/test_daily_report.py`.
