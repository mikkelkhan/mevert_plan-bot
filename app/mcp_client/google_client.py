
import sys
import os

from langchain_mcp_adapters.client import MultiServerMCPClient


REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "GOOGLE_ACCOUNT_EMAIL",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "FERNET_KEY",
    "GROQ_API_KEY",
    "MODEL_NAME",
    "TELEGRAM_BOT_TOKEN",
    "WEBHOOK_SECRET_TOKEN",
]

MCP_ENV = {
    key: os.environ[key]
    for key in REQUIRED_ENV_VARS
    if key in os.environ
}

MCP_SERVERS = {
    "gmail": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.google_gmail_mcp"],
        "env": MCP_ENV,
    },
    "calendar": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.google_calender_mcp"],
        "env": MCP_ENV,
    },
}


def get_mcp_server():
    return MultiServerMCPClient(MCP_SERVERS)
