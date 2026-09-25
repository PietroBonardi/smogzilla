"""End-to-end tests: drive real Telegram Updates through the wired Application.

These use the application produced by bot.build_application (same handlers as
production) and feed it command updates, asserting on the outgoing messages.
Only the network boundary (Bot.send_message) is mocked.
"""

from unittest.mock import AsyncMock

import pytest

from tests.conftest import build_command_update, make_record

pytestmark = pytest.mark.e2e


def _capture_send_message(app):
    sent = AsyncMock(return_value=None)

    async def fake_send_message(chat_id, text, **kwargs):
        await sent(chat_id=chat_id, text=text, **kwargs)
        return None

    object.__setattr__(app.bot, "send_message", fake_send_message)
    return sent


async def test_start_command_end_to_end(air_app):
    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/start", chat_id=99)

    await air_app.process_update(update)

    assert sent.await_count == 1
    call = sent.await_args
    assert call.kwargs["chat_id"] == 99
    assert "SMOGZILLA" in call.kwargs["text"]


async def test_cities_command_end_to_end(air_app):
    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/cities", chat_id=7)

    await air_app.process_update(update)

    assert sent.await_count == 1
    assert "SMOGZILLA // CITIES" in sent.await_args.kwargs["text"]


async def test_air_command_end_to_end_with_mocked_api(air_app, monkeypatch, no_retry_wait):
    import scrapers.sensor_community as sc
    from tests.conftest import patch_httpx_transport, json_response

    def handler(request):
        return json_response(
            200,
            [make_record(1, "t1", [("P1", "9.0"), ("P2", "4.0")])],
        )

    patch_httpx_transport(monkeypatch, sc, handler)

    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/air milano", chat_id=5)

    await air_app.process_update(update)

    texts = [c.kwargs["text"] for c in sent.await_args_list]
    assert any("scanning MILANO" in t for t in texts)
    assert any("SMOGZILLA // MILANO" in t for t in texts)


async def test_air_unknown_city_end_to_end(air_app):
    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/air atlantis", chat_id=3)

    await air_app.process_update(update)

    assert sent.await_count == 1
    assert "not found" in sent.await_args.kwargs["text"]


async def test_air_missing_argument_end_to_end(air_app):
    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/air", chat_id=3)

    await air_app.process_update(update)

    assert sent.await_count == 1
    assert "missing argument" in sent.await_args.kwargs["text"]


async def test_unknown_command_produces_no_reply(air_app):
    sent = _capture_send_message(air_app)
    update = build_command_update(air_app, "/subscribe milano", chat_id=1)

    await air_app.process_update(update)

    assert sent.await_count == 0
