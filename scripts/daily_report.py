#!/usr/bin/env python3
"""日报服务 HTTP API 的纯标准库客户端。"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


DEFAULT_BASE_URL = "https://report.lehuicheng.top"
DEFAULT_CONFIG = Path.home() / ".config" / "daily-report" / "config.json"
DEFAULT_STATE = Path.home() / ".config" / "daily-report" / "claim.json"


class ConfigError(Exception):
    pass


class TransportError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status: int, data: Any):
        self.status = status
        self.data = data if isinstance(data, dict) else {}
        self.code = str(self.data.get("code", "HTTP_ERROR"))
        self.message = str(self.data.get("message", f"HTTP {status}"))
        self.request_id = self.data.get("requestId")
        super().__init__(self.message)


@dataclass(frozen=True)
class ApiResponse:
    status: int
    data: Any


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _parse_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransportError("服务端返回了无效 JSON") from exc


def _secure_state_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)


def _write_state(path: Path, value: dict[str, Any]) -> None:
    _secure_state_path(path)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _read_state(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"没有活动中的租约，请先执行 fetch（{path}）") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"无法读取租约状态 {path}") from exc
    if not isinstance(value, dict) or not value.get("reportId") or not value.get("leaseToken"):
        raise ConfigError(f"租约状态不完整：{path}")
    return value


class ReportClient:
    def __init__(
        self,
        base_url: str,
        producer_key: str = "",
        consumer_key: str = "",
        state_file: Path = DEFAULT_STATE,
        timeout: float = 20.0,
    ):
        if not base_url.startswith(("http://", "https://")):
            raise ConfigError("base_url 必须以 http:// 或 https:// 开头")
        self.base_url = base_url.rstrip("/")
        self.producer_key = producer_key
        self.consumer_key = consumer_key
        self.state_file = Path(state_file).expanduser()
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}))

    def _producer_token(self) -> str:
        if not self.producer_key:
            raise ConfigError("发送或查询需要配置 producer_key")
        return self.producer_key

    def _consumer_token(self) -> str:
        if not self.consumer_key:
            raise ConfigError("获取或回执需要配置 consumer_key")
        return self.consumer_key

    def _request(
        self,
        method: str,
        path: str,
        token: str,
        body: Any | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        data = None
        if body is not None:
            data = _json_bytes(body)
            headers["Content-Type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return ApiResponse(response.status, _parse_json(response.read()))
        except HTTPError as exc:
            raise ApiError(exc.code, _parse_json(exc.read())) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise TransportError(f"请求失败：{exc}") from exc

    def health(self) -> Any:
        return self._request("GET", "/health/ready", "health-check").data

    def push(self, payload: dict[str, Any], idempotency_key: str) -> Any:
        if not idempotency_key.strip():
            raise ConfigError("必须提供 idempotency_key")
        return self._request(
            "POST",
            "/api/v1/reports",
            self._producer_token(),
            payload,
            {"Idempotency-Key": idempotency_key},
        ).data

    def fetch(self) -> Any:
        consumer_key = self._consumer_token()
        if self.state_file.exists():
            raise ConfigError(
                f"已有活动租约：{self.state_file}；请先执行 complete 或 fail"
            )
        response = self._request("POST", "/api/v1/reports/claim", consumer_key)
        if response.status == 204:
            return {"claimed": False}
        data = response.data
        if not isinstance(data, dict) or not data.get("leaseToken"):
            raise TransportError("领取响应缺少 leaseToken")
        report = data.get("report") or {}
        report_id = report.get("id") or data.get("reportId")
        if not report_id:
            raise TransportError("领取响应缺少 report.id")
        _write_state(
            self.state_file,
            {
                "reportId": report_id,
                "leaseToken": data["leaseToken"],
                "submissionKey": report.get("submissionKey") or data.get("submissionKey"),
                "report": report,
            },
        )
        return data

    def get(self, report_id: str) -> Any:
        return self._request(
            "GET", f"/api/v1/reports/{report_id}", self._producer_token()
        ).data

    def append(self, report_id: str, patch: dict[str, Any]) -> Any:
        return self._update(report_id, patch, "append")

    def modify(self, report_id: str, patch: dict[str, Any]) -> Any:
        return self._update(report_id, patch, "replace")

    def _update(self, report_id: str, patch: dict[str, Any], mode: str) -> Any:
        if not report_id.strip():
            raise ConfigError("必须提供日报 ID")
        if not patch:
            raise ConfigError("追加或修改内容不能为空")
        if "mode" in patch:
            raise ConfigError("请求正文不能包含 mode，请使用 append 或 modify 命令")
        body = {"mode": mode, **patch}
        return self._request(
            "PATCH",
            f"/api/v1/reports/{report_id}",
            self._producer_token(),
            body,
        ).data

    def complete(self, report_id: str | None = None, lease_token: str | None = None) -> Any:
        consumer_key = self._consumer_token()
        report_id, lease_token = self._claim_values(report_id, lease_token)
        result = self._request(
            "POST",
            f"/api/v1/reports/{report_id}/complete",
            consumer_key,
            {"leaseToken": lease_token},
        ).data
        self._clear_matching_state(report_id)
        return result

    def fail(
        self,
        error_code: str,
        error_message: str,
        retryable: bool,
        report_id: str | None = None,
        lease_token: str | None = None,
    ) -> Any:
        consumer_key = self._consumer_token()
        report_id, lease_token = self._claim_values(report_id, lease_token)
        result = self._request(
            "POST",
            f"/api/v1/reports/{report_id}/fail",
            consumer_key,
            {
                "leaseToken": lease_token,
                "errorCode": error_code,
                "errorMessage": error_message,
                "retryable": retryable,
            },
        ).data
        self._clear_matching_state(report_id)
        return result

    def _claim_values(self, report_id: str | None, lease_token: str | None) -> tuple[str, str]:
        if report_id and lease_token:
            return report_id, lease_token
        state = _read_state(self.state_file)
        return report_id or state["reportId"], lease_token or state["leaseToken"]

    def _clear_matching_state(self, report_id: str) -> None:
        try:
            state = _read_state(self.state_file)
        except ConfigError:
            return
        if state.get("reportId") == report_id:
            self.state_file.unlink(missing_ok=True)


def load_client() -> ReportClient:
    config_path = Path(os.environ.get("DAILY_REPORT_CONFIG", DEFAULT_CONFIG)).expanduser()
    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            with config_path.open(encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise ConfigError(f"配置必须是 JSON 对象：{config_path}")
            config = loaded
        except json.JSONDecodeError as exc:
            raise ConfigError(f"配置不是有效 JSON：{config_path}") from exc
    base_url = os.environ.get("DAILY_REPORT_BASE_URL", config.get("base_url", DEFAULT_BASE_URL))
    producer_key = os.environ.get("DAILY_REPORT_PRODUCER_KEY", config.get("producer_key", ""))
    consumer_key = os.environ.get("DAILY_REPORT_CONSUMER_KEY", config.get("consumer_key", ""))
    state_file = Path(
        os.environ.get("DAILY_REPORT_STATE_FILE", config.get("state_file", DEFAULT_STATE))
    ).expanduser()
    return ReportClient(base_url, producer_key, consumer_key, state_file)


def _read_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ConfigError("日报请求正文必须是 JSON 对象")
    return value


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


class ChineseArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._positionals.title = "位置参数"
        self._optionals.title = "可选参数"
        for action in self._actions:
            if action.dest == "help":
                action.help = "显示帮助信息并退出"

    def format_help(self) -> str:
        return super().format_help().replace("usage: ", "用法：", 1)


def build_parser() -> argparse.ArgumentParser:
    parser = ChineseArgumentParser(prog="daily-report", description="日报发送与获取客户端")
    commands = parser.add_subparsers(title="命令", dest="command", required=True)
    commands.add_parser("health", help="检查服务健康状态")
    push = commands.add_parser("push", help="提交日报 JSON 对象")
    push.add_argument("--idempotency-key", required=True)
    push.add_argument("--payload-file")
    fetch = commands.add_parser("fetch", help="领取一条待处理日报")
    fetch.add_argument("--state-file")
    get = commands.add_parser("get", help="查询日报")
    get.add_argument("report_id")
    append = commands.add_parser("append", help="追加日报内容")
    append.add_argument("report_id")
    append.add_argument("--payload-file")
    modify = commands.add_parser("modify", help="修改日报内容")
    modify.add_argument("report_id")
    modify.add_argument("--payload-file")
    complete = commands.add_parser("complete", help="回传下游成功结果")
    complete.add_argument("--report-id")
    complete.add_argument("--lease-token")
    fail = commands.add_parser("fail", help="回传下游失败结果")
    fail.add_argument("--error-code", required=True)
    fail.add_argument("--error-message", required=True)
    retry = fail.add_mutually_exclusive_group(required=True)
    retry.add_argument("--retryable", action="store_true")
    retry.add_argument("--no-retryable", dest="retryable", action="store_false")
    fail.add_argument("--report-id")
    fail.add_argument("--lease-token")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = load_client()
        if args.command == "health":
            result = client.health()
        elif args.command == "push":
            result = client.push(_read_payload(args.payload_file), args.idempotency_key)
        elif args.command == "fetch":
            if args.state_file:
                client.state_file = Path(args.state_file).expanduser()
            result = client.fetch()
        elif args.command == "get":
            result = client.get(args.report_id)
        elif args.command == "append":
            result = client.append(args.report_id, _read_payload(args.payload_file))
        elif args.command == "modify":
            result = client.modify(args.report_id, _read_payload(args.payload_file))
        elif args.command == "complete":
            result = client.complete(args.report_id, args.lease_token)
        else:
            result = client.fail(
                args.error_code,
                args.error_message,
                args.retryable,
                args.report_id,
                args.lease_token,
            )
        _print_json(result)
        return 0
    except (ConfigError, ApiError, TransportError, OSError, json.JSONDecodeError) as exc:
        if isinstance(exc, ApiError):
            detail = f"{exc.code}: {exc.message} (HTTP {exc.status})"
            if exc.request_id:
                detail += f" requestId={exc.request_id}"
            print(detail, file=sys.stderr)
            return 2
        print(str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
