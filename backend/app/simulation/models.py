"""Data models for the simulated system."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

ServiceStatus = Literal["healthy", "warning", "down"]


class SystemPhase(StrEnum):
    HEALTHY = "healthy"
    FAULTED = "faulted"
    RECOVERED = "recovered"


class MetricPoint(BaseModel):
    time: str  # "HH:MM" simulation clock
    requests_per_min: int
    error_rate_pct: float
    latency_p95_ms: int


class LogEntry(BaseModel):
    time: str
    severity: Literal["INFO", "WARNING", "ERROR"]
    message: str


class Revision(BaseModel):
    revision: str
    deployed_at: str
    status: Literal["serving", "retired"]
    traffic_pct: int
    stable: bool
    rollback_available: bool


class ServiceInfo(BaseModel):
    name: str
    kind: Literal["client", "load_balancer", "application", "database"]
    label: str
    status: ServiceStatus
