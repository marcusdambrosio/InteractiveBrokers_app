from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.ticktype import TickTypeEnum
import datetime as dt
import time
import numpy as np
import pandas as pd
import os
#from mailer import send_email


class TestApp(EClient, EWrapper):

    def __init__(self):

        EClient.__init__(self, self)

        self.current_price = {}
        self.init_ID = None
        self.current_positions = {}
        self.position_average_costs = {}
        self.start_up = True

        self.watchlist = {'INSERT TICKERS AS KEYS' = 'TRIGGER PRICES HERE'}

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

        if self.start_up:
            print(
                f'UPDATING PORTFOLIO INFORMATION\n Symbol: {contract.symbol}|SecType: {contract.secType}|Exchange: {contract.exchange}'
                f'|Position: {position}|Market Price: {marketPrice}|Market Value: {marketValue}|Average Cost: {averageCost}|Unrealized PnL: {unrealizedPNL}'
                f'|Realized PnL: {realizedPNL}|Account: {accountName}')

            self.start_up = False

        self.position_average_costs[f'{contract.symbol}'] = averageCost
        self.current_positions[f'{contract.symbol}'] = position

    def init_mkt_data(self, tickers, printing=False):
        req_id = 1
        self.reqMarketDataType(4)
        self.printing = printing
        self.IDtoTicker = {}

        for ticker in tickers:
            self.IDtoTicker[f'{req_id}'] = ticker
            self.reqMktData(req_id, self.create_contract(ticker), '', False, False, [])
            req_id += 1


    def change_position(self, symbol, quantity, side):

        if side == 'BUY':
            self.current_positions[f'{symbol}'] += quantity

        else:
            self.current_positions[f'{symbol}'] -= quantity

    # def trade_information(self, data):
    #     self.watchlist = {}
    #     for item in data:
    #         self.watchlist[f'{item[0]}'] = item[1]


    def tickPrice(self, reqId, tickType, price, attrib):

        super().tickPrice(reqId, tickType, price, attrib)
        TickName = self.IDtoTicker[f'{reqId}']
        self.current_price[f'{TickName}'] = price

        if self.printing == True:
            print(self.current_price)

        #LOGIC


        for ticker in self.watchlist.keys():

            if ticker not in self.current_positions.keys():

                if self.current_price[f'{ticker}'] >= watchlist[f'{ticker}']:

                    quantity = 5
                    self.execute_order(self.init_ID, f'{ticker}', 'BUY', str(quantity),
                                       'LMT', price = str(self.current_price[f'{ticker}'] + .02),
                                       bracket = True, stop_val = str(watchlist[f'{ticker}'] -.08), prof_val = str(watchlist[f'{tiker}'] + .12))
                    self.init_ID += 1
                    self.current_positions[f'{ticker}'] = quantity

                else:
                    print('Ticker not in positions. Looking...')

            else:
                  print(f'already have pos of {ticker}')
                # if self.current_positions[f'{ticker}'] == 0:
                #
                #     if self.current_price[f'{TickName}'] >= 322.3:
                #         quantity = 5
                #         self.execute_order(self.init_ID, f'{TickName}', 'SELL', str(quantity), 'MKT')
                #         self.init_ID += 1
                #         self.current_positions[f'{TickName}'] = quantity
                #
                #     elif 0 < self.current_price[f'{TickName}'] <= 322.1:
                #         quantity = 5
                #         self.execute_order(self.init_ID, f'{TickName}', 'BUY', str(quantity), 'MKT')
                #         self.init_ID += 1
                #         self.current_positions[f'{TickName}'] = quantity
                #
                #
                # else:
                #     print('Already have pos')

`



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
            stop_loss.orderType = 'LMT'
            stop_loss.lmtPrice = stop_val
            stop_loss.transmit = True

            take_prof = Order()
            take_prof.action = 'SELL' if side == 'BUY' else 'BUY'
            take_prof.totalQuantity = quantity
            take_prof.orderType = 'LMT'
            take_prof.lmtPrice = prof_val
            take_prof.transmit = True

            print(f'Bracket order for {symbol} created successfully.')
            return [parent_order, stop_loss, take_prof]

        else:
            parent_order.transmit = True
            print(f'{ord_type} for {symbol} created successfully.')
            return parent_order


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
        send_email('marcusdambrosio@gmail.com', 'marcusdambrosio@gmail.com',
                   f'At {the_time} a {ord_type} order for {quantity} shares of {symbol} was placed.\n'
                   f'The average cost was $AVGCOSTHERE for a total purchase of $TOTALCOSTHERE.\n'
                   f'The stop is set at ${stop_val} and profit will be taken at ${prof_val}.',
                   subject = 'ORDER PLACED\n')


    def nextValidId(self, orderId):
        print(f'The next valid order ID is {orderId}')
        self.init_ID = orderId
        self.reqAccountUpdates(True, '')

        for ticker in self.watchlist.keys():

            self.init_mkt_data([f'ticker'], printing = True)




app = TestApp()

while __name__ == '__main__':


    app.connect('127.0.0.1', 7497, 1117)

    if app.isConnected():
        print('Connected')


    app.run()
