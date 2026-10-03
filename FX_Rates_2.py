
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 09:20:17 2021

@author: robertspringett
get USD/KRW FX rate from ECB api
"""

import requests
import time
import threading
from os.path import expanduser
import pandas as pd
import data_paths
import os

class FX_rates(object):
    
    def __init__(self):

        api_key = os.environ.get('EXCHANGERATE_API_KEY')
        if not api_key:
            raise Exception('EXCHANGERATE_API_KEY is not set')
        self.uri = 'https://v6.exchangerate-api.com/v6/'+api_key+'/latest/USD'
        self.session = requests.session()
        self.response = None
        self._json_options = {}
        self.FX_rates_KRW()
        return
            
    def json_options(self, **kwargs):
        self._json_options = kwargs
        return self
    
    def get_query(self):
        url = self.uri
        self.response = self.session.get(url)
        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()
        return self.response.json(**self._json_options)
    
    def FX_rates_KRW(self):
        temp = self.get_query()
        self.last_update  = temp['time_last_update_unix']
        self.next_update = temp['time_next_update_unix']
        self.fx_rates = temp['conversion_rates']
        self.krw_rate = temp['conversion_rates']['KRW']
        print ("Update FX : %s" % time.ctime())
        filename = data_paths.FX_HISTORY_CSV
        data = {'Unix': self.last_update,'Close':self.krw_rate}
        df = pd.DataFrame(data,index=[0])
        df['Date'] = pd.to_datetime(df['Unix'],unit='s').dt.date
        df.to_csv(filename,mode='a',index=False, header=False)
        return

class fx_Rates_Auto_Update(object):
    
    def __init__(self):
        self.fx_api = FX_rates()
        self.update_thread()
        return

    def auto_update(self):
        while True:
          if time.time()-60 > self.fx_api.next_update:
            self.fx_api.FX_rates_KRW()

    def update_thread(self):
      fxt = threading.Thread(target=self.auto_update)
      fxt.daemon = True
      fxt.start()