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


watchlist = {'PRCP' : 7.59, 'INMB' : 18, 'IMV' : 7}

class TestApp(EClient, EWrapper):

    def __init__(self):

        EClient.__init__(self, self)

        self.current_price = {}
        self.scaled_price = {}
        self.init_ID = None
        self.trading_ready = False
        self.donetrading = []

        self.triggers = {}
        self.positions = {}
        self.current_price = {}


        for ticker in watchlist.keys():
            self.triggers[ticker] = watchlist[ticker]
            self.positions[ticker] = 0
            self.current_price[ticker] = 0
        #
        # self.triggers = {'WIMI' : 9.21,
        #                  'WAFU' : 8.50}
        #
        #
        #
        # self.positions = {'WIMI':0,
        #                  'WAFU': 0}
        #
        #
        # self.current_price = {'WIMI':0,
        #                  'WAFU' : 0}

        self.email_count = 0

        self.stock_info = {'current price' : self.current_price,
                           'trigger' : self.triggers,
                           'position' : self.positions,
                           'trade time': {},
                           'take profit': {},
                           'stop loss' : {},
                           'avg cost': {},
                           'unreal pnl' : {},
                           'real pnl' : {}
                           }

    def liquidate(self):

        for ticker in watchlist:
            position = self.stock_info['position'][f'{ticker}']

            if position != 0:

                self.execute_order(self.init_ID, ticker, 'SELL', str(position), 'MKT')
                self.init_ID += 1
                print(f'{position} shares of {ticker} have been sold')

    def error(self, Id, errorCode:int, errorString:str):
        print(f'There is an error with {Id} errorcode {errorCode} that says {errorString}')


    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        # Doesn't work yet
        # if not self.avgcost_for_data or not len(self.avgcost_for_data):
        #     self.avgcost_for_data = []
        #
        # else:
        #     self.avgcost_for_data.append([contract.symbol, averageCost])
        printing = False

        if printing:
            print(
                f'UPDATING PORTFOLIO INFORMATION\n Symbol: {contract.symbol}|SecType: {contract.secType}|Exchange: {contract.exchange}'
                f'|Position: {position}|Market Price: {marketPrice}|Market Value: {marketValue}|Average Cost: {averageCost}|Unrealized PnL: {unrealizedPNL}'
                f'|Realized PnL: {realizedPNL}|Account: {accountName}')

        self.stock_info['position'][f'{contract.symbol}'] = position


        self.stock_info['unreal pnl'][f'{contract.symbol}'] = unrealizedPNL
        self.stock_info['real pnl'][f'{contract.symbol}'] = realizedPNL
        #
        # if sum(self.stock_info['real pnl'].values()) < -1000:
        #     self.liquidate()
        #     time.sleep(2)
        #
        #     sys.exit('stopped out')



    def init_mkt_data(self, tickers, printing = False):
        #self.current_price = np.ones(len(tickers)).tolist()
        req_id = 1
        self.reqMarketDataType(4)
        self.printing = printing
        self.IDtoTicker = {}


        for ticker in tickers:
            self.IDtoTicker[f'{req_id}'] = ticker
            self.reqMktData(req_id, self.create_contract(ticker), '', False, False, [])
            req_id += 1


    def tickPrice(self, reqId, tickType, price, attrib):

        #
        # send_email('marcusdambrosio@gmail.com', 'marcusdambrosio@gmail.com',
        #            'TRADING STARTED',
        #            subject='TRADING STARTED\n')

        super().tickPrice(reqId, tickType, price, attrib)
        ticker = self.IDtoTicker[f'{reqId}']
        # self.stock_info['current price'][f'{ticker}'] = price

        #LOGIC

        if dt.datetime.today().strftime('%H:%M:%S')[:-1] == '14:59:3':
            self.liquidate()
            sys.exit('MKT CLOSED')


        self.logic(ticker = ticker, price = price, trigger = self.stock_info['trigger'][ticker])


    def logic(self, ticker, price, trigger):

        print(ticker,price,trigger)

        if price >= trigger and self.stock_info['position'][ticker] == 0:

            quantity = 10000 / price
            self.execute_order(self.init_ID, ticker, 'BUY', str(quantity), 'MKT', bracket = True, stop_val = price - .1, prof_val = price + .15)
            self.stock_info['position'][ticker] = quantity
            self.stock_info['trade time'][ticker] = int(dt.datetime.today().strftime('%S'))

        elif self.stock_info['position'][ticker] != 0:
            quantity = 10000 / price
            dT = int(dt.datetime.today().strftime('%S'))  - self.stock_info['trade time'][ticker]
            if dT > 20:
                if dT > 40:
                    dT = 60 - dT

                else:
                    self.execute_order(self.init_ID, ticker, 'SELL', str(quantity), 'MKT')



    def create_contract(self, symbol, sec_type='STK', exchange='SMART', curr='USD'):
        if not symbol:
            raise ValueError('No ticker specified.')

        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = curr
        return contract

    def create_order(self, symbol, side, quantity, ord_type, price= 0,
                     bracket=False, stop_val=None, prof_val=None):

        # Order config

        parent_order = Order()

        parent_order.action = side
        parent_order.totalQuantity = quantity
        parent_order.orderType = ord_type

        if ord_type == 'LMT':
            parent_order.lmtPrice = price

        if bracket:
            parent_order.transmit = True

            stop_loss = Order()
            stop_loss.action = 'SELL' if side == 'BUY' else 'BUY'
            stop_loss.totalQuantity = quantity
            stop_loss.orderType = 'STP'
            stop_loss.lmtPrice = stop_val
            #stop_loss.parentId = parent_order.orderId
            stop_loss.transmit = True

            take_prof = Order()
            take_prof.action = 'SELL' if side == 'BUY' else 'BUY'
            take_prof.totalQuantity = quantity
            take_prof.orderType = 'LMT'
            take_prof.lmtPrice = prof_val
            #take_prof.parentId = parent_order.orderId
            take_prof.transmit = True

            print(f'Bracket order for {symbol} created successfully.')
            return [parent_order, stop_loss, take_prof]

        else:
            parent_order.transmit = True
            print(f'{ord_type} for {symbol} created successfully.')
            return parent_order

    def store_send_data(self, symbol, side, quantity, ord_type, stop_val, prof_val):

        current_date = dt.datetime.today().strftime('%m-%d-%y')
        current_time = dt.datetime.now().strftime('%H:%M:%S')

        #doesn't work yet
        #avg_cost = [c for c in self.avgcost_for_data if c[0] == symbol][-1]
        avg_cost = 5
        new_data = {'Time': current_time,
                    'Symbol': symbol,
                    'Side': side,
                    'Quantity': quantity,
                    'Order Type': ord_type,
                    'Average Cost': avg_cost,
                    'Stop Loss' : stop_val,
                    'Take Profit' : prof_val}

        if f'{current_date}.csv' not in os.listdir('data_storage'):
            new_data = pd.DataFrame(new_data, index = np.arange(len(new_data)))
            new_data.to_csv(f'data_storage/{current_date}.csv')
            print('DATA ADDED SUCCESSFULLY')

        else:
            old_data = pd.read_csv(f'data_storage/{current_date}.csv')
            new_data = old_data.append(new_data, ignore_index = True)
            new_data.to_csv(f'data_storage/{current_date}.csv')
            print('DATA ADDED SUCCESSFULLY')


    def execute_order(self, nextOrderID, symbol, side, quantity, ord_type, price='0',
                     bracket=False, stop_val=None, prof_val=None):

        if not symbol:
            raise ValueError('No ticker specified')

        if not side:
            raise ValueError('Buy or Sell?')

        if not quantity:
            raise ValueError('No quantity specified')

        if not ord_type:
            raise ValueError('No order type specified')

        if ord_type == 'LMT' and price == '0':
            raise ValueError('Limit value not specified')

        '''
        GET MKT PRICE FOR DATA STORAGE REASONS
        else:
            mkt_price = ...
        '''
        self.nextID = nextOrderID

        theContract = self.create_contract(symbol)
        theOrder = self.create_order(symbol, side, quantity, ord_type, price = price,
                     bracket = bracket, stop_val = stop_val, prof_val= prof_val)

        if bracket:
            for i in theOrder:
                self.placeOrder(self.nextID, theContract, i)
                self.nextID += 1

            print(f'Bracketed {side} order for {quantity} shares of {symbol} was placed.')
            print(f'Stop loss at {stop_val} and take profit at {prof_val}')

        else:
            self.placeOrder(self.nextID, theContract, theOrder)
            #self.nextID += 1
            print(f'ORDER ID: {self.nextID} \n'
                  f'{side} order for {quantity} shares of {symbol} was placed.')

        self.store_send_data(symbol, side, quantity, ord_type, stop_val=stop_val, prof_val=prof_val)

        the_time = dt.datetime.now().strftime('%H:%M:%S')

        # time.sleep(2)
        # send_email('marcusdambrosio@gmail.com', 'marcusdambrosio@gmail.com', 'ORDER PLACED')
        #            # f'At {the_time} a {ord_type} order for {quantity} shares of {symbol} was placed.\n'
        #            # f'The average cost was {self.current_price[symbol]} for a total purchase of {self.current_price[symbol] * quantity}-.\n'
        #            # f'The stop is set at ${stop_val} and profit will be taken at ${prof_val}.',
        #            # subject = 'ORDER PLACED\n')
        # self.email_count += 1
        
        if self.email_count > 15:
            sys.exit('TERMINATE')




    def nextValidId(self, orderId):
        print(f'The next valid order ID is {orderId}')
        self.init_ID = orderId
        self.reqAccountUpdates(True, '')
        self.init_mkt_data(watchlist, printing = False)



app = TestApp()
start = True


while __name__ == '__main__':


    if dt.datetime.today().strftime('%H:%M') == '08:30':
        start = True

    if start:

        print('Startup successful.')
        app.connect('127.0.0.1', 7497, 1117)

        if app.isConnected():
            print('Connected')

        app.run()


