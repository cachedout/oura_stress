# Privacy Policy

Last updated: 2026-10-23

oura_stress is a self-hosted tool. It runs on the computer of the person who installs it
(the "user") and has no server operated by the developer. This policy describes what the
tool does with data.

## Data accessed

With the user's authorization through Oura's OAuth flow, the tool requests the `daily` and `stress`
scopes and reads the user's Oura `daily_stress` summary (time spent in stressed and
restored states for the current day).

## Data storage

- OAuth credentials and tokens are stored in the user's macOS Keychain.
- A small state file on the user's computer (`~/.local/state/oura_stress/`) holds the
  latest stress total, the date, and the time of the last notification.
- If the user enables the optional `--log-raw` flag, raw API responses are appended to a
  local file in the same directory.

All of this stays on the user's computer.

## Data sharing

The developer does not receive, collect, sell, or share any user data. Data is
transmitted only between the user's computer and Oura's API. No analytics, advertising,
or third-party services are used.

## Retention and deletion

Data is kept until the user deletes it. To remove everything: run
`oura-stress uninstall-agent`, delete `~/.local/state/oura_stress/`, remove the
`oura_stress` entries from the macOS Keychain, and revoke the app's access in the Oura
account settings.

## Children

The tool is not directed at children.

## Changes and contact

Changes to this policy are published in the project repository. Questions can be raised
as issues at <https://github.com/cachedout/oura_stress/issues>.
