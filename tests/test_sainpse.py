import sys
import tomllib
import types
from pathlib import Path

import sainpse
from sainpse import __version__


def test_version():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as file:
        config = tomllib.load(file)

    assert __version__ == config["tool"]["poetry"]["version"]


def test_twelve_data_is_available_from_package_root(monkeypatch):
    fake_exceptions = types.ModuleType("twelvedata.exceptions")

    class FakeInvalidApiKeyError(Exception):
        pass

    fake_exceptions.InvalidApiKeyError = FakeInvalidApiKeyError

    fake_twelvedata = types.ModuleType("twelvedata")

    class FakeTDClient:
        def __init__(self, apikey):
            self.apikey = apikey

    fake_twelvedata.TDClient = FakeTDClient

    fake_pendulum = types.ModuleType("pendulum")
    fake_pendulum.parse = lambda value, tz=None: value

    monkeypatch.setitem(sys.modules, "twelvedata", fake_twelvedata)
    monkeypatch.setitem(sys.modules, "twelvedata.exceptions", fake_exceptions)
    monkeypatch.setitem(sys.modules, "pendulum", fake_pendulum)
    sys.modules.pop("sainpse.finance", None)
    sys.modules.pop("sainpse.finance.data", None)
    sys.modules.pop("sainpse.finance.data.TwelveData", None)

    assert sainpse.TwelveData.__name__ == "TwelveData"
