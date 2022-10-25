from iexfinance.stocks import get_historical_data
import datetime as dt
import time
import os

os.environ['IEX_TOKEN'] = 'sk_129d923338c640f99167d869165e8f52'

def get_scalers(tickers):

    days_back = 0
    scaler_dict = {}
    close = []
    data = []
    while not len(data):

        days_back += 1
        yesterday = dt.datetime.today() - dt.timedelta(days_back)
        data = get_historical_data('GOOG', yesterday, dt.datetime.today(), output_format='pandas')


    for ticker in tickers:

        data = get_historical_data(ticker, yesterday, dt.datetime.today(), output_format = 'pandas')
        close = data['close']
        open = data['open']
        scaler_dict[f'{ticker}'] = open[0]

    if len(scaler_dict) < len(tickers):
        raise TypeError('Dictionary insufficiently full.')

    print(scaler_dict)
    return scaler_dict


def sleep_time(offset = 5):

    targethr = 8
    targetmin = 30

    hour = dt.datetime.today().strftime('%H')
    minute = dt.datetime.today().strftime('%M')
    second = dt.datetime.today().strftime('%S')

    offset = offset
    seconds_until = 3600 * (targethr - hour) + 60 * (targetmin - minute) + second + offset

    #time.sleep(seconds_until)
    return seconds_until



