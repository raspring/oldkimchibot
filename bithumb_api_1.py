#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 21:25:08 2021
slght change to order book query
removed hardcoding of secret and key
error record added... need to test

@author: robertspringett
"""

import time
import math
import base64
import hmac, hashlib
import urllib.parse
import pycurl
import json
import requests
import pandas as pd
from os.path import expanduser
import load_keys
import data_paths
import os

class XCoinAPI():

  def __init__(self,bithumb_key=None, bithumb_secret=None):
    if bithumb_key == None:
        temp,temp1,bithumb_key, bithumb_secret, temp2, temp3 = load_keys.load_key()
    self.api_key = bithumb_key
    self.api_secret = bithumb_secret
    self.api_url = "https://api.bithumb.com"
    self.session = requests.session()
    self.response = None
    self._json_options = {}
    self.file_name = data_paths.ERRORS_CSV
    if self.api_key:
      self.balance()
    else:
      print('Bithumb: no API key set, skipping balance query')

  def body_callback(self, buf):
    self.contents = buf;

  def microtime(self, get_as_float = False):
    if get_as_float:
      return time.time()
    else:
      return '%f %d' % math.modf(time.time())

  def usecTime(self) :
    mt = self.microtime(False)
    mt_array = mt.split(" ")[:2];
    return mt_array[1] + mt_array[0][2:5];

  def xcoinApiCall(self, endpoint, rgParams):
		
    endpoint_item_array = {"endpoint" : endpoint};

    uri_array = dict(endpoint_item_array, **rgParams); # Concatenate the two arrays.
    str_data = urllib.parse.urlencode(uri_array);

    nonce = self.usecTime();
    data = endpoint + chr(0) + str_data + chr(0) + nonce;
    utf8_data = data.encode('utf-8');

    key = self.api_secret;
    utf8_key = key.encode('utf-8');

    h = hmac.new(bytes(utf8_key), utf8_data, hashlib.sha512);
    hex_output = h.hexdigest();
    utf8_hex_output = hex_output.encode('utf-8');

    api_sign = base64.b64encode(utf8_hex_output);
    utf8_api_sign = api_sign.decode('utf-8');


    curl_handle = pycurl.Curl();
    curl_handle.setopt(pycurl.POST, 1);
    curl_handle.setopt(pycurl.POSTFIELDS, str_data);

    url = self.api_url + endpoint;
    curl_handle.setopt(curl_handle.URL, url);
   
    curl_handle.setopt(curl_handle.HTTPHEADER, ['Api-Key: ' + self.api_key, 'Api-Sign: ' + utf8_api_sign, 'Api-Nonce: ' + nonce]);
    curl_handle.setopt(curl_handle.WRITEFUNCTION, self.body_callback);
    curl_handle.perform();
    curl_handle.close();

    temp = (json.loads(self.contents))
    
    if temp['status'] != '0000':
      res1 = str(endpoint + " " + str(rgParams))
      status = str(temp['status'] + temp['message'])
      self.create_error_record(status,res1)
    
    return temp

  def create_error_record(self,res,res1):
        temp = pd.DataFrame({'Query': [res1], 'Errors': [str(res)]})
        temp.to_csv(self.file_name,mode='a',index=False,header=not os.path.exists(self.file_name))
        return

  def balance(self):
      '''returns dictionary'''
      rgParams = {}
      temp = self.xcoinApiCall('/info/balance',rgParams)
      self.balances = temp
      return temp

      
  def account(self):
      '''returns dictionary includign trade fees'''
      rgParams = {"order_currency":"BTC"}
      temp = self.xcoinApiCall('/info/account',rgParams)
      return temp
  
  def transactions(self,coin):
      rgParams = {"searchGb":0,'order_currency':coin,'payment_currency':'KRW'}
      temp = self.xcoinApiCall('/info/user_transactions',rgParams)
      return temp  
    
  def orders(self,coin):  
    '''check if working'''
    rgParams = {"order_currency":coin,'type':'bid','payment_currency':'KRW'}
    temp = self.xcoinApiCall('/info/orders',rgParams)
    return temp
   
  def orders_executed(self,coin):
    rgParams = {"order_currency":coin}
    temp = self.xcoinApiCall('/info/orders',rgParams)
    return temp
   
  def buy_market(self,coin,units,ccy='KRW'):
      rgParams = {"order_currency":coin,"payment_currency":"KRW","units":units}
      temp = self.xcoinApiCall('/trade/market_buy',rgParams)
      return temp
  
  def sell_market(self,coin,units,ccy='KRW'):
      rgParams = {"order_currency":coin,"payment_currency":ccy,"units":units}
      temp = self.xcoinApiCall('/trade/market_sell',rgParams)
      return temp
  
  def limit_order(self,coin, ccy, units, px, order):
      """coin = string of coin to buy/sell
      ccy = string of how to pay for coin
      units = float of quantiy
      px = integer of limit px
      order = string of buy/sell"""
      
      rgParams = {"order_currency":coin,"payment_currency":ccy,"units":units,"price":px,"type":order}
      temp = self.xcoinApiCall('/trade/place',rgParams)
      return temp
  
  def cancel_order(self,order_type,order_id,order_ccy,payment_ccy):
      rgParams = {"type":order_type,"order_id":order_id,"order_currency":order_ccy,"payment_currency":payment_ccy}
      temp = self.xcoinApiCall('/trade/cancel',rgParams)
      return temp

  def wallet(self):
      rgParams = {'currency':'BTC'}
      temp = self.xcoinApiCall('/wallet_address',rgParams)
      return temp

  def get_px(self,coinpair):
      temp = self.public_transactions(coinpair)
      b = int(temp['price'][temp.index[-1]])
      return b
  
  def public_transactions(self,coinpair):
    temp = coinpair
    url = self.api_url + '/public/transaction_history/' + temp
    self.response = self.session.get(url)
    if self.response.status_code not in (200, 201, 202):
      self.response.raise_for_status()
    a = self.response.json(**self._json_options)
    b = a['data']
    c = pd.DataFrame(b)
    c['Unix'] = pd.to_datetime(c['transaction_date']).astype(int)/1000000000
    c['Unix'] = c['Unix']-32400
    return c
  
  def query_orderbook(self,coin,coin_bal,payment_ccy_bal=None):  
    temp = coin
    url = self.api_url + '/public/orderbook/' + temp
    self.response = self.session.get(url)
    if self.response.status_code not in (200, 201, 202):
      self.response.raise_for_status()
    a = self.response.json(**self._json_options)
    b = a['data']
    bids = pd.DataFrame(b['bids'])
    bids['price'] = bids['price'].astype(float)
    bids['quantity'] = bids['quantity'].astype(float)
    asks = pd.DataFrame(b['asks'])
    asks['price'] = asks['price'].astype(float)
    asks['quantity'] = asks['quantity'].astype(float)
    if payment_ccy_bal == None:
      asks = asks[0:asks['quantity'].cumsum().searchsorted(coin_bal)+1]
      asks.iloc[-1,asks.columns.get_loc('quantity')] -= (asks['quantity'].cumsum().iloc[-1]-coin_bal) 
    else:
      asks = asks[0:(asks['price']*asks['quantity']).cumsum().searchsorted(payment_ccy_bal)+1]
      asks['total'] = (asks['price']*asks['quantity']).cumsum()
      asks.iloc[-1,asks.columns.get_loc('quantity')]-= (asks.iloc[-1,asks.columns.get_loc('total')] - payment_ccy_bal) / asks.iloc[-1,asks.columns.get_loc('price')]
      del asks['total']
    bids = bids[0:bids['quantity'].cumsum().searchsorted(coin_bal)+1]
    bids.iloc[-1,bids.columns.get_loc('quantity')] -= (bids['quantity'].cumsum().iloc[-1]-coin_bal)
    return bids,asks

  def query_ohlc(self,coinpair,interval):
    temp = coinpair+'_krw/'+interval
    url = self.api_url + '/public/candlestick/' + temp
    self.response = self.session.get(url)
    if self.response.status_code not in (200, 201, 202):
      self.response.raise_for_status()
    a = self.response.json(**self._json_options)
    a = a['data']
    b_ohlc = pd.DataFrame(a,columns=['Unix','Open',"High",'Low','Close','Vol'])
    return b_ohlc  
     
  def query_raw_orderbook(self,coin):  
    temp = coin
    url = self.api_url + '/public/orderbook/' + temp
    self.response = self.session.get(url)
    if self.response.status_code not in (200, 201, 202):
      self.response.raise_for_status()
    a = self.response.json(**self._json_options)
    b = a['data']
    return b
    