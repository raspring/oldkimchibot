#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Where the CSV files live. Uses KIMCHI_DATA_DIR if set, otherwise the iCloud
Crypto folder if this process can read it (macOS privacy settings can block
it for terminal apps), otherwise ./data next to this file.
"""
import os
from os.path import expanduser

ICLOUD_DIR = expanduser("~")+"/Library/Mobile Documents/com~apple~CloudDocs/Crypto"
LOCAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def _data_dir():
    if os.environ.get('KIMCHI_DATA_DIR'):
        return os.environ['KIMCHI_DATA_DIR']
    try:
        os.listdir(ICLOUD_DIR)
        return ICLOUD_DIR
    except OSError:
        return LOCAL_DIR

DATA_DIR = _data_dir()
ERRORS_CSV = os.path.join(DATA_DIR, "errors.csv")
FX_HISTORY_CSV = os.path.join(DATA_DIR, "New Arb", "krw_usd_historical.csv")

os.makedirs(os.path.dirname(FX_HISTORY_CSV), exist_ok=True)
