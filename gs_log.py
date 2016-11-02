#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
from datetime import datetime

CUR_DIR = os.path.abspath(os.path.dirname(__file__))
SAVE_LOG = False
TARGETS = []

def mlog(s):
    msg = '[%s] %s' %(datetime.now(), s)
    print msg

    if not SAVE_LOG:
        return
    msg = '%s\n' %msg

    if TARGETS:
        for f in TARGETS:
            with open(f, 'a') as out:
                out.write(msg)
    else:
        f = datetime.strftime(datetime.now(), '%Y_%m_%d.log')
        f = os.path.join(CUR_DIR, f)
        with open(f, 'a') as out:
            out.write(msg)
        
        


