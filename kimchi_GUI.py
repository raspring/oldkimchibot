#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 17:39:20 2022

@author: robertspringett
"""
from tkinter import Tk, Label, Button, Entry

class visual():
    def __init__(self):

        self.top = Tk()
        self.top.title("Crypto Summary - Kimchi Premium")
        '''labels'''
        self.L1_0 = Label(self.top, text="Timestamps",).grid(row=1,column=0)
        self.L3_0 = Label(self.top, text="Assets",).grid(row=3,column=0)
        self.L7_0 = Label(self.top, text="Close Trade",).grid(row=7,column=0)
        self.L5_0 = Label(self.top, text="Open Trade",).grid(row=5,column=0)
        self.L9_0 = Label(self.top, text="Premium Details",).grid(row=9,column=0)
        
        '''timestamps'''
        self.L0_1 = Label(self.top, text="Kraken Book Timestamp",).grid(row=0,column=1)
        self.kraken_book_ts_holder = Entry(self.top, bd =5 )
        self.kraken_book_ts_holder.grid(row=1,column=1)
        self.L0_2 = Label(self.top, text="Bithumb Book Timestamp",).grid(row=0,column=2)
        self.bithumb_book_ts_holder = Entry(self.top, bd =5)
        self.bithumb_book_ts_holder.grid(row=1,column=2)
        self.L0_4 = Label(self.top, text="FX Timestamp",).grid(row=0,column=3)
        self.fx_ts_holder = Entry(self.top, bd =5 )
        self.fx_ts_holder.grid(row=1,column=3)
        self.L0_4 = Label(self.top, text="FX Next Update",).grid(row=0,column=4)
        self.fx_update_holder = Entry(self.top, bd =5 )
        self.fx_update_holder.grid(row=1,column=4)
        self.L0_5 = Label(self.top, text="Program Timestamp",).grid(row=0,column=5)
        self.program_ts_holder = Entry(self.top, bd =5 )
        self.program_ts_holder.grid(row=1,column=5)
        
        '''assets'''
        self.L2_2 = Label(self.top, text="Kraken BTC",).grid(row=2,column=2)
        self.kraken_btc_holder = Entry(self.top, bd =5 )
        self.kraken_btc_holder.grid(row=3,column=2)
        self.L2_4 = Label(self.top, text="Bithumb BTC",).grid(row=2,column=4) 
        self.bithumb_btc_holder = Entry(self.top, bd =5 )
        self.bithumb_btc_holder.grid(row=3,column=4)
        self.L2_1 = Label(self.top, text="Kraken USD",).grid(row=2,column=1)
        self.kraken_usd_holder = Entry(self.top, bd =5 )
        self.kraken_usd_holder.grid(row=3,column=1)
        self.L2_3 = Label(self.top, text="Bithumb KRW",).grid(row=2,column=3)
        self.bithumb_krw_holder = Entry(self.top, bd =5 )
        self.bithumb_krw_holder.grid(row=3,column=3)

        '''FX'''
        self.L2_5 = Label(self.top, text="FX Rate",).grid(row=2,column=5)
        self.fx_rate_holder = Entry(self.top, bd =5)
        self.fx_rate_holder.grid(row=3,column=5)
        
        '''bids/ask data'''
        self.L4_1 = Label(self.top, text="Kraken Best Ask",).grid(row=4,column=1)
        self.kraken_best_ask_holder = Entry(self.top, bd=5)
        self.kraken_best_ask_holder.grid(row=5,column=1)
        self.L4_2 = Label(self.top, text="Bithumb Best Bid",).grid(row=4,column=2)
        self.bithumb_best_bid_holder = Entry(self.top, bd =5 )
        self.bithumb_best_bid_holder.grid(row=5,column=2)
        self.L6_1 = Label(self.top, text="Kraken Best Bid",).grid(row=6,column=1)
        self.kraken_best_bid_holder = Entry(self.top, bd =5 )
        self.kraken_best_bid_holder.grid(row=7,column=1)
        self.L6_2 = Label(self.top, text="Bithumb Best Ask",).grid(row=6,column=2)
        self.bithumb_best_ask_holder = Entry(self.top, bd =5 )
        self.bithumb_best_ask_holder.grid(row=7,column=2)
        self.L6_3 = Label(self.top, text="Volume",).grid(row=6,column=3)
        self.close_trade_vol_holder = Entry(self.top, bd =5 )
        self.close_trade_vol_holder.grid(row=7,column=3)
        self.L4_3 = Label(self.top, text="Volume",).grid(row=4,column=3)
        self.open_trade_vol_holder = Entry(self.top, bd =5 )
        self.open_trade_vol_holder.grid(row=5,column=3)
        
        '''premium data'''
        self.L4_4 = Label(self.top, text="Premium",).grid(row=4,column=4)
        self.open_trade_premium_holder = Entry(self.top, bd =5)
        self.open_trade_premium_holder.grid(row=5,column=4)
        self.L6_4 = Label(self.top, text="Premium",).grid(row=6,column=4)
        self.close_trade_premium_holder = Entry(self.top, bd =5 )
        self.close_trade_premium_holder.grid(row=7,column=4)
        
        self.L8_1 = Label(self.top, text="Hour Median Premium",).grid(row=8,column=1)
        self.hour_prem_holder = Entry(self.top, bd =5 )
        self.hour_prem_holder.grid(row=9,column=1)
        
        self.L8_1 = Label(self.top, text="12HR Median Premium",).grid(row=8,column=2)
        self.halfday_prem_holder = Entry(self.top, bd =5 )
        self.halfday_prem_holder.grid(row=9,column=2)
        
        self.L8_1 = Label(self.top, text="Today's Median Premium",).grid(row=8,column=3)
        self.today_prem_holder = Entry(self.top, bd =5 )
        self.today_prem_holder.grid(row=9,column=3)
        
        self.L8_2 = Label(self.top, text="Week Median Premium",).grid(row=8,column=4)
        self.week_prem_holder = Entry(self.top, bd =5 )
        self.week_prem_holder.grid(row=9,column=4)
        
        self.visual_close_button = Button(self.top, text ="Close",command = self.gui_quit).grid(row=12,column=1)
        return
    
    def main_loop(self):
        self.top.mainloop()
    
    def refresher(self):
      self.top.update()
      self.top.after(1000, self.refresher) # refresh in 10 seconds

      
    def gui_quit(self):
        self.top.destroy()
        return
        