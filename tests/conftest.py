"""Shared fixtures and helpers for the Smogzilla test suite."""

from unittest.mock import AsyncMock

import httpx
import pytest
from telegram import Chat, Message, MessageEntity, Update, User


# --------------------------------------------------------------------- helpers


def make_record(sensor_id, timestamp, values):
    """Build one raw airrohr API record as returned by sensor.community."""
    return {
        "sensor": {"id": sensor_id},
        "timestamp": timestamp,
        "sensordatavalues": [
            {"value_type": vtype, "value": value} for vtype, value in values
        ],
    }


def json_response(status_code=200, payload=None):
    """An httpx.Response with a dummy request attached (needed by raise_for_status)."""
    return httpx.Response(
        status_code,
        json=payload if payload is not None else [],
        request=httpx.Request("GET", "http://test"),
    )


def patch_httpx_transport(monkeypatch, module, handler):
    """Route every httpx.AsyncClient created inside `module` through MockTransport."""
    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def factory(**kwargs):
        return original_client(**{**kwargs, "transport": transport})

    monkeypatch.setattr(module.httpx, "AsyncClient", factory)


def build_command_update(app, text, chat_id=42):
    """Construct a Telegram Update that looks like `/command args` from a chat."""
    command = text.split()[0].lstrip("/")
    entities = [
        MessageEntity(
            type=MessageEntity.BOT_COMMAND,
            offset=0,
            length=len("/" + command),
        )
    ]
    message = Message(
        message_id=1,
        date=None,
        chat=Chat(id=chat_id, type="private"),
        text=text,
        from_user=User(id=chat_id, first_name="tester", is_bot=False),
        entities=entities,
    )
    message.set_bot(app.bot)
    update = Update(update_id=1, message=message)
    update.set_bot(app.bot)
    return update


# --------------------------------------------------------------------- fixtures


@pytest.fixture
def bot_user():
    return User(id=123456, first_name="smogzilla", is_bot=True, username="smogzilla_bot")


@pytest.fixture
def no_retry_wait(monkeypatch):
    """Make tenacity retries instant so retry tests don't sleep."""
    from tenacity import wait_none

    import scrapers.sensor_community as sc

    monkeypatch.setattr(sc._fetch.retry, "wait", wait_none())
    return sc


@pytest.fixture
def fake_air_data():
    """One parsed reading per sensor, as fetch_by_area would return."""
    return [
        {"sensor_id": 1, "pm2.5": 8.4, "pm10": 19.2, "timestamp": "2026-06-02T08:00:00"},
        {"sensor_id": 2, "pm2.5": 21.0, "pm10": 40.3, "timestamp": "2026-06-02T08:00:00"},
        {"sensor_id": 3, "pm2.5": 10.5, "pm10": 27.0, "timestamp": "2026-06-02T07:59:00"},
        {"sensor_id": 4, "pm2.5": 9.0, "pm10": 25.0, "timestamp": "2026-06-02T07:58:00"},
    ]


@pytest.fixture
def air_app(bot_user):
    """A real Application (no network) wired like production, for update dispatch."""
    from bot import build_application

    app = build_application(token="123456:TESTTOKEN")
    object.__setattr__(app.bot, "_bot_user", bot_user)
    object.__setattr__(app.bot, "_initialized", True)
    object.__setattr__(app, "_initialized", True)
    return app


@pytest.fixture
def capture_replies(monkeypatch):
    """Patch Message.reply_text and return the AsyncMock capturing all replies."""
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr(Message, "reply_text", mock)
    return mock
