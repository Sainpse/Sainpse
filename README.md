# Sainpse
The institute utility package

## To install use
```bash
pip install sainpse pendulum
```

## Usage
- The only utltiy function available now is TwelveData financial history data set.
- Get token here: https://twelvedata.com/

### Example

```python
from sainpse.finance.data.TwelveData import TwelveData
```

```python
start    = pendulum.parse('2020-05-30 07:00:00',tz='Africa/Johannesburg')
end      = pendulum.parse('2022-01-14 17:00:00',tz='Africa/Johannesburg')
TDH      = TwelveData(start=start,end=end,interval="1min",asset="EUR/USD",token="Your Twelve Data Token")
history  = TDH.getHistory()
```

 #### Note:
 ##### interval (str, required):time frame: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 8h, 1day, 1week, 1month. Defaults to "15min".


[section]