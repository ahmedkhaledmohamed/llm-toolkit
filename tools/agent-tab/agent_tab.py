#!/usr/bin/env python3
"""Status badges for coding agents in Cursor/VS Code terminal titles (macOS/Linux)."""

import argparse
import difflib
import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shlex
import shutil
import signal
import socket
import struct
import sys
import tempfile
import termios
import time
import tty


STATES = {
    "running": "🟢 {agent} — working",
    "waiting": "🟡 {agent} — needs input",
    "error": "🔴 {agent} — failed",
    "idle": "⚪ {agent} — finished",
    "unknown": "⚪ {agent} — status unknown",
}
LABELS = {"claude": "Claude", "codex": "Codex", "cursor": "Cursor"}
SOCKET_ENV = "AGENT_TAB_SOCKET"
MARKER = "AGENT_TAB_HOOK=1"
SCRIPT = Path(__file__).resolve()
EVENTS = {
    "claude": ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
               "PermissionRequest", "Notification", "Stop"],
    "codex": ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
              "PermissionRequest", "Stop", "Interrupt"],
    "cursor": ["beforeSubmitPrompt", "afterAgentThought", "afterShellExecution",
               "afterMCPExecution", "stop"],
}


def title(agent, state):
    return ("\x1b]2;" + STATES[state].format(agent=LABELS.get(agent, agent)) + "\x07").encode()


def event_state(agent, event):
    """Only explicit lifecycle signals change state; failed tools aren't failed turns."""
    name = event.get("hook_event_name")
    if agent == "claude" and event.get("agent_id"):
        return None  # Nested agents must not overwrite the parent tab.
    if name in ("SessionStart", "Interrupt"):
        return "unknown"
    if name in ("Stop", "stop"):
        return {"error": "error", "aborted": "unknown"}.get(event.get("status"), "idle")
    if name == "PermissionRequest":
        return "waiting"
    if name == "Notification":
        # idle_prompt is a delayed reminder, not evidence of a pending question.
        if event.get("notification_type") in (
            "permission_prompt", "elicitation_dialog", "elicitation_url_dialog", "agent_needs_input"
        ):
            return "waiting"
        return None
    if name == "PreToolUse" and event.get("tool_name") in ("AskUserQuestion", "AskQuestion"):
        return "waiting"
    if name in ("UserPromptSubmit", "PreToolUse", "PostToolUse", "beforeSubmitPrompt",
                "afterAgentThought", "afterShellExecution", "afterMCPExecution"):
        return "running"
    return None


def hook(agent):
    """Fail open; never return permission decisions or store hook payloads."""
    event = {}
    try:
        event = json.loads(sys.stdin.buffer.read(1024 * 1024))
        if not isinstance(event, dict):
            event = {}
        state = event_state(agent, event)
        endpoint = os.environ.get(SOCKET_ENV)
        if state and endpoint:
            message = {"state": state, "session": event.get("session_id") or event.get("conversation_id")}
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
                client.settimeout(0.1)
                client.sendto(json.dumps(message).encode(), endpoint)
    except (OSError, ValueError, TypeError):
        pass
    # Cursor's submit hook has an explicit continue contract. No permission overrides.
    print(json.dumps({"continue": True} if event.get("hook_event_name") == "beforeSubmitPrompt" else {}))
    return 0


def hook_config(agent):
    command = f"{MARKER} {shlex.quote(sys.executable)} {shlex.quote(str(SCRIPT))} hook {agent}"
    handler = {"command": command, "timeout": 2}
    if agent == "cursor":
        return {"version": 1, "hooks": {event: [dict(handler)] for event in EVENTS[agent]}}
    handler["type"] = "command"
    return {"hooks": {event: [{"hooks": [dict(handler)]}] for event in EVENTS[agent]}}


