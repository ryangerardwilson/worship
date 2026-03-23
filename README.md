# worship

`worship` is a terminal-native course selector for scripture study and memorisation drills.

## Install

Install from the local checkout:

```bash
bash install.sh -b "$(pwd)"
```

Install the latest tagged release:

```bash
curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/worship/main/install.sh | bash
```

If `~/.local/bin` is not already on your `PATH`, add it once to `~/.bashrc`
and reload your shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

Install a specific version:

```bash
curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/worship/main/install.sh | bash -s -- -v 0.1.0
```

## Usage

```bash
worship
worship -h
worship -v
worship -u
worship -b -l
worship -b 2
worship -b -d 2
```

- `worship` launches the course selector in doc mode.
- `worship -h` shows help.
- `worship -v` prints the installed version from `_version.py`.
- `worship -u` upgrades through `install.sh`.

Source checkouts keep `_version.py` at `0.0.0`; tagged release bundles stamp the shipped artifact with the real version.
