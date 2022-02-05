# Sainpse
The institute utility package

## To install use
pip install sainpse

## Usage
- The only utltiy function available now is TwelveData financial history data set.

### Example
from sainpse.finance.data import TwelveData

- start    = pendulum.parse('2020-05-30 07:00:00',tz='Africa/Johannesburg')
- end      = pendulum.parse('2022-01-14 17:00:00',tz='Africa/Johannesburg')

- TDH      = TwelveData(start=start,end=end,interval="1min",asset="EUR/USD")

- history  = TDH.getHistory()


