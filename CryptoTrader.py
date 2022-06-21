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


Alpaca_api_key = ""
Alpaca_api_secret = ""
Alpaca_trade_url = "https://paper-api.alpaca.markets" # Needs to be changed to non-paper for real trading
#endregion

Alpaca_trade = tradeapi.REST(Alpaca_api_key, Alpaca_api_secret, Alpaca_trade_url)
while True:
    try:
        positions = Alpaca_trade.list_positions()
        owned_list = []
        for position in positions:
            owned_list.append(str(position.symbol))


        account = Alpaca_trade.get_account()
        balance = float(account.buying_power) - 20.00

        url = "https://www.investing.com/crypto/ethereum/eth-usd-technical"

        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.headless = True
        driver = webdriver.Firefox(options=fireFoxOptions)

        # get web page
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        button = driver.find_elements_by_xpath("/html/body/div[5]/section/div[8]/ul/li[1]")[0]
        time.sleep(1)
        try:
            button.click()
        except:
            driver.close() 
            continue
        indicator = driver.find_elements_by_xpath("/html/body/div[5]/section/div[10]/div[1]/div[1]/span")[0].text
        

        if (indicator == "BUY" or indicator == "STRONG BUY") and "ETHUSD" not in owned_list:
            price = driver.find_elements_by_xpath("/html/body/div[5]/section/div[4]/div[1]/div[1]/div[2]/div[1]/span[1]")[0].text.replace(",", "")
            quantity = balance/float(price)
            print("Indicating Buy, Buying Bitcoin.")
            Alpaca_trade.submit_order("ETHUSD", quantity, 'buy', 'market', 'day')

        elif (indicator == "SELL" or indicator == "STRONG SELL") and "ETHUSD" in owned_list:
            stock_pos = Alpaca_trade.get_position("ETHUSD")
            num = stock_pos.qty
            print("Indicating Sell, Selling Bitcoin")
            Alpaca_trade.submit_order("ETHUSD", num, 'sell', 'market', 'day')
        driver.close()
        time.sleep(5)
    except:
        driver.close()
        continue
