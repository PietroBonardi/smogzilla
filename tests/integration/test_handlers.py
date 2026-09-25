"""Integration tests for handlers wired to the scraper and formatter.

Mock only the network boundary; let the real handler, scraper parsing, and
formatter run together.
"""

from unittest.mock import AsyncMock

import pytest
from telegram import Chat, Message, Update, User

from handlers.air import air
from handlers.cities import cities
from handlers.start import start
from tests.conftest import make_record
from utils.city_data import CITIES

pytestmark = pytest.mark.integration


def _update(text, chat_id=42):
    message = Message(
        message_id=1,
        date=None,
        chat=Chat(id=chat_id, type="private"),
        text=text,
        from_user=User(id=chat_id, first_name="tester", is_bot=False),
    )
    return Update(update_id=1, message=message)


class _Context:
    def __init__(self, args=None):
        self.args = args or []


async def test_air_handler_renders_report_from_parsed_readings(monkeypatch):
    records = [make_record(1, "t1", [("P1", "9.0"), ("P2", "4.0")])]
    parsed = [
        {"sensor_id": 1, "pm2.5": 4.0, "pm10": 9.0, "timestamp": "t1"},
    ]

    import handlers.air as air_module

    async def fake_fetch(lat, lng, radius_km=None):
        assert (lat, lng) == (CITIES["milano"].lat, CITIES["milano"].lng)
        return parsed

    monkeypatch.setattr(air_module, "fetch_by_area", fake_fetch)

    reply = AsyncMock()
    monkeypatch.setattr(Message, "reply_text", reply)

    await air(_update("/air milano"), _Context(args=["milano"]))

    assert reply.await_count == 2
    report = reply.await_args_list[-1].args[0]
    assert "SMOGZILLA // MILANO" in report
    assert "sensors  1 active" in report
    assert "4.0" in report


async def test_air_handler_no_data_path(monkeypatch):
    import handlers.air as air_module

    async def fake_fetch(lat, lng, radius_km=None):
        return []

    monkeypatch.setattr(air_module, "fetch_by_area", fake_fetch)
    reply = AsyncMock()
    monkeypatch.setattr(Message, "reply_text", reply)

    await air(_update("/air milano"), _Context(args=["milano"]))
    assert reply.await_count == 2
    assert "no sensor data" in reply.await_args_list[-1].args[0]


async def test_cities_handler_lists_all_cities(capture_replies):
    await cities(_update("/cities"), _Context())
    text = capture_replies.await_args.args[0]
    assert "SMOGZILLA // CITIES" in text
    for city in CITIES.values():
        assert city.name in text


async def test_start_handler_lists_only_supported_commands(capture_replies):
    await start(_update("/start"), _Context())
    text = capture_replies.await_args.args[0]
    assert "/air" in text
    assert "/cities" in text
    assert "/subscribe" not in text
    assert "/subscriptions" not in text
