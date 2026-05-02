import importlib
import time

import pendulum
from twelvedata import TDClient
from twelvedata.exceptions import InvalidApiKeyError


DEFAULT_INTERVAL = "15min"
DEFAULT_REALTIME_LOOKBACK = 120
DEFAULT_HISTORY_OUTPUTSIZE = 5000
DEFAULT_RETRY_DELAY_SECONDS = 62
DEFAULT_TIMEZONE = "Africa/Johannesburg"
VALID_INTERVALS = (
    "1min",
    "5min",
    "15min",
    "30min",
    "45min",
    "1h",
    "2h",
    "4h",
    "8h",
    "1day",
    "1week",
    "1month",
)
DEFAULT_OBSERVATION_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "percent_b",
    "slow_k",
    "slow_d",
    "apo",
    "supertrend",
    "trange",
    "ultosc",
)
_INFER_SHAPE = -1


def _append_history(history, new_history):
    append = getattr(history, "append", None)

    if callable(append):
        return append(new_history)

    return importlib.import_module("pandas").concat([history, new_history])


class TwelveData:
    def __init__(
        self,
        start=None,
        end=None,
        interval=DEFAULT_INTERVAL,
        asset=None,
        token=None,
        timezone=DEFAULT_TIMEZONE,
        history_outputsize=DEFAULT_HISTORY_OUTPUTSIZE,
        retry_delay_seconds=DEFAULT_RETRY_DELAY_SECONDS,
        max_retries=None,
        columns=DEFAULT_OBSERVATION_COLUMNS,
    ):
        self.start = start
        self.end = end
        self.interval = self._validate_interval(interval)
        self.asset = self._validate_required_text(asset, "asset")
        self.token = self._validate_required_text(token, "token")
        self.timezone = self._validate_required_text(timezone, "timezone")
        self.history_outputsize = self._validate_positive_int(history_outputsize, "history_outputsize")
        self.retry_delay_seconds = self._validate_non_negative_number(retry_delay_seconds, "retry_delay_seconds")
        self.max_retries = self._validate_max_retries(max_retries)
        self.columns = self._validate_columns(columns)
        self.history = None
        self.td = TDClient(apikey=self.token)

        if self.start is not None and self.end is not None:
            self._ensure_history_window()

    @staticmethod
    def _validate_required_text(value, name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")

        return value

    @staticmethod
    def _validate_interval(interval):
        if interval not in VALID_INTERVALS:
            raise ValueError(f"interval must be one of: {', '.join(VALID_INTERVALS)}")

        return interval

    @staticmethod
    def _validate_positive_int(value, name):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")

        return value

    @staticmethod
    def _validate_non_negative_int(value, name):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

        return value

    @staticmethod
    def _validate_non_negative_number(value, name):
        if value < 0:
            raise ValueError(f"{name} must be non-negative")

        return value

    @staticmethod
    def _validate_max_retries(value):
        if value is None:
            return value

        if not isinstance(value, int) or value < 0:
            raise ValueError("max_retries must be a non-negative integer or None")

        return value

    @staticmethod
    def _validate_columns(columns):
        if not columns:
            raise ValueError("columns must contain at least one column name")

        return tuple(columns)

    def _ensure_history_window(self):
        if self.start is None or self.end is None:
            raise ValueError("start and end are required for historical data requests")

        if self.end < self.start:
            raise ValueError("end must not be earlier than start")

    def _build_time_series(self, **kwargs):
        return self.td.time_series(symbol=self.asset, interval=self.interval, timezone=self.timezone, **kwargs)

    @staticmethod
    def _apply_indicators(time_series):
        return (
            time_series.with_percent_b()
            .with_stoch(slow_k_period=3)
            .with_apo()
            .with_supertrend()
            .with_trange()
            .with_ultosc()
            .as_pandas()
        )

    def getEarliestDataPoint(self):
        tstamp = self.td.get_earliest_timestamp(interval=self.interval, symbol=self.asset)
        response = tstamp.execute()
        return response.content

    def getHistory(self):
        self._ensure_history_window()
        attempts = 0

        while True:
            try:
                next_history = self._get_history_data()

                if self.history is None:
                    self.history = next_history
                else:
                    self.history = _append_history(self.history, next_history)

                self.history = self.history.drop_duplicates(keep="first").sort_index()

                if self.history.empty:
                    return self.history

                new_start = self.history.tail(1).index[0].strftime("%Y-%m-%d %H:%M:%S")
                self.end = pendulum.parse(new_start, tz=self.timezone)

                if self.end.date() <= self.start.date():
                    return self.history
            except InvalidApiKeyError as error:
                print(error)
                return None
            except Exception as error:
                attempts += 1

                if self.max_retries is not None and attempts > self.max_retries:
                    raise

                print(error)
                print(f"Retrying request after {self.retry_delay_seconds} seconds")
                time.sleep(self.retry_delay_seconds)
                print("Retrying request...")

    def _get_history_data(self):
        time_series = self._build_time_series(
            start_date=self.start.to_datetime_string(),
            end_date=self.end.to_datetime_string(),
            outputsize=self.history_outputsize,
            order="desc",
        )
        return self._apply_indicators(time_series)

    def getTimeSeries(self):
        self._ensure_history_window()
        return self._get_history_data()

    def getRealTime(self, lookback=DEFAULT_REALTIME_LOOKBACK):
        lookback = self._validate_non_negative_int(lookback, "lookback")
        time_series = self._build_time_series(outputsize=lookback, order="desc")
        technical_indicator_data = self._apply_indicators(time_series)
        ordered_data = technical_indicator_data.sort_index(ascending=True)
        observations = ordered_data[list(self.columns)]
        return observations.values.reshape(_INFER_SHAPE)
