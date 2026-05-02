# Sainpse
The institute utility package.

## To install use
```bash
pip install sainpse pendulum
```

## Usage
- The main utility available now is the TwelveData financial history data set client.
- Get token here: https://twelvedata.com/

### Quick start

```python
import pendulum

from sainpse.finance import TwelveData
```

```python
start = pendulum.parse("2020-05-30 07:00:00", tz="Africa/Johannesburg")
end = pendulum.parse("2022-01-14 17:00:00", tz="Africa/Johannesburg")
client = TwelveData(
    start=start,
    end=end,
    interval="1min",
    asset="EUR/USD",
    token="Your Twelve Data Token",
)
history = client.getHistory()
realtime_observation = client.getRealTime(lookback=60)
```

### Configuration

- `asset` and `token` are required.
- `interval` supports: `1min`, `5min`, `15min`, `30min`, `45min`, `1h`, `2h`, `4h`, `8h`, `1day`, `1week`, `1month`.
- `timezone` defaults to `Africa/Johannesburg`.
- `history_outputsize`, `retry_delay_seconds`, `max_retries`, and `columns` can be customised for larger data workflows.

### Notes

- `getHistory()` requires both `start` and `end`.
- `getRealTime()` returns a flattened observation array based on the selected columns and requested `lookback`.
