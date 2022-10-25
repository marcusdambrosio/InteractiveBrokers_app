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
from mailer import send_email
import sys
from get_init_info import get_scalers, sleep_time

ticker_list = ['GOOG', 'GOOGL', 'FITB', 'CFG', 'C', 'KEY', 'DISCA', 'DISCK']

class TestApp(EClient, EWrapper):

    def __init__(self):

        EClient.__init__(self, self)

        self.current_price = {}
        self.scaled_price = {}
        self.init_ID = None
        self.trading_ready = False

        self.parameters = {'GOOG': [0.01, 0.005],
                           'GOOGL' : [.01 , .005],
                           'C' : [0.01, 0.005],
                           'KEY' : [.01, .005],
                           'FITB' : [0.05, 0.02],
                           'CFG' : [.05, .02],
                           'DISCA' :  [0.02333, 0.005],
                           'DISCK' : [.02333, .005]}

        self.pairs = {'GOOG' : 'GOOGL',
                      'GOOGL' : 'GOOG',
                      'C' : 'KEY',
                      'KEY' : 'C',
                      'FITB' : 'CFG',
                      'CFG' : 'FITB',
                      'DISCA' : 'DISCK',
                      'DISCK' : 'DISCA'}

        self.scalers = get_scalers(ticker_list)


        self.positions = {'GOOG': 0,
                        'GOOGL': 0,
                        'C': 0,
                        'KEY': 0,
                        'CFG': 0,
                        'FITB': 0,
                        'DISCA': 0,
                        'DISCK': 0}

        self.current_price = {'GOOG': 1,
                          'GOOGL': 1,
                          'C': 1,
                          'KEY': 1,
                          'CFG': 1,
                          'FITB': 1,
                          'DISCA': 1,
                          'DISCK': 1}

        self.scaled_price = {'GOOG': -1,
                              'GOOGL': -1,
                              'C': -1,
                              'KEY': -1,
                              'CFG': -1,
                              'FITB': -1,
                              'DISCA': -1,
                              'DISCK': -1}


        self.email_count = 0

        self.stock_info = {'current price' : self.current_price,
                           'scaler' : self.scalers,
                           'scaled price' : self.scaled_price,
                           'pair': self.pairs,
                           'parameters' : self.parameters,
                           'position' : self.positions,
                           'side' : {},
                           'avg cost': {},
                           'unreal pnl' : {},
                           'real pnl' : {}
                           }



    def error(self, Id, errorCode:int, errorString:str):
        print(f'There is an error with {Id} errorcode {errorCode} that says {errorString}')


    def liquidate(self):

        for ticker in ticker_list:
            position = self.stock_info['position'][f'{ticker}']

            if position != 0:
                side = self.stock_info['side'][f'{ticker}']
                position = -position if side == 'SELL' else position
                self.execute_order(self.init_ID, ticker, side, str(position), 'MKT')
                self.stock_info['position'][ticker] = 0
                self.init_ID += 1
                print(f'{position} shares of {ticker} have been {side}')


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


        self.stock_info['avg cost'][f'{contract.symbol}'] = averageCost
        self.stock_info['position'][f'{contract.symbol}'] = position

        if position > 0:
            self.stock_info['side'][f'{contract.symbol}'] = 'BUY'
        elif position < 0:
            self.stock_info['side'][f'{contract.symbol}'] = 'SELL'

        self.stock_info['unreal pnl'][f'{contract.symbol}'] = unrealizedPNL
        self.stock_info['real pnl'][f'{contract.symbol}'] = realizedPNL







        #MORE TRAADE INFO LIKE TYPE AND OTEER SHIT HERE TO HANDEL PROGRAM FAILES



    #
    # PROBABLY NOT NECESSARY YET
    #
    # def updateAccountValue(self, key:str, val:str, currency:str,
    #                         accountName:str):
    #     relevant_keys = ['BuyingPower', 'TotalCashBalance', 'FullInitMarginReq', 'FullMaintMarginReq']
    #     if key in relevant_keys:
    #         print(f'UPDATED ACCOUNT VALUES\n KEY: {key}\n Value: {val}\n Currency: {currency}\n Account: {accountName}')
    #
    # def updateAccountTime(self, timeStamp:str):
    #     print(f'Time: {timeStamp}')
    #
    # def accountDownloadEnd(self, accountName:str):
    #     print(f'ACCOUNT {accountName} DOWNLOAD FINISHED')



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
        self.stock_info['current price'][f'{ticker}'] = price
        self.stock_info['scaled price'][f'{ticker}'] = price / self.stock_info['scaler'][f'{ticker}']

        pair = self.stock_info['pair'][f'{ticker}']
        #self.stock_info['current price'][f'{pair}'] = price
        self.stock_info['scaled price'][f'{pair}'] = self.stock_info['current price'][f'{pair}'] / self.stock_info['scaler'][f'{pair}']

        #LOGIC

        if dt.datetime.today().strftime('%H:%M:%S')[:-1] == '14:59:3':
            self.liquidate()
            sys.exit('MKT CLOSED')

        if not self.trading_ready:
            condition = self.scaled_price['GOOG'] > 0 and self.scaled_price['GOOGL'] > 0 and self.scaled_price['C'] > 0 \
                        and self.scaled_price['KEY'] > 0 and self.scaled_price['FITB'] > 0 and self.scaled_price['CFG'] > 0 \
                        and self.scaled_price['DISCA'] > 0 and self.scaled_price['DISCK'] > 0

            if condition:
                self.trading_ready = True

        if self.trading_ready:
            self.logic(ticker = ticker, pair = pair)


    def logic(self, ticker, pair):

        scaled_tick = self.stock_info['scaled price'][f'{ticker}']
        scaled_pair = self.stock_info['scaled price'][f'{pair}']
        current_params = self.stock_info['parameters'][f'{ticker}']

        if self.stock_info['position'][f'{ticker}'] == 0.0:
            print(ticker, current_params[0], np.abs(scaled_tick-scaled_pair))
            quantity_tick = np.floor(100000 / self.stock_info['current price'][f'{ticker}'])
            quantity_pair = np.floor(100000 / self.stock_info['current price'][f'{pair}'])

            if np.abs(scaled_tick - scaled_pair) >= current_params[0]:

                if scaled_tick > scaled_pair:
                    self.stock_info['side'][f'{ticker}'] = 'SELL'
                    self.stock_info['side'][f'{pair}'] = 'BUY'

                    self.execute_order(self.init_ID, ticker, 'SELL', str(quantity_tick), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{ticker}'] = -quantity_tick

                    self.execute_order(self.init_ID, pair, 'BUY', str(quantity_pair), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{pair}'] = quantity_pair

                else:
                    self.stock_info['side'][f'{ticker}'] = 'BUY'
                    self.stock_info['side'][f'{pair}'] = 'SELL'

                    self.execute_order(self.init_ID, ticker, 'BUY', str(quantity_tick), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{ticker}'] = quantity_tick

                    self.execute_order(self.init_ID, pair, 'SELL', str(quantity_pair), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{pair}'] = -quantity_pair



        else:

            if np.abs(scaled_tick - scaled_pair) <= current_params[1]:

                if self.stock_info['position'][f'{ticker}'] < 0:
                    self.stock_info['position'][f'{ticker}'] *= -1

                else:
                    self.stock_info['position'][f'{pair}'] *= -1

                self.execute_order(self.init_ID, ticker, self.stock_info['side'][f'{pair}'], self.stock_info['position'][f'{ticker}'], 'MKT')
                self.init_ID += 1

                self.execute_order(self.init_ID, pair,  self.stock_info['side'][f'{ticker}'], self.stock_info['position'][f'{pair}'], 'MKT')
                self.init_ID += 1

                # if self.type[f'{ticker}'] == 'BUY':
                #
                #     self.execute_order(self.init_ID, f'{pair}', 'SELL', str(quantity2), 'MKT')
                #     self.init_ID += 1
                #
                #     self.execute_order(self.init_ID, f'{ticker}', 'BUY', str(quantity1), 'MKT')
                #     self.init_ID += 1
                #
                #
                # elif self.type[f'{ticker}'] == 'short2':
                #
                #     self.execute_order(self.init_ID, f'{ticker}', 'SELL', str(quantity1), 'MKT')
                #     self.init_ID += 1
                #
                #     self.execute_order(self.init_ID, f'{pair}', 'BUY', str(quantity2), 'MKT')
                #     self.init_ID += 1
                #
                # else:
                #     print('invalid type value')


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
            stop_loss.orderType = 'LMT'
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





    def nextValidId(self, orderId):
        print(f'The next valid order ID is {orderId}')
        self.init_ID = orderId
        self.reqAccountUpdates(True, '')
        self.init_mkt_data(['GOOG', 'GOOGL', 'C', 'KEY', 'FITB', 'CFG', 'DISCA', 'DISCK'], printing = False)
    def __init__(self):

        EClient.__init__(self, self)

        self.current_price = {}
        self.scaled_price = {}
        self.init_ID = None
        self.trading_ready = False

        self.parameters = {'GOOG': [0.01, 0.005],
                           'GOOGL' : [.01 , .005],
                           'C' : [0.01, 0.005],
                           'KEY' : [.01, .005],
                           'FITB' : [0.05, 0.02],
                           'CFG' : [.05, .02],
                           'DISCA' :  [0.02333, 0.005],
                           'DISCK' : [.02333, .005]}

        self.pairs = {'GOOG' : 'GOOGL',
                      'GOOGL' : 'GOOG',
                      'C' : 'KEY',
                      'KEY' : 'C',
                      'FITB' : 'CFG',
                      'CFG' : 'FITB',
                      'DISCA' : 'DISCK',
                      'DISCK' : 'DISCA'}

        self.scalers = get_scalers(ticker_list)


        self.positions = {'GOOG': 0,
                        'GOOGL': 0,
                        'C': 0,
                        'KEY': 0,
                        'CFG': 0,
                        'FITB': 0,
                        'DISCA': 0,
                        'DISCK': 0}

        self.current_price = {'GOOG': 1,
                          'GOOGL': 1,
                          'C': 1,
                          'KEY': 1,
                          'CFG': 1,
                          'FITB': 1,
                          'DISCA': 1,
                          'DISCK': 1}

        self.scaled_price = {'GOOG': -1,
                              'GOOGL': -1,
                              'C': -1,
                              'KEY': -1,
                              'CFG': -1,
                              'FITB': -1,
                              'DISCA': -1,
                              'DISCK': -1}


        self.email_count = 0

        self.stock_info = {'current price' : self.current_price,
                           'scaler' : self.scalers,
                           'scaled price' : self.scaled_price,
                           'pair': self.pairs,
                           'parameters' : self.parameters,
                           'position' : self.positions,
                           'side' : {},
                           'avg cost': {},
                           'unreal pnl' : {},
                           'real pnl' : {}
                           }



    def error(self, Id, errorCode:int, errorString:str):
        print(f'There is an error with {Id} errorcode {errorCode} that says {errorString}')


    def liquidate(self):

        for ticker in ticker_list:
            position = self.stock_info['position'][f'{ticker}']

            if position != 0:
                side = self.stock_info['side'][f'{ticker}']
                position = -position if side == 'SELL' else position
                self.execute_order(self.init_ID, ticker, side, str(position), 'MKT')
                self.stock_info['position'][ticker] = 0
                self.init_ID += 1
                print(f'{position} shares of {ticker} have been {side}')


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


        self.stock_info['avg cost'][f'{contract.symbol}'] = averageCost
        self.stock_info['position'][f'{contract.symbol}'] = position

        if position > 0:
            self.stock_info['side'][f'{contract.symbol}'] = 'BUY'
        elif position < 0:
            self.stock_info['side'][f'{contract.symbol}'] = 'SELL'

        self.stock_info['unreal pnl'][f'{contract.symbol}'] = unrealizedPNL
        self.stock_info['real pnl'][f'{contract.symbol}'] = realizedPNL







        #MORE TRAADE INFO LIKE TYPE AND OTEER SHIT HERE TO HANDEL PROGRAM FAILES



    #
    # PROBABLY NOT NECESSARY YET
    #
    # def updateAccountValue(self, key:str, val:str, currency:str,
    #                         accountName:str):
    #     relevant_keys = ['BuyingPower', 'TotalCashBalance', 'FullInitMarginReq', 'FullMaintMarginReq']
    #     if key in relevant_keys:
    #         print(f'UPDATED ACCOUNT VALUES\n KEY: {key}\n Value: {val}\n Currency: {currency}\n Account: {accountName}')
    #
    # def updateAccountTime(self, timeStamp:str):
    #     print(f'Time: {timeStamp}')
    #
    # def accountDownloadEnd(self, accountName:str):
    #     print(f'ACCOUNT {accountName} DOWNLOAD FINISHED')



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
        self.stock_info['current price'][f'{ticker}'] = price
        self.stock_info['scaled price'][f'{ticker}'] = price / self.stock_info['scaler'][f'{ticker}']

        pair = self.stock_info['pair'][f'{ticker}']
        #self.stock_info['current price'][f'{pair}'] = price
        self.stock_info['scaled price'][f'{pair}'] = self.stock_info['current price'][f'{pair}'] / self.stock_info['scaler'][f'{pair}']

        #LOGIC

        if dt.datetime.today().strftime('%H:%M:%S')[:-1] == '14:59:3':
            self.liquidate()
            sys.exit('MKT CLOSED')

        if not self.trading_ready:
            condition = self.scaled_price['GOOG'] > 0 and self.scaled_price['GOOGL'] > 0 and self.scaled_price['C'] > 0 \
                        and self.scaled_price['KEY'] > 0 and self.scaled_price['FITB'] > 0 and self.scaled_price['CFG'] > 0 \
                        and self.scaled_price['DISCA'] > 0 and self.scaled_price['DISCK'] > 0

            if condition:
                self.trading_ready = True

        if self.trading_ready:
            self.logic(ticker = ticker, pair = pair)


    def logic(self, ticker, pair):

        scaled_tick = self.stock_info['scaled price'][f'{ticker}']
        scaled_pair = self.stock_info['scaled price'][f'{pair}']
        current_params = self.stock_info['parameters'][f'{ticker}']

        if self.stock_info['position'][f'{ticker}'] == 0.0:
            print(ticker, current_params[0], np.abs(scaled_tick-scaled_pair))
            quantity_tick = np.floor(100000 / self.stock_info['current price'][f'{ticker}'])
            quantity_pair = np.floor(100000 / self.stock_info['current price'][f'{pair}'])

            if np.abs(scaled_tick - scaled_pair) >= current_params[0]:

                if scaled_tick > scaled_pair:
                    self.stock_info['side'][f'{ticker}'] = 'SELL'
                    self.stock_info['side'][f'{pair}'] = 'BUY'

                    self.execute_order(self.init_ID, ticker, 'SELL', str(quantity_tick), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{ticker}'] = -quantity_tick

                    self.execute_order(self.init_ID, pair, 'BUY', str(quantity_pair), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{pair}'] = quantity_pair

                else:
                    self.stock_info['side'][f'{ticker}'] = 'BUY'
                    self.stock_info['side'][f'{pair}'] = 'SELL'

                    self.execute_order(self.init_ID, ticker, 'BUY', str(quantity_tick), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{ticker}'] = quantity_tick

                    self.execute_order(self.init_ID, pair, 'SELL', str(quantity_pair), 'MKT')
                    self.init_ID += 1
                    self.stock_info['position'][f'{pair}'] = -quantity_pair



        else:

            if np.abs(scaled_tick - scaled_pair) <= current_params[1]:

                if self.stock_info['position'][f'{ticker}'] < 0:
                    self.stock_info['position'][f'{ticker}'] *= -1

                else:
                    self.stock_info['position'][f'{pair}'] *= -1

                self.execute_order(self.init_ID, ticker, self.stock_info['side'][f'{pair}'], self.stock_info['position'][f'{ticker}'], 'MKT')
                self.init_ID += 1

                self.execute_order(self.init_ID, pair,  self.stock_info['side'][f'{ticker}'], self.stock_info['position'][f'{pair}'], 'MKT')
                self.init_ID += 1

                # if self.type[f'{ticker}'] == 'BUY':
                #
                #     self.execute_order(self.init_ID, f'{pair}', 'SELL', str(quantity2), 'MKT')
                #     self.init_ID += 1
                #
                #     self.execute_order(self.init_ID, f'{ticker}', 'BUY', str(quantity1), 'MKT')
                #     self.init_ID += 1
                #
                #
                # elif self.type[f'{ticker}'] == 'short2':
                #
                #     self.execute_order(self.init_ID, f'{ticker}', 'SELL', str(quantity1), 'MKT')
                #     self.init_ID += 1
                #
                #     self.execute_order(self.init_ID, f'{pair}', 'BUY', str(quantity2), 'MKT')
                #     self.init_ID += 1
                #
                # else:
                #     print('invalid type value')


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
            stop_loss.orderType = 'LMT'
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
        self.init_mkt_data(['GOOG', 'GOOGL', 'C', 'KEY', 'FITB', 'CFG', 'DISCA', 'DISCK'], printing = False)



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


