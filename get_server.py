#-*- coding:utf-8 -*-

import re
import urllib
import urllib2
import cookielib
import traceback
import time
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup

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

username = 'M201672711'
passwd = '123456'

ins_id_pattern = re.compile(u'ca\d{2}')
ins_id_exculde = ['ca32']

opener = None

def resp2soup(resp):
    return BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')

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
        owner_tag = owner_pre_tag.next_element
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
        
def loginout_exec(func, **kwargs):
    return_result = None
    try:
        print 'login'
        resp = login(username=username, password=passwd)
        if func:
            print 'exec...'
            return_result = func(login_resp = resp, **kwargs)

    except Exception as e:
        print traceback.format_exc()
    finally:
        resp = logout()
        print 'logout'
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

    print 'relaxs:%s' %','.join(relaxs)
    #print_ins_map(not_relax_map)
    
    todo_list = get_list_to_apply(not_relax_map)
    for line in todo_list:
        print '%s: %s' %(line[0], line[-1])
        
        
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
    
    
def apply_run(end_date=None):
    while True:
        if end_date < datetime.now():
            return
        relaxs = get_relaxs()
        relaxs = get_need(relaxs)
        ins_id = apply_one(todo_list=relaxs)
        if ins_id:
            print 'applyed:%s' %ins_id
            return
        time.sleep(1000)
    
    
        
def apply_loop(login_resp=None, end_date=None):
    if not end_date:
        return None
        
    thr = threading.Thread(target=apply_run, kwargs={'end_date':end_date})
    
    thr.start()
    thr.join()
    
        
if __name__ == '__main__':
    not_relax_map, relaxs, todo_list = loginout_exec(to_get_list)
    ins_id = loginout_exec(apply_one, todo_list=['gd09'])
    print 'apply ', ins_id
    print 'throw ', loginout_exec(throw_one, ins_id=ins_id, user_id=username)
    
    
    
    
    
    
    
    
    
    
    
    
    
    


