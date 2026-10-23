# oura_stress

Polls the Oura `daily_stress` summary and posts a macOS notification when
stressed time has grown past a threshold since the previous poll.

## Setup

1. Register an app at https://developer.ouraring.com with redirect URI
   `http://localhost:8765/callback` and the `daily` and `stress` scopes.
2. `uv sync`
3. `uv run oura-stress login` (prompts for client id and secret, opens the browser;
   credentials and tokens are stored in the macOS Keychain).
4. Optional: copy `config.example.toml` to `~/.config/oura_stress/config.toml`.
5. `uv run oura-stress check --dry-run --log-raw` to confirm data flows.
6. `uv run oura-stress install-agent` to run every `poll_minutes`.

## Commands

`login`, `check [--dry-run] [--log-raw] [--force-alert]`, `status`,
`install-agent`, `uninstall-agent`.

State: `~/.local/state/oura_stress/` (`state.json`, `agent.log`, `raw.jsonl`).

## Caveat

Oura exposes only a running daily total, and data reaches the API with a lag of
minutes to hours. Run `check --log-raw` through a workday to confirm that
`stress_high` updates intraday before relying on alerts.
