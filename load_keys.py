#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API keys read from environment variables, so nothing is hardcoded.
Any key that is not set comes back as None.

KRAKEN_API_KEY / KRAKEN_API_SECRET        - Kraken, user 'rs' (default)
BITHUMB_API_KEY / BITHUMB_API_SECRET      - Bithumb
KRAKEN_JK_API_KEY / KRAKEN_JK_API_SECRET  - Kraken, user 'JK'
"""
import os

def load_key():
    names = ['KRAKEN_API_KEY', 'KRAKEN_API_SECRET',
             'BITHUMB_API_KEY', 'BITHUMB_API_SECRET',
             'KRAKEN_JK_API_KEY', 'KRAKEN_JK_API_SECRET']
    return tuple(os.environ.get(name) or None for name in names)
