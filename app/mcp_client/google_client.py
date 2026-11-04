import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_SERVERS = {
    "gmail": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.google_gmail_mcp"],
    },
    "calendar": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.google_calender_mcp"],
    },
}


def get_mcp_server():
    return MultiServerMCPClient(MCP_SERVERS)