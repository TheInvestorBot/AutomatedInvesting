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
Alpaca_api_key = ""
Alpaca_api_secret = ""
Alpaca_trade_url = "https://paper-api.alpaca.markets"
#endregion


class MakeMoola:
    def __init__(self):
        self.Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
        self.ticker_list = []
        self.previous_market = 1
    # Meat of code
    def run(self):
        while True:
            market_status = self.Alpaca_trade.get_clock()
            if market_status.is_open:
                if self.previous_market == 1:
                    print("Markets open, getting data on top moving stocks.")
                    self.update()
                self.previous_market = 0
                positions = self.Alpaca_trade.list_positions()
                self.owned_list = []
                for position in positions:
                    self.owned_list.append(str(position.symbol))
                account = self.Alpaca_trade.get_account()
                balance = account.buying_power
                max_spend = (float(balance) / 10)
                # Meat of code
                for ticker in self.owned_list:
                    print("Getting data for owned stock " + ticker)
                    # specify the url
                    urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
                    # run firefox webdriver from executable path of your choice
                    fireFoxOptions = webdriver.FirefoxOptions()
                    fireFoxOptions.set_headless()
                    driver = webdriver.Firefox(options=fireFoxOptions)

                    # get web page
                    driver.get(urlpage)
                    # navigate to correct page and execute script to scroll down the page
                    button = driver.find_elements_by_class_name("tv-tabs__tab")[-1]
                    button.click()
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                    # sleep for 30s
                    time.sleep(5)
                    #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
                    #python_button.click()
                    results = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                    results += driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[2]/div[2]/table/tbody")
                    tiList = []
                    for result in results:
                        tiList.append(result.text)
                    driver.close()
                    oscilatorList = tiList[0].split("\n")
                    OscInd = 0
                    for ind in oscilatorList:
                        if ind.split()[-1] == "Buy":
                            OscInd += 1
                        elif ind.split()[-1] == "Sell":
                            OscInd -= 1
                        else:
                            continue
                    maList = tiList[1].split("\n")
                    maList = maList[:5]
                    MaInd = 0
                    for ma in maList :
                        if ma == "Buy" :
                            MaInd += 1
                        elif ma == "Sell" :
                            MaInd -= 1
                        else: 
                            continue
                    print(ticker + " indicating " + str(OscInd) + " from Oscillators.")
                    if OscInd <= -2:
                        stock_pos = self.Alpaca_trade.get_position (ticker)
                        num = stock_pos.qty
                        print(ticker + " indicating downtrend. Selling " + ticker)
                        try:
                            self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                        except:
                            print("Error in Sell Order, Day Trade Protection Activated")
                    time.sleep(2)

                for ticker in self.ticker_list:
                    print("Getting data for " + ticker)
                    # specify the url
                    urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
                    # run firefox webdriver from executable path of your choice
                    fireFoxOptions = webdriver.FirefoxOptions()
                    fireFoxOptions.set_headless()
                    driver = webdriver.Firefox(options=fireFoxOptions)
                    # get web page
                    driver.get(urlpage)
                    # navigate to correct page and execute script to scroll down the page
                    button = driver.find_elements_by_class_name("tv-tabs__tab")[2]
                    button.click()
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                    # sleep for 30s
                    time.sleep(2)
                    #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
                    #python_button.click()
                    results = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                    results += driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[2]/div[2]/table/tbody")
                    tiList = []
                    for result in results:
                        tiList.append(result.text)
                    driver.close()
                    try:
                        oscilatorList = tiList[0].split("\n")
                        OscInd = 0
                        for ind in oscilatorList:
                            if ind.split()[-1] == "Buy":
                                OscInd += 1
                            elif ind.split()[-1] == "Sell":
                                OscInd -= 1
                            else:
                                continue
                        maList = tiList[1].split("\n")
                        maList = maList[:5]
                        MaInd = 0
                        for ma in maList :
                            if ma == "Buy" :
                                MaInd += 1
                            elif ma == "Sell" :
                                MaInd -= 1
                            else: 
                                continue
                        print(ticker + " indicating " + str(OscInd) + " from Oscillators.")
                        if  OscInd >= 2 and (ticker not in self.owned_list) :
                            barset = self.Alpaca_trade.get_barset(ticker, "minute")
                            ticker_bars = barset[ticker]
                            hour_close = ticker_bars[-1].c
                            quantity = max_spend//hour_close
                            if quantity >= 0:
                                print(ticker + " indicating upward trend. Buying " + str(quantity) + " of " + ticker)
                                try:
                                    self.Alpaca_trade.submit_order(ticker, quantity, 'buy', 'market', 'day')
                                except:
                                    print("Error in Buy Order, aborting.")
                            else:
                                print("Negative Quantity on Purchase error")
                        time.sleep(1)
                    except:
                        print("Error getting stock data. Moving to next stock.")
            else:
                if self.previous_market == 1 :
                    print("Markets closed, waiting.")
                self.previous_market = 0
                time.sleep(720)
        time.sleep(30)
    def update(self):
        # specify the url
        urlpage = 'https://www.tradingview.com/markets/stocks-usa/market-movers-active/' 
        # run firefox webdriver from executable path of your choice
        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.set_headless()
        driver = webdriver.Firefox(options=fireFoxOptions)
        # get web page
        driver.get(urlpage)
        # execute script to scroll down the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        # sleep for 30s
        time.sleep(5)
        i = 1
        while i <= 99 :
            self.ticker_list.append(driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div[3]/div[2]/div[3]/table/tbody/tr[" + str(i) + "]/td[1]/div/div[2]/a")[0].text)
            i += 1
        driver.close()



ls = MakeMoola()
ls.run()


