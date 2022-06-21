import alpaca_trade_api as tradeapi
import urllib.request
from selenium import webdriver
import pandas as pd
import requests
from bs4 import BeautifulSoup
import threading
import time
import datetime
import logging
import argparse
# You must initialize logging, otherwise you'll not see debug output.
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

# API KEYS
#region
Alpaca_api_key = "PKPMDT7MUODYJCW39BWY"
Alpaca_api_secret = "Bu1Z8FpUk/ep/Fdc7azJYhWJZahc6FC3nZgwHERs"
Alpaca_trade_url = "https://paper-api.alpaca.markets"
Alpaca_data_url = "https://data.alpaca.markets/v1"
#endregion


class MakeMoola:
    def __init__(self):
        self.Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url, api_version='v2')
        self.Alpaca_data = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_data_url, api_version='v2')
        self.ticker_list = []
    # Meat of code
    def run(self):
        market_status = self.Alpaca_trade.get_clock()
        if market_status.is_open:
            positions = self.Alpaca_trade.list_positions()
            self.owned_list = []
            for position in positions:
                self.owned_list.append(str(position.symbol))
            account = self.Alpaca_trade.get_account()
            balance = account.buying_power
            max_spend = (float(balance) / 6) - 25000.00
            # Meat of code
            for stock in self.owned_list:
                print("Getting data on owned stock " + stock)
                # specify the url
                urlpage = 'https://www.tradingview.com/symbols/NYSE-' + stock.upper() + '/technicals/' 
                # run firefox webdriver from executable path of your choice
                fireFoxOptions = webdriver.FirefoxOptions()
                fireFoxOptions.set_headless()
                driver = webdriver.Firefox(options=fireFoxOptions)

                # get web page
                driver.get(urlpage)
                # execute script to scroll down the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                # sleep for 1s
                time.sleep(1)
                python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
                python_button.click()
                results = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                results += driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[2]/div[2]/table/tbody")
                tiList = []
                for result in results:
                    tiList.append(result.text)
                oscilatorList = tiList[0].split("\n")
                indication = 0
                for ind in oscilatorList:
                    if ind.split()[-1] == "Buy":
                        indication += 1
                    elif ind.split()[-1] == "Sell":
                        indication -= 1
                    else:
                        continue
                maList = tiList[1].split("\n")
                driver.close()
                print(stock + " indicating " + str(indication))
                if indication <= -2:
                    stock_pos = self.Alpaca_trade.get_position (stock)
                    num = stock_pos.qty
                    print(stock + " indicating downtrend. Selling " + stock)
                    self.Alpaca_trade.submit_order(stock, num, 'sell', 'market', 'day')
                time.sleep(5)

            for ticker in self.ticker_list:
                print("Getting data for " + ticker)
                # specify the url
                urlpage = 'https://www.tradingview.com/symbols/NYSE-' + ticker.upper() + '/technicals/' 
                # run firefox webdriver from executable path of your choice
                fireFoxOptions = webdriver.FirefoxOptions()
                fireFoxOptions.set_headless()
                driver = webdriver.Firefox(options=fireFoxOptions)

                # get web page
                driver.get(urlpage)
                # execute script to scroll down the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                # sleep for 30s
                time.sleep(1)
                python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
                python_button.click()
                results = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                results += driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[2]/div[2]/table/tbody")
                tiList = []
                for result in results:
                    tiList.append(result.text)
                oscilatorList = tiList[0].split("\n")
                indication = 0
                for ind in oscilatorList:
                    if ind.split()[-1] == "Buy":
                        indication += 1
                    elif ind.split()[-1] == "Sell":
                        indication -= 1
                    else:
                        continue
                maList = tiList[1].split("\n")
                print(ticker + " indicating " + str(indication))
                driver.close()
                if  indication >= 3 and (ticker not in self.owned_list) :
                    barset = self.Alpaca_trade.get_barset(ticker, "minute")
                    ticker_bars = barset[ticker]
                    hour_close = ticker_bars[-1].c
                    quantity = max_spend//hour_close
                    if quantity != 0:
                        print(ticker + " indicating upward trend. Buying " + str(quantity) + " of " + ticker)
                        self.Alpaca_trade.submit_order(ticker, quantity, 'buy', 'market', 'day')
                time.sleep(5)
        else:
            print("Markets closed, waiting.")
            time.sleep(720)
    
    def update(self):
        URL = 'https://money.cnn.com/data/hotstocks/'
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find_all('a', class_='wsod_symbol')
        self.ticker_list = []
        for result in results:
            self.ticker_list.append(result.text)
        self.ticker_list = self.ticker_list[3:]


ls = MakeMoola()
while True:
    ls.update()
    ls.run()
    time.sleep(60)

