from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query

from .client import UrjaPortalClient
from .config import settings
from .models import (
    AuthLoginResponse,
    DashboardSummary,
    HistoryResponse,
    HierarchyResponse,
    LoginRequest,
    LogoutResponse,
    MeterConsumptionResponse,
    MeterDetailResponse,
    MeterListResponse,
)

app = FastAPI(
    title="Flock Energy - Urja Meter Ops API",
    version="1.0.0",
    description=(
        "A clean REST API wrapper over the legacy Urja Meter Ops web portal. "
        "It handles session authentication, HTML parsing, and normalized JSON output."
    ),
)

portal_client = UrjaPortalClient(base_url=settings.base_url, username=settings.username, password=settings.password)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "flock-energy-api", "base_url": settings.base_url}


@app.post("/api/v1/auth/login", response_model=AuthLoginResponse, tags=["auth"])
def login(payload: LoginRequest) -> AuthLoginResponse:
    try:
        result = portal_client.login(payload.email, payload.password)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy login failed: {exc}") from exc

    if not result["authenticated"]:
        raise HTTPException(status_code=401, detail="Unable to authenticate with the legacy portal.")

    return AuthLoginResponse(**result, service="Urja Meter Ops")


@app.post("/api/v1/auth/logout", response_model=LogoutResponse, tags=["auth"])
def logout() -> LogoutResponse:
    try:
        result = portal_client.logout()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy logout failed: {exc}") from exc

    return LogoutResponse(**result, service="Urja Meter Ops")


@app.get("/api/v1/dashboard", response_model=DashboardSummary, tags=["dashboard"])
def dashboard() -> DashboardSummary:
    try:
        payload = portal_client.get_dashboard()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy dashboard request failed: {exc}") from exc

    return DashboardSummary(**payload)


@app.get("/api/v1/home", response_model=DashboardSummary, tags=["dashboard"])
def home() -> DashboardSummary:
    try:
        payload = portal_client.get_home()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy home request failed: {exc}") from exc

    return DashboardSummary(**payload)


@app.get("/api/v1/history", response_model=HistoryResponse, tags=["history"])
def get_history(limit: Annotated[int, Query(ge=1, le=100)] = 20) -> HistoryResponse:
    try:
        payload = portal_client.get_history(limit=limit)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy history request failed: {exc}") from exc

    return HistoryResponse(**payload)


@app.get("/api/v1/meters", response_model=MeterListResponse, tags=["meters"])
def list_meters(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 25,
    query: str | None = None,
) -> MeterListResponse:
    try:
        payload = portal_client.get_meters(page=page, page_size=page_size, query=query)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy request failed: {exc}") from exc

    return MeterListResponse(
        meters=payload["meters"],
        total=payload["total"],
        page=payload["page"],
        page_size=payload["page_size"],
    )


@app.get("/api/v1/meters/{meter_id}", response_model=MeterDetailResponse, tags=["meters"])
def get_meter_detail(meter_id: str) -> MeterDetailResponse:
    try:
        payload = portal_client.get_meter_detail(meter_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy request failed: {exc}") from exc

    return MeterDetailResponse(**payload)


@app.get("/api/v1/meters/{meter_id}/consumption", response_model=MeterConsumptionResponse, tags=["meters"])
def get_meter_consumption(meter_id: str, days: Annotated[int, Query(ge=1, le=365)] = 30) -> MeterConsumptionResponse:
    try:
        payload = portal_client.get_meter_consumption(meter_id, days=days)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy request failed: {exc}") from exc

    return MeterConsumptionResponse(**payload)


@app.get("/api/v1/hierarchy", response_model=HierarchyResponse, tags=["hierarchy"])
def get_hierarchy() -> HierarchyResponse:
    try:
        payload = portal_client.get_hierarchy()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Legacy request failed: {exc}") from exc

    return HierarchyResponse(**payload)
