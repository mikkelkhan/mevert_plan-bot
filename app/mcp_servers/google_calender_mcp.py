from mcp.server import MCPServer
from app.auth.google_auth import get_calendar_service
from datetime import datetime, timezone
mcp = MCPServer("Google Calender Server")

@mcp.tool()
def list_calendars() -> list[dict]:
    """List available Google Calendars."""

    calendar = get_calendar_service()

    results = calendar.calendarList().list(
        maxResults=50
    ).execute()

    return [
        {
            "calendar_id": item["id"],
            "summary": item.get("summary"),
            "primary": item.get("primary", False),
            "time_zone": item.get("timeZone"),
        }
        for item in results.get("items", [])
    ]


@mcp.tool()
def get_upcoming_events(
    max_results: int = 10,
    calendar_id: str = "primary",
) -> list[dict]:
    """Get upcoming events from Google Calendar."""

    if not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50")

    calendar = get_calendar_service()

    results = calendar.events().list(
        calendarId=calendar_id,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
        timeMin=datetime.now(timezone.utc).isoformat(),
    ).execute()

    return [
        {
            "event_id": event["id"],
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end"),
            "location": event.get("location"),
            "description": event.get("description"),
        }
        for event in results.get("items", [])
    ]

if __name__ == "__main__":
    mcp.run()