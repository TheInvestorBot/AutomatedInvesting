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
Alpaca_api_key = "PK8DQMWBOMNFBUM7ZF1L"
Alpaca_api_secret = "L9O5z6RI45Qr7Ms6YwkZ9PsAltwcmLVoxOfWvEUM"
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading
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
                for ticker in self.owned_list:
                    position = self.Alpaca_trade.get_position(ticker)
                    PL = position.unrealized_plpc
                    num = position.qty
                    if float(PL) >= 0.05:
                        print("Profit margin hit on " + ticker + ", selling.")
                        self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                    elif float(PL) <= -0.03:
                        print("Stop-loss hit on " + ticker + ", selling.")
                        self.Alpaca_trade.submit_order(ticker, num, 'sell', 'market', 'day')
                        time.sleep(1)
                for ticker in self.ticker_list:
                    print("Getting data for " + ticker)
                    # specify the url
                    urlpage = 'https://www.tradingview.com/symbols/' + ticker.upper()
                    # run firefox webdriver from executable path of your choice
                    fireFoxOptions = webdriver.FirefoxOptions()
                    fireFoxOptions.headless = True
                    # This method of setting headless mode is outdated, but I'm too lazy to correct it until it breaks the code.
                    driver = webdriver.Firefox(options=fireFoxOptions)
                    # get web page
                    driver.get(urlpage)
                    try:# navigate to correct page and execute script to scroll down the page
                        button = driver.find_elements_by_class_name("tv-tabs__tab")[-1]
                        button.click()
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                        # sleep for 2s
                        # Commented python_button code will allow the headless driver to click on a different timeframe for analysis, changing the timeframe of making trades
                        #python_button = driver.find_elements_by_xpath("/html/body/div[2]/div[5]/div/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[1]/div/div/div[1]/div/div/div[3]")[0]
                        #python_button.click()
                        #results = driver.find_elements_by_xpath("/html/body/div[2]/div[4]/div[3]/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                        #results += driver.find_elements_by_xpath("/html/body/div[2]/div[4]/div[3]/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[2]/div[2]/table/tbody")
                        try:
                            tiList = driver.find_elements_by_xpath("/html/body/div[2]/div[4]/div[3]/div/div/div/div/div/div/div[2]/div/div[2]/div/div/div[3]/div[1]/div[2]/table/tbody")
                            indicatorList = []
                            for item in tiList[0].text.split('\n'):
                                indicatorList.append(item)
                            driver.close()
                            OscInd = 0
                            for item in indicatorList:
                                if item.split(" ")[-1] == "Buy":
                                    OscInd += 1
                                elif item.split(" ")[-1] == "Sell":
                                    OscInd -= 1
                                else:
                                    continue
                            # Parsing results from HTML scraping and using them to determine trends
                            # The reason there is a try/except is because sometimes it doesn't work and I don't want that to crash the bot :)
                            # Also some of the stocks pages are slightly different if they don't contain a field. That throws off the parsing
                            #for result in results:
                                #tiList.append(result.text)
                            
                            print(ticker + " indicating " + str(OscInd) + " from Oscillators.")
                        except:
                            driver.close()
                            OscInd = 0
                            print("Error pulling stock data, moving to next stock.")
                    except:
                        driver.close()
                        OscInd = 0
                        print("Go fuck yourself.")
                    if  OscInd >= 3 and (ticker not in self.owned_list) :
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
            else:
                if self.previous_market == 1 :
                    print("Markets closed, waiting.")
                self.previous_market = 0
                time.sleep(720)
        time.sleep(30)
    def update(self):
        # specify the url.
        # This is where I pull my list of stocks to monitor, I am using the top 100 market movers.
        # If you had another stock you wanted to trade you could just make the list manually or pull from somwhere else.
        urlpage = 'https://www.tradingview.com/markets/stocks-usa/market-movers-active/' 
        # run firefox webdriver from executable path of your choice
        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.headless = True
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
            self.ticker_list.append(driver.find_elements_by_xpath("/html/body/div[2]/div[4]/div[2]/div/div/div[3]/div[2]/div[4]/table/tbody/tr[" + str(i) + "]/td[1]/div/div[2]/a")[0].text)
            i += 1
        # P.S. if you mess something up when developing that causes the below line of code to not execute you will make
        # Firefox headless tabs until your computer explodes. (Not literally)
        driver.close()


if __name__ == '__main__':
    # This is the code making the object and running the bot if the program is called directly.
    ls = MakeMoola()
    ls.run()


