import json

import httpx
import pytest
import respx

from oura_stress import auth


@pytest.fixture
def keystore(monkeypatch):
    store = {
        ("oura_stress", "client_id"): "cid",
        ("oura_stress", "client_secret"): "sec",
        ("oura_stress", "tokens"): json.dumps(
            {"access_token": "a1", "refresh_token": "r1"}
        ),
    }
    monkeypatch.setattr(auth.keyring, "get_password", lambda s, k: store.get((s, k)))
    monkeypatch.setattr(
        auth.keyring, "set_password", lambda s, k, v: store.__setitem__((s, k), v)
    )
    return store


@respx.mock
def test_refresh_persists_rotated_refresh_token(keystore):
    respx.post(auth.TOKEN_URL).mock(
        return_value=httpx.Response(
            200, json={"access_token": "a2", "refresh_token": "r2"}
        )
    )
    assert auth.refresh_tokens() == "a2"
    assert json.loads(keystore[("oura_stress", "tokens")]) == {
        "access_token": "a2",
        "refresh_token": "r2",
    }


@respx.mock
def test_failed_refresh_raises_and_keeps_tokens(keystore):
    before = keystore[("oura_stress", "tokens")]
    respx.post(auth.TOKEN_URL).mock(return_value=httpx.Response(400))
    with pytest.raises(auth.AuthError):
        auth.refresh_tokens()
    assert keystore[("oura_stress", "tokens")] == before


def test_missing_tokens_raises(keystore):
    del keystore[("oura_stress", "tokens")]
    with pytest.raises(auth.AuthError):
        auth.load_tokens()
