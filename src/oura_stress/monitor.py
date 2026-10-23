from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from oura_stress.config import Config


@dataclass(frozen=True)
class State:
    day: str | None = None
    stress_high: int | None = None
    last_alert_at: str | None = None
    message_index: int = -1
    auth_error_notified: bool = False


def in_window(now: datetime, cfg: Config) -> bool:
    if cfg.weekdays_only and now.weekday() >= 5:
        return False
    return cfg.window_start_hour <= now.hour < cfg.window_end_hour


def decide(
    state: State, stress_high: int | None, now: datetime, cfg: Config
) -> tuple[State, str | None]:
    """Return the next state and the alert message, if any."""
    if not in_window(now, cfg) or stress_high is None:
        return state, None

    today = now.date().isoformat()
    if state.day != today or state.stress_high is None:
        return replace(state, day=today, stress_high=stress_high), None

    delta = stress_high - state.stress_high
    new = replace(state, stress_high=stress_high)
    if delta < cfg.threshold_seconds:
        return new, None

    if state.last_alert_at is not None:
        elapsed = now - datetime.fromisoformat(state.last_alert_at)
        if elapsed < timedelta(minutes=cfg.cooldown_minutes):
            return new, None

    index = (state.message_index + 1) % len(cfg.messages)
    new = replace(new, last_alert_at=now.isoformat(), message_index=index)
    return new, cfg.messages[index]
