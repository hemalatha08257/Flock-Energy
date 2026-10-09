from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(default="operator@urja.local")
    password: str = Field(default="urja-ops-2026")


class AuthLoginResponse(BaseModel):
    authenticated: bool
    status_code: int
    token_present: bool
    service: str = "Urja Meter Ops"


class LogoutResponse(BaseModel):
    logged_out: bool
    status_code: int
    redirected_to: str | None = None
    service: str = "Urja Meter Ops"


class MeterSummary(BaseModel):
    meter_id: str
    serial_number: str | None = None
    make: str | None = None
    phase: str | None = None
    status: str | None = None
    dt: str | None = None
    source: str = "legacy_html"


class MeterListResponse(BaseModel):
    meters: list[MeterSummary]
    total: int
    page: int
    page_size: int


class MeterDetailResponse(BaseModel):
    meter_id: str
    meter_number: str | None = None
    serial_number: str | None = None
    make: str | None = None
    phase: str | None = None
    status: str | None = None
    last_updated: str | None = None
    raw_html_snippet: str | None = None


class ConsumptionPoint(BaseModel):
    timestamp: str | None = None
    value: float | None = None
    unit: str = "kWh"
    source: str = "legacy_html"


class MeterConsumptionResponse(BaseModel):
    meter_id: str
    days: int
    points: list[ConsumptionPoint]


class HierarchyNode(BaseModel):
    name: str
    type: str
    children: list["HierarchyNode"] = Field(default_factory=list)


class DashboardTotals(BaseModel):
    total_meters: int = 0
    active_meters: int = 0
    inactive_meters: int = 0
    unknown_status: int = 0


class DashboardSummary(BaseModel):
    service: str = "Urja Meter Ops"
    page_title: str = "Dashboard"
    totals: DashboardTotals = Field(default_factory=DashboardTotals)
    latest_meters: list[MeterSummary] = Field(default_factory=list)


class HistoryEvent(BaseModel):
    meter_id: str | None = None
    timestamp: str | None = None
    event_type: str = "meter_snapshot"
    status: str | None = None
    details: str | None = None


class HistoryResponse(BaseModel):
    service: str = "Urja Meter Ops"
    page_title: str = "History"
    events: list[HistoryEvent] = Field(default_factory=list)


class HierarchyResponse(BaseModel):
    hierarchy: list[HierarchyNode]