def own_handler(entry):
    if not isinstance(entry, dict):
        return False
    if entry.get("command", "").startswith(MARKER + " "):
        return True
    handlers = entry.get("hooks", [])
    return bool(handlers) and all(own_handler(item) for item in handlers)


def merge_config(original, agent):
    result = json.loads(json.dumps(original))
    hooks = result.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("existing hooks must be a JSON object")
    generated = hook_config(agent)
    if agent == "cursor":
        if result.get("version", 1) != 1:
            raise ValueError("unsupported Cursor hooks version")
        result.setdefault("version", 1)
    for event, entries in generated["hooks"].items():
        existing = hooks.setdefault(event, [])
        if not isinstance(existing, list):
            raise ValueError(f"existing {event} hooks must be an array")
        hooks[event] = [item for item in existing if not own_handler(item)] + entries
    return result


def setup(agent, config_path, apply):
    defaults = {"claude": ".claude/settings.json", "codex": ".codex/hooks.json", "cursor": ".cursor/hooks.json"}
    path = Path(config_path).expanduser() if config_path else Path.home() / defaults[agent]
    before = path.read_text() if path.exists() else ""
    original = json.loads(before) if before.strip() else {}
    if not isinstance(original, dict):
        raise ValueError("config must be a JSON object")
    after = json.dumps(merge_config(original, agent), indent=2, ensure_ascii=False) + "\n"
    if before == after:
        print(f"Already configured: {path}")
        return 0
    if not apply:
        # Diff may contain existing settings: only show this locally, never publish it.
        sys.stdout.writelines(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                                fromfile=str(path), tofile=str(path)))
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    if before:
        backup = path.with_name(path.name + f".agent-tab-{time.time_ns()}.bak")
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(before)
    fd, temporary = tempfile.mkstemp(prefix=".agent-tab-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(after)
        if path.exists() and path.read_text() != before:
            raise ValueError("config changed during setup; retry without concurrent edits")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"Configured {agent}: {path}")
    if agent == "codex":
        print("In Codex, use /hooks to review and trust the new status hooks.")
    return 0


class TitleFilter:
    """Suppress competing OSC 0/1/2 titles, preserving other output byte for byte."""

    def __init__(self):
        self.pending = b""

    def feed(self, data):
        data = self.pending + data
        self.pending = b""
        output = bytearray()
        while data:
            start = data.find(b"\x1b]")
            if start < 0:
                if data.endswith(b"\x1b"):
                    self.pending = b"\x1b"
                    data = data[:-1]
                output.extend(data)
                break
            output.extend(data[:start])
            data = data[start:]
            ends = [(pos, size) for pos, size in ((data.find(b"\x07", 2), 1),
                                                  (data.find(b"\x1b\\", 2), 2)) if pos >= 0]
            if not ends:
                if len(data) <= 65536:
                    self.pending = data
                else:
                    output.extend(data)
                break
            end, size = min(ends)
            sequence, data = data[:end + size], data[end + size:]
            if sequence[2:].split(b";", 1)[0] not in (b"0", b"1", b"2"):
                output.extend(sequence)
        return bytes(output)


def write_all(fd, data):
    while data:
        count = os.write(fd, data)
        data = data[count:]


