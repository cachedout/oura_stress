import time
from datetime import date

import httpx

from oura_stress import auth

API = "https://api.ouraring.com"


def get_daily_stress(day: date, http: httpx.Client | None = None) -> dict | None:
    """Return the daily_stress document for `day`, or None if not yet available."""
    http = http or httpx.Client(timeout=30)
    token = auth.load_tokens()["access_token"]
    refreshed = False
    for _ in range(3):
        resp = http.get(
            f"{API}/v2/usercollection/daily_stress",
            params={"start_date": day.isoformat(), "end_date": day.isoformat()},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 401 and not refreshed:
            token = auth.refresh_tokens(http)
            refreshed = True
            continue
        if resp.status_code == 429:
            time.sleep(min(int(resp.headers.get("Retry-After", "30")), 60))
            continue
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data[-1] if data else None
    raise httpx.HTTPError("daily_stress request failed after retries")
