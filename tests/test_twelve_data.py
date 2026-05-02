import importlib
import sys
import types

import pytest


def load_twelve_data_module(monkeypatch):
    fake_exceptions = types.ModuleType("twelvedata.exceptions")

    class FakeInvalidApiKeyError(Exception):
        pass

    fake_exceptions.InvalidApiKeyError = FakeInvalidApiKeyError

    fake_twelvedata = types.ModuleType("twelvedata")

    class FakeTDClient:
        def __init__(self, apikey):
            self.apikey = apikey
            self.calls = []

        def time_series(self, **kwargs):
            self.calls.append(kwargs)
            return kwargs

    fake_twelvedata.TDClient = FakeTDClient

    fake_pendulum = types.ModuleType("pendulum")
    fake_pendulum.parse = lambda value, tz=None: value

    monkeypatch.setitem(sys.modules, "twelvedata", fake_twelvedata)
    monkeypatch.setitem(sys.modules, "twelvedata.exceptions", fake_exceptions)
    monkeypatch.setitem(sys.modules, "pendulum", fake_pendulum)
    sys.modules.pop("sainpse.finance.data.TwelveData", None)

    return importlib.import_module("sainpse.finance.data.TwelveData")


def build_client(module, **kwargs):
    params = {"asset": "EUR/USD", "token": "token"}
    params.update(kwargs)
    return module.TwelveData(**params)


def test_append_history_falls_back_to_pandas_concat(monkeypatch):
    module = load_twelve_data_module(monkeypatch)
    calls = []

    fake_pandas = types.ModuleType("pandas")

    def fake_concat(histories):
        calls.append(histories)
        return "combined-history"

    fake_pandas.concat = fake_concat
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)

    result = module._append_history(object(), object())

    assert result == "combined-history"
    assert len(calls) == 1
    assert len(calls[0]) == 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"asset": ""}, "asset is required"),
        ({"token": ""}, "token is required"),
        ({"interval": "bad-interval"}, "interval must be one of"),
        ({"history_outputsize": 0}, "history_outputsize must be a positive integer"),
        ({"retry_delay_seconds": -1}, "retry_delay_seconds must be non-negative"),
        ({"max_retries": -1}, "max_retries must be a non-negative integer or None"),
        ({"columns": []}, "columns must contain at least one column name"),
    ],
)
def test_init_validates_configuration(monkeypatch, kwargs, message):
    module = load_twelve_data_module(monkeypatch)

    with pytest.raises(ValueError, match=message):
        build_client(module, **kwargs)


def test_get_time_series_uses_configured_request_arguments(monkeypatch):
    module = load_twelve_data_module(monkeypatch)

    class FakeDateTime:
        def __init__(self, text):
            self.text = text

        def to_datetime_string(self):
            return self.text

        def __lt__(self, other):
            return self.text < other.text

    client = build_client(
        module,
        start=FakeDateTime("2024-01-01 00:00:00"),
        end=FakeDateTime("2024-01-02 00:00:00"),
        interval="1h",
        timezone="UTC",
        history_outputsize=42,
    )
    applied = []

    def fake_apply_indicators(time_series):
        applied.append(time_series)
        return "history-data"

    client._apply_indicators = fake_apply_indicators

    result = client.getTimeSeries()

    assert result == "history-data"
    assert client.td.calls == [
        {
            "symbol": "EUR/USD",
            "interval": "1h",
            "timezone": "UTC",
            "start_date": "2024-01-01 00:00:00",
            "end_date": "2024-01-02 00:00:00",
            "outputsize": 42,
            "order": "desc",
        }
    ]
    assert applied == [client.td.calls[0]]


def test_get_history_requires_start_and_end(monkeypatch):
    module = load_twelve_data_module(monkeypatch)
    client = build_client(module)

    with pytest.raises(ValueError, match="start and end are required"):
        client.getHistory()


@pytest.mark.parametrize("lookback", [0, 2])
def test_get_real_time_flattens_selected_columns(monkeypatch, lookback):
    module = load_twelve_data_module(monkeypatch)

    class FakeValues:
        def __init__(self):
            self.shape = None

        def reshape(self, *shape):
            self.shape = shape
            return shape

    class FakeFrame:
        def __init__(self, values):
            self.values = values
            self.selected_columns = None
            self.sorted_ascending = None

        def sort_index(self, ascending=True):
            self.sorted_ascending = ascending
            return self

        def __getitem__(self, columns):
            self.selected_columns = columns
            return self

    values = FakeValues()
    frame = FakeFrame(values)
    client = build_client(module, columns=("open", "close"))
    applied = []

    def fake_apply_indicators(time_series):
        applied.append(time_series)
        return frame

    client._apply_indicators = fake_apply_indicators

    result = client.getRealTime(lookback=lookback)

    assert result == (-1,)
    assert values.shape == (-1,)
    assert frame.sorted_ascending is True
    assert frame.selected_columns == ["open", "close"]
    assert client.td.calls[0]["outputsize"] == lookback
    assert applied == [client.td.calls[0]]


def test_get_real_time_validates_lookback(monkeypatch):
    module = load_twelve_data_module(monkeypatch)
    client = build_client(module)

    with pytest.raises(ValueError, match="lookback must be a non-negative integer"):
        client.getRealTime(lookback=-1)
