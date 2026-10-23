import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "oura_stress" / "config.toml"

DEFAULT_MESSAGES = [
    "Stress is building. Take 2 minutes of slow breathing (4 in, 6 out).",
    "Stress is building. Step away from the screen and walk for 5 minutes.",
    "Stress is building. Stand up, drop the shoulders, look out a window.",
]


@dataclass(frozen=True)
class Config:
    poll_minutes: int = 15
    window_start_hour: int = 9
    window_end_hour: int = 18
    weekdays_only: bool = True
    threshold_seconds: int = 600
    cooldown_minutes: int = 45
    messages: list[str] = field(default_factory=lambda: list(DEFAULT_MESSAGES))


def load_config(path: Path = CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text())
    known = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in known})
