from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import datetime as dt
from ibapi.order import *
from ibapi.utils import iswrapper

def create_contract(symbol, sec_type = 'STK', exchange = 'SMART', curr = 'USD'):

    if not symbol:
        raise ValueError('No ticker specified.')

    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = curr
    return contract

def create_order(ordId, symbol, side, quantity, ord_type, price = '0',
                 bracket = False, stop_val = None, prof_val = None):

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

    #Order config
    parent_order = Order()
    parent_order.orderId = ordId
    parent_order.action = side
    parent_order.totalQuantity = quantity
    parent_order.orderType = ord_type

    if ord_type == 'LMT':
        parent_order.lmtPrice = price

    #Create contract
    contract = create_contract(symbol)

    #Place Parent Order
    app.placeOrder(parent_order.orderId, contract, parent_order)

    if bracket:
        parent_order.transmit = False

        stop_loss = Order()
        stop_loss.orderId = parent_order.orderId + 1
        stop_loss.action = 'SELL' if side == 'BUY' else 'BUY'
        stop_loss.totalQuantity = quantity
        stop_loss.orderType = 'LMT'
        stop_loss.lmtPrice = stop_val
        stop_loss.parentId = parent_order.orderId
        stop_loss.transmit = False

        take_prof = Order()
        take_prof.orderId = parent_order.orderId + 2
        take_prof.action = 'SELL' if side == 'BUY' else 'BUY'
        take_prof.totalQuantity = quantity
        take_prof.orderType = 'LMT'
        take_prof.lmtPrice = prof_val
        take_prof.parentId = parent_order.orderId
        take_prof.transmit = True

        app.placeOrder(stop_loss.orderId, contract, stop_loss)
        app.placeOrder(take_prof.orderId, contract, take_prof)

        print(f'Bracket order for {symbol} created successfully.')
        return take_prof.orderId

    else:
        parent_order.transmit = True
        print(f'{ord_type} for {symbol} created successfully.')
        return parent_order.orderId



class IBapi(EWrapper, EClient):

    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)


app = IBapi()
app.connect('127.0.0.1', 7497, 1117)

reset = True
if reset:
    app.nextorderId = 0

def run_loop():
    app.run()

api_thread = threading.Thread(target = run_loop, daemon = True)
api_thread.start()

while True:
    if isinstance(app.nextorderId, int):
        print('connected')
        break
    else:
        print('connecting...')
        time.sleep(1)

init_ord_ID = 100


test_orders = False
while test_orders:

    init_ord_ID = create_order(init_ord_ID, 'SPY', 'SELL', '1', 'MKT', bracket = False ) + 1
    time.sleep(5)

SPY = create_contract('SPY')

app.reqManagedAccts()

time.sleep(2)
app.disconnect()