import ccxt
import time
import numpy as np
import pandas as pd
from datetime import datetime

# Binance API keys
api_key = 'aVjdYS1kbn2n2n5q9bDSsgbdVfV4FDEKPPSF9oNB5K1btgE13Dots73mebC6rr7y'
secret_key = 'shYZ4CVQM6p8JQ6CYy4poy1m8Hc3r32QUVHCrKDJpN85Qi7l83KIgfWTZri1AmtF'

# Initialize the Binance API
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret_key,
})

# Configure the bot
symbol = 'BTC/USDT'
fast_ma_length = 9
slow_ma_length = 21
timeframe = '1h'

def get_data():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def get_last_order():
    orders = exchange.fetch_closed_orders(symbol)
    if orders:
        return orders[-1]
    return None

def get_balance():
    balance = exchange.fetch_balance()
    return balance['free']['USDT'], balance['free']['BTC']

def buy_sell_signal(df):
    df['fast_ma'] = df['close'].rolling(window=fast_ma_length).mean()
    df['slow_ma'] = df['close'].rolling(window=slow_ma_length).mean()
    df['signal'] = np.where(df['fast_ma'] > df['slow_ma'], 1, -1)
    return df['signal'].iloc[-1]

def create_order(signal, free_usdt, free_btc):
    if signal > 0 and free_usdt > 10:
        amount = free_usdt / exchange.fetch_ticker(symbol)['ask']
        exchange.create_market_buy_order(symbol, amount)
        print("Buy Order Executed")
    elif signal < 0 and free_btc > 0.0001:
        exchange.create_market_sell_order(symbol, free_btc)
        print("Sell Order Executed")

while True:
    try:
        df = get_data()
        signal = buy_sell_signal(df)
        free_usdt, free_btc = get_balance()
        last_order = get_last_order()
        
        print(f"Signal: {signal}")
        print(f"Free USDT: {free_usdt}")
        print(f"Free BTC: {free_btc}")
        
        if last_order:
            print(f"Last Order: {last_order['side']} at {datetime.fromtimestamp(last_order['timestamp'] / 1000)}")
        
        create_order(signal, free_usdt, free_btc)
        
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(60 * 60)  # Wait for an hour before checking again
