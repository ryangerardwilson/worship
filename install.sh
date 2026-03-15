#!/usr/bin/env bash
set -euo pipefail

APP="worship"
REPO="ryangerardwilson/${APP}"
APP_HOME="${HOME}/.${APP}"
INSTALL_DIR="${APP_HOME}/bin"
APP_DIR="${APP_HOME}/app"
SOURCE_DIR="${APP_DIR}/source"
VENV_DIR="${APP_HOME}/venv"
SOURCE_PATH_FILE="${APP_HOME}/source_path"
ARCHIVE_NAME="${APP}.tar.gz"
LATEST_VERSION_URL="https://raw.githubusercontent.com/${REPO}/main/_version.py"
MAIN_ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"

MUTED='\033[0;2m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
  cat <<EOF
${APP} Installer

Usage: install.sh [options]

Options:
  -h                         Show this help and exit
  -v [<version>]             Print the latest source version, or install a specific tag
  -u                         Upgrade to the latest source version only when newer
  -b, --binary <path>        Install from a local checkout or source archive
      --no-modify-path       Skip editing shell rc files

Notes:
  - This app currently installs from source rather than GitHub release bundles.
  - With no arguments, install.sh installs the latest main-branch source snapshot.
EOF
}

info() {
  echo -e "${MUTED}$1${NC}"
}

die() {
  echo -e "${RED}$1${NC}" >&2
  exit 1
}

requested_version=""
show_latest=false
upgrade=false
binary_path=""
no_modify_path=false
latest_version_cache=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -v|--version)
      if [[ -n "${2:-}" && "${2:0:1}" != "-" ]]; then
        requested_version="${2#v}"
        shift 2
      else
        show_latest=true
        shift
      fi
      ;;
    -u|--upgrade)
      upgrade=true
      shift
      ;;
    -b|--binary)
      [[ -n "${2:-}" ]] || die "-b/--binary requires a path"
      binary_path="$2"
      shift 2
      ;;
    --no-modify-path)
      no_modify_path=true
      shift
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

extract_version_from_file() {
  local version_file="$1"
  sed -n 's/^__version__ = "\([^"]*\)"$/\1/p' "$version_file" | head -n 1
}

get_local_source_path() {
  [[ -f "$SOURCE_PATH_FILE" ]] || return 0
  local local_source
  local_source="$(cat "$SOURCE_PATH_FILE")"
  [[ -n "$local_source" && -d "$local_source" ]] || return 0
  printf '%s\n' "$local_source"
}

get_latest_version() {
  local local_source=""
  local_source="$(get_local_source_path)"
  if [[ -z "$latest_version_cache" ]]; then
    if [[ -n "$local_source" && -f "$local_source/_version.py" ]]; then
      latest_version_cache="$(extract_version_from_file "$local_source/_version.py")"
    else
      command -v curl >/dev/null 2>&1 || die "'curl' is required"
      latest_version_cache="$(
        curl -fsSL "$LATEST_VERSION_URL" | sed -n 's/^__version__ = "\([^"]*\)"$/\1/p' | head -n 1
      )"
    fi
    [[ -n "$latest_version_cache" ]] || die "unable to determine latest source version"
  fi
  printf '%s\n' "$latest_version_cache"
}

extract_source() {
  local src_path="$1"
  local out_dir="$2"

  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  if [[ -d "$src_path" ]]; then
    cp -R "$src_path"/. "$out_dir"/
  else
    command -v tar >/dev/null 2>&1 || die "'tar' is required"
    tar -xzf "$src_path" -C "$tmp_dir"
    local extracted
    extracted="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    [[ -n "$extracted" ]] || die "failed to extract source archive"
    cp -R "$extracted"/. "$out_dir"/
  fi

  rm -rf "$out_dir/.git" "$out_dir/.ruff_cache"
  find "$out_dir" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
}

maybe_add_path() {
  local command="$1"
  local shell_name
  local rc_files=()
  shell_name="$(basename "${SHELL:-bash}")"

  case "$shell_name" in
    zsh) rc_files=("$HOME/.zshrc" "$HOME/.zshenv" "$HOME/.config/zsh/.zshrc") ;;
    bash) rc_files=("$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile") ;;
    fish) rc_files=("$HOME/.config/fish/config.fish") ;;
    *) rc_files=("$HOME/.profile") ;;
  esac

  for rc in "${rc_files[@]}"; do
    [[ -f "$rc" ]] || continue
    if grep -Fq "$command" "$rc" 2>/dev/null; then
      return
    fi
    printf '\n# %s\n%s\n' "$APP" "$command" >> "$rc"
    info "Added ${APP} to PATH in $rc"
    return
  done

  info "Add to PATH manually: $command"
}

