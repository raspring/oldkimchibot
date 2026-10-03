#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  5 09:14:35 2022

dictionary
status
coins
    unix = only 1 transaction per unix

@author: robertspringett
"""

import websocket
import time
import json
import threading
import datetime

class bithumb_trade_WS():
    
  def __init__(self,parent_class=None):
        if parent_class != None:
            self.parent_class = parent_class
        self.pair = ["BTC_KRW","ETH_KRW"]
        self.data = {}
        for items in self.pair:
          self.data[items] = []
        self.connect_websocket()
        return

  def ws_message(self,ws,message):
    temp = json.loads(message)
    if 'status' in temp:
      self.status_message(temp)
    elif temp['type'] == 'transaction':
      self.transaction_message(temp)

  def ws_open(self,ws):
    '''coins hardcoded'''
    self.ws.send('{"type":"transaction", "symbols":["BTC_KRW", "ETH_KRW"]}')
    print("bithumb connection established")

  def connect_websocket(self):
      self.ws = websocket.WebSocketApp("wss://pubwss.bithumb.com/pub/ws", on_open = self.ws_open, on_message = self.ws_message,on_close = self.on_close)
      wst = threading.Thread(target=self.ws.run_forever)
      wst.start()

  def on_close(self,ws):
    print ("Bithumb Retry : %s" % time.ctime())
    time.sleep(10)
    self.connect_websocket() # retry per 10 seconds

  def status_message(self,raw_message):
      self.status = raw_message
      
  def transaction_message(self,raw_message):
      raw_message = raw_message['content']['list'][0]
      unix = int(time.mktime(datetime.datetime.strptime(raw_message['contDtm'], "%Y-%m-%d %H:%M:%S.%f").timetuple()))
      unix = unix-3600
      symbol = raw_message['symbol']
      coin = symbol[0:3]
      px = int(raw_message['contPrice'])
      qty = float(raw_message['contQty'])
      if unix not in [x[0] for x in self.data[symbol]]:
          self.data[symbol].append([unix,coin,symbol,px,qty])
          self.parent_class.trades[coin]['bithumb'] = [unix,coin,symbol,px,qty]
          if unix == self.parent_class.trades[coin]['kraken'][0]:
              self.parent_class.both.append([self.parent_class.trades[coin]['kraken'][0:4],unix,coin,symbol,px])

class kraken_trade_WS():
    
  def __init__(self,parent_class=None):
        if parent_class != None:
            self.parent_class = parent_class
        self.pair = ["XBT/USD","ETH/USD"]
        self.data = {}
        for items in self.pair:
          self.data[items] = []
        self.connect_websocket()
        return

  def ws_message(self,ws,message):
    temp = json.loads(message)
    if "connectionID" in temp:
      self.status_message(temp)
    elif temp[3] in self.data:
      self.transaction_message(temp)

  def ws_open(self,ws):
    self.ws.send('{"event":"subscribe", "subscription":{"name":"trade"}, "pair":["XBT/USD","ETH/USD"]}')
    print("kraken connection established")

  def connect_websocket(self):
    self.ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open = self.ws_open, on_message = self.ws_message, on_close = self.on_close)
    wst = threading.Thread(target=self.ws.run_forever)
    wst.start()
    
  def on_close(self,ws):
    print ("Kraken Retry : %s" % time.ctime())
    time.sleep(10)
    self.connect_websocket() # retry per 10 seconds
    
  def status_message(self,raw_message):
      self.status = raw_message
      
  def transaction_message(self,raw_message):
      symbol = raw_message[3]
      coin = symbol[0:3]
      if coin == 'XBT':
        coin = 'BTC'
      unix = int(float(raw_message[1][0][2]))
      px = float(raw_message[1][0][0])
      qty = float(raw_message[1][0][1])
      if unix not in [x[0] for x in self.data[symbol]]:
          self.data[symbol].append([unix,coin,symbol,px,qty])
          self.parent_class.trades[coin]['kraken'] = [unix,coin,symbol,px,qty]
          if unix == self.parent_class.trades[coin]['bithumb'][0]:
              self.parent_class.both.append([unix,coin,symbol,px,self.parent_class.trades[coin]['bithumb'][0:4]])
    
class Bithumb_WS():
  '''best bid/ask for BTC_KRW from the orderbook snapshot feed, written to the arbitrage class'''

  def __init__(self,arb_class=None):
        self.pair = 'BTC_KRW'
        self.status = 'TBD'
        self.timestamp = time.time()
        self.arb = arb_class
        self.last_msg = {}
        self.connect_websocket()
        return

  def ws_message(self,ws,message):
    temp = json.loads(message)
    self.timestamp = time.time()
    if 'status' in temp:
      self.last_msg['status'] = temp
      self.status = temp
    elif temp.get('type') == 'orderbooksnapshot':
      self.last_msg['update'] = temp
      self.snapshot_message(temp['content'])

  def snapshot_message(self,content):
      '''levels are [price, qty] strings, qty "0" means the level is empty'''
      bids = [(int(px),float(qty)) for px,qty in content['bids'] if float(qty) > 0]
      asks = [(int(px),float(qty)) for px,qty in content['asks'] if float(qty) > 0]
      if not bids or not asks or self.arb is None:
          return
      best_bid = max(bids)
      best_ask = min(asks)
      self.arb.bithumb_best_bid = best_bid[0]
      self.arb.bithumb_best_bid_vol = best_bid[1]
      self.arb.bithumb_best_ask = best_ask[0]
      self.arb.bithumb_best_ask_vol = best_ask[1]
      self.arb.bithumb_timestamp = time.time()

  def ws_open(self,ws):
    self.ws.send('{"type":"orderbooksnapshot", "symbols":["BTC_KRW"]}')
    print("bithumb connection established")

  def on_error(self,ws,error):
    print (error)

  def on_close(self,ws,*args):
    print ("Bithumb Retry : %s" % time.ctime())
    time.sleep(10)
    self.connect_websocket() # retry per 10 seconds

  def connect_websocket(self):
      self.ws = websocket.WebSocketApp("wss://pubwss.bithumb.com/pub/ws", on_open = self.ws_open, on_message = self.ws_message, on_error = self.on_error, on_close = self.on_close)
      wst = threading.Thread(target=self.ws.run_forever)
      wst.start()

class arb():

    def __init__(self):
        self.kraken = kraken_trade_WS(self)
        self.bithumb = bithumb_trade_WS(self)
        '''trades[symbol]:[unix, symbol, usd px, krw px]'''
        self.trades = {'BTC':{},'ETH':{}}
        self.both = []
        return
    
    
    
    
    