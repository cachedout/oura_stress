from datetime import date

import httpx
import respx

from oura_stress import client


def _patch_tokens(monkeypatch, store):
    monkeypatch.setattr(client.auth, "load_tokens", lambda: dict(store))

    def fake_refresh(http=None):
        store["access_token"] = "new"
        return "new"

    monkeypatch.setattr(client.auth, "refresh_tokens", fake_refresh)


@respx.mock
def test_returns_latest_document(monkeypatch):
    _patch_tokens(monkeypatch, {"access_token": "t", "refresh_token": "r"})
    respx.get(f"{client.API}/v2/usercollection/daily_stress").mock(
        return_value=httpx.Response(200, json={"data": [{"stress_high": 1200}]})
    )
    assert client.get_daily_stress(date(2026, 10, 19))["stress_high"] == 1200


@respx.mock
def test_empty_data_returns_none(monkeypatch):
    _patch_tokens(monkeypatch, {"access_token": "t", "refresh_token": "r"})
    respx.get(f"{client.API}/v2/usercollection/daily_stress").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    assert client.get_daily_stress(date(2026, 10, 19)) is None


@respx.mock
def test_refreshes_once_on_401(monkeypatch):
    _patch_tokens(monkeypatch, {"access_token": "old", "refresh_token": "r"})
    route = respx.get(f"{client.API}/v2/usercollection/daily_stress").mock(
        side_effect=[
            httpx.Response(401),
            httpx.Response(200, json={"data": [{"stress_high": 5}]}),
        ]
    )
    assert client.get_daily_stress(date(2026, 10, 19))["stress_high"] == 5
    assert route.calls.last.request.headers["authorization"] == "Bearer new"
