# The Investor Bot
# This is the bot I have designed to do some trading for me. I have tested it on paper-trading markets and had mixed
# results, overall positive. Currently the way I am pulling data on stocks is a little janky, lots of sketchy HTML
# scraping that I'm not sure the websites would be ecstatic about. Additionally, the current was that the program
# decides when to buy and sell is about as basic as it gets. It essentially looks at all the technical indicators
# and moving averages the site provides and gives +2 if they indicate strong buy, +1 for buy, 0 for neutral, -1 for
# sell, and -2 for strong sell. If the sum of all indicators is +3 or greater, we buy. We then check back on that 
# stock and then sell if the average drops under -2. Long term I would like this software to be something that allows
# individuals to enter a trading strategy based of off specific indicators and allows the bot to trade for them.
# First thing on the adgenda, though, is making a more effective trading algorithm.


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

# You must initialize logging, otherwise you'll not see debug output, but who needs that.
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

# API KEYS
#region
Alpaca_api_key = "INSERT API KEY"
Alpaca_api_secret = "INSERT SECRET KEY"
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading
#endregion


class MakeMoola:
    def __init__(self):
        self.Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
        self.ticker_list = []
        self.previous_market = 1
        self.stock_source = 1
        self.trading_strategy = 5
        self.max_spend = .20
        self.balance = 0
        self.RSI_buy_limit = 35
        self.RSI_sell_limit = 70
        self.owned_list = []
        self.trading_timeframe = 1

    def Wait(self):
        # This code should run first to wait for market open
        market_status = self.Alpaca_trade.get_clock()
        if market_status.is_open:
            if self.previous_market == 1 and self.stock_source == 2:
                print("Markets open, getting data on top moving stocks.")
                self.ImportStocks()
            self.previous_market = 0
        else:
            time.sleep(720)

    def UpdateOwned(self):
        # This code needs to run after any trade to update balance and stocks owned.
        positions = self.Alpaca_trade.list_positions()
        for position in positions:
            self.owned_list.append(str(position.symbol))
        account = self.Alpaca_trade.get_account()
        self.balance = account.buying_power
            
    def ImportStocks(self):
        # specify the url.
        # This is where I pull my list of stocks to monitor, I am using the top 100 market movers.
        # If you had another stock you wanted to trade you could just make the list manually or pull from somwhere else.
        urlpage = 'https://www.tradingview.com/markets/stocks-usa/market-movers-active/' 
        # run firefox webdriver from executable path of your choice
        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.set_headless()
        driver = webdriver.Firefox(options=fireFoxOptions)
        # get web page
        driver.get(urlpage)
        # execute script to scroll down the page, this ensures that all content is loaded.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        # sleep for 5s
        time.sleep(5)
        # Maybe the dumbest possible way of doing this.
        i = 1
        while i <= 50 :
            self.ticker_list.append(driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/div/div/div[3]/div[2]/div[3]/table/tbody/tr[" + str(i) + "]/td[1]/div/div[2]/a")[0].text)
            i += 1
        # P.S. if you mess something up when developing that causes the below line of code to not execute you will make
        # Firefox headless tabs until your computer explodes. (Not literally)
        driver.close()
        self.stock_source = 2

    def UserStocks(self):
        # Allow the user to input stocks to monitor rather than pulling from top mover list.
        stocks = input("Please enter stocks to moniter separated by commas (APPL, TSLA, GME): ")
        try:
            self.ticker_list = stocks.split(", ")
            self.stock_source = 1
        except:
            print("Please enter data in valid format.")
            exit()

    def RSIStrategy(self):
        for ticker in self.owned_list:
            print("Getting data for owned stock " + ticker)
            urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
            # run firefox webdriver from executable path of your choice
            fireFoxOptions = webdriver.FirefoxOptions()
            fireFoxOptions.set_headless()
            driver = webdriver.Firefox(options=fireFoxOptions)
            # get web page
            driver.get(urlpage)
            # navigate to correct page and execute script to scroll down the page
            market = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/header/div/div[2]/div[1]/h1/div/span/span[2]/span")[0]
            if market.text == "NYSE":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-4]
            elif market.text == "NASDAQ":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-5]
            button.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            # sleep for 5s
            time.sleep(5)
            # Commented python_button code will allow the headless driver to click on a different timeframe for analysis, changing the timeframe of making trades
            #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
            #python_button.click()
            RSI = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]")[0]
            driver.close()
            if RSI >= self.RSI_sell_limit:
                stock_pos = self.Alpaca_trade.get_position(ticker)
                num = stock_pos.qty
                print(ticker + " indicating downtrend. Selling " + ticker)
                try:
                    self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                except:
                    print("Error in Sell Order, Day Trade Protection Activated")
            time.sleep(2)
        for ticker in self.ticker_list:
            print("Getting data for owned stock " + ticker)
            urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
            # run firefox webdriver from executable path of your choice
            fireFoxOptions = webdriver.FirefoxOptions()
            fireFoxOptions.set_headless()
            driver = webdriver.Firefox(options=fireFoxOptions)
            # get web page
            driver.get(urlpage)
            # navigate to correct page and execute script to scroll down the page
            market = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/header/div/div[2]/div[1]/h1/div/span/span[2]/span")[0]
            if market.text == "NYSE":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-4]
            elif market.text == "NASDAQ":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-5]
            button.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            # sleep for 5s
            time.sleep(5)
            # Commented python_button code will allow the headless driver to click on a different timeframe for analysis, changing the timeframe of making trades
            #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
            #python_button.click()
            RSI = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]")[0]
            driver.close()
            if RSI <= self.RSI_buy_limit:
                stock_pos = self.Alpaca_trade.get_position(ticker)
                num = stock_pos.qty
                print(ticker + " indicating downtrend. Selling " + ticker)
                try:
                    self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                except:
                    print("Error in Sell Order, Day Trade Protection Activated")
            time.sleep(2)

    def MovingAverageSum(self):
        for ticker in self.owned_list:
            print("Getting data for owned stock " + ticker)
            urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
            # run firefox webdriver from executable path of your choice
            fireFoxOptions = webdriver.FirefoxOptions()
            fireFoxOptions.set_headless()
            driver = webdriver.Firefox(options=fireFoxOptions)
            # get web page
            driver.get(urlpage)
            # navigate to correct page and execute script to scroll down the page
            market = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/header/div/div[2]/div[1]/h1/div/span/span[2]/span")[0]
            if market.text == "NYSE":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-4]
            elif market.text == "NASDAQ":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-5]
            button.click()
            button = driver.find_elements_by_xpath('//*[@id="technicals-root"]/div/div/div[1]/div/div/div')[self.trading_timeframe + 2]
            button.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            # sleep for 5s
            time.sleep(5)
            #Commented python_button code will allow the headless driver to click on a different timeframe for analysis, changing the timeframe of making trades
            #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
            #python_button.click()
            MANum = 0
            i = 1
            while i<= 15:
                i += 1
                MAIndication = driver.find_elements_by_xpath('//*[@id="technicals-root"]/div/div/div[3]/div[2]/div[2]/table/tbody/tr[' + str(i) + ']/td[3]')
                if MAIndication.text == 'Buy':
                    MANum += 1
                elif MAIndication.text == 'Sell':
                    MANum -= 1
                else:
                    continue

            driver.close()
            if MANum >= self.RSI_sell_limit:
                stock_pos = self.Alpaca_trade.get_position(ticker)
                num = stock_pos.qty
                print(ticker + " indicating downtrend. Selling " + ticker)
                try:
                    self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                except:
                    print("Error in Sell Order, Day Trade Protection Activated")
            time.sleep(2)
        for ticker in self.ticker_list:
            print("Getting data for owned stock " + ticker)
            urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
            # run firefox webdriver from executable path of your choice
            fireFoxOptions = webdriver.FirefoxOptions()
            fireFoxOptions.set_headless()
            driver = webdriver.Firefox(options=fireFoxOptions)
            # get web page
            driver.get(urlpage)
            # navigate to correct page and execute script to scroll down the page
            market = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/header/div/div[2]/div[1]/h1/div/span/span[2]/span")[0]
            if market.text == "NYSE":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-4]
            elif market.text == "NASDAQ":
                button = driver.find_elements_by_class_name("tv-tabs__tab")[-5]
            button.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            # sleep for 5s
            time.sleep(5)
            # Commented python_button code will allow the headless driver to click on a different timeframe for analysis, changing the timeframe of making trades
            #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
            #python_button.click()
            RSI = driver.find_elements_by_xpath("/html/body/div[2]/div[6]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]")[0]
            driver.close()
            if RSI <= self.RSI_buy_limit:
                stock_pos = self.Alpaca_trade.get_position(ticker)
                num = stock_pos.qty
                print(ticker + " indicating downtrend. Selling " + ticker)
                try:
                    self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                except:
                    print("Error in Sell Order, Day Trade Protection Activated")
            time.sleep(2)

