from mcp.server import MCPServer
from app.auth.google_auth import get_gmail_service

mcp = MCPServer("Google Gmail Server")


@mcp.tool()
def search_emails(query,max_result=10):
    """Search Gmail messages using a Gmail search query."""
    if not 1 <= max_result <= 50:
        raise ValueError("max_result must be between 1 and 50")

    gmail = get_gmail_service()
    result = gmail.users().messages().list(userId="me",q=query,maxResults=max_result).execute()
    result_final = []
    for i in result.get("messages",[]):
        email_data = { "message_id": i["id"], "thread_id": i["threadId"]}
        result_final.append(email_data)
    return result_final


@mcp.tool()
def get_email(message_id: str) -> dict:
    """Get email metadata and snippet."""

    gmail = get_gmail_service()

    message = gmail.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "To", "Subject", "Date"],
    ).execute()

    headers = message.get("payload", {}).get("headers", [])

    email_data = {
        h["name"].lower(): h["value"]
        for h in headers
    }

    return {
        "message_id": message["id"],
        "thread_id": message["threadId"],
        "from": email_data.get("from"),
        "to": email_data.get("to"),
        "subject": email_data.get("subject"),
        "date": email_data.get("date"),
        "snippet": message.get("snippet"),
    }


@mcp.tool()
def get_unread_emails(max_results: int = 10) -> list[dict]:
    """Get unread emails."""

    return search_emails("is:unread", max_results)




if __name__ == "__main__":
    mcp.run()