from datetime import datetime, timedelta

from oura_stress.config import Config
from oura_stress.monitor import State, decide

CFG = Config()  # threshold 600s, cooldown 45 min, window 09:00-18:00 weekdays

MON = datetime(2026, 10, 19, 10, 0)  # a Monday


def at(minutes: int, base: datetime = MON) -> datetime:
    return base + timedelta(minutes=minutes)


def test_outside_window_does_nothing():
    state = State(day="2026-10-19", stress_high=0)
    new, alert = decide(state, 5000, datetime(2026, 10, 19, 8, 59), CFG)
    assert new == state and alert is None
    new, alert = decide(state, 5000, datetime(2026, 10, 19, 18, 0), CFG)
    assert new == state and alert is None


def test_weekend_does_nothing():
    state = State(day="2026-10-24", stress_high=0)
    sat = datetime(2026, 10, 24, 10, 0)
    new, alert = decide(state, 5000, sat, CFG)
    assert new == state and alert is None


def test_no_reading_does_nothing():
    state = State()
    new, alert = decide(state, None, MON, CFG)
    assert new == state and alert is None


def test_first_reading_of_day_sets_baseline_without_alert():
    new, alert = decide(State(), 7200, MON, CFG)
    assert alert is None
    assert new.day == "2026-10-19" and new.stress_high == 7200


def test_day_rollover_rebaselines():
    state = State(day="2026-10-16", stress_high=100)
    new, alert = decide(state, 9000, MON, CFG)
    assert alert is None and new.stress_high == 9000 and new.day == "2026-10-19"


def test_negative_delta_rebaselines_without_alert():
    state = State(day="2026-10-19", stress_high=3000)
    new, alert = decide(state, 2000, MON, CFG)
    assert alert is None and new.stress_high == 2000


def test_below_threshold_updates_baseline_without_alert():
    state = State(day="2026-10-19", stress_high=1000)
    new, alert = decide(state, 1599, MON, CFG)
    assert alert is None and new.stress_high == 1599


def test_threshold_boundary_alerts():
    state = State(day="2026-10-19", stress_high=1000)
    new, alert = decide(state, 1600, MON, CFG)
    assert alert is not None
    assert new.stress_high == 1600 and new.last_alert_at == MON.isoformat()


def test_cooldown_suppresses_alert_but_updates_baseline():
    state = State(
        day="2026-10-19", stress_high=1000, last_alert_at=at(-10).isoformat()
    )
    new, alert = decide(state, 3000, MON, CFG)
    assert alert is None
    assert new.stress_high == 3000 and new.last_alert_at == state.last_alert_at


def test_alert_after_cooldown_elapsed():
    state = State(
        day="2026-10-19", stress_high=1000, last_alert_at=at(-45).isoformat()
    )
    _, alert = decide(state, 3000, MON, CFG)
    assert alert is not None


def test_messages_rotate_without_immediate_repeat():
    cfg = Config(messages=["a", "b", "c"])
    state = State(day="2026-10-19", stress_high=0, message_index=0)
    seen = []
    for i in range(4):
        state, alert = decide(state, (i + 1) * 1000, at(i * 60), cfg)
        seen.append(alert)
    assert seen == ["b", "c", "a", "b"]
