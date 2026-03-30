from core.config import get_settings
from services.calendar.provider import authenticate_google_calendar


def main() -> None:
    settings = get_settings()
    token_path = authenticate_google_calendar(settings)
    print(
        f"Google Calendar authentication complete. Token saved to {token_path}.",
    )


if __name__ == "__main__":
    main()
