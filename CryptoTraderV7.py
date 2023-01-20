import alpaca_trade_api as tradeapi
from alpaca_trade_api.entity import Order
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from Historic_Crypto import HistoricalData

Alpaca_api_key = "xxxxx"
Alpaca_api_secret = "xxxxxx"
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading

class CryptoTrader:
    def __init__(self):       
        self.Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
        self.balance = 0
        self.owned_list = []
    
    def update(self):
        positions = self.Alpaca_trade.list_positions()
        for position in positions:
            self.owned_list.append(str(position.symbol))
        account = self.Alpaca_trade.get_account()
        self.balance = account.buying_power

    def pull_crypto_data(self, ticker):
        date = str(datetime.now()-timedelta(days = 4))
        dates = date.split(" ")
        hour = dates[-1].split(":")[0]
        minutes = dates[-1].split(":")[1]
        date = dates[0] + "-" + hour + "-" + minutes
        crypto_data = HistoricalData(ticker, 60, date).retrieve_data()
        return(crypto_data)

    def calculate_technicals(self, dataset):
        # Create Bollinger Bands not using today but going to implement in a future version with more options
        dataset['ma41'] = dataset['Close'].rolling(window = 41).mean()
        dataset['20sd'] = dataset['Close'].rolling(window = 41).std()
        dataset['upper_band'] = dataset['ma41'] + (dataset['20sd']*2)
        dataset['lower_band'] = dataset['ma41'] - (dataset['20sd']*2)
        return(dataset)

    def check_for_crossover(self, dataset, ticker):
        previous_upper_band = dataset['upper_band'][-2]
        previous_lower_band = dataset['lower_band'][-2]
        previous_close = dataset['close'][-2]
        current_upper_band = dataset['upper_band'][-1]
        current_lower_band = dataset['lower_band'][-1]
        current_close = dataset['close'][-1]

        if (previous_close < previous_upper_band) and (current_close >= current_upper_band) and (ticker not in self.owned):
            # This indicates we have a positive signal on a crypto we do not own and want to enter a long position, we will return enter_long
            indication = "enter_long"

        elif (previous_close > previous_lower_band) and (current_close <= current_lower_band) and (ticker not in self.owned):
            # This indicates we have a negative signal on a crypto we do not own and we want to enter a short position, we will return enter_short
            indication = "enter_short"

        elif (previous_close > previous_lower_band) and (current_close <= current_lower_band) and (ticker in self.owned):
            # This indicates we have a negative signal on an owned crypto and we want to close our long position and enter a short, we will return close_long_enter_short
            indication = "close_long_enter_short"

        elif (previous_close < previous_upper_band) and (current_close >= current_upper_band) and (ticker in self.owned):
            # This indicates we have a positive signal on an owned crypto, we want to close our short and enter a long position, we will return close_short_enter_long
            indication = "close_short_enter_long"

        else:
            # If none of the above conditions are met, we want to maintain our current positions, we will return hold
            indication = "hold"

        return indication

    def execute_trade(self, indication, ticker, most_recent_price):
        buying_power = self.balance/3
        quantity = round(buying_power/most_recent_price, 3)

        if indication == "enter_long":
            self.Alpaca_trade.submit_order(ticker, qty=quantity, side='buy')
            print("Entering Long Position")

        elif indication == "enter_short":
            self.Alpaca_trade.submit_order(ticker, qty=quantity, side='sell')
            print("Entering Short Position")

        elif indication == "close_long_enter_short":
            owned = self.Alpaca_trade.get_position(ticker).qty
            self.Alpaca_trade.submit_order(ticker, qty=owned, side='sell')
            self.update()
            buying_power = self.balance/3
            quantity = round(buying_power/most_recent_price, 3)
            self.Alpaca_trade.submit_order(ticker, qty=quantity, side='sell')
            print("Closing Long Entering Short")

        elif indication == "close_short_enter_long":
            owned = self.Alpaca_trade.get_position(ticker).qty
            self.Alpaca_trade.submit_order(ticker, qty=owned, side='buy')
            self.update()
            buying_power = self.balance/3
            quantity = round(buying_power/most_recent_price, 3)
            self.Alpaca_trade.submit_order(ticker, qty=quantity, side='buy')
            print("Closing Long Entering Short")

    def run(self):
        while True:
            self.update()
            dataset = self.pull_crypto_data("ETHUSD")
            dataset_w_bollinger = self.calculate_technicals(dataset)
            indication = self.check_for_crossover(dataset_w_bollinger, "ETHUSD")
            self.execute_trade(indication, "ETHUSD", dataset['close'][-1])

if __name__ == "__main__":
    trader = CryptoTrader()
    trader.run
