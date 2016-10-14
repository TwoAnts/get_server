# -*- coding : utf-8 -*-
import re
import urllib
import urllib2
import cookielib
from bs4 import BeautifulSoup

post_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
	'Content-Type': 'application/x-www-form-urlencoded',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

url_login = 'http://115.156.209.252/dcms/userlogin.php'

username = 'M201672711'
passwd = '123456'


def login(data):
	post_data = urllib.urlencode(data)
	cj=cookielib.CookieJar()   
	opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	req = urllib2.Request(url_login, post_data, post_headers)
	content=opener.open(req)
	
	return content.read().decode('utf-8')
	

	
if __name__ == '__main__':
	data = {
		'username': username,
		'password': passwd,
		'submit': 'login',
	}
	
	result = login(data)
	soup = BeautifulSoup(result, "html.parser")
	
	is_relax = {}
	relaxs = []
	
	for td in soup.find_all('td'):
		#print td.a.text, td.font.attrs['color']
		is_relax[td.a.text] = (td.font.attrs['color'] == 'green')
		if is_relax[td.a.text]:
			relaxs.append(td.a.text)

	print 'relaxs:%s' %','.join(relaxs)
	
	
	
	
	
	


