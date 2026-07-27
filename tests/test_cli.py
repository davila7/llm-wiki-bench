from __future__ import annotations

import importlib
import subprocess
import sys

import pytest

from harness.cli import build_parser, main


def test_help_exits_clean() -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0


def test_unimplemented_commands_say_so_rather_than_faking_it(capsys) -> None:
    for name in ("run", "eval", "report"):
        assert main([name]) == 2
        assert "not implemented yet" in capsys.readouterr().err


def test_no_network_at_import_time() -> None:
    """The brief forbids network calls at import. Import every harness module
    with socket disabled; anything that dials out fails here.
    """
    code = (
        "import socket\n"
        "socket.socket = lambda *a, **k: (_ for _ in ()).throw("
        "AssertionError('network at import time'))\n"
        "import harness, harness.cli, harness.contract, harness.manifest, harness.env\n"
        "print('ok')\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "ok" in proc.stdout


def test_modules_import_without_credentials() -> None:
    for mod in ("harness.cli", "harness.contract", "harness.manifest", "harness.env"):
        importlib.import_module(mod)
