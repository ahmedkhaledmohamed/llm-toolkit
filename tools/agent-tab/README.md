# Agent terminal badges

A dependency-free prototype for Claude Code, Codex CLI and Cursor CLI in Cursor/VS Code terminal tabs. Requires Python 3.9+. Verified on macOS; Linux support is unverified. This standalone script is separate from the `llmtk` Python package and is not installed by `pip install llm-toolkit`.

## Try the badge

Set this in Cursor's Settings JSON so terminal tabs display application titles:

```json
"terminal.integrated.tabs.title": "${sequence}"
```

Remove any manually assigned terminal name, then run:

```sh
python3 agent_tab.py demo
```

The title cycles through green (working), yellow (needs input), red (failed), and white (finished). This changes a symbol in the title, rather than the native terminal icon colour.

## Install and connect agents

Install the single script at a stable path on your PATH before configuring hooks:

```sh
mkdir -p ~/.local/bin
cp agent_tab.py ~/.local/bin/agent-tab
chmod +x ~/.local/bin/agent-tab
```

Preview the changes, then install status-only hooks. Existing hooks are preserved and existing config is backed up before replacement. Hooks reference the installed script; keep that script at a stable path.

```sh
agent-tab setup claude
agent-tab setup claude --apply
agent-tab setup codex --apply
agent-tab setup cursor --apply
```

Default destinations are `~/.claude/settings.json`, `~/.codex/hooks.json`, and `~/.cursor/hooks.json`. Use `--config PATH` for a project-specific destination. Codex also requires review and trust through `/hooks`; the launcher never bypasses hook trust. Managed policies can disable custom hooks.

Start an agent through the launcher in each terminal:

```sh
agent-tab run claude
agent-tab run codex
agent-tab run cursor
# Arguments are forwarded to the CLI:
agent-tab run claude --resume
```

The Cursor CLI executable is `agent`. Codex runs with `--no-daemon` so hooks inherit the per-tab connection. Agent authentication, permission decisions and existing configuration remain with the original CLI. Hooks return no permission decisions and are inert outside the launcher. No prompts, transcripts or command output are saved or sent over the network.

## Detection limits

- Claude: explicit prompt submission, tool activity, permission/question events and turn completion.
- Codex: prompt submission, tool activity, permission requests and turn completion. A permission hook can fire before another hook or automatic reviewer resolves the request; yellow can therefore be transient. Question coverage depends on the CLI's tool events.
- Cursor: prompt submission, thought/tool completion and final status. There is no verified permission-wait signal in the installed CLI. Silence is never treated as waiting. A blocked approval may retain the last known state.
- Red indicates a failed agent process or an explicit failed turn, not an individual tool error the agent is recovering from. Claude/Codex turn hooks do not cover every fatal error while their TUI remains open.
- White “status unknown” means no usable event has arrived. Finished means a turn ended, not that every requested task was achieved. Other continuation hooks can restart a turn.
- Existing sessions must be restarted through the launcher. Background tasks, remote shells, multiplexers and Windows are outside this prototype's verified scope.

To remove, delete entries whose command begins with `AGENT_TAB_HOOK=1` from the three hook configurations, or restore the timestamped backups if no later settings changes need preserving. Restore the previous terminal tab-title setting if desired.

## Validation status

This is an early prototype. A real Cursor development window reported all four changing badge titles through its terminal API. Local behavioral checks covered generated hooks, session isolation, input, resize, exit codes, title filtering and terminal restoration. The launcher also started all three installed CLIs successfully with their version commands, and lint passed. Authenticated approval/completion flows for each CLI still need validation; synthetic hook checks do not substitute for those live checks.
