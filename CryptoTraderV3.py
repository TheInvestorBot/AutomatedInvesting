import alpaca_trade_api as tradeapi
import urllib.request
from alpaca_trade_api.entity import Order
from selenium import webdriver
import pandas as pd
import requests
from bs4 import BeautifulSoup
import threading
import time
import datetime
import logging
import argparse

#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True


Alpaca_api_key = "PKOJ0W85OW99DJP4YTZT"
Alpaca_api_secret = "7FY9FbNbPR8fgHGho9f6KCH33b4u6gWymEzOlpSX"
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading
#endregion
firstRun = 0
EMA20 = 0
EMA50 = 0
previous50EMA = 0
previous20EMA = 0
Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
while True:

    positions = Alpaca_trade.list_positions()
    owned_list = []
    for position in positions:
        owned_list.append(str(position.symbol))


    account = Alpaca_trade.get_account()
    balance = float(account.buying_power) - 500.00

    url = "https://www.investing.com/crypto/ethereum/eth-usd-technical"

    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.headless = True
    driver = webdriver.Firefox(options=fireFoxOptions)

    # get web page
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    button = driver.find_elements_by_xpath("/html/body/div[4]/section/div[8]/ul/li[2]")[0]
    time.sleep(1)
    button.click()
    driver.refresh()
    EMA20 = driver.find_elements_by_xpath("/html/body/div[4]/section/div[10]/div[4]/table/tbody/tr[3]/td[3]")[0].text.split("\n")[0]
    time.sleep(1)
    print("Current EMA20 is " + str(EMA20))
    EMA50 = driver.find_elements_by_xpath("/html/body/div[4]/section/div[10]/div[4]/table/tbody/tr[4]/td[3]")[0].text.split("\n")[0]
    time.sleep(1)
    print("Current EMA50 is " + str(EMA50))
    if firstRun == 0:
        print("Logging initial EMA20 and EMA50")
        previous20EMA = EMA20
        previous50EMA = EMA50
        firstRun = 1
        driver.close()
        time.sleep(300)
        continue
    else: 
        if (previous20EMA <= previous50EMA) and (EMA20 > EMA50) and ("ETHUSD" not in owned_list):
            price = driver.find_elements_by_xpath("/html/body/div[4]/section/div[4]/div[1]/div[1]/div[2]/div[1]/span[1]")[0].text.replace(",", "")
            quantity = round(balance/float(price), 3)
            print(quantity)
            print("Indicating Buy, Buying Ethereum.")
            print(Alpaca_trade.submit_order("ETHUSD", qty=quantity, side='buy'))
            continue
        
        elif ("ETHUSD" in owned_list):
            position = Alpaca_trade.get_position("ETHUSD")
            if float(position.unrealized_plpc) >= 0.10:
                print("Take profit hit, selling Ethereum.")
                Alpaca_trade.submit_order("ETHUSD", qty=position.qty, side='sell')
            elif float(position.unrealized_plpc) <= -0.08:
                print("Stop loss hit. Selling Ethereum.")
                Alpaca_trade.submit_order("ETHUSD", qty=position.qty, side='sell')
        
        previous50EMA = EMA50
        previous20EMA = EMA20
        driver.close()
        time.sleep(300)