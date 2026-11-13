from mcp.server.fastmcp import FastMCP
from app.auth.google_auth import get_gmail_service
import logging
import sys

mcp = FastMCP("Google Gmail Server")

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@mcp.tool()
def search_emails(query: str, max_result: int = 10) -> list[dict]:
    """Search Gmail messages using a Gmail search query."""

    logger.info("search_emails started")
    logger.info("Query: %s", query)

    if not 1 <= max_result <= 50:
        raise ValueError("max_result must be between 1 and 50")

    logger.info("Loading Gmail service...")

    gmail = get_gmail_service()

    logger.info("Gmail service created successfully")

    logger.info("Calling Gmail API...")

    result = gmail.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_result
    ).execute()

    logger.info("Gmail API response received")

    result_final = []

    for i in result.get("messages", []):
        email_data = {
            "message_id": i["id"],
            "thread_id": i["threadId"]
        }
        result_final.append(email_data)

    logger.info("Returning %s emails", len(result_final))

    return result_final



@mcp.tool()
def get_email(message_id: str) -> dict:
    """Get email metadata and snippet."""

    logger.info("get_email started")
    logger.info("Message ID: %s", message_id)

    try:
        logger.info("Creating Gmail service")

        gmail = get_gmail_service()

        logger.info("Gmail service created")

        logger.info("Calling Gmail API")

        message = gmail.users().messages().get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute(num_retries=0)

        logger.info("Gmail API response received")

        headers = message.get("payload", {}).get("headers", [])

        email_data = {
            h["name"].lower(): h["value"]
            for h in headers
        }

        result = {
            "message_id": message["id"],
            "thread_id": message["threadId"],
            "from": email_data.get("from"),
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "date": email_data.get("date"),
            "snippet": message.get("snippet"),
        }

        logger.info("get_email completed successfully")

        return result

    except Exception:
        logger.exception("get_email failed")
        raise


@mcp.tool()
def get_unread_emails(max_results: int = 10) -> list[dict]:
    """Get unread emails with sender, subject, date and snippet."""

    logger.info("get_unread_emails started")

    if not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50")

    try:
        gmail = get_gmail_service()

        result = gmail.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=max_results
        ).execute(num_retries=0)

        emails = []

        for item in result.get("messages", []):
            message = gmail.users().messages().get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"]
            ).execute(num_retries=0)

            headers = message.get("payload", {}).get("headers", [])

            email_data = {
                h["name"].lower(): h["value"]
                for h in headers
            }

            emails.append({
                "message_id": message["id"],
                "thread_id": message["threadId"],
                "from": email_data.get("from"),
                "to": email_data.get("to"),
                "subject": email_data.get("subject"),
                "date": email_data.get("date"),
                "snippet": message.get("snippet")
            })

        logger.info("Total unread emails fetched: %s", len(emails))
        return emails

    except Exception:
        logger.exception("get_unread_emails failed")



if __name__ == "__main__":
    mcp.run()