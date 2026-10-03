import websocket
import time
import json
import threading

class kraken_ticker_WS():
  def __init__(self,arb_class=None):
        self.connectionID = 0
        self.event = 'TBD'
        self.status = 'TBD'
        self.version = 'TBD'
        self.channelID = 0
        self.channelName = 'TBD'
        self.pair = 'XBT/USD'
        self.timestamp = int(time.time())
        if arb_class !=None:
          self.arb = arb_class
        self.last_msg = {}
        self.connect_websocket()
        return

  def ws_message(self,ws,message):
    temp = json.loads(message)
    self.timestamp = time.time()
    if "connectionID" in temp:
      self.last_msg['connection'] = temp
      self.connectionID = temp["connectionID"]
      self.event = temp["event"]
      self.status = temp['status']
      self.version = temp['version']
    elif "channelID" in temp:
      self.last_msg['channel'] = temp
      self.channelID = temp["channelID"]
      self.channelName = temp["channelName"]
      self.event = temp["event"]
      self.pair = temp['pair']
      self.status = temp['status']
      self.subscription = temp['subscription']
    elif "event" in temp:
      self.last_msg['event'] = temp
      self.event = temp["event"]
      self.arb.kraken_timestamp = time.time()
      '''self.arb.update_gui()'''
    elif temp[0]==self.channelID and bool(self.arb):
      self.last_msg['update'] = temp
      self.arb.kraken_best_bid = float(temp[1]['b'][0])
      self.arb.kraken_best_bid_vol = float(temp[1]['b'][2])
      self.arb.kraken_best_ask = float(temp[1]['a'][0])
      self.arb.kraken_best_ask_vol = float(temp[1]['a'][2])
      self.arb.kraken_timestamp = time.time()
      self.arb.update_premium()
      if bool(self.arb.gui):
          self.arb.update_gui()

  def ws_open(self,ws):
    self.ws.send('{"event":"subscribe", "subscription":{"name":"ticker"}, "pair":["XBT/USD"]}')
    print("kraken connection established")

  def on_error(self,ws, error):
    # print('disconnected from server')
    print (error)

  def connect_websocket(self):
    self.ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open = self.ws_open, on_message = self.ws_message, on_error = self.on_error)
    wst = threading.Thread(target=self.ws.run_forever)
    wst.start()
    
class kraken_book_WS():
  def __init__(self,arb_class=None):
        self.connectionID = 0
        self.event = 'TBD'
        self.status = 'TBD'
        self.version = 'TBD'
        self.channelID = 0
        self.channelName = 'TBD'
        self.pair = 'XBT/USD'
        self.timestamp = time.time()
        if arb_class !=None:
          self.arb = arb_class
        self.orderbook = {}
        return

  def ws_message(self,ws,message):
    temp = json.loads(message)
    self.timestamp = time.time()
    if "connectionID" in temp:
      self.connectionID = temp["connectionID"]
      self.event = temp["event"]
      self.status = temp['status']
      self.version = temp['version']
    elif "channelID" in temp:
      self.channelID = temp["channelID"]
      self.channelName = temp["channelName"]
      self.event = temp["event"]
      self.pair = temp['pair']
      self.status = temp['status']
    elif "event" in temp:
      self.event = temp["event"]
    elif temp[0]==self.channelID:
      if 'as' in temp[1]:
        orderbook = {'bids':{},'asks':{}}
        orderbook['payment_currency'] = self.pair[4:]
        orderbook['order_currency'] = self.pair[0:3]
        orderbook['bids'] = {item[0]:{'price':item[0],'quantity':item[1],'update':item[2]} for item in temp[1]['bs']}
        orderbook['asks'] = {item[0]:{'price':item[0],'quantity':item[1],'update':item[2]} for item in temp[1]['as']}
        self.orderbook = orderbook
      if 'a' in temp[1]:
        for items in temp[1]['a']:
          if float(items[1]) != 0.0 :
            self.orderbook['asks'][items[0]] = {'price':items[0],'quantity':items[1],'update':items[2]}
          elif items[0] in self.orderbook['asks'].keys():
            self.orderbook['asks'].pop(items[0])
      if 'b' in temp[1]:
        for items in temp[1]['b']:
          self.updates.append(items)
          if float(items[1]) != 0.0 :
            self.orderbook['bids'][items[0]] = {'price':items[0],'quantity':items[1],'update':items[2]}
          elif items[0] in self.orderbook['bids'].keys():
            self.orderbook['asks'].pop(items[0])
      if bool(self.arb):
        self.arb.kraken_best_bid = float(max(self.orderbook['bids'].keys()))
        self.arb.kraken_best_bid_vol = float(self.orderbook['bids'][max(self.orderbook['bids'].keys())]['quantity'])
        self.arb.kraken_best_ask = float(min(self.orderbook['asks'].keys()))
        self.arb.kraken_best_ask_vol = float(self.orderbook['asks'][min(self.orderbook['asks'].keys())]['quantity'])
        self.arb.kraken_timestamp = time.time()
        self.arb.update_premium()


  def on_close(self,ws):
    # print('disconnected from server')
    print ("Retry : %s" % time.ctime())
    time.sleep(10)
    self.connect_websocket() # retry per 10 seconds
    
  def connect_websocket(self):
    self.ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open = self.ws_open, on_message = self.ws_message,on_close = self.on_close)
    wst = threading.Thread(target=self.ws.run_forever)
    wst.start()

  def ws_open(self,ws):
    self.ws.send('{"event":"subscribe", "subscription":{"name":"book","depth": 10},"pair":["XBT/USD"]}')
    print("connection established")
    

    
    
    
    
    
    