if $show_latest; then
  [[ "$upgrade" == false && -z "$binary_path" && -z "$requested_version" ]] || \
    die "-v (no arg) cannot be combined with other options"
  get_latest_version
  exit 0
fi

if $upgrade; then
  [[ -z "$binary_path" ]] || die "-u cannot be used with -b/--binary"
  [[ -z "$requested_version" ]] || die "-u cannot be combined with -v <version>"
  latest="$(get_latest_version)"
  if command -v "$APP" >/dev/null 2>&1; then
    installed="$("$APP" -v 2>/dev/null || true)"
    installed="${installed#v}"
    if [[ -n "$installed" && "$installed" == "$latest" ]]; then
      info "${APP} ${latest} already installed"
      exit 0
    fi
  fi
  requested_version="$latest"
fi

command -v curl >/dev/null 2>&1 || die "'curl' is required"
command -v python3 >/dev/null 2>&1 || die "'python3' is required"

mkdir -p "$INSTALL_DIR" "$APP_DIR"
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/${APP}.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT

installed_label=""

if [[ -n "$binary_path" ]]; then
  [[ -e "$binary_path" ]] || die "bundle not found: $binary_path"
  extract_source "$binary_path" "$SOURCE_DIR"
  installed_label="$(extract_version_from_file "$SOURCE_DIR/_version.py" || true)"
  [[ -n "$installed_label" ]] || installed_label="local"
  if [[ -d "$binary_path" ]]; then
    realpath "$binary_path" > "$SOURCE_PATH_FILE"
  else
    rm -f "$SOURCE_PATH_FILE"
  fi
else
  local_source_path="$(get_local_source_path)"
  if [[ -n "$local_source_path" && -z "$requested_version" ]]; then
    requested_version="$(get_latest_version)"
    if command -v "$APP" >/dev/null 2>&1; then
      installed="$("$APP" -v 2>/dev/null || true)"
      installed="${installed#v}"
      if [[ -n "$installed" && "$installed" == "$requested_version" ]]; then
        info "${APP} ${requested_version} already installed"
        exit 0
      fi
    fi
    extract_source "$local_source_path" "$SOURCE_DIR"
    installed_label="$requested_version"
    realpath "$local_source_path" > "$SOURCE_PATH_FILE"
  elif [[ -z "$requested_version" ]]; then
    requested_version="$(get_latest_version)"
    archive_url="$MAIN_ARCHIVE_URL"
  else
    requested_version="${requested_version#v}"
    archive_url="https://github.com/${REPO}/archive/refs/tags/v${requested_version}.tar.gz"
    http_status="$(curl -sI -o /dev/null -w "%{http_code}" "https://github.com/${REPO}/tree/v${requested_version}")"
    [[ "$http_status" != "404" ]] || die "tag v${requested_version} not found"
  fi

  if command -v "$APP" >/dev/null 2>&1; then
    installed="$("$APP" -v 2>/dev/null || true)"
    installed="${installed#v}"
    if [[ -n "$installed" && "$installed" == "$requested_version" ]]; then
      info "${APP} ${requested_version} already installed"
      exit 0
    fi
  fi

  curl -# -L -o "${tmp_dir}/${ARCHIVE_NAME}" "$archive_url"
  extract_source "${tmp_dir}/${ARCHIVE_NAME}" "$SOURCE_DIR"
  installed_label="$requested_version"
  rm -f "$SOURCE_PATH_FILE"
fi

[[ -f "${SOURCE_DIR}/main.py" ]] || die "bundle missing main.py"
[[ -f "${SOURCE_DIR}/_version.py" ]] || die "bundle missing _version.py"
[[ -d "${SOURCE_DIR}/modules" ]] || die "bundle missing modules/"
[[ -d "${SOURCE_DIR}/courses" ]] || die "bundle missing courses/"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --disable-pip-version-check -U pip
if [[ -f "${SOURCE_DIR}/requirements.txt" ]]; then
  "$VENV_DIR/bin/pip" install --disable-pip-version-check -r "${SOURCE_DIR}/requirements.txt"
fi

cat > "${INSTALL_DIR}/${APP}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${VENV_DIR}/bin/python" "${SOURCE_DIR}/main.py" "\$@"
EOF
chmod 755 "${INSTALL_DIR}/${APP}"

if [[ "$no_modify_path" != "true" && ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  if [[ "$(basename "${SHELL:-bash}")" == "fish" ]]; then
    maybe_add_path "fish_add_path $INSTALL_DIR"
  else
    maybe_add_path "export PATH=$INSTALL_DIR:\$PATH"
  fi
fi

info "Installed ${APP} (${installed_label:-unknown}) to ${INSTALL_DIR}/${APP}"
info "Run: ${APP} -h"
