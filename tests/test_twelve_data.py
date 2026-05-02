import importlib
import sys
import types


def load_twelve_data_module(monkeypatch):
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
    sys.modules.pop("sainpse.finance.data.TwelveData", None)

    return importlib.import_module("sainpse.finance.data.TwelveData")


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


def test_get_real_time_flattens_for_any_lookback(monkeypatch):
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

    class FakeSeries:
        def __init__(self, frame):
            self.frame = frame

        def with_percent_b(self):
            return self

        def with_stoch(self, slow_k_period=3):
            return self

        def with_apo(self):
            return self

        def with_supertrend(self):
            return self

        def with_trange(self):
            return self

        def with_ultosc(self):
            return self

        def as_pandas(self):
            return self.frame

    class FakeClient:
        def __init__(self, frame):
            self.frame = frame
            self.calls = []

        def time_series(self, **kwargs):
            self.calls.append(kwargs)
            return FakeSeries(self.frame)

    values = FakeValues()
    frame = FakeFrame(values)
    client = module.TwelveData(start=None, end=None, asset="EUR/USD", token="token")
    client.td = FakeClient(frame)

    result = client.getRealTime(lookback=2)

    assert result == (-1,)
    assert values.shape == (-1,)
    assert frame.sorted_ascending is True
    assert client.td.calls[0]["outputsize"] == 2
