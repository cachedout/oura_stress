import json
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import keyring

SERVICE = "oura_stress"
AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
REDIRECT_URI = "http://localhost:8765/callback"
SCOPES = "daily stress"


class AuthError(Exception):
    pass


def save_app_credentials(client_id: str, client_secret: str) -> None:
    keyring.set_password(SERVICE, "client_id", client_id)
    keyring.set_password(SERVICE, "client_secret", client_secret)


def _app_credentials() -> tuple[str, str]:
    cid = keyring.get_password(SERVICE, "client_id")
    secret = keyring.get_password(SERVICE, "client_secret")
    if not cid or not secret:
        raise AuthError("No Oura app credentials stored; run `oura-stress login`.")
    return cid, secret


def _store_tokens(payload: dict) -> None:
    # Refresh tokens are single-use: always persist the newest pair.
    keyring.set_password(
        SERVICE,
        "tokens",
        json.dumps(
            {
                "access_token": payload["access_token"],
                "refresh_token": payload["refresh_token"],
            }
        ),
    )


def load_tokens() -> dict:
    raw = keyring.get_password(SERVICE, "tokens")
    if not raw:
        raise AuthError("Not logged in; run `oura-stress login`.")
    return json.loads(raw)


def refresh_tokens(http: httpx.Client | None = None) -> str:
    """Exchange the stored refresh token for a new pair; return the access token."""
    cid, secret = _app_credentials()
    tokens = load_tokens()
    http = http or httpx.Client()
    resp = http.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": cid,
            "client_secret": secret,
        },
    )
    if resp.status_code != 200:
        raise AuthError(f"Token refresh failed ({resp.status_code}).")
    payload = resp.json()
    _store_tokens(payload)
    return payload["access_token"]


def login(http: httpx.Client | None = None) -> None:
    """Run the authorization-code flow via a one-shot local callback server."""
    cid, secret = _app_credentials()
    http = http or httpx.Client()
    state = secrets.token_urlsafe(16)
    result: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            query = parse_qs(urlparse(self.path).query)
            result["code"] = query.get("code", [None])[0]
            result["state"] = query.get("state", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Login complete. This tab can be closed.")

        def log_message(self, *args):
            pass

    url = AUTHORIZE_URL + "?" + urlencode(
        {
            "client_id": cid,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
        }
    )
    server = HTTPServer(("localhost", 8765), Handler)
    webbrowser.open(url)
    server.handle_request()
    server.server_close()

    if not result.get("code") or result.get("state") != state:
        raise AuthError("Authorization callback missing code or state mismatch.")
    resp = http.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": cid,
            "client_secret": secret,
        },
    )
    if resp.status_code != 200:
        raise AuthError(f"Code exchange failed ({resp.status_code}).")
    _store_tokens(resp.json())