def run(agent, arguments):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("run requires an interactive terminal")
    executable = {"claude": "claude", "codex": "codex", "cursor": "agent"}[agent]
    if not shutil.which(executable):
        raise ValueError(f"{executable} is not on PATH")
    command = [executable, *arguments]
    if agent == "codex":
        # A pre-existing shared daemon cannot inherit this tab's socket environment.
        command.insert(1, "--no-daemon")
    original = termios.tcgetattr(sys.stdin.fileno())
    handlers = {}
    status = 0
    with tempfile.TemporaryDirectory(prefix="agent-tab-", dir="/tmp") as directory:
        endpoint = str(Path(directory) / "events.sock")
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
            server.bind(endpoint)
            server.setblocking(False)
            pid, master = pty.fork()
            if pid == 0:
                os.environ[SOCKET_ENV] = endpoint
                os.environ["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] = "1"
                try:
                    os.execvp(command[0], command)
                except OSError:
                    os.write(2, b"agent-tab: could not launch agent\r\n")
                    os._exit(127)

            def resize(*_):
                try:
                    size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
                    fcntl.ioctl(master, termios.TIOCSWINSZ, size)
                except OSError:
                    pass

            def forward(signum, _):
                try:
                    os.killpg(pid, signum)
                except ProcessLookupError:
                    pass

            for signum, handler in ((signal.SIGWINCH, resize), (signal.SIGTERM, forward),
                                    (signal.SIGHUP, forward), (signal.SIGINT, forward)):
                handlers[signum] = signal.signal(signum, handler)
            state, session, filter_ = "unknown", None, TitleFilter()
            try:
                tty.setraw(sys.stdin.fileno())
                resize()
                write_all(1, title(agent, state))
                inputs = [master, sys.stdin.fileno(), server]
                while True:
                    ready, _, _ = select.select(inputs, [], [], 0.2)
                    if master in ready:
                        try:
                            data = os.read(master, 65536)
                        except OSError as error:
                            if error.errno != errno.EIO:
                                raise
                            data = b""
                        if not data:
                            break
                        write_all(1, filter_.feed(data))
                    if sys.stdin.fileno() in ready:
                        data = os.read(sys.stdin.fileno(), 65536)
                        if not data:
                            inputs.remove(sys.stdin.fileno())
                            forward(signal.SIGHUP, None)
                        else:
                            write_all(master, data)
                    if server in ready:
                        try:
                            event = json.loads(server.recv(4096))
                            incoming = event.get("session")
                            if session and incoming and incoming != session:
                                continue
                            session = session or incoming
                            if event.get("state") in STATES:
                                state = event["state"]
                                write_all(1, title(agent, state))
                        except (ValueError, TypeError, AttributeError, BlockingIOError):
                            pass
                _, status = os.waitpid(pid, 0)
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original)
                for signum, previous in handlers.items():
                    signal.signal(signum, previous)
                os.close(master)
                try:
                    remaining, _ = os.waitpid(pid, os.WNOHANG)
                    if remaining == 0:
                        os.killpg(pid, signal.SIGHUP)
                except (ChildProcessError, ProcessLookupError):
                    pass
            exit_code = os.waitstatus_to_exitcode(status)
            final = "error" if exit_code or state == "error" else "idle"
            if exit_code == -signal.SIGINT:
                final = "unknown"
            write_all(1, title(agent, final))
            return exit_code if exit_code >= 0 else 128 - exit_code


def demo():
    if not sys.stdout.isatty():
        raise ValueError("demo requires an interactive terminal")
    for state in ("running", "waiting", "error", "idle"):
        write_all(1, title("claude", state))
        print(STATES[state].format(agent="Claude"), flush=True)
        time.sleep(2)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    launch = sub.add_parser("run", help="Launch an agent with a tab badge")
    launch.add_argument("agent", choices=LABELS)
    launch.add_argument("arguments", nargs=argparse.REMAINDER)
    configure = sub.add_parser("setup", help="Preview hook configuration; --apply installs with a backup")
    configure.add_argument("agent", choices=LABELS)
    configure.add_argument("--config", help="Override config destination (useful for a project)")
    configure.add_argument("--apply", action="store_true")
    callback = sub.add_parser("hook", help=argparse.SUPPRESS)
    callback.add_argument("agent", choices=LABELS)
    sub.add_parser("demo", help="Cycle the tab badge through all four states")
    args = parser.parse_args()
    try:
        if args.command == "hook":
            return hook(args.agent)
        if args.command == "setup":
            return setup(args.agent, args.config, args.apply)
        if args.command == "demo":
            return demo()
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        return run(args.agent, arguments)
    except (OSError, ValueError) as error:
        print(f"agent-tab: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
