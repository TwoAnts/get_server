#!/usr/bin/python
#-*- coding:utf-8 -*-

import re
import urllib
import urllib2
import cookielib
import traceback
import time
import os
from datetime import datetime
from datetime import timedelta

from bs4 import BeautifulSoup
from dateutil.parser import parse as du_parse
from dateutil import tz

tzlocal = tz.tzlocal()

import gs_log
gs_log.SAVE_LOG=True

from gs_log import mlog

get_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

post_headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}
post_headers.update(get_headers)

url_root = 'http://115.156.209.252/dcms/'

url_login = 'userlogin.php'
url_index = 'index.php'
url_detail = 'showdetail.php'
url_apply = 'applyins.php'
url_myins = 'myins.php'
url_throw = 'abandonapply.php'
url_logout = 'logout.php'


queue = [('M201672711', '123456'),
 #('M201672696', '123456')
 ]

ins_id_pattern = re.compile(u'ca\d{2}')
ins_id_exculde = ['ca32']

opener = None

def wraper(func):
    def w(**kwargs):
        new_kw = {}
        #print func.func_name
        #print func.func_code.co_varnames
        for i in xrange(func.func_code.co_argcount):
            name = func.func_code.co_varnames[i]
            new_kw[name] = kwargs.get(name, None)
            if not new_kw[name]:
                mlog('func %s need %s arg!' %(func.func_name, name))
                return None
        return func(**new_kw)
    w.func_name = func.func_name
    return w
        
'''        
def mlog(str):
    print '[%s] %s' %(datetime.now(), str)
'''

def resp2soup(resp):
    return BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')

def dumpresp(resp, save_body=False):
    if not resp:
        return
    try:
        msg = '%s %s\n%s\n%s\n' %(resp.code, resp.msg, resp.url, str(resp.headers))
        if save_body:
            msg = msg + resp.read().decode('utf-8')
        mlog(msg)
    except Exception as e:
        mlog(traceback.format_exc())
        
def request(url, get_params={}, post_data={}):
    url_with_params = url_root + url
    if get_params:
        url_with_params = url_with_params + '?' + '&'.join(['%s=%s' %(k, v) for k,v in get_params.iteritems()])
    if post_data:
        data = urllib.urlencode(post_data)
        headers = post_headers
    else:
        data = None
        headers = get_headers
    
    req = urllib2.Request(url_with_params, data=data, headers=headers)
    global opener
    if not opener:
        cj = cookielib.CookieJar()  
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    resp = opener.open(req)
    return resp

def post(url, get_params={}, **data):
    return request(url, get_params=get_params, post_data=data)

def get(url, **data):
    return request(url, get_params=data)
    
def get_server_time():
    '''
    When your time not same as web server's time.
    Use it's response's Date as your time.
    '''
    resp = get(url_login)
    date = resp.headers.get('Date')
    if date:
        now_tz = du_parse(date)
        now_tz = now_tz.astimezone(tz=tzlocal)
        return now_tz.replace(tzinfo=None)
    return None

def login(username=None, password=None, submit='login'):
    return post(url_login, username=username, password=password, submit=submit)
    
def apply(ins_id=None, sel_num=12):
    return post(url_apply, {'ins_id' : ins_id}, ins_id=ins_id, sel_num=sel_num)
    
def throw(ins_id=None, user_id=None):
    return get(url_throw, ins_id=ins_id, user_id=user_id)
    
def get_owner(ins_id):
    resp = get(url_detail, ins_id=ins_id)
    soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
    owner_pre_tag = soup.find('td', text=u'使用人')
    if owner_pre_tag:
        owner_tag = owner_pre_tag.findNext('td')
        return owner_tag.text
    return None
    
def check_my(ins_id):
    resp = get(url_myins)
    soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
    
    for td in soup.find_all('td', text=re.compile(u'[a-zA-Z]{2,3}\d{2}')):
        if td.text == ins_id:
            return True
    
    return False   
    
def get_detail(ins_id):
    resp = get(url_detail, ins_id=ins_id)
    soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
    start_date_tag = soup.find('td', text=re.compile('\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{1,2}:\d{1,2}'))
    start_date = datetime.strptime(start_date_tag.text, '%Y-%m-%d %H:%M:%S') if start_date_tag else None
    
    use_days_tag = soup.find('td', text=re.compile(u'\d{1,2} *天'))
    use_days = int(use_days_tag.text[:-1]) if use_days_tag else None
    
    end_date = start_date + timedelta(days=use_days) if start_date and use_days else None
    
    return {'start_date':start_date, 'use_days':use_days, 'end_date': end_date}
    

