
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import datetime as dt
from ibapi.order import *
from ibapi.utils import iswrapper

class IBapi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining,
              'lastFillPrice', lastFillPrice)

    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action,
              order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
              execution.orderId, execution.shares, execution.lastLiquidity)


def create_contract(symbol, sec_type = 'STK', exchange = 'SMART', curr = 'USD'):

    if not symbol:
        raise ValueError('No ticker specified.')

    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = curr
    return contract

def create_order(symbol, side, quantity, type, price = '0', _returninfo = False):

    if not symbol:
        raise ValueError('No ticker specified')

    if not side:
        raise ValueError('Buy or Sell?')

    if not quantity:
        raise ValueError('No quantity specified')

    if not type:
        raise ValueError('No order type specified')

    if type == 'LMT' and price == '0':
        raise ValueError('Limit value not specified')

    #Order config

    ord = Order()
    ord.action = side
    ord.totalQuantity = quantity
    ord.orderType = type

    if type == 'LMT':
        ord.lmtPrice = price

    #Create contract
    contract = create_contract(symbol)

    #Place Order
    app.placeOrder(app.nextorderId, contract, ord)

    #app.nextorderId += 1

    if _returninfo:

        return symbol, side, quantity, type, price

def stop_loss(stop_price, parent):

    stop = Order()
    stop.action = 'SELL'

    # SET QUANTITY AS OPEN POS
    #stop.totalQuantity = quantity
    stop.orderType = 'STP'
    stop.auxPrice = stop_price
    stop.orderId = app.nextorderId
    app.nextorderId += 1
    #figure out how to get Order() object ord into this function
    stop.parentId = parent.orderId
    parent.transmit = True

    app.placeOrder(stop_order.orderId, create_contract(symbol), stop)


def run_loop():
    app.run()

app = IBapi()

app.nextorderId = None

'''
app.connect('127.0.0.1', 7497, 1117)
app.nextorderId = None

api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
'''
while True:
    if isinstance(app.nextorderId, int):
        print('connected')
        break
    else:
        print('connecting...')
        time.sleep(1)

'''
order('SPY', 'BUY', '10', 'LMT', price = '150')

orders = app.reqOpenOrders()

print(orders)

time.sleep(5)
'''


