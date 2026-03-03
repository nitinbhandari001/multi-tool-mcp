"""Tools registry — container accessor and tool registration."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services import ServiceContainer

_container: "ServiceContainer | None" = None


def get_container() -> "ServiceContainer | None":
    return _container


def set_container(container: "ServiceContainer") -> None:
    global _container
    _container = container


def register_all_tools(mcp) -> None:
    from .db_tools import register as register_db
    from .api_tools import register as register_api
    from .fs_tools import register as register_fs
    from .admin_tools import register as register_admin

    register_db(mcp)
    register_api(mcp)
    register_fs(mcp)
    register_admin(mcp)
