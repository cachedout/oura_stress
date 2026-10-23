# oura_stress design

## Context
Personal tool: notify on macOS when Oura-measured daytime stress is building so a
restorative break can be taken. Triggers of the stress are unknown; finding them is out of scope.

## Decisions
- Trigger: growth of `stress_high` (seconds) in `daily_stress` between polls.
- Signal: macOS notification (osascript) with a rotating suggested action.
- Python, uv, Typer, httpx, keyring; run by a LaunchAgent every 15 min.
- Defaults (adjustable in config): weekdays 09:00-18:00, threshold 600 s, cooldown 45 min.

## Anti-goals
- Repeated alerts for one episode or alerts outside work hours.
- Silent breakage: auth failure notifies once.
- Treating stale data as new.

## Constraints
- Oura has no intraday stress series; data lags hours at times.
- OAuth2 only (PATs removed); refresh tokens are single-use and are re-persisted on every refresh.

## Open
- Whether `stress_high` updates frequently enough intraday (verify with `check --log-raw`).
