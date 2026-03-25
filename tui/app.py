"""
Interactive terminal UI for the Homework API.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from tui.http_client import LoggedAPIClient


def _print_json(console: Console, data: Any) -> None:
    console.print_json(data=data if isinstance(data, (dict, list)) else {"result": data})


def login_flow(client: LoggedAPIClient, console: Console) -> Optional[Dict[str, Any]]:
    console.rule("[bold]Login")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    r = client.post("/api/auth/token/", json_body={"username": username, "password": password})
    if r.status_code != 200:
        console.print("[red]Login failed.[/] Check username/password and that the API is running.")
        try:
            console.print_json(data=r.json())
        except Exception:
            console.print(r.text)
        return None
    token = r.json().get("token")
    if not token:
        console.print("[red]No token in response.[/]")
        return None
    client.set_token(token)
    r2 = client.get("/api/me/")
    if r2.status_code != 200:
        console.print("[red]Could not load /api/me/[/]")
        client.set_token(None)
        return None
    me = r2.json()
    console.print(f"[green]Logged in as[/] [bold]{me.get('username')}[/] ([cyan]{me.get('role')}[/])")
    return me


def menu_student(client: LoggedAPIClient, console: Console) -> None:
    console.rule("[bold]Student menu")
    table = Table(box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Action")
    table.add_row("1", "List assignments")
    table.add_row("2", "List my submissions")
    table.add_row("3", "Submit / resubmit homework")
    table.add_row("q", "Logout")
    console.print(table)
    choice = Prompt.ask("Choose", default="1")
    if choice == "q":
        client.set_token(None)
        return
    if choice == "1":
        r = client.get("/api/assignments/")
        if r.status_code == 200:
            _show_paginated_results(console, r.json())
        else:
            console.print(f"[red]Error {r.status_code}[/]")
    elif choice == "2":
        grade = Prompt.ask("Filter grade (A-F, ungraded, incomplete, or blank)", default="")
        params = {}
        if grade.strip():
            params["grade"] = grade.strip()
        aname = Prompt.ask("Filter assignment name (contains, or blank)", default="")
        if aname.strip():
            params["assignment_name"] = aname.strip()
        r = client.get("/api/submissions/", params=params or None)
        if r.status_code == 200:
            _show_paginated_results(console, r.json())
        else:
            console.print(f"[red]Error {r.status_code}[/]")
    elif choice == "3":
        while True:
            aid = Prompt.ask("Assignment ID", default="1")
            try:
                assignment_id = int(aid.strip())
            except ValueError:
                console.print("[red]Assignment ID must be a whole number.[/]")
                continue
            break
        content = Prompt.ask("Submission content (single line for demo; use \\n in text if needed)")
        r = client.post(
            "/api/submissions/",
            json_body={"assignment_id": assignment_id, "content": content.replace("\\n", "\n")},
        )
        if r.status_code in (200, 201):
            console.print("[green]Submission saved.[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)
        else:
            console.print(f"[red]Error {r.status_code}[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)


def menu_teacher(client: LoggedAPIClient, console: Console) -> None:
    console.rule("[bold]Teacher menu")
    table = Table(box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Action")
    table.add_row("1", "List all submissions (filters)")
    table.add_row("2", "Grade a submission")
    table.add_row("3", "Create assignment")
    table.add_row("q", "Logout")
    console.print(table)
    choice = Prompt.ask("Choose", default="1")
    if choice == "q":
        client.set_token(None)
        return
    if choice == "1":
        params: Dict[str, str] = {}
        for key, label in [
            ("assignment_name", "Assignment name contains"),
            ("student_name", "Student name contains"),
            ("date_from", "Submission from (ISO e.g. 2025-01-01T00:00:00Z, or blank)"),
            ("date_to", "Submission to (ISO, or blank)"),
            ("grade", "Grade filter (A-F, ungraded, incomplete, or blank)"),
        ]:
            v = Prompt.ask(label, default="")
            if v.strip():
                params[key] = v.strip()
        r = client.get("/api/submissions/", params=params or None)
        if r.status_code == 200:
            _show_paginated_results(console, r.json())
        else:
            console.print(f"[red]Error {r.status_code}[/]")
    elif choice == "2":
        while True:
            sid = Prompt.ask("Submission ID to grade")
            try:
                submission_id = int(sid.strip())
            except ValueError:
                console.print("[red]Submission ID must be a whole number.[/]")
                continue
            break
        grade = Prompt.ask("Final grade (A-F)", default="A")
        notes = Prompt.ask("Teacher notes", default="")
        r = client.patch(
            f"/api/submissions/{submission_id}/",
            json_body={"final_grade": grade, "teachers_notes": notes},
        )
        if r.status_code == 200:
            console.print("[green]Graded.[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)
        else:
            console.print(f"[red]Error {r.status_code}[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)
    elif choice == "3":
        name = Prompt.ask("Assignment name")
        due = Prompt.ask("Due date (ISO 8601)", default="2026-12-31T23:59:59Z")
        r = client.post("/api/assignments/", json_body={"name": name, "due_date": due})
        if r.status_code == 201:
            console.print("[green]Assignment created.[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)
        else:
            console.print(f"[red]Error {r.status_code}[/]")
            try:
                _print_json(console, r.json())
            except Exception:
                console.print(r.text)


def _show_paginated_results(console: Console, payload: Dict[str, Any]) -> None:
    """Pretty-print DRF paginated list or raw list."""
    results = payload.get("results", payload)
    if isinstance(results, list):
        if not results:
            console.print("[dim]No rows.[/]")
            return
        table = Table(box=box.SIMPLE_HEAD)
        keys = set()
        for row in results:
            if isinstance(row, dict):
                keys.update(row.keys())
        preferred = [
            "id",
            "name",
            "assignment",
            "student",
            "content",
            "submission_date",
            "final_grade",
            "teachers_notes",
        ]
        col_order = [k for k in preferred if k in keys]
        for k in sorted(keys):
            if k not in col_order:
                col_order.append(k)
        for k in col_order[:12]:
            table.add_column(k.replace("_", " "), overflow="fold")
        for row in results:
            if not isinstance(row, dict):
                table.add_row(str(row))
                continue
            table.add_row(*[_cell_preview(row.get(k)) for k in col_order[:12]])
        console.print(table)
        console.print(f"[dim]Count:[/] {payload.get('count', len(results))}")
    else:
        _print_json(console, payload)


def _cell_preview(val: Any, max_len: int = 40) -> str:
    if val is None:
        return "—"
    if isinstance(val, dict):
        if "id" in val and "name" in val:
            return f"#{val['id']} {val['name']}"
        return json.dumps(val)[:max_len]
    s = str(val)
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Homework API terminal UI (logs all HTTP calls).")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("HOMEWORK_API_BASE_URL", "http://127.0.0.1:8000"),
        help="API base URL",
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("HOMEWORK_API_LOG_FILE", "tui_api_calls.log"),
        help="Append all API traffic to this file (plain text)",
    )
    parser.add_argument("--no-log-file", action="store_true", help="Disable file logging")
    args = parser.parse_args(argv)

    console = Console()
    log_path = None if args.no_log_file else args.log_file
    client = LoggedAPIClient(args.base_url, console=console, log_to_file=log_path)

    console.print(
        Panel.fit(
            "[bold]Homework API — Terminal UI[/]\n"
            "Every request/response is shown above each [cyan]API call[/] panel.\n"
            f"Base URL: [yellow]{args.base_url}[/]\n"
            + (f"Log file: [dim]{log_path}[/]" if log_path else "[dim]File logging off[/]"),
            border_style="green",
        )
    )

    if log_path:
        console.print(f"[dim]Appending API logs to:[/] {os.path.abspath(log_path)}\n")

    me: Optional[Dict[str, Any]] = None
    while True:
        if not client.token:
            me = login_flow(client, console)
            if not me:
                if not Confirm.ask("Retry login?", default=True):
                    return 1
                continue
        assert me is not None
        role = me.get("role")
        if role == "student":
            menu_student(client, console)
        elif role == "teacher":
            menu_teacher(client, console)
        else:
            console.print("[red]Unknown role.[/] Log in again.")
            client.set_token(None)
            me = None
        if not client.token:
            me = None
            if not Confirm.ask("Exit?", default=False):
                continue
            break

    console.print("[dim]Goodbye.[/]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
