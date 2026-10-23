import json
from dataclasses import asdict
from pathlib import Path

from oura_stress.monitor import State

STATE_DIR = Path.home() / ".local" / "state" / "oura_stress"
STATE_PATH = STATE_DIR / "state.json"


def load_state(path: Path = STATE_PATH) -> State:
    if not path.exists():
        return State()
    try:
        return State(**json.loads(path.read_text()))
    except (json.JSONDecodeError, TypeError):
        return State()


def save_state(state: State, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(state)))
    tmp.replace(path)
