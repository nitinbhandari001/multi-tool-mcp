"""FastMCP server entry point for multi-tool-mcp."""
import structlog
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from .config import get_settings, configure_logging
from .services import create_services
from .tools import set_container, register_all_tools

log = structlog.get_logger(__name__)

settings = get_settings()

# JWT auth — only enabled when jwt_secret is configured
auth = None
if settings.jwt_secret:
    try:
        from fastmcp.server.auth.providers.jwt import JWTVerifier
        auth = JWTVerifier(
            public_key=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    except Exception as e:
        log.warning("jwt_auth_setup_failed", error=str(e))


@lifespan
async def server_lifespan(server: FastMCP):
    """Startup: create services. Shutdown: close connections."""
    configure_logging(settings.log_level)
    container = await create_services(settings)
    set_container(container)
    log.info("server_ready", tools=18)
    yield {}
    await container.close()
    log.info("server_shutdown")


mcp = FastMCP(
    "Multi-Tool MCP Server",
    instructions=(
        "Enterprise MCP server with RBAC, audit logging, and secure multi-tool access "
        "to databases, APIs, and filesystem."
    ),
    auth=auth,
    lifespan=server_lifespan,
)

register_all_tools(mcp)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
