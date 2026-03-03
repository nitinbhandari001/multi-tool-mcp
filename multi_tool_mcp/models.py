"""Pydantic v2 frozen models for multi-tool-mcp."""

from pydantic import BaseModel, ConfigDict


class QueryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    columns: list[str]
    rows: list[list]
    row_count: int


class ColumnInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    data_type: str
    nullable: bool
    default: str | None


class TableInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    schema_name: str
    columns: list[ColumnInfo]


class FileEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    path: str
    is_dir: bool
    size: int | None
    modified: str | None


class APIResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status_code: int
    headers: dict
    body: str
    url: str


class AuditEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: str
    user: str
    role: str
    tool: str
    resource: str
    operation: str
    duration_ms: float
    success: bool
    detail: str | None
