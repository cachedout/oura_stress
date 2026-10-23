import json
import plistlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import typer

from oura_stress import auth, client
from oura_stress.config import load_config
from oura_stress.monitor import State, decide
from oura_stress.notify import notify
from oura_stress.state import STATE_DIR, load_state, save_state

app = typer.Typer(no_args_is_help=True, help="Notify when Oura daytime stress is building.")

LABEL = "com.mikeplace.oura-stress"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
RAW_LOG = STATE_DIR / "raw.jsonl"


@app.command()
def login(
    client_id: str = typer.Option(..., prompt=True),
    client_secret: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    """Store Oura app credentials and run the browser authorization flow."""
    auth.save_app_credentials(client_id, client_secret)
    auth.login()
    typer.echo("Logged in.")


@app.command()
def check(
    dry_run: bool = typer.Option(False, help="Do not notify or save state."),
    log_raw: bool = typer.Option(False, help="Append the raw API response to raw.jsonl."),
    force_alert: bool = typer.Option(False, help="Send a test notification and exit."),
) -> None:
    """Poll Oura once and notify if stress has grown past the threshold."""
    cfg = load_config()
    if force_alert:
        notify(cfg.messages[0])
        return

    now = datetime.now()
    state = load_state()
    try:
        doc = client.get_daily_stress(now.date())
    except auth.AuthError as exc:
        if not state.auth_error_notified and not dry_run:
            notify("Oura login expired. Run `oura-stress login`.")
            save_state(State(**{**state.__dict__, "auth_error_notified": True}))
        typer.echo(f"auth error: {exc}", err=True)
        raise typer.Exit(1)

    if log_raw:
        RAW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with RAW_LOG.open("a") as fh:
            fh.write(json.dumps({"at": now.isoformat(), "doc": doc}) + "\n")

    stress_high = doc.get("stress_high") if doc else None
    new, message = decide(state, stress_high, now, cfg)
    if state.auth_error_notified:
        new = State(**{**new.__dict__, "auth_error_notified": False})
    typer.echo(f"stress_high={stress_high} baseline={state.stress_high} alert={bool(message)}")
    if dry_run:
        return
    save_state(new)
    if message:
        notify(message)


@app.command()
def status() -> None:
    """Show the stored baseline and last alert, plus today's Oura summary."""
    state = load_state()
    doc = client.get_daily_stress(datetime.now().date())
    typer.echo(f"baseline stress_high: {state.stress_high} (day {state.day})")
    typer.echo(f"last alert: {state.last_alert_at}")
    if doc:
        stressed = (doc.get("stress_high") or 0) // 60
        restored = (doc.get("recovery_high") or 0) // 60
        typer.echo(f"today: {stressed} min stressed, {restored} min restored ({doc.get('day_summary')})")
    else:
        typer.echo("today: no daily_stress data yet")


@app.command("install-agent")
def install_agent() -> None:
    """Install and load the LaunchAgent that runs `check` on an interval."""
    cfg = load_config()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    plist = {
        "Label": LABEL,
        "ProgramArguments": [str(Path(sys.executable).parent / "oura-stress"), "check"],
        "StartInterval": cfg.poll_minutes * 60,
        "StandardOutPath": str(STATE_DIR / "agent.log"),
        "StandardErrorPath": str(STATE_DIR / "agent.log"),
    }
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_bytes(plistlib.dumps(plist))
    uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(PLIST_PATH)], check=False)
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(PLIST_PATH)], check=True)
    typer.echo(f"Installed {PLIST_PATH}")


@app.command("uninstall-agent")
def uninstall_agent() -> None:
    """Unload and remove the LaunchAgent."""
    uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(PLIST_PATH)], check=False)
    PLIST_PATH.unlink(missing_ok=True)
    typer.echo("Removed agent.")
