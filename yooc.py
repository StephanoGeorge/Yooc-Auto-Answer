import requests
import time
from lxml import etree
import re

# 此处填写cookie字符串
cookie_temp = ''
cookie = {i.split('=')[0]: i.split('=')[1] for i in cookie_temp.split(';')}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"}
repeat_url = 'https://www.yooc.me/group/166710/exam/104336/examuser/25503057/repeat'
detail_url = 'https://www.yooc.me/group/166710/exam/104336/detail'
#发送重做请求
respnse1 = requests.post(repeat_url, headers=headers, cookies=cookie)
time.sleep(2)
#发送获取详情请求
respnse2 = requests.get(detail_url, headers=headers, cookies=cookie)
respnse2.encoding = 'utf-8'
x = respnse2.text
with open('detail.tet', 'w', encoding='utf-8') as h:
    h.write(x)
#获取到每一道题目的正确形式
detail_html = etree.HTML(respnse2)
questions_temp = detail_html.xpath('//div[@class="question-board"]/p[2]/text()')
questions = []
for i in questions_temp:
    n2 = re.sub('[^\u4e00-\u9fa5、a-zA-Z0-9\n]', '', i)
    questions.append(n2)
print(questions)