def logout():
    return get(url_logout)
    
def get_relaxs():
    resp = get(url_index)
    soup = resp2soup(resp)
    relaxs = []
    for td in soup.find_all('td'):
        if hasattr(td, 'font') and hasattr(td, 'a') and td.font.color == 'green':
                relaxs.append(td.a.text)
    
    return relaxs
    
def is_need(ins_id, ins_id_pattern=None, ins_id_exculde=None):
    if ins_id_pattern and not ins_id_pattern.match(ins_id):
        return False
    if ins_id_exculde and ins_id in ins_id_exculde:
        return False
    return True
    
def get_one_need(ins_id_pattern=None, ins_id_exculde=None):
    resp = get(url_index)
    soup = resp2soup(resp)
    relaxs = []
    for td in soup.find_all('td'):
        if hasattr(td, 'font') and hasattr(td, 'a') and td.font.color == 'green':
                if is_need(td.a.text, ins_id_pattern=ins_id_pattern, ins_id_exculde=ins_id_exculde):
                    return td.a.text
    return None
            
def get_need(relaxs, ins_id_pattern=None, ins_id_exculde=None):
    relaxs = get_relaxs()
    if ins_id_pattern:
        relaxs = filter(ins_id_pattern.match, relaxs)
    if ins_id_exculde:
        relaxs = [i for i in relaxs if i not in ins_id_exculde]
    return relaxs

def get_list_to_apply(ins_map):
    kvlist = []
    for k, v in ins_map.iteritems():
        if ins_id_pattern.match(k) \
                and k not in ins_id_exculde \
                and v['end_date'] \
                and v['end_date'] > datetime.now():
            kvlist.append(( k, v['start_date'], v['use_days'], v['end_date'] ))
    
    kvlist.sort(key=lambda x: x[-1])
    return kvlist
    
def print_ins_map(ins_map):
    kvlist = []
    for k, v in ins_map.iteritems():
        kvlist.append( ( k, '%s +%sdays' %(v['start_date'], v['use_days']) ) )
    
    kvlist.sort(key=lambda x:x[0])
    
    for line in kvlist:
        print '%s:%s' %line
        
def loginout_exec(func, username, passwd, **kwargs):
    return_result = None
    try:
        mlog('login %s' %username)
        resp = login(username=username, password=passwd)
        if func:
            mlog('exec %s ...' %func.func_name)
            kwargs['login_resp'] = resp
            return_result = func(**kwargs)

    except Exception as e:
        mlog(traceback.format_exc())
    finally:
        resp = logout()
        mlog('logout')
        return return_result
    
    
        
def to_get_list(login_resp=None, **kwargs):
    soup = resp2soup(login_resp)
        
    not_relax_map = {}
    relaxs = []
    
    for td in soup.find_all('td'):
        #print td.a.text, td.font.attrs['color']
        if td.font.attrs['color'] == 'green':
            relaxs.append(td.a.text)
        else:
            not_relax_map[td.a.text] = get_detail(td.a.text)

    #print 'relaxs:%s' %','.join(relaxs)
    #print_ins_map(not_relax_map)
    
    todo_list = get_list_to_apply(not_relax_map)
    #for line in todo_list:
        #print '%s: %s' %(line[0], line[-1])
        
        
    #result = apply(sel_num=1, ins_id=relaxs[0])
    return not_relax_map, relaxs, todo_list
    
    
def apply_one(login_resp=None, todo_list=None):
    if not todo_list:
        return None
        
    for ins_id in todo_list:
        owner = get_owner(ins_id)
        if not owner:
            apply(ins_id)
            if check_my(ins_id):
                return ins_id
    
    return None
        
def throw_one(login_resp=None, ins_id=None, user_id=None):
    if not ins_id or not username:
        return ins_id
    
    if check_my(ins_id):
        throw(ins_id, user_id)
        if not check_my(ins_id):
            return ins_id
    else:
        print 'Don\'t need throw.'
        return ins_id
    
    return None
   
def apply_one_run(login_resp=None, end_date=None, ins_id=None):
    if not ins_id or not end_date:
        mlog('end_date or ins_id is None!')
        return None

    if check_my(ins_id):
        mlog('already my ins, don\'t need get.')
        return None
        
    resp = None
    i = 0
    while True:
        i += 1
        if end_date < datetime.now():
            #print 'enddata come! quit this loop! %s' %datetime.now()
            mlog('try %s times.' %i)
            dumpresp(resp, save_body=True)
            return None

        owner = get_owner(ins_id)
        if owner:
            time.sleep(5)
            continue
        #work when no owner

        resp = apply(ins_id)
        if check_my(ins_id):
            #print 'applyed:%s' %(need)
            mlog('try %s times.' %i)
            return ins_id
            
        time.sleep(10)   
    
