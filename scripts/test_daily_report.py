import json
import os
import stat
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from daily_report import ApiError, ConfigError, DEFAULT_BASE_URL, ReportClient, load_client


class FakeHandler(BaseHTTPRequestHandler):
    requests = []
    responses = {}

    def do_POST(self):
        self._handle_json_request()

    def do_PATCH(self):
        self._handle_json_request()

    def _handle_json_request(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.__class__.requests.append((self.command, self.path, dict(self.headers), body))
        status, payload = self.__class__.responses.get(self.path, (404, {"error": "missing"}))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        self.do_POST()

    def log_message(self, *_args):
        pass


class ReportClientTests(unittest.TestCase):
    def test_default_service_uses_public_https_endpoint(self):
        self.assertEqual(DEFAULT_BASE_URL, "https://report.lehuicheng.top")

    def setUp(self):
        FakeHandler.requests = []
        FakeHandler.responses = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.tempdir.name) / "claim.json"
        self.client = ReportClient(
            f"http://127.0.0.1:{self.server.server_port}",
            producer_key="producer-secret",
            consumer_key="consumer-secret",
            state_file=self.state_file,
        )

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tempdir.cleanup()

    def test_push_preserves_payload_and_idempotency_key(self):
        FakeHandler.responses["/api/v1/reports"] = (201, {"report": {"id": "report-1"}})
        payload = {"reportDate": "2026-07-22", "completed": ["done"]}

        result = self.client.push(payload, "daily-2026-07-22")

        self.assertEqual(result["report"]["id"], "report-1")
        _, path, headers, body = FakeHandler.requests[0]
        self.assertEqual(path, "/api/v1/reports")
        self.assertEqual(headers["Authorization"], "Bearer producer-secret")
        self.assertEqual(headers["Idempotency-Key"], "daily-2026-07-22")
        self.assertEqual(json.loads(body), payload)

    def test_append_uses_producer_patch_without_creating_new_report(self):
        FakeHandler.responses["/api/v1/reports/report-1"] = (
            200,
            {"id": "report-1", "status": "received"},
        )

        result = self.client.append("report-1", {"completed": ["追加事项"]})

        self.assertEqual(result["id"], "report-1")
        method, path, headers, body = FakeHandler.requests[0]
        self.assertEqual(method, "PATCH")
        self.assertEqual(path, "/api/v1/reports/report-1")
        self.assertEqual(headers["Authorization"], "Bearer producer-secret")
        self.assertEqual(
            json.loads(body),
            {"mode": "append", "completed": ["追加事项"]},
        )

    def test_modify_uses_replace_mode(self):
        FakeHandler.responses["/api/v1/reports/report-1"] = (
            200,
            {"id": "report-1", "status": "received"},
        )

        self.client.modify("report-1", {"inProgress": ["修改事项"]})

        self.assertEqual(
            json.loads(FakeHandler.requests[0][3]),
            {"mode": "replace", "inProgress": ["修改事项"]},
        )

    def test_producer_only_config_can_push(self):
        config_file = Path(self.tempdir.name) / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_url": f"http://127.0.0.1:{self.server.server_port}",
                    "producer_key": "producer-only-secret",
                }
            ),
            encoding="utf-8",
        )
        FakeHandler.responses["/api/v1/reports"] = (201, {"report": {"id": "report-2"}})

        with patch.dict(
            os.environ,
            {"DAILY_REPORT_CONFIG": str(config_file)},
            clear=True,
        ):
            client = load_client()
            result = client.push({"completed": ["done"]}, "producer-only")

        self.assertEqual(result["report"]["id"], "report-2")
        self.assertEqual(
            FakeHandler.requests[0][2]["Authorization"],
            "Bearer producer-only-secret",
        )

    def test_fetch_requires_consumer_key(self):
        client = ReportClient(
            f"http://127.0.0.1:{self.server.server_port}",
            producer_key="producer-secret",
            state_file=self.state_file,
        )

        with self.assertRaisesRegex(ConfigError, "获取或回执.*consumer_key"):
            client.fetch()

        self.assertEqual(FakeHandler.requests, [])

    def test_consumer_only_config_can_fetch(self):
        config_file = Path(self.tempdir.name) / "consumer-config.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_url": f"http://127.0.0.1:{self.server.server_port}",
                    "consumer_key": "consumer-only-secret",
                }
            ),
            encoding="utf-8",
        )
        FakeHandler.responses["/api/v1/reports/claim"] = (204, None)

        with patch.dict(
            os.environ,
            {"DAILY_REPORT_CONFIG": str(config_file)},
            clear=True,
        ):
            client = load_client()
            result = client.fetch()

        self.assertEqual(result, {"claimed": False})
        self.assertEqual(
            FakeHandler.requests[0][2]["Authorization"],
            "Bearer consumer-only-secret",
        )

    def test_fetch_204_is_a_normal_empty_result(self):
        FakeHandler.responses["/api/v1/reports/claim"] = (204, None)

        result = self.client.fetch()

        self.assertEqual(result, {"claimed": False})
        self.assertFalse(self.state_file.exists())

    def test_fetch_refuses_to_overwrite_an_active_claim(self):
        self.state_file.write_text(
            json.dumps({"reportId": "existing", "leaseToken": "existing-lease"}),
            encoding="utf-8",
        )

        with self.assertRaises(ConfigError):
            self.client.fetch()

        self.assertEqual(FakeHandler.requests, [])

    def test_fetch_persists_lease_and_complete_clears_it(self):
        FakeHandler.responses["/api/v1/reports/claim"] = (
            200,
            {
                "report": {"id": "report-1", "status": "processing"},
                "leaseToken": "lease-secret",
                "submissionKey": "daily-report-report-1",
            },
        )
        FakeHandler.responses["/api/v1/reports/report-1/complete"] = (
            200,
            {"report": {"id": "report-1", "status": "submitted"}},
        )

        claimed = self.client.fetch()
        state_mode = stat.S_IMODE(self.state_file.stat().st_mode)
        completed = self.client.complete()

        self.assertEqual(claimed["leaseToken"], "lease-secret")
        self.assertEqual(completed["report"]["status"], "submitted")
        self.assertEqual(state_mode, 0o600)
        self.assertFalse(self.state_file.exists())

    def test_fail_sends_error_and_retry_flag(self):
        FakeHandler.responses["/api/v1/reports/claim"] = (
            200,
            {"report": {"id": "report-1"}, "leaseToken": "lease-secret"},
        )
        FakeHandler.responses["/api/v1/reports/report-1/fail"] = (
            200,
            {"report": {"id": "report-1", "status": "dead_letter"}},
        )
        self.client.fetch()

        result = self.client.fail("DOWNSTREAM_BAD_DATA", "invalid field", retryable=False)

        self.assertEqual(result["report"]["status"], "dead_letter")
        body = json.loads(FakeHandler.requests[-1][3])
        self.assertEqual(body["leaseToken"], "lease-secret")
        self.assertFalse(body["retryable"])

    def test_api_error_keeps_code_and_http_status(self):
        FakeHandler.responses["/api/v1/reports"] = (
            409,
            {"code": "REPORT_CONFLICT", "message": "conflict", "requestId": "req-1"},
        )

        with self.assertRaises(ApiError) as context:
            self.client.push({}, "same-key")

        self.assertEqual(context.exception.status, 409)
        self.assertEqual(context.exception.code, "REPORT_CONFLICT")


if __name__ == "__main__":
    unittest.main()
