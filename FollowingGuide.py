from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from threading import Thread
import queue
import datetime as dt
import time
import numpy as np
from finishable_Queue import finishableQueue
import pandas as pd
import os
import smtplib
from mailer import send_email

# objects for finishing queue
FINISHED = object()
STARTED = object()
TIME_OUT = object()


class TestWrapper(EWrapper):

    def init_error(self):
        error_queue = queue.Queue()
        self.my_errors_queue = error_queue

    def is_error(self):
        error_exist = not self.my_errors_queue.empty()
        return error_exist

    def get_error(self, timeout = 5):
        if self.is_error():

            try:
                return self.my_errors_queue.get(timeout = timeout)

            except queue.Empty:
                return None

        return None

    def error(self, id, errorCode, errorString):

        errormessage = f'IB returns an error with {id} errorcode {errorCode} that says {errorString}'
        self.my_errors_queue.put(errormessage)

    def init_time(self):
        time_queue = queue.Queue()
        self.my_time_queue = time_queue
        return time_queue


    def currentTime(self, server_time):
        self.my_time_queue.put(server_time)

    '''
    def init_positions(self):
        position_queue = queue.Queue()
        self.my_positions = position_queue
        return position_queue

    def position(self, account, contract, position, average_cost):
        pos_object = (account, contract, position, average_cost)
        self.my_positions.put(pos_object)

    def positionEnd(self):
        self.my_positions.put(FINISHED)
    '''
class TestClient(EClient):

    def __init__(self, wrapper):

        EClient.__init__(self, wrapper)

    def server_clock(self):
        print('Asking server for time')

        time_storage = self.wrapper.init_time()
        self.reqCurrentTime()

        max_wait_time = 10

        try:
            requested_time = time_storage.get(timeout = max_wait_time)

        except queue.Empty:
            print('The queue was empty or max time reached.')
            requested_time = None

        while self.wrapper.is_error():
            print('Error found')
            print(self.get_error(timeout = 5))

        return requested_time
'''
    def get_positions(self):
        pos_queue = finishableQueue(self.init_positions())
        self.reqPositions()

        max_wait = 10
        position_list = pos_queue.get(timeout = max_wait)

        while self.wrapper.is_error():
            print(self.get_error())

        if pos_queue.timed_out():
            print('Timed out.')

        return position_list
    '''
class TestApp(TestWrapper, TestClient):

    def __init__(self, ipaddress, portid, clientid):

        self.nextID = 312

        TestWrapper.__init__(self)
        TestClient.__init__(self, self)

        #connect to server
        self.connect(ipaddress, portid, clientid)

        # initialize thread
        thread = Thread(target = self.run)
        thread.start()
        setattr(self, '_thread', thread)

        #check for errors
        self.posns = []

    '''
    def get_account_summary(self, reqId: int, account: str, tag: str):
        self.reqAccountSummary(reqId, account, tag)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        print("AccountSummary. ReqId:", reqId, "Account:", account, "Tag: ", tag, "Value:", value, "Currency:", currency)

    def accountSummaryEnd(self, reqId:int):
        super().accountSummaryEnd(reqId)
        print('Account summary ended. ReqID:', reqId)
   

    def nextValidId(self, orderId: int):
        print(f'The next valid order ID is {orderId}')
        self.start()

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        self.posns.append((account, contract.symbol, position, avgCost))
        print(contract.symbol, position)

    def positionEnd(self):
        print("end, disconnecting")
        #self.disconnect()
    '''

    def nextValidId(self, orderId: int):
        print(f'The next valid order ID is {orderId}')
        self.start()


    def updatePortfolio(self, contract:Contract, position:float,
                        marketPrice:float, marketValue:float,
                        averageCost:float, unrealizedPNL:float,
                        realizedPNL:float, accountName:str):

        #Doesn't work yet
        # if not self.avgcost_for_data or not len(self.avgcost_for_data):
        #     self.avgcost_for_data = []
        #
        # else:
        #     self.avgcost_for_data.append([contract.symbol, averageCost])


        print(f'UPDATING PORTFOLIO INFORMATION\n Symbol: {contract.symbol}|SecType: {contract.secType}|Exchange: {contract.exchange}'
              f'|Position: {position}|Market Price: {marketPrice}|Market Value: {marketValue}|Average Cost: {averageCost}|Unrealized PnL: {unrealizedPNL}'
              f'|Realized PnL: {realizedPNL}|Account: {accountName}')

    def updateAccountValue(self, key:str, val:str, currency:str,
                            accountName:str):
        relevant_keys = ['BuyingPower', 'TotalCashBalance', 'FullInitMarginReq', 'FullMaintMarginReq']
        if key in relevant_keys:
            print(f'UPDATED ACCOUNT VALUES\n KEY: {key}\n Value: {val}\n Currency: {currency}\n Account: {accountName}')

    def updateAccountTime(self, timeStamp:str):
        print(f'Time: {timeStamp}')

    def accountDownloadEnd(self, accountName:str):
        print(f'ACCOUNT {accountName} DOWNLOAD FINISHED')





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

        #data = pd.DataFrame(columns=['Time', 'Symbol', 'Side', 'Quantity', 'Order Type', 'Average Cost', 'Bracketed', 'Stop Loss', 'Take Profit'])

    def execute_order(self, symbol, side, quantity, ord_type, price='0',
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

        theContract = self.create_contract(symbol)
        theOrder = self.create_order(symbol, side, quantity, ord_type, price= price,
                     bracket = bracket, stop_val = stop_val, prof_val= prof_val)

        if bracket:
            for i in theOrder:
                self.placeOrder(self.nextID, theContract, i)
                self.nextID += 1

            print(f'Bracketed {side} order for {quantity} shares of {symbol} was placed.')
            print(f'Stop loss at {stop_val} and take profit at {prof_val}')


        else:
            self.placeOrder(self.nextID, theContract, theOrder)
            self.nextID += 1
            print(f'{side} order for {quantity} shares of {symbol} was placed.')

        time.sleep(2)
        self.store_send_data(symbol, side, quantity, ord_type, stop_val=stop_val, prof_val=prof_val)

        the_time = dt.datetime.now().strftime('%H:%M:%S')
        send_email('marcusdambrosio@gmail.com', 'marcusdambrosio@gmail.com',
                   f'At {the_time} a {ord_type} for {quantity} shares of {symbol} was placed.\n'
                   f'The average cost was $AVGCOSTHERE for a total purchase of $TOTALCOSTHERE.\n'
                   f'The stop is set at ${stop_val} and profit will be taken at ${prof_val}.',
                   subject = 'ORDER PLACED\n')


    def start(self):
        #self.reqPositions()
        self.reqAccountUpdates(True, '')
        #
        # if dt.datetime.today().strftime('%H:%M') == '12:57':
        #     self.execute_order('SPY', 'BUY', 10, 'MKT', price=295, bracket=False, stop_val=293, prof_val=298)

    def stop(self):

        self.reqAccountUpdates(False, '')
        self.done = True
        self.disconnect()


RUN = True

while __name__ == '__main__' and RUN:

    print('starting...')

    #connect with local host and paper account
    try:
        app = TestApp('127.0.0.1', 7497, 1117)
        print('Connected.')

    except:
        print('Connection failed.')
        app.disconnect()

    app.run()
    app.start()


    #req_time = app.server_clock()

    #print(f'The current time from the server is {dt.datetime.fromtimestamp((req_time))}')

    app.stop()
    time.sleep(5)

    #test order




