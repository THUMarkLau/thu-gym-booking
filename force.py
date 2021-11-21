import datetime
import json
import time
import utils

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

#########################################################################

# 格式为2021-11-06这种，默认为当前日期加3。
date = (datetime.datetime.now().date() + datetime.timedelta(days=3)) \
    .strftime('%Y-%m-%d')


#########################################################################

class SpecialDict(dict):
    def __missing__(self, key):
        return key


with open("config.json", "r", encoding="utf8") as f:
    config = json.load(f)
username = config['username']
password = config['password']
phone_number = config['phone']
date_time = config['time']
station = config['station']
weight_map = utils.gen_weight_map(config)

firefox_option = Options()
firefox_option.add_argument('--headless')
driver = webdriver.Firefox(options=firefox_option)
driver.get('https://50.tsinghua.edu.cn/login_m.jsp')
driver.implicitly_wait(1)
driver.find_elements_by_id('login_username')[0].send_keys(username)
driver.find_elements_by_id('login_password')[0].send_keys(password)
elements = driver.find_elements_by_tag_name('input')
for element in elements:
    if element.get_attribute('value') == '登录':
        element.click()
ret = driver.get_cookies()
cookies = {}
for cookie in ret:
    cookies[cookie['name']] = cookie['value']
driver.quit()

import requests
from io import BytesIO
from PIL import Image

session = requests.session()
session.cookies.update(cookies)

re = session.get('https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=&viewType=m')

for line in re.content.decode('gbk').split('\n'):
    line = line.strip()
    if line.find('<a onclick="chooseItem(\'') != -1 and \
            line.find('气膜馆') != -1:
        qimo = int(line.split("'")[1])
    if line.find('<a onclick="chooseItem(\'') != -1 and \
            line.find('西体育馆') != -1:
        xiti = int(line.split("'")[1])
    if line.find('<a onclick="chooseItem(\'') != -1 and \
            line.find('综合体育馆') != -1:
        zongti = int(line.split("'")[1])

stations = {'气膜': qimo, '西体': xiti, '综体': zongti}  # 399800, 4836273, 4797914
print(stations)

station = stations[station]

re = session.get('https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=' + str(
    station) + '&item_id=&time_date=&viewType=m')

prefix = '<a href="javascript:chooseItem(\'' + str(station) + "','"

for line in re.content.decode('gbk').split('\n'):
    line = line.strip()
    if line.find(prefix) != -1 and line.find('羽毛球') != -1:
        item_id = line.split("'")[3]
        break

re = session.get('https://50.tsinghua.edu.cn/Kaptcha.jpg')
Image.open(BytesIO(re.content)).show()

print('Please enter the captcha: ', end='', flush=True)

captcha = input()
print('Captcha:', captcha)

start_time = datetime.datetime.now()

cost = {}
re = session.get('https://50.tsinghua.edu.cn/gymsite/cacheAction.do?ms=viewBook&gymnasium_id=' + str(
    station) + '&item_id=' + item_id + '&time_date=' + date + '&userType=1')

for line in re.content.decode('gbk').split('\n'):
    line = line.strip()
    if line.find('addCost(\'') != -1:
        cost[line.split("'")[1]] = int(float(line.split("'")[3]))

print(cost)
times = 0

while True:
    time.sleep(0.5)
    end_time = datetime.datetime.now()
    if (end_time - start_time).seconds >= 1800:
        print('30min. Exit.')
        exit(0)
    times += 1
    print(times, ':', (end_time - start_time).seconds)

    flag_not_open = False
    re = session.get('https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=' + str(
        station) + '&item_id=&time_date=' + date + '&viewType=m')
    for line in re.content.decode('gbk').split('\n'):
        line = line.strip()
        if line.find('第三天以后网上预约已关闭，开放时间为每天') != -1:
            flag_not_open = True
            break
    if flag_not_open:
        continue

    re = session.get('https://50.tsinghua.edu.cn/gymsite/cacheAction.do?ms=viewBook&gymnasium_id=' + str(
        station) + '&item_id=' + item_id + '&time_date=' + date + '&userType=1')

    marked_ids = set()
    flag_find = False

    for line in re.content.decode('gbk').split('\n'):
        line = line.strip()
        if line.find('markResStatus(\'') != -1:
            marked_ids.add(line.split("'")[3])

    places = []
    for line in (re.content.decode('gbk').split('\n')):
        line = line.strip()
        if line.find('resourceArray.push({id:\'') != -1:
            place = eval(line[line.find('('): -1], SpecialDict())
            if not place['id'] in marked_ids and place['time_session'] in date_time:
                flag_find = True
                places.append(place)
    places = utils.sorted_by_weights(places, weight_map)

    if flag_find:
        for place in places:
            id = place['id']
            re = session.post('https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=saveGymBook', data={
                'bookData.totalCost': cost[id],
                'bookData.book_person_zjh': '',
                'bookData.book_person_name': '',
                'bookData.book_person_phone': phone_number,
                'bookData.book_mode': 'from-phone',
                'item_idForCache': id,
                'time_dateForCache': date,
                'userTypeNumForCache': '1',
                'putongRes': 'putongRes',
                'code': captcha,
                'selectedPayWay': '1',
                'allFieldTime': id + '#' + date
            })
            if re.content.decode('gbk').find("成功") != -1:
                print(re.content.decode('gbk'))
                exit(0)
        print("没有场地可以预定！")
