#!/usr/bin/env python3
"""Small standard-library client for the daily_report HTTP API."""

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
        raise TransportError("server returned invalid JSON") from exc


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
        raise ConfigError(f"no active claim; run fetch first ({path})") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read claim state {path}") from exc
    if not isinstance(value, dict) or not value.get("reportId") or not value.get("leaseToken"):
        raise ConfigError(f"claim state is incomplete: {path}")
    return value


class ReportClient:
    def __init__(
        self,
        base_url: str,
        producer_key: str,
        consumer_key: str,
        state_file: Path = DEFAULT_STATE,
        timeout: float = 20.0,
    ):
        if not base_url.startswith(("http://", "https://")):
            raise ConfigError("base_url must start with http:// or https://")
        if not producer_key or not consumer_key:
            raise ConfigError("producer_key and consumer_key are required")
        self.base_url = base_url.rstrip("/")
        self.producer_key = producer_key
        self.consumer_key = consumer_key
        self.state_file = Path(state_file).expanduser()
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}))

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
            raise TransportError(f"request failed: {exc}") from exc

    def health(self) -> Any:
        return self._request("GET", "/health/ready", "health-check").data

    def push(self, payload: dict[str, Any], idempotency_key: str) -> Any:
        if not idempotency_key.strip():
            raise ConfigError("idempotency_key is required")
        return self._request(
            "POST",
            "/api/v1/reports",
            self.producer_key,
            payload,
            {"Idempotency-Key": idempotency_key},
        ).data

    def fetch(self) -> Any:
        if self.state_file.exists():
            raise ConfigError(
                f"an active claim already exists at {self.state_file}; complete or fail it first"
            )
        response = self._request("POST", "/api/v1/reports/claim", self.consumer_key)
        if response.status == 204:
            return {"claimed": False}
        data = response.data
        if not isinstance(data, dict) or not data.get("leaseToken"):
            raise TransportError("claim response did not contain leaseToken")
        report = data.get("report") or {}
        report_id = report.get("id") or data.get("reportId")
        if not report_id:
            raise TransportError("claim response did not contain report.id")
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
        return self._request("GET", f"/api/v1/reports/{report_id}", self.producer_key).data

    def complete(self, report_id: str | None = None, lease_token: str | None = None) -> Any:
        report_id, lease_token = self._claim_values(report_id, lease_token)
        result = self._request(
            "POST",
            f"/api/v1/reports/{report_id}/complete",
            self.consumer_key,
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
        report_id, lease_token = self._claim_values(report_id, lease_token)
        result = self._request(
            "POST",
            f"/api/v1/reports/{report_id}/fail",
            self.consumer_key,
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
                raise ConfigError(f"config must be a JSON object: {config_path}")
            config = loaded
        except json.JSONDecodeError as exc:
            raise ConfigError(f"invalid JSON config: {config_path}") from exc
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
        raise ConfigError("report payload must be a JSON object")
    return value


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="daily-report")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("health")
    push = commands.add_parser("push", help="submit a report JSON object")
    push.add_argument("--idempotency-key", required=True)
    push.add_argument("--payload-file")
    fetch = commands.add_parser("fetch", help="claim one pending report")
    fetch.add_argument("--state-file")
    get = commands.add_parser("get", help="read a report")
    get.add_argument("report_id")
    complete = commands.add_parser("complete", help="acknowledge a successful downstream submission")
    complete.add_argument("--report-id")
    complete.add_argument("--lease-token")
    fail = commands.add_parser("fail", help="report downstream failure")
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
