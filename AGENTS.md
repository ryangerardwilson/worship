# AGENTS

## Workspace Defaults
- Follow `/home/ryan/Documents/agent_context/CLI_TUI_STYLE_GUIDE.md` for CLI/TUI taste and help shape.
- Follow `/home/ryan/Documents/agent_context/CANONICAL_REFERENCE_IMPLEMENTATION_FOR_CLI_AND_TUI_APPS.md` for executable contract details such as `-h`, `-v`, `-u`, installer behavior, and regression expectations.
- This file only records `worship`-specific constraints or durable deviations.

## Project-specific Rules
- `worship` keeps its no-arg behavior as the primary launch path into the curses UI. `-h` must document that clearly.
- `worship` does not currently own a user-editable config file. Do not add `conf` unless the app starts persisting user-facing config.
- Until a tagged release workflow exists, `worship` installs from source snapshots rather than GitHub release artifacts.
- During that source-install phase, checked-in `_version.py` is the runtime version source of truth and should be updated deliberately when install-facing behavior changes.
- Keep global flag parsing in `main.py` ahead of curses-heavy imports so `-h`, `-v`, and `-u` stay fast.
