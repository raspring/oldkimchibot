#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 26 14:50:28 2022

@author: robertspringett
"""
import time
import pandas as pd
import numpy as np
import kimchi_GUI
import kraken_api_1
import bithumb_api_1
import FX_Rates_2
import data_paths
from statistics import median
import bithumb_ws_class_1
import kraken_ws_classes_1
from tkinter import Entry
import threading

class arbitrage():
    def __init__(self,kraken_api=None, bithumb_api=None,fx_api=None,GUI='No'):
        
        if kraken_api ==None:
          self.kraken_api = kraken_api_1.K_API()
        else:
          self.kraken_api = kraken_api
        
        if bithumb_api !=None:
          self.bithumb_api = bithumb_api
        else:
          self.bithumb_api = bithumb_api_1.XCoinAPI()
        
        if fx_api !=None:
          self.fx_api = fx_api
        else:
          self.fx_api = FX_Rates_2.FX_rates()
          
        if GUI == "Yes":
            self.gui = kimchi_GUI.visual()
        else:
            self.gui = None
        
        self.target_spread = 0.005
        self.trade_count = 0
        self.trade = []
          
        '''assets source from old api
        self.kraken_btc = float(self.kraken_api.balances['XXBT'])
        self.kraken_usd = float(self.kraken_api.balances['ZUSD'])
        
        self.bithumb_btc = float(self.bithumb_api.balances['data']['available_btc'])
        self.bithumb_krw = int(float(self.bithumb_api.balances['data']['available_krw']))'''
        
        '''from websockets'''
        self.bithumb_best_bid = 0
        self.bithumb_best_bid_vol = 0
        self.bithumb_best_ask = 0
        self.bithumb_best_ask_vol = 0
        self.kraken_best_bid = 0
        self.kraken_best_bid_vol = 0
        self.kraken_best_ask = 0
        self.kraken_best_ask_vol = 0

        '''fx details'''
        self.usd_krw_rate = self.fx_api.krw_rate
        
        '''list of premium details, bid, ask fx timestamp'''
        self.current_premium = 0
        self.historical_prem = []
        self.calc_hist_prem()
        self.calc_median_prem()
        
        '''timestamps'''
        self.bithumb_timestamp = 0
        self.kraken_timestamp = 0
        self.premium_timestamp = 0
        self.fx_last_update = self.fx_api.last_update
        self.fx_next_update = self.fx_api.next_update
        
        '''test balances'''
        self.kraken_btc = 0
        self.kraken_usd = 10000
        self.bithumb_btc = 0.22
        self.bithumb_krw = 0
        return

    def update_premium(self):
        # wait until both books have a price
        if not (self.bithumb_best_bid and self.kraken_best_ask):
            return
        self.current_premium = ((self.bithumb_best_bid/self.fx_api.krw_rate)-self.kraken_best_ask)/self.kraken_best_ask
        self.historical_prem.append([time.time(),self.current_premium])
        self.premium_timestamp = time.time()
        
        if self.current_premium > (self.target_spread+self.hour_median) and self.kraken_usd >0 and self.bithumb_btc >0:
            trade_vol = min(self.kraken_best_ask_vol,self.bithumb_best_bid_vol,self.kraken_best_ask/self.kraken_usd,self.bithumb_btc)
            self.trade.append(['open',trade_vol,self.kraken_best_ask,self.bithumb_best_bid,self.fx_api.krw_rate,self.premium_timestamp,self.current_premium,self.hour_median])
            self.bithumb_btc = self.bithumb_btc - trade_vol
            self.kraken_btc = self.kraken_btc + trade_vol
            self.kraken_usd = self.kraken_usd - (trade_vol*self.kraken_best_ask)
            self.bithumb_krw = self.bithumb_krw + (trade_vol*self.bithumb_best_bid)
            print("Execute open trade")
        elif self.current_premium < (self.hour_median-self.target_spread) and self.kraken_btc >0 and self.bithumb_krw >0:
            trade_vol = min(self.kraken_best_bid_vol,self.bithumb_best_ask_vol,self.bithumb_best_ask/self.bithumb_krw,self.kraken_btc)
            self.bithumb_btc = self.bithumb_btc + trade_vol
            self.kraken_btc = self.kraken_btc - trade_vol
            self.kraken_usd = self.kraken_usd + (trade_vol*self.kraken_best_bid)
            self.bithumb_krw = self.bithumb_krw - (trade_vol*self.bithumb_best_ask)
            self.trade.append(['close',trade_vol,self.kraken_best_ask,self.bithumb_best_bid,self.fx_api.krw_rate,self.premium_timestamp,self.current_premium,self.hour_median])
            print("Execute open trade")
        return
    
    def update_assets(self):
        self.kraken_api.query_balance()
        self.bithumb_api.balance()
        self.kraken_btc = float(self.kraken_api.balances['XXBT'])
        self.kraken_usd = float(self.kraken_api.balances['ZUSD'])
        self.bithumb_btc = float(self.bithumb_api.balances['data']['available_btc'])
        self.bithumb_krw = int(float(self.bithumb_api.balances['data']['available_krw']))
        return

    def calc_hist_prem(self):
        historical_fx = self.load_hist_fx()

        k_ohlc = []
        for interval in ['1','5','15','30','60']:
            k_ohlc.append(self.kraken_api.query_ohlc('XBTUSD',interval))
            time.sleep(2)
        k_ohlc = pd.concat(k_ohlc)
        k_ohlc.rename(columns={"open": "kraken_open", "close": "kraken_close"},inplace=True)
        k_ohlc['Unix'] = k_ohlc['Unix'].astype('int64')

        b_ohlc = []
        for interval in ['1m','5m','10m','30m']:
            b_ohlc.append(self.bithumb_api.query_ohlc('BTC',interval))
            time.sleep(2)
        b_ohlc = pd.concat(b_ohlc)
        b_ohlc.rename(columns={"Open": "bithumb_open", "Close": "bithumb_close"},inplace=True)
        b_ohlc['Unix'] = b_ohlc['Unix'].astype('int64')//1000
        b_ohlc['bithumb_open'] = b_ohlc['bithumb_open'].astype(int)

        ohlc = k_ohlc.merge(b_ohlc,how='inner',on='Unix')
        ohlc.drop_duplicates(subset=['Unix'],inplace=True)
        ohlc = ohlc.sort_values(by=['Unix'])
        ohlc.reset_index(inplace=True,drop=True)

        # fx rate in force at each candle, current rate where there is no history
        ohlc1 = pd.merge_asof(ohlc, historical_fx[['Unix','fx_rate']], on='Unix', direction='backward')
        ohlc1['fx_rate'] = ohlc1['fx_rate'].fillna(self.fx_api.krw_rate)
        ohlc1['premium'] = ((ohlc1['bithumb_open']/ohlc1['fx_rate'])-ohlc1['kraken_open'])/ohlc1['kraken_open']
        for i in range(len(ohlc1)):
            self.historical_prem.append([ohlc1.loc[i,'Unix'],ohlc1.loc[i,'premium']])
        self.historical_prem = [x for x in self.historical_prem if not np.isnan(x[1])]
        print('historical premiums created')
        return

    def load_hist_fx(self):
        # rows written by FX_Rates_2 are: Unix, rate, date (no header)
        try:
            historical_fx = pd.read_csv(data_paths.FX_HISTORY_CSV,header=None,names=['Unix','fx_rate','Date'])
        except (FileNotFoundError, pd.errors.EmptyDataError):
            historical_fx = pd.DataFrame(columns=['Unix','fx_rate','Date'])
        historical_fx['Unix'] = pd.to_numeric(historical_fx['Unix'],errors='coerce')
        historical_fx['fx_rate'] = pd.to_numeric(historical_fx['fx_rate'],errors='coerce')
        historical_fx = historical_fx.dropna(subset=['Unix','fx_rate'])
        historical_fx['Unix'] = historical_fx['Unix'].astype('int64')
        return historical_fx.drop_duplicates(subset=['Unix']).sort_values(by=['Unix'])

    def calc_median_prem(self):
        self.hour_median = median([round(el[1],3) for el in [x for x in self.historical_prem if x[0]>time.time()-(3600)]])
        self.halfday_median = median([round(el[1],3) for el in [x for x in self.historical_prem if x[0]>time.time()-(43200)]])
        self.day_median = median([round(el[1],3) for el in [x for x in self.historical_prem if x[0]>time.time()-(86400)]])
        self.week_median = median([round(el[1],3) for el in [x for x in self.historical_prem if x[0]>time.time()-(604800)]])
        self.month_median = median([round(el[1],3) for el in [x for x in self.historical_prem if x[0]>time.time()-(2592000)]])
        return

    def update_gui(self):
          self.gui.kraken_book_ts_holder.delete(0,'end')
          Entry.insert(self.gui.kraken_book_ts_holder,0,pd.to_datetime(round(self.kraken_timestamp,0),unit='s'))
        
          self.gui.bithumb_book_ts_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_book_ts_holder,0,pd.to_datetime(round(self.bithumb_timestamp,0),unit='s'))
       
          self.gui.fx_ts_holder.delete(0,'end')
          Entry.insert(self.gui.fx_ts_holder,0,pd.to_datetime(self.fx_last_update,unit='s'))
       
          self.gui.fx_update_holder.delete(0,'end')
          Entry.insert(self.gui.fx_update_holder,0,pd.to_datetime(self.fx_next_update,unit='s'))
       
          self.gui.program_ts_holder.delete(0,'end')
          Entry.insert(self.gui.program_ts_holder,0,pd.to_datetime(round(self.premium_timestamp,0),unit='s'))
        
          '''assets'''
          self.gui.kraken_btc_holder.delete(0,'end')
          Entry.insert(self.gui.kraken_btc_holder,0,self.kraken_btc)
       
          self.gui.bithumb_btc_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_btc_holder,0,self.bithumb_btc)
        
          self.gui.kraken_usd_holder.delete(0,'end')
          Entry.insert(self.gui.kraken_usd_holder,0,"${:,.2f}".format(self.kraken_usd))
       
          self.gui.bithumb_krw_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_krw_holder,0,"{:,}".format(self.bithumb_krw)+ ' KRW')

          '''FX'''
          self.gui.fx_rate_holder.delete(0,'end')
          Entry.insert(self.gui.fx_rate_holder,0,round(self.fx_api.krw_rate,1))
        
          '''bids/ask data'''
          self.gui.kraken_best_ask_holder.delete(0,'end')
          Entry.insert(self.gui.kraken_best_ask_holder,0,"${:,.2f}".format(self.kraken_best_ask))
       
          self.gui.bithumb_best_bid_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_best_bid_holder,0,"{:,}".format(int(self.bithumb_best_bid))+ ' KRW')
        
          self.gui.kraken_best_bid_holder.delete(0,'end')
          Entry.insert(self.gui.kraken_best_bid_holder,0,"${:,.2f}".format(self.kraken_best_bid))
        
          self.gui.bithumb_best_ask_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_best_ask_holder,0,"{:,}".format(int(self.bithumb_best_ask))+ ' KRW')
     
          self.gui.close_trade_vol_holder.delete(0,'end')
          Entry.insert(self.gui.close_trade_vol_holder,0,min(self.kraken_best_ask_vol,self.bithumb_best_bid_vol))
      
          self.gui.open_trade_vol_holder.delete(0,'end')
          Entry.insert(self.gui.open_trade_vol_holder,0,min(self.kraken_best_bid_vol,self.bithumb_best_ask_vol))
        
          '''premium data'''
          self.gui.open_trade_premium_holder.delete(0,'end')
          Entry.insert(self.gui.open_trade_premium_holder,0,"{:.2%}".format(self.current_premium))
     
          self.gui.close_trade_premium_holder.delete(0,'end')
          Entry.insert(self.gui.close_trade_premium_holder,0,"{:.2%}".format(self.current_premium))
        
          self.gui.hour_prem_holder.delete(0,'end')
          Entry.insert(self.gui.hour_prem_holder,0,"{:.2%}".format(self.hour_median))
        
          self.gui.halfday_prem_holder.delete(0,'end')
          Entry.insert(self.gui.halfday_prem_holder,0,"{:.2%}".format(self.day_median))
        
          self.gui.today_prem_holder.delete(0,'end')
          Entry.insert(self.gui.today_prem_holder,0,"{:.2%}".format(self.day_median))
       
          self.gui.week_prem_holder.delete(0,'end')
          Entry.insert(self.gui.week_prem_holder,0,"{:.2%}".format(self.week_median))

          self.gui.bithumb_book_ts_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_book_ts_holder,0,pd.to_datetime(round(self.bithumb_timestamp,0),unit='s'))

          self.gui.program_ts_holder.delete(0,'end')
          Entry.insert(self.gui.program_ts_holder,0,pd.to_datetime(round(self.premium_timestamp,0),unit='s'))
        
          '''bids/ask data'''
          self.gui.bithumb_best_bid_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_best_bid_holder,0,"{:,}".format(int(self.bithumb_best_bid))+ ' KRW')
        
          self.gui.bithumb_best_ask_holder.delete(0,'end')
          Entry.insert(self.gui.bithumb_best_ask_holder,0,"{:,}".format(int(self.bithumb_best_ask))+ ' KRW')

          self.gui.close_trade_vol_holder.delete(0,'end')
          Entry.insert(self.gui.close_trade_vol_holder,0,min(self.kraken_best_ask_vol,self.bithumb_best_bid_vol))

          self.gui.open_trade_vol_holder.delete(0,'end')
          Entry.insert(self.gui.open_trade_vol_holder,0,min(self.kraken_best_bid_vol,self.bithumb_best_ask_vol))
          return

    def update_median_thread(self):
      while True:
        self.calc_median_prem()
        print ("Update median : %s" % time.ctime())
        time.sleep(900)


arb = arbitrage(GUI='No')
kraken = kraken_ws_classes_1.kraken_ticker_WS(arb)
bithumb = bithumb_ws_class_1.Bithumb_WS(arb)
med_t = threading.Thread(target=arb.update_median_thread)
med_t.start()