if __name__ == '__main__':
    # This is the code making the object and running the bot if the program is called directly.
    ls = MakeMoola()
    print('''   1. Input own stocks
    2. Get 50 top moving stocks from web''')
    choice = int(input("Enter Option: "))
    if choice == 1:
        ls.UserStocks()
    elif choice == 2:
        ls.ImportStocks()

    print("TRADING STRATEGIES")
    print('''   1. Pure RSI Trading
    2. Moving Average Summing
    3. Technical Indicator Summing 
    4. Price Deviation Trading
    5. All Indications Sum''')
    trade_strat = int(input("Please pick trading strategy: "))
    print("TIMEFRAMES")
    print(''' 1. 30 Minutes  
    2. 1 Hour
    3. 2 Hour
    4. 4 Hour
    5. 1 Day
    6. 1 Week ''')
    ls.trading_timeframe = int(input("Please select a timeframe for your trading strategy: "))
    if trade_strat == 1:
        ls.RSI_buy_limit = input("Please enter the RSI you would like to buy at or below: ")
        ls.RSI_sell_limit = input("Please enter the RSI you would like to sell at or above: ")
        while True:
            ls.UpdateOwned()
            ls.RSIStrategy()
    elif trade_strat == 2:
        print("Trading stocks based on a sum of moving averages.")
        ls.UpdateOwned()
        ls.MovingAverageSum()
    elif trade_strat == 3:
        pass
    elif trade_strat == 4:
        pass
    elif trade_strat == 5:
        pass
    else:
        print("Pick a valid number you ape.")


