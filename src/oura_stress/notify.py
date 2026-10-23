import subprocess


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def notify(message: str, title: str = "Oura stress") -> None:
    script = f'display notification "{_escape(message)}" with title "{_escape(title)}"'
    subprocess.run(["osascript", "-e", script], check=False)
