from contract_creator import create_contract
from ibapi.order import *

def create_order(symbol, side, quantity, ord_type, price = '0',
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
    parent_order.action = side
    parent_order.totalQuantity = quantity
    parent_order.orderType = ord_type

    if ord_type == 'LMT':
        parent_order.lmtPrice = price

    #Create contract
    contract = create_contract(symbol)

    #Place Parent Order
    app.placeOrder(app.nextorderId, contract, ord)

    app.nextorderId += 1

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

        print(f'Bracket order for {symbol} created successfully.')
        return [parent_order, stop_loss, take_prof]

    else:
        parent_order.transmit = True
        print(f'{ord_type} for {symbol} created successfully.')
        return parent_order


