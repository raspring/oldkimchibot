#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 22:23:42 2020

@author: Rob
API interface with Kraken exchange
added error audit
new trade type for buying dip
secret and key removed hardcoding
modified query_open_orders to bring back more than one per ticker
"""


import requests
import pandas as pd
import time
import calendar
import urllib.parse
import hashlib
import hmac
import base64
import datetime
from os.path import expanduser
import load_keys
import data_paths
import os
import scipy.stats as stats



class K_API(object):

    def __init__(self,kraken_key=None, kraken_secret=None,user='rs'):
        
        rs_kraken_key, rs_kraken_secret,temp, temp2, jk_kraken_key, jk_kraken_secret = load_keys.load_key()
    
        if user == 'JK':
            self.key = jk_kraken_key
            self.secret = jk_kraken_secret
        else:
            self.key = rs_kraken_key
            self.secret = rs_kraken_secret

        self.uri = 'https://api.kraken.com'
        self.file_name = data_paths.ERRORS_CSV
        self.apiversion = '0'
        self.session = requests.session()
        self.response = None
        self._json_options = {}
        self.create_dict()
        if self.key:
            self.query_balance()
        else:
            print('Kraken: no API key set, skipping balance query')
        return

    def json_options(self, **kwargs):
        self._json_options = kwargs
        return self
    
    def date_nix(self,str_date):
        return calendar.timegm(str_date.timetuple())

    def date_str(self,nix_time):
        return datetime.datetime.fromtimestamp(nix_time).strftime('%m, %d, %Y')
    
    def date_form(self,start, end, ofs):
        req_data = {'type': 'all',
                    'trades': 'true',
                    'start': str(self.date_nix(start)),
                    'end': str(self.date_nix(end)),
                    'ofs': str(ofs)}
        return req_data
    
    def close(self):
        self.session.close()
        return
    
    def _query(self, urlpath, data, headers=None, timeout=None):
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = self.uri + urlpath
        self.response = self.session.post(url, data = data, headers = headers,
                                          timeout = timeout)
        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()
            res1 = str(url + str(data) + str(headers))
            self.create_error_record(self.response.status_code,res1) 
        return self.response.json(**self._json_options)

    def query_public(self, method, data=None, timeout=None):
        if data is None:
            data = {}
        urlpath = '/' + self.apiversion + '/public/' + method
        response = self._query(urlpath, data, timeout = timeout)
        if 'result' not in response.keys():
            res1 = str("self.query_private("+method+","+str(data)+")")
            self.create_error_record(response,res1)
        return response
    
    def query_private(self, method, data=None, timeout=None):
        """ Performs an API query that requires a valid key/secret pair.
        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        """
        if data is None:
            data = {}
        if not self.key:
            raise Exception('Either key or secret is not set! (Use `load_key()`.')
        data['nonce'] = self._nonce()
        urlpath = '/' + self.apiversion + '/private/' + method
        
        headers = {'API-Key': self.key,'API-Sign': self._sign(data, urlpath)}
        response = self._query(urlpath, data, headers, timeout = timeout)
        if 'result' not in response.keys():
            res1 = str("self.query_private("+method+","+str(data)+")")
            print(res1)
            self.create_error_record(response,res1)
        return response
    
    def _nonce(self):
        return int(1000*time.time())
    
    def _sign(self, data, urlpath):
        """ Sign request data according to Kraken's scheme.
        :param data: API request parameters
        :type data: dict
        :param urlpath: API URL path sans host
        :type urlpath: str
        :returns: signature digest
        """
        postdata = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode()
    
    def create_error_record(self,res,res1):
        temp = pd.DataFrame({'Query': [res1], 'Errors': [str(res)]})
        temp.to_csv(self.file_name,mode='a',index=False,header=not os.path.exists(self.file_name))
        return
    
    def create_dict(self):
        a = self.query_public('AssetPairs')
        b =  a['result']
        dict = {}
        for keys in b.keys():
            dict[b[keys]['altname']] = {'Ticker': keys}
            dict[b[keys]['altname']]['base'] = b[keys]['base']
            dict[b[keys]['altname']]['quote'] = b[keys]['quote']
            dict[b[keys]['altname']]['leverage_buy'] = b[keys]['leverage_buy']
            dict[b[keys]['altname']]['leverage_sell'] = b[keys]['leverage_sell']
            dict[b[keys]['altname']]['fees'] = b[keys]['fees']
        self.kraken_dict = dict
        return
    
    def query_trades(self,Ticker,Since):
        '''returns dataframe of trades and Unix of last trade'''
        temp = 'Trades?pair=' + self.kraken_dict[Ticker]['Ticker'] + '&since=' + Since
        a = self.query_public(temp)
        b = a['result']
        c = b[self.kraken_dict[Ticker]['Ticker']]
        last = str(b['last'])
        d = pd.DataFrame(c)
        d.rename(columns={0:'price',1:'volume',2:'Timestamp'},inplace=True)
        d = d.drop(d.columns[[4,5,3]],axis=1)
        d = d[["Timestamp","price","volume"]]
        return d,last
    
    def update_trade_history_thumb_drive(self,Ticker):
        '''returns dataframe of trades and Unix of last trade'''
        temp_df = pd.read_csv('/Volumes/CryptoFiles/trade_history/'+Ticker+'.csv')
        temp_df.columns = ['unix','price','vol']
        since = temp_df['unix'].max()
        since_str = str(since)
        '''while since < (time.time()-3456000):'''
        while since<1625183998:
          url = 'Trades?pair=' + self.kraken_dict[Ticker]['Ticker'] + '&since=' + since_str
          a = self.query_public(url)
          b = a['result']
          c = b[self.kraken_dict[Ticker]['Ticker']]
          since = int(b['last'][0:10])
          since_str = b['last']
          d = pd.DataFrame(c)
          d.rename(columns={0:'price',1:'vol',2:'unix'},inplace=True)
          d = d.drop(d.columns[[4,5,3]],axis=1)
          d = d[["unix","price","vol"]]
          temp_df = temp_df.append(d)
          time.sleep(2)
        temp_df.to_csv('/Volumes/CryptoFiles/trade_history/'+Ticker+'.csv',index=False,columns=['unix','price','vol'],header=False)
        return temp_df
                    
    def query_ohlc(self,Ticker,interval):
        '''returns dataframe fo OHLCV'''
        temp = 'OHLC?pair=' + Ticker + '&interval='+interval
        items = Ticker
        a = self.query_public(temp)
        a = a['result']
        a = a[self.kraken_dict[Ticker]['Ticker']]
        b = pd.DataFrame(a)
        b.columns =['Unix','open','high','low','close','vwap','volume','count']
        b['Timestamp'] = pd.to_datetime(b['Unix'].astype(int),unit='s')
        del b['count']
        del b['vwap']
        b['open'] = b['open'].astype(float)
        b['close'] = b['close'].astype(float)
        b['high'] = b['high'].astype(float)
        b['low'] = b['low'].astype(float)
        b['volume'] = b['volume'].astype(float)
        return b   
        
    def query_balance(self):
        a = self.query_private('Balance')
        a = a['result']
        self.balances = a
        return
    
    def get_px(self,Ticker):
        temp = 'Ticker?pair=' + Ticker
        a = self.query_public(temp)
        b = a['result']
        c = float(b[self.kraken_dict[Ticker]['Ticker']]['c'][0])
        return c
    
    def query_ledger(self,end):
        a = self.query_private('Ledgers',{'end':end})
        a = a['result']
        return a
    
    def query_tradebalance(self):
        a = self.query_private('TradeBalance')
        a = a['result']
        b = {'TotalBalance':a['eb'],'TradeBalance':a['tb'],'OpenMargin':a['m'],'UnrealPNL':a['n'],'costbasis':a['c']}
        return b
    
    def query_open_orders(self):
        '''returns ionary with trade ref as key'''
        a = self.query_private('OpenOrders')       
        b = a['result']['open']  
        return b
    
    def query_open_orders_byref(self,userref):
        '''returns dictionary with trade ref as key'''
        a = self.query_private('OpenOrders',{'userref':userref})
        b = a['result']['open']  
        return b
    
    def query_closed_orders(self,end):
        a = self.query_private('ClosedOrders',{'trades':"true","end":end})
        return a
     
    def query_open_positions(self):
        '''returns dictionary of open positions consolidated to pair'''
        a = self.query_private('OpenPositions',{'docalcs':"true",'consolidation':'market'})
        try:
          b = a['result']
        except:
          b=a
        c = {}
        for items in b:
          c[items['pair']] = items           
        return c
    
    def query_open_positions_raw(self):
        a = self.query_private('OpenPositions')
        try:
          b = a['result']
        except:
          b=b 
        return b
    
    def transaction_history(self,end):
        a = self.query_private('TradesHistory',{'type':"all",'trades':'true',"end":end})
        return a
    
    def cancel_order(self,txid):
        """cancel the order with txid"""
        res = self.query_private('CancelOrder',{'txid':txid})
        return res
    
    def get_trade_info(self,txid):
        res = self.query_private('QueryTrades',{'txid':txid})
        return res
    
    def get_order_info(self,txid):
        res = self.query_private('QueryOrders',{'txid':txid})
        return res
    
    def margin_limit(self,Ticker,order_type,px,vol,userref):
        res = self.query_private('AddOrder', {'pair':Ticker,
                                              'type':order_type,
                                              'ordertype':'limit',
                                              'price':px,
                                              'volume':vol,
                                              'leverage':'5:1',
                                              'oflags':'fciq',
                                              'userref':userref})
        return res
    
    def margin_limit_conditional_close(self,Ticker,order_type,px,vol,userref):
        if order_type == 'buy':
            close_order_type = "sell"
        else:
            close_order_type = 'buy'
        res = self.query_private('AddOrder', {'pair':Ticker,
                                              'type':order_type,
                                              'ordertype':'limit',
                                              'price':px,
                                              'volume':vol,
                                              'leverage':'5:1',
                                              'oflags':'fciq',
                                              'userref':userref,
                                              'close[type]': close_order_type,
                                              'close[ordertype]':'limit',
                                              'close[price]': '+10%',
                                              'close[leverage]':'5:1',
                                              'close[oflags]':'fciq'})

        return 
     
    def cash_limit(self,Ticker,buy_sell,order_type,price,price2,vol,userref=123):
        '''can'''
        res = self.query_private('AddOrder', {'pair':Ticker,
                                              'type':buy_sell,
                                              'ordertype':order_type,
                                              'price':price,
                                              'volume':vol,
                                              'leverage':'none',
                                              'oflags':'fciq',
                                              'userref':userref})
        return res
    
    def cash_limit_1(self,userref,ordertype,buy_sell,volume,pair,price,price2=None,trigger='last',leverage='none',oflags='fciq',timeinforce='GTC',expiretm=0,close_ordertype=None,close_price=None,close_price2=None):
        '''can'''
        params = {'pair':pair,
                     'type':buy_sell,
                     'ordertype':ordertype,
                     'price':int(price),
                     'volume':volume,
                     'leverage':leverage,
                     'oflags':oflags,
                     'userref':userref,
                     'timeinforce':timeinforce,
                     'expiretm':expiretm}
        if price2 is not None:
            params['price2'] = int(price2)
        if close_ordertype is not None:
            params['close[ordertype]'] = close_ordertype
        if close_price is not None:
            params['close[price]'] = close_price
        if close_price2 is not None:
            params['close[price2]'] = close_price2
        res = self.query_private('AddOrder',params)
        return res
    
    def query_orderbook(self,Ticker):
        temp = 'Depth?pair=' + self.kraken_dict[Ticker]['Ticker'] + '&count=500'
        temp = self.query_public(temp)
        temp = temp['result']
        temp = temp[self.kraken_dict[Ticker]['Ticker']]
        bids = pd.DataFrame(temp['bids'])
        bids.columns = ['Price','Vol',"Unix"]
        bids['Vol'] = bids['Vol'].astype(float)
        bids['Price'] = bids['Price'].astype(float)
        asks = pd.DataFrame(temp['asks'])
        asks.columns = ['Price','Vol',"Unix"]
        asks['Vol'] = asks['Vol'].astype(float)
        asks['Price'] = asks['Price'].astype(float)
        return bids,asks
    
    def find_support_resistance(self,Ticker):
        '''currently configured for BTC only'''
        bids,asks = self.query_orderbook(Ticker)
        freq1 = 100
        bids1 = pd.interval_range(start=int(round(bids.loc[499,"Price"],-2)),freq=freq1,end=bids.loc[0,"Price"]+100)
        asks1 = pd.interval_range(start=int(round(asks.loc[0,"Price"],-2)),freq=freq1,end=asks.loc[499,"Price"]+100)
        bids2 = bids.groupby(pd.cut(bids['Price'],bids1)).sum()
        asks2 = asks.groupby(pd.cut(asks['Price'],asks1)).sum()
        del bids2['Unix']
        del bids2['Price']
        del asks2['Unix']
        del asks2['Price']
        bids2['type'] = 'support'
        asks2['type'] = 'resistance'
        bids2['range_high'] = bids1.right
        asks2['range_high'] = asks1.right
        bids2['range_low'] = bids1.left
        asks2['range_low'] = asks1.left
        bids2.reset_index(inplace=True,drop=True)
        asks2.reset_index(inplace=True,drop=True)
        bids2['z_score'] = stats.zscore(bids2['Vol'])
        asks2['z_score'] = stats.zscore(asks2['Vol'])

        return bids2, asks2
    
        
        
    