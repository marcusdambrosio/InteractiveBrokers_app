from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
import datetime as dt
import time
import numpy as np
import pandas as pd
import os
from mailer import send_email
import sys
from get_init_info import get_scalers, sleep_time
from ibapi.client import BarData

watchlist = ['ES']
class TestApp(EClient, EWrapper):

    def __init__(self):

        EClient.__init__(self, self)



    def init_mkt_data(self, tickers):
        #self.current_price = np.ones(len(tickers)).tolist()
        req_id = 1

        enddate = dt.datetime.today().strftime('%Y%m%d %H:%M:%S')

        for ticker in tickers:

            self.reqHistoricalData(req_id, self.create_contract(ticker, sec_type = 'FUT', exchange='GLOBEX'), enddate, '365 D', '1 min', 'TRADES', 0, 1, False, [])
            req_id += 1


    def create_contract(self, symbol, sec_type='STK', exchange='CME', curr='USD'):
        if not symbol:
            raise ValueError('No ticker specified.')

        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = curr
        contract.lastTradeDateOrContractMonth = '202009'
        # contract.localSymbol = 'ESH1' #FIX THIS LINE
        return contract

    def historicalData(self, reqId: int, bar: BarData):
        print("historical data reqID:", reqId, 'bar:', bar)

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        super().historicalDataEnd(reqId, start, end)
        print('ending historical data', reqId, 'from', start,'to', end)


    def nextValidId(self, orderId):
        print(f'The next valid order ID is {orderId}')
        self.init_ID = orderId
        self.init_mkt_data(watchlist)


app = TestApp()
app.connect('127.0.0.1', 7497, 1117)
app.run()