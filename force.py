import datetime
import json
import time
import utils
import ddddocr
import urllib.request
import os
import cv2
import random
import sys

from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options

#########################################################################
with open("config.json", "r", encoding="utf8") as f:
    config = json.load(f)
test_mode = config['test_mode'] == "true"
username = config['username']
password = config['password']
phone_number = config['phone']
date_time = config['time']
if test_mode:
    date_time = ["11:30-13:00"]
station_list = config['station']
station = config['station']
pay_way = config['pay-way']
pay_way = "1" if pay_way == "online" else "0"
weight_map = utils.gen_weight_map(config)
logf = open("./run.log", "w", encoding="utf-8")


def my_print(self, *args):
    s = str(self)
    if len(args) != 0:
        for arg in args:
            s += str(arg)
    logf.write(s + "\n")
    logf.flush()
    print(s)


if not test_mode:
    localtime = time.localtime(time.time())
    if localtime.tm_hour > 8:
        # wait for the second day
        now = time.localtime(time.time())
        today = datetime.datetime.today()
        tomorrow = today + datetime.timedelta(days=1)
        next_day_str = tomorrow.strftime("%Y-%m-%d 07:58:30")
        my_print(next_day_str)
        start_ts = time.mktime(time.strptime(next_day_str, "%Y-%m-%d %H:%M:%S"))
    else:
        # wait for current day
        start_str = datetime.datetime.today().strftime("%Y-%m-%d 07:58:30")
        my_print(start_str)
        start_ts = time.mktime(time.strptime(start_str, "%Y-%m-%d %H:%M:%S"))
        pass

    urls = ["http://www.baidu.com", "https://www.tsinghua.edu.cn/", "https://www.zhihu.com/", "https://www.jd.com",
            "https://learn.pingcap.com/", "http://www.aiyuke.com/", "https://www.csdn.net/"]
    while time.time() < start_ts:
        # get random website to keep campus network alive
        try:
            req = urllib.request.urlopen(random.choice(urls))
        except Exception as e:
            pass
        time.sleep(min(60, start_ts - time.time()))

my_print("now is " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

# 格式为2021-11-06这种，默认为当前日期加3。
date = (datetime.datetime.now().date() + datetime.timedelta(days=3)) \
    .strftime('%Y-%m-%d')
if test_mode:
    date = "2022-04-22"
my_print(date)


#########################################################################

class SpecialDict(dict):
    def __missing__(self, key):
        return key


browser_option = Options()
browser_option.add_argument('--headless')
driver = webdriver.Chrome(options=browser_option)
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

session = requests.session()  # this is a test sentence
session.cookies.update(cookies)

re = session.get('https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=&viewType=m')

for line in re.content.decode('gbk').split('\n\r'):
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
my_print(str(stations))
my_print(str(date_time))
station_idx = 0
while True:
    station_name = station_list[station_idx]
    my_print("booking " + station_name)
    station = stations[station_name]

    re = session.get('https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=' + str(
        station) + '&item_id=&time_date=&viewType=m')

    prefix = '<a href="javascript:chooseItem(\'' + str(station) + "','"

    for line in re.content.decode('gbk').split('\n'):
        line = line.strip()
        if line.find(prefix) != -1 and line.find('羽毛球') != -1:
            item_id = line.split("'")[3]
            break

    captcha = utils.get_verification_code(session)
    if test_mode:
        captcha = "test"
    my_print('Captcha: ' + captcha)

    # os.remove('raw.jpeg')
    # os.remove('done.jpeg')

    start_time = datetime.datetime.now()

    cost = {}
    if test_mode:
        item_id = "4037036"
    re = session.get('https://50.tsinghua.edu.cn/gymsite/cacheAction.do?ms=viewBook&gymnasium_id=' + str(
        station) + '&item_id=' + item_id + '&time_date=' + date + '&userType=1')

    for line in re.content.decode('gbk').split('\n'):
        line = line.strip()
        if line.find('addCost(\'') != -1:
            cost[line.split("'")[1]] = int(float(line.split("'")[3]))

    times = 0
    open_times = 0
    while open_times < 3:
        time.sleep(0.5)
        end_time = datetime.datetime.now()
        if (end_time - start_time).seconds >= 300:
            my_print('30min. Exit.')
            exit(0)
        times += 1
        my_print(times, ':', (end_time - start_time).seconds)

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
            for idx, place in enumerate(places):
                if idx > 10 and (station_name == "综体" or station_name == "西体"):
                    break
                id = place['id']
                re = session.post('https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=saveGymBook',
                                  data={
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
                                      'selectedPayWay': pay_way,  # 0 为现场支付，1 为线上支付
                                      'allFieldTime': id + '#' + date
                                  })
                my_print(re.content.decode('gbk'))
                if re.content.decode('gbk').find("验证码错误") != -1:
                    my_print("验证码错误")
                    captcha = utils.get_verification_code(session)
                if re.content.decode('gbk').find("成功") != -1:
                    my_print("预定成功")
                    exit(0)
            open_times += 1
            my_print("没有场地可以预定！")
