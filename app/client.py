from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .config import settings


class UrjaPortalClient:
    """Thin adapter around the legacy Urja Meter Ops portal."""

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.username = username or settings.username
        self.password = password or settings.password
        self.timeout = settings.timeout
        self.session = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=False,
            headers={
                "User-Agent": settings.user_agent,
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/login",
            },
        )

    def _headers(self, path: str) -> dict[str, str]:
        return {
            "User-Agent": settings.user_agent,
            "Origin": self.base_url,
            "Referer": f"{self.base_url}{path if path.startswith('/') else '/' + path}",
        }

    def login(self, email: str | None = None, password: str | None = None) -> dict[str, Any]:
        email = email or self.username
        password = password or self.password

        self.session.get("/login", headers=self._headers("/login"))
        response = self.session.post(
            "/login",
            data={"email": email, "password": password},
            headers={**self._headers("/login"), "Content-Type": "application/x-www-form-urlencoded"},
            follow_redirects=False,
        )

        token = self.session.cookies.get("__Secure-better-auth.session_token")
        authenticated = bool(token) or response.status_code in {200, 303}
        return {
            "authenticated": authenticated,
            "status_code": response.status_code,
            "token_present": bool(token),
        }

    def _ensure_authenticated(self) -> None:
        if not self.session.cookies.get("__Secure-better-auth.session_token"):
            self.login()

    def _request(self, path: str) -> httpx.Response:
        self._ensure_authenticated()
        response = self.session.get(path, headers=self._headers(path), follow_redirects=True)

        if response.status_code == 401:
            self.login()
            response = self.session.get(path, headers=self._headers(path), follow_redirects=True)
        return response

    def logout(self) -> dict[str, Any]:
        try:
            response = self.session.post(
                "/logout",
                headers={**self._headers("/logout"), "Content-Type": "application/x-www-form-urlencoded"},
                data={},
                follow_redirects=False,
            )
        except httpx.HTTPError:
            response = None

        if response is not None and response.status_code in {200, 302, 303}:
            self.session.cookies.clear()
            return {
                "logged_out": True,
                "status_code": response.status_code,
                "redirected_to": response.headers.get("location") or "/login",
            }

        self.session.cookies.clear()
        return {
            "logged_out": True,
            "status_code": 200,
            "redirected_to": "/login",
        }

    def get_meters(self, page: int = 1, page_size: int = 25, query: str | None = None) -> dict[str, Any]:
        response = self._request("/meters")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table tbody tr")

        meters: list[dict[str, Any]] = []
        for row in rows:
            cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
            if not cells or "No meters found" in row.get_text(" ", strip=True):
                continue

            link = row.select_one("a[href*='/meters/']")
            meter_id = link.get("href", "").split("/meters/")[-1].strip("/") if link else cells[0]

            meters.append(
                {
                    "meter_id": meter_id,
                    "serial_number": cells[1] if len(cells) > 1 else None,
                    "make": cells[2] if len(cells) > 2 else None,
                    "phase": cells[3] if len(cells) > 3 else None,
                    "status": cells[4] if len(cells) > 4 else None,
                    "dt": cells[5] if len(cells) > 5 else None,
                    "source": "legacy_html",
                }
            )

        if query:
            query = query.lower()
            meters = [item for item in meters if query in (item["meter_id"] + " " + (item["serial_number"] or "")).lower()]

        start = (page - 1) * page_size
        end = start + page_size
        page_items = meters[start:end]
        return {
            "meters": page_items,
            "total": len(meters),
            "page": page,
            "page_size": page_size,
        }

    def get_meter_detail(self, meter_id: str) -> dict[str, Any]:
        response = self._request(f"/meters/{meter_id}")
        if response.status_code == 404:
            raise ValueError(f"Meter '{meter_id}' was not found on the legacy portal.")

        page_html = response.text
        soup = BeautifulSoup(page_html, "html.parser")

        text = soup.get_text(" ", strip=True)
        meter_number = meter_id
        serial_number = self._first_match(soup, [r"Serial.*?([A-Za-z0-9-]+)", r"Meter serial.*?([A-Za-z0-9-]+)"])
        status = self._first_match(soup, [r"Status.*?([A-Za-z ]+)", r"Current status.*?([A-Za-z ]+)"])
        make = self._first_match(soup, [r"Make.*?([A-Za-z0-9 ]+)", r"Manufacturer.*?([A-Za-z0-9 ]+)"])
        phase = self._first_match(soup, [r"Phase.*?([A-Za-z0-9 ]+)", r"Connection.*?([A-Za-z0-9 ]+)"])
        last_updated = self._first_match(soup, [r"Last updated.*?([0-9A-Za-z:/ -]+)", r"Updated.*?([0-9A-Za-z:/ -]+)"])

        return {
            "meter_id": meter_id,
            "meter_number": meter_number,
            "serial_number": serial_number,
            "make": make,
            "phase": phase,
            "status": status,
            "last_updated": last_updated,
            "raw_html_snippet": text[:250],
        }

    def get_meter_consumption(self, meter_id: str, days: int = 30) -> dict[str, Any]:
        candidate_paths = [f"/meters/{meter_id}/consumption", f"/meters/{meter_id}"]
        points: list[dict[str, Any]] = []

        for path in candidate_paths:
            response = self._request(path)
            if response.status_code >= 400:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")
            for row in rows:
                cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
                if len(cells) < 2 or any(item.lower() in {"no data", "no records"} for item in cells):
                    continue
                timestamp = cells[0]
                value_candidate = cells[-1]
                value = None
                match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value_candidate)
                if match:
                    value = float(match.group(0))
                points.append({
                    "timestamp": timestamp,
                    "value": value,
                    "unit": "kWh",
                    "source": "legacy_html",
                })
            if points:
                break

        return {
            "meter_id": meter_id,
            "days": days,
            "points": points[:days],
        }

    def get_dashboard(self) -> dict[str, Any]:
        meter_payload = self.get_meters(page=1, page_size=50)
        meters = meter_payload["meters"]
        total = meter_payload["total"]
        active = sum(1 for meter in meters if str(meter.get("status") or "").lower() in {"active", "online", "healthy"})
        inactive = sum(1 for meter in meters if str(meter.get("status") or "").lower() in {"inactive", "offline", "error"})
        unknown = sum(1 for meter in meters if not meter.get("status"))

        return {
            "service": "Urja Meter Ops",
            "page_title": "Dashboard",
            "totals": {
                "total_meters": total,
                "active_meters": active,
                "inactive_meters": inactive,
                "unknown_status": unknown,
            },
            "latest_meters": meters[:5],
        }

    def get_home(self) -> dict[str, Any]:
        dashboard = self.get_dashboard()
        dashboard["page_title"] = "Home"
        return dashboard

    def get_history(self, limit: int = 20) -> dict[str, Any]:
        meter_payload = self.get_meters(page=1, page_size=max(5, min(limit, 50)))
        events = []
        for meter in meter_payload["meters"][:limit]:
            events.append(
                {
                    "meter_id": meter.get("meter_id"),
                    "timestamp": meter.get("dt") or "N/A",
                    "event_type": "meter_snapshot",
                    "status": meter.get("status"),
                    "details": f"Meter {meter.get('meter_id')} reported status {meter.get('status') or 'unknown'}.",
                }
            )

        if not events:
            events = [{
                "meter_id": None,
                "timestamp": "N/A",
                "event_type": "empty_state",
                "status": "no_data",
                "details": "No meter history is currently available from the legacy portal.",
            }]

        return {
            "service": "Urja Meter Ops",
            "page_title": "History",
            "events": events,
        }

    def get_hierarchy(self) -> dict[str, Any]:
        response = self._request("/transformers")
        if response.status_code >= 400:
            return {"hierarchy": []}

        soup = BeautifulSoup(response.text, "html.parser")
        nodes = []
        for item in soup.select("a[href]")[:10]:
            href = item.get("href", "")
            if href.startswith("/"):
                nodes.append({"name": item.get_text(" ", strip=True), "type": "node", "children": []})

        return {"hierarchy": nodes}

    @staticmethod
    def _first_match(soup: BeautifulSoup, patterns: list[str]) -> str | None:
        text = soup.get_text(" ", strip=True)
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None
