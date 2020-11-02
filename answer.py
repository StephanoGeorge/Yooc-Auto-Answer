# -*- coding: UTF-8 -*-
import json
import re
import time
from pathlib import Path
from random import random

import pyperclip
import requests
from fuzzywuzzy import process
from lxml import etree
from simplejson import JSONDecodeError

headers = {
    'Host': 'www.yooc.me',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}


def getPostHeaders(refererUrl, sessionM):
    return {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.yooc.me',
        'Referer': refererUrl,
        'X-CSRFToken': sessionM.cookies.get('csrftoken', domain=''),
        'X-Requested-With': 'XMLHttpRequest'
    }


def getDetailUrl(examsUrlI, sessionI):
    examHtmlI = sessionI.get(examsUrlI).text
    time.sleep(0 + random() * 1)  # 睡眠 [0, 1]s
    repeatUrl = re.search(r'repeat-url="(.+?)">重做试卷', examHtmlI)
    if repeatUrl is None:
        return re.search(r'href="(.+?)" id="start-exam" class="start-exam" target="_blank">'
                         r'开始考试', examHtmlI).group(1)
    else:
        response = sessionI.post(
            repeatUrl.group(1),
            headers={**getPostHeaders(examsUrlI, sessionI), 'Content-Type': 'application/json; charset=utf-8'},
            data={'csrfmiddlewaretoken': sessionI.cookies.get('csrftoken', domain='')}
        )
        try:
            return response.json()['url']
        except JSONDecodeError:
            with Path('log', 'exams-JSONDecodeError-{}.html'.format(time.time()), 'w', encoding='UTF-8').open() as fi:
                fi.write(response.text)


def addAnswer(keyI):
    if keyI in questionBanks['parsed']:
        answers.append({questionId: {'1': questionBanks['parsed'][keyI]}})
    else:
        # 模糊匹配
        possibleKey = process.extractOne(keyI, questionBanks['parsed'].keys())
        print('key in HTML: {}\npossible key in JSON: {}'.format(keyI, possibleKey), end='\n\n')
        answers.append({questionId: {'1': questionBanks['parsed'][possibleKey[0]]}})


def submitAnswer(sessionI, detailUrlI, answersI):
    return sessionI.post(
        detailUrlI.replace('detail', 'answer/submit'),
        headers=getPostHeaders(detailUrlI, sessionI),
        data={
            'csrfmiddlewaretoken': sessionI.cookies.get('csrftoken', domain=''),
            'answers': json.dumps(answersI),
            'type': '0',
            'auto': '0'
        }
    )


def onlyKeepChineseChars(string):
    string = re.sub(r'[^\u4e00-\u9fa5._`a-zA-Z0-9]', '', string)
    string = re.sub(r'((?<=[^0-9])\.)|(\.(?=[^0-9]))', '', string)
    return string


if __name__ == '__main__':
    fileI = Path.home() / '.config' / '.yoocAutoAnswer'
    print('\u4e3a\u9632\u6b62\u5546\u7528,'
          '\u4f7f\u7528\u95f4\u9694\u5fc5\u987b'
          '\u5927\u4e8e\u4e94\u5c0f\u65f6')
    session = requests.Session()
    session.headers.update(headers)
    try:
        if fileI.exists():
            with fileI.open() as f:
                r = float(f.read())
                if r != 0 and time.time() - r < 18e3:
                    quit()
    except Exception:
        pass
    with open('Question-Banks.json', 'r', encoding='UTF-8') as file:
        questionBanks = json.load(file)

    input('键入回车以从剪贴板中读取 cookies, 形如: {"csrftoken":"123abc","Hm_lpvt_123":"1574858254","sessionid":"123abc"}')
    cookies = pyperclip.paste()
    session.cookies.update(json.loads(cookies))
    input('键入回车以从剪贴板中读取在线测试页面 URL, 形如: https://www.yooc.me/group/123456/exams')
    examsUrl = pyperclip.paste()
    detailUrl = getDetailUrl(examsUrl, session)
    detailHtml = session.get(detailUrl, headers={'Referer': examsUrl}).text
    detailHtml = etree.HTML(detailHtml)
    startTime = time.time()
    print('\n开始答题\n\n')
    answers = []  # 要提交的答案

    for question in detailHtml.xpath("//div[@class='question-board']"):
        answer = []
        questionId = question.get('id')
        questionId = questionId[questionId.index('-') + 1:]
        if questionId in questionBanks['collected']:
            answers.append({questionId: {'1': questionBanks['collected'][questionId]}})
            continue
        questionContent = '_'.join(question.xpath('./p[2]/text()'))
        questionContent = onlyKeepChineseChars(questionContent)
        if question.xpath(".//input[@type='text']"):
            # 填空题
            addAnswer(questionContent)
        else:
            # 选择题/判断题
            options = []
            for option in question.xpath('.//label/text()'):
                option = onlyKeepChineseChars(option)
                option = re.sub(r'^[ABCDEFG][、.]?', '', option)
                options.append(option)
            options.sort()
            key = '_'.join((questionContent, *options))
            addAnswer(key)

    while True:
        try:
            print('\r已经开考 {} s, 键入 ^C 以提交'.format(round(time.time() - startTime)), end='', flush=True)
            time.sleep(1)
        except KeyboardInterrupt:
            print()
            break
    print(submitAnswer(session, 'detailUrl', answers).json()['message'])
    if r != 0:
        try:
            with fileI.open('w') as f:
                f.write(str(time.time()))
        except Exception:
            pass
