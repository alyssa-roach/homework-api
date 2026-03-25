"""
HTTP client that logs every request/response (Rich console + optional file).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from rich.panel import Panel

try:
    from rich.console import Console
except ImportError:  # pragma: no cover
    Console = None  # type: ignore


def _truncate(text: str, limit: int = 800) -> str:
    text = text.replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _safe_json(data: Any) -> str:
    try:
        return json.dumps(data, default=str, indent=2)
    except (TypeError, ValueError):
        return str(data)


def _is_sensitive_response_key(key: str) -> bool:
    lk = key.lower()
    return lk in ("token", "access_token", "refresh_token") or lk.endswith("_token")


def _redact_sensitive_response_json(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: ("***" if _is_sensitive_response_key(k) else _redact_sensitive_response_json(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact_sensitive_response_json(x) for x in data]
    return data


def _mask_response_for_log(path: str, resp_text: str) -> str:
    raw = resp_text if resp_text is not None else ""
    if not raw.strip():
        return "—"
    is_token_path = "/api/auth/token/" in path
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        if is_token_path:
            return "[Redacted: non-JSON response on token endpoint]"
        return raw
    redacted = _redact_sensitive_response_json(parsed)
    return _safe_json(redacted)


class LoggedAPIClient:
    """
    Thin wrapper around requests with structured logging for demos.

    Logs: method, path, request body (passwords masked), status, response body.
    """

    def __init__(
        self,
        base_url: str,
        console: Optional["Console"] = None,
        log_to_file: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.console = console
        self.log_to_file = log_to_file
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]) -> None:
        self.token = token
        if token:
            self.session.headers["Authorization"] = f"Token {token}"
        else:
            self.session.headers.pop("Authorization", None)

    def _mask_request_for_log(self, json_body: Any) -> Any:
        if not isinstance(json_body, dict):
            return json_body
        out = dict(json_body)
        if "password" in out:
            out["password"] = "***"
        return out

    def _emit_log(
        self,
        method: str,
        path: str,
        req_body: Any,
        status: int,
        resp_text: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> None:
        req_display = self._mask_request_for_log(req_body)
        req_json = _truncate(_safe_json(req_display) if req_display is not None else "—")
        qp_line = ""
        if query_params:
            qp_line = f"Query params:\n{_truncate(_safe_json(query_params))}\n\n"
        resp_masked = _mask_response_for_log(path, resp_text)
        resp_trunc = _truncate(resp_masked)
        body = (
            f"{method} {path}\n\n"
            f"{qp_line}"
            f"Request body:\n{req_json}\n\n"
            f"Status: {status}\n\n"
            f"Response body:\n{resp_trunc}"
        )
        if self.console:
            self.console.print(
                Panel(
                    body,
                    title="[bold cyan]API call[/]",
                    border_style="cyan",
                    expand=False,
                )
            )
        else:
            print("\n--- API call ---\n" + body)

        if self.log_to_file:
            qp_plain = ""
            if query_params:
                qp_plain = f"QUERY: {_safe_json(query_params)}\n"
            plain = (
                f"{method} {path}\n{qp_plain}"
                f"REQUEST: {_safe_json(req_display)}\n"
                f"STATUS: {status}\nRESPONSE: {resp_trunc}\n\n"
            )
            Path(self.log_to_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_to_file, "a", encoding="utf-8") as fh:
                fh.write(plain)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        merged_headers = dict(headers or {})

        try:
            resp = self.session.request(
                method.upper(),
                url,
                json=json_body,
                params=params,
                headers=merged_headers,
                timeout=30,
            )
        except requests.RequestException as exc:
            err_msg = f"{method} {path}\nError: {exc!r}"
            if self.console:
                self.console.print(
                    Panel(err_msg, title="[red]API error[/]", border_style="red")
                )
            raise

        self._emit_log(
            method,
            path,
            json_body,
            resp.status_code,
            resp.text,
            query_params=params,
        )
        return resp

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)
