# worship

`worship` is a terminal-native course selector for scripture study and memorisation drills.

## Install

Install from the local checkout:

```bash
bash install.sh -b "$(pwd)"
```

Install the latest main-branch source snapshot:

```bash
curl -fsSL https://raw.githubusercontent.com/ryangerardwilson/worship/main/install.sh | bash
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
