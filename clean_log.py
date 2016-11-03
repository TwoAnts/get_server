#!/usr/bin/python
#-*- coding:utf-8 -*-
import os
from datetime import datetime, timedelta

import gs_log
gs_log.SAVE_LOG = True
from gs_log import mlog

CUR_DIR = os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    mlog('clean logs.')
    now = datetime.now()
    # clean logs  before 7 days ago.
    before_start = now + timedelta(days=-7)
    for f in os.listdir(CUR_DIR):
        if f.endswith('.log'):
            date = None
            try:
                date = datetime.strptime(f, '%Y_%m_%d.log')
            except Exception as e:
                continue
            
            if date < before_start:
                rf = os.path.join(CUR_DIR, f)
                os.remove(rf)
            
            
                
        
