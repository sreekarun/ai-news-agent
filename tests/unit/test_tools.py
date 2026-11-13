import datetime

from ai_news_agent.agent import get_current_date


def test_get_current_date_returns_iso_date() -> None:
    result = get_current_date()
    assert result["status"] == "success"
    datetime.date.fromisoformat(result["date"])
    assert result["timezone"]
