from ibapi.contract import Contract

def create_contract(symbol, sec_type = 'STK', exchange = 'SMART', curr = 'USD'):

    if not symbol:
        raise ValueError('No ticker specified.')

    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = curr
    return contract
