from twelvedata import TDClient
from twelvedata.exceptions import InvalidApiKeyError
import pendulum
import time



class TwelveData():

    
    def __init__(self,start=None,end=None,interval="15min",asset=None,token=None):

        """ The initialization function expects the start and end of the time period, interval, asset symbol and TwelveData token

        Args:
            start ([pendulum.datetime, required): Start period, note that depending on the asset selected some start time period may not be available use getEarliestDataPoint to check up to what time data is available. Defaults to None.
            end (pendulum.datetime, required):  End period,. Defaults to None.
            interval (str, required):time frame: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 8h, 1day, 1week, 1month. Defaults to "15min".
            asset (str, required): 	stock ticker (e.g. AAPL, MSFT);
                                    physical currency pair (e.g. EUR/USD, CNY/JPY);
                                    digital currency pair (BTC/USD, XRP/ETH). Defaults to None.
            token (str, required): get token from TwelveData Site. Defaults to None.
        """

        self.start    = start
        self.end      = end
        self._end     = self.end
        self.interval = interval
        self.asset    = asset
        self.history  = None
        self.token    = token


        self.td     = TDClient(apikey=self.token)


    def getEarliestDataPoint(self):
        """Gets the earliest data point available for the specific interval and symbol

        Returns:
            string: Date of the earliest datapoint
        """
        EarliestData = ""

        tstamp       = self.td.get_earliest_timestamp(interval=self.interval,symbol=self.asset)
        response     = tstamp.execute()
        EarliestData = response.content


        return EarliestData


    

    def getHistory(self):

        """recursively gets history and retries every minutes once free minute tokens are exhausted

        Returns:
            [pandas.DataFrame]: Returns the symbol/asset history along with several indicators
        """
        printMessage = True
        try:

            if self.history is None:
                self.history = self.getTimeSeries()
            else:
                self.history = self.history.append(self.getTimeSeries())

            newStart = self.history.tail(1).index[0].strftime("%Y-%m-%d %H:%M:%S")
            self.end = pendulum.parse(newStart,tz='Africa/Johannesburg')
           
            if self.end.date() >= self.start.date():
                return self.history
            else:
                self.getHistory()
                
        
        except InvalidApiKeyError as e:
            print(e)
            return None
        except Exception as e:
            if printMessage:
                print(e)
                printMessage = False
            print("Retrying request after 1:min,2:sec")
            time.sleep(62)
            print("Retrying request...")
            self.getHistory()

        ### Drop Dublicates
        self.history = self.history.drop_duplicates(keep = 'first')

        return self.history

            

    
    def getTimeSeries(self):

        ts = self.td.time_series(
            symbol=self.asset,
            interval=self.interval,
            start_date=self.start.to_datetime_string(),
            end_date=self.end.to_datetime_string(),
            outputsize=5000,
            order="desc",
            timezone="Africa/Johannesburg",
        )

        dataHistory = ts.with_percent_b().with_stoch(slow_k_period=3).with_apo().with_supertrend().with_trange().with_ultosc().as_pandas()
        return dataHistory

            
    def getRealTime(self):

        ts = self.td.time_series(
            symbol=self.asset,
            interval=self.interval,
            outputsize=60,
            order="desc",
            timezone="Africa/Johannesburg",
        )

        dataReal = ts.with_percent_b().with_stoch(slow_k_period=3).with_apo().with_supertrend().with_trange().with_ultosc().as_pandas()

        data = dataReal.sort_index(ascending=True)
        data = data[["open","high","low","close","percent_b","slow_k","slow_d","apo","supertrend","trange","ultosc"]]
        obs  = data.tail(15).values
        obs  = obs.reshape(165,)

        return obs