def apply_run(login_resp=None, end_date=None):
    while True:
        if end_date < datetime.now():
            #print 'enddata come! quit this loop! %s' %datetime.now()
            return None
        need = get_one_need(ins_id_pattern=ins_id_pattern, ins_id_exculde=ins_id_exculde)
        if not need:
            #mlog('no need found!')
            time.sleep(1)
            continue
            
        apply(need)
        if check_my(need):
            #print 'applyed:%s' %(need)
            return need
            
        time.sleep(0.5)
    
    
        
def apply_loop(login_resp=None, end_date=None):
    if not end_date:
        return None
        
    thr = threading.Thread(target=apply_run, kwargs={'end_date':end_date})
    
    thr.start()
    thr.join()

def sleep_to_apply_one(ins_id, time_delta, username, passwd):
    detail = loginout_exec(wraper(get_detail), username=username, passwd=passwd, ins_id=ins_id) 
    start_date = detail['end_date']
    if not start_date:
        start_date = get_server_time()

    notify = start_date - get_server_time()
    notify = notify.total_seconds()
    if notify > 24 * 60 *60:
        mlog('free time is %s' %start_date)
        mlog('too long time to wait. exit!')
        return 

    if notify > 0:
        mlog('sleep to %s' %start_date)
        time.sleep(notify)
    
    mlog('server time is %s' %get_server_time())
    end_date = datetime.now() + time_delta
    mlog('work until %s for %s seconds...' %(end_date, time_delta.total_seconds()))
    ins_id = loginout_exec(apply_one_run, username=username, passwd=passwd,\
                                 end_date=end_date, ins_id=ins_id)
    mlog('end!')
    if ins_id:
        mlog('get %s.' %ins_id)
    



def print_(l):
    for line in l:
        print line 
        
if __name__ == '__main__':

    '''
    ins_id_queue = []
    need_len = len(queue)
    not_relax_map, relaxs, todo_list = loginout_exec(to_get_list, username='M201672711', passwd='123456')
    
    now = datetime.now()
    main_enddate = now + timedelta(days=1)
    print_(todo_list)
    exit(0)
    '''
    
    '''
    todo_list = filter(lambda e: e[-1] < main_enddate, todo_list)
    
    print todo_list
    print ''
    
    #print type(todo_list[0][-1]), type(datetime.now())
    #exit(0)
    
    #todo_list = [('ca01', now, now+timedelta(seconds=5))]
    
    mlog('start mainloop!')
    while todo_list:
        one = todo_list.pop(0)
        #print '%s %s %s' %(one[0], one[1], one[2])
        notify = one[-1] - datetime.now()
        if notify:
            notify = notify.total_seconds()
            
        if notify < -120:
            continue
        elif notify > 0:
            mlog('sleep %ss, notify on %s for %s' %(notify, one[-1], one[0]))
            time.sleep(notify)
        
        mlog('work')
        while len(ins_id_queue) < len(queue):
            user = queue[len(ins_id_queue)]
            mlog('start %s to apply' % user[0])
            #ins_id = loginout_exec(apply_one_run, username=user[0], passwd=user[1], end_date=(one[2] + timedelta(seconds=120)), ins_id='ca15')
            ins_id = loginout_exec(apply_run, username=user[0], passwd=user[1], end_date=(one[2] + timedelta(seconds=65)))
            if ins_id:
                mlog('%s apply %s' %(user[0], ins_id))
                ins_id_queue.push(ins_id)
                continue                   
            else:
                mlog('no ins_id applyed, to next loop------>')
                break
        
        if len(ins_id_queue) > len(queue):
            break
           
    mlog('stop')
    
    for i in xrange(len(ins_id_queue)):
        print queue[i], ins_id_queue[i]
    
    print '%s/%s done!' %(len(ins_id_queue), len(queue))
    #ins_id = loginout_exec(apply_one, todo_list=['gd09'])
    #print 'apply ', ins_id
    #print 'throw ', loginout_exec(throw_one, ins_id=ins_id, user_id=username)
    '''
    mlog('='*45)
    try:
        ins_id = 'ca15'
        tl = timedelta(seconds=240)
        username = 'M201672711'
        passwd = '123456'
        sleep_to_apply_one(ins_id, tl, username, passwd)
    except Exception as e:
        mlog(traceback.format_exc())
    mlog('='*45)
        
    
