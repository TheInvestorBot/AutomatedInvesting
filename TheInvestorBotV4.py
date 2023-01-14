import alpaca_trade_api as tradeapi
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time


Alpaca_api_key = "PKUNS9X8WQWRV2IPEBK8"
Alpaca_api_secret = "I53FZoZSRNEIdSntSkJHSmktliAFX7CjFil13Lxo"
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading


class AutoTrader:
    def __init__(self):
        self.Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
        self.ticker_list = ['MMM', 'AOS', 'ABT', 'ACN', 'ATVI', 'ADM', 'ADBE', 'ADP', 'AAP', 'ABBV', 'AES', 'AFL', 'A', 'APD', 'AKAM', 'ALK', 'ALB', 'ARE', 'ALGN', 'ALLE', 'LNT', 'ALL', 'BAX', 'SYF', 'TFC', 'KEY', 'SCHW', 'BSX', 'AMCR', 'GLW', 'WMB', 'D', 'NCLH', 'CRM', 'RCL', 'EQR', 'CRL', 'WST', 'NOW', 'CMG', 'CDAY', 'AES']
        self.owned_list = []
        self.balance = 0


    def pull_stock_data(self, ticker):
        data = yf.download(ticker, start= (datetime.now() - timedelta( days = 4)), end = datetime.now(), interval = "5m")
        return data


    def execute_trade(self, side, ticker):
        # Trade with 1/5th of account value
        if side == 'buy':
            buying_power = (float(self.balance)/5)
            barset = self.Alpaca_trade.get_bars(ticker, "1Min")
            minute_close = barset[-1].c
            # Get most recent price of stock to calculate quantity
            quantity = buying_power/minute_close
            print("Putting in order for " + str(quantity) + " shares of " + ticker + " at " + str(minute_close))
            # Execute trade through Alpaca and send completion message to command line
            self.Alpaca_trade.submit_order(ticker, quantity, side, 'market', 'day')
            print("Purchased " + str(quantity) + " shares of " + ticker)
        elif side == 'sell':
            quantity = self.Alpaca_trade.get_position(ticker).qty
            self.Alpaca_trade.submit_order(ticker, quantity, side, 'market', 'day')
            print("Selling " + str(quantity) + " shares of " + ticker)

    def user_in(self):
        stocks_to_watch = input("Enter stocks tickers to watch seperated by a space.")
        self.ticker_list = stocks_to_watch.split(' ')


    def calculate_technicals(self, dataset):
        # Create 20 and 50 minute exponential moving average
        dataset['20ema'] = dataset['Close'].ewm(span = 20, adjust = False).mean()
        dataset['50ema'] = dataset['Close'].ewm(span = 50, adjust = False).mean()
        return dataset


    def update(self):
        # Updates code on current state of account with owned stocks and balance
        positions = self.Alpaca_trade.list_positions()
        for position in positions:
            self.owned_list.append(str(position.symbol))
        account = self.Alpaca_trade.get_account()
        self.balance = account.buying_power


    def check_ema_crossover(self, dataset, ticker):
        # Compares current and previous 
        # previous20ema = dataset["20ema"][-2]
        # previous50ema = dataset["50ema"][-2]
        current20ema = dataset["20ema"][-1]
        current50ema = dataset["50ema"][-1]
        if (current20ema > current50ema) and (ticker not in self.owned_list):
            # Indicates stock is entering an uptrend so we return True
            return True
        else:
            # Stock is not in an uptrend or we own the stock so we return False
            return False


    def check_bollinger_bands(self, dataset, ticker):
        # Create Bollinger Bands not using today but going to implement in a future version with more options
        dataset['ma21'] = dataset['Close'].rolling(window=21).mean()
        dataset['20sd'] = dataset['Close'].rolling(window = 21).std()
        dataset['upper_band'] = dataset['ma21'] + (dataset['20sd']*2)
        dataset['lower_band'] = dataset['ma21'] - (dataset['20sd']*2)
        if dataset['Close'][-1] <= dataset['lower_band'][-1]:
            # Indication that stock is oversold
            return True
        if dataset['Close'][-1] >= dataset['upper_band'][-1]:
            # Indication that stock is overbought
            return False
        else:
            # We are between Bollinger Bands
            return None


    def check_current_PL(self):
        positions = self.Alpaca_trade.list_positions()
        for position in positions:
            print(position.symbol + " " + position.unrealized_pl)


    def check_for_sell(self, dataset):
        previous20ema = dataset["20ema"][-2]
        previous50ema = dataset["50ema"][-2]
        current20ema = dataset["20ema"][-1]
        current50ema = dataset["50ema"][-1]
        if (previous20ema >= previous50ema) and (current20ema < current50ema):
            # A sell signal is present due to an EMA crossover to the negative side, we return True
            return True
        else:
            # Sell signal not present, we return False
            return False


    def run(self):
        while True:
            self.check_current_PL()
            for stock in self.ticker_list:
                try:
                    self.update()
                    stock_data = self.pull_stock_data(stock)
                    stock_data_updated = self.calculate_technicals(stock_data)
                    result = self.check_ema_crossover(stock_data_updated, stock)
                    if result:
                        self.execute_trade('buy', stock)
                    elif stock in self.owned_list:
                        result = self.check_for_sell(stock_data_updated)
                        if result:
                            self.execute_trade('sell', stock)
                except:
                    continue
                
                time.sleep(250)
            

if __name__ == '__main__':
    # This is the code creating the object and running the bot if the program is called directly.
    TheInvestorBot = AutoTrader()
    TheInvestorBot.run()
                        
