import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main as worship_main


def test_main_delegates_upgrade_to_contract_runtime(monkeypatch):
    recorded = {}

    def fake_run_app(spec, argv, dispatch):  # type: ignore[no-untyped-def]
        recorded["spec"] = spec
        recorded["argv"] = argv
        recorded["dispatch"] = dispatch
        return 0

    monkeypatch.setattr(worship_main, "run_app", fake_run_app)

    rc = worship_main.main(["-u"])

    assert rc == 0
    assert recorded["argv"] == ["-u"]
    assert recorded["dispatch"] is worship_main._run_app


def test_install_script_creates_app_local_venv():
    script = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'VENV_DIR="$APP_HOME/venv"' in script
    assert 'python3 -m venv "$VENV_DIR"' in script
    assert '"$VENV_DIR/bin/pip" install --disable-pip-version-check -r "${SOURCE_DIR}/requirements.txt"' in script
    assert 'exec "${VENV_DIR}/bin/python" "${SOURCE_DIR}/main.py" "\\$@"' in script
