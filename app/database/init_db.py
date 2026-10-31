from app.database.connection import engine
from app.database.base import Base

# Import models so SQLAlchemy registers them.
from app.database.models import OAuthToken


def initialize_database() -> None:
    """Create database tables if they do not exist."""

    Base.metadata.create_all(bind=engine)

    print("Database tables initialized successfully.")


if __name__ == "__main__":
    initialize_database()