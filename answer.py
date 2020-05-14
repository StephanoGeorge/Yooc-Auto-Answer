# -*- coding: UTF-8 -*-
import json
import re
import time
from pathlib import Path
from random import random

import requests
from fuzzywuzzy import process
from simplejson import JSONDecodeError

headers = {'Host': 'www.yooc.me',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
           'Accept-Encoding': 'gzip, deflate',
           'DNT': '1',
           'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
           'Pragma': 'no-cache',
           'Cache-Control': 'no-cache'}


def getPostHeaders(refererUrl, sessionM):
    return {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.yooc.me',
            'Referer': refererUrl,
            'X-CSRFToken': sessionM.cookies.get('csrftoken', domain=''),
            'X-Requested-With': 'XMLHttpRequest'}


def getDetailUrl(examsUrlI, sessionI):
    examHtmlI = sessionI.get(examsUrlI).text
    time.sleep(0 + random() * 1)  # 睡眠 [0, 1]s
    repeatUrl = re.search(r'repeat-url="(.+?)">重做试卷', examHtmlI)
    if repeatUrl is not None:
        try:
            response = sessionI.post(repeatUrl.group(1),
                                     headers={**getPostHeaders(examsUrlI, sessionI),
                                              'Content-Type': 'application/json; charset=utf-8'},
                                     data={'csrfmiddlewaretoken': sessionI.cookies.get('csrftoken', domain='')})
            return response.json()['url']
        except JSONDecodeError:
            with Path('log', 'exams-JSONDecodeError-{}.html'.format(time.time()), 'w', encoding='UTF-8').open() as fi:
                fi.write(response.text)
    else:
        with Path('log', 'exams-{}.html'.format(time.time())).open('w', encoding='UTF-8') as fi:
            fi.write(examHtmlI)
        return re.search(r'href="(.+?)" id="start-exam" class="start-exam" target="_blank">'
                         r'开始考试', examHtmlI).group(1)


def addAnswer(keyI):
    if keyI in questionBanks['parsed']:
        answers.append({questionId: {'1': questionBanks['parsed'][keyI]}})
    else:
        # 模糊匹配
        possibleKey = process.extractOne(keyI, questionBanks['parsed'].keys())
        print('key: {}\npossibleKey: {}'.format(keyI, possibleKey), end='\n\n')
        answers.append({questionId: {'1': questionBanks['parsed'][possibleKey[0]]}})


def submitAnswer(sessionI, detailUrlI, answersI):
    return sessionI.post(detailUrlI.replace('detail', 'answer/submit'),
                         headers=getPostHeaders(detailUrlI, sessionI),
                         data={
                             'csrfmiddlewaretoken': sessionI.cookies.get('csrftoken', domain=''),
                             'answers': json.dumps(answersI),
                             'type': '0',
                             'auto': '0'
                         })


def onlyKeepChineseChars(string):
    string = re.sub(r'[^\u4e00-\u9fa5.`a-zA-Z0-9]', '', string)
    string = re.sub(r'((?<=[^0-9])\.)|(\.(?=[^0-9]))', '', string)
    return string


if __name__ == '__main__':
    fileI = Path.home() / '.config' / '.yoocAutoAnswer'
    print('\u4e3a\u9632\u6b62\u5546\u7528,'
          '\u4f7f\u7528\u95f4\u9694\u5fc5\u987b'
          '\u5927\u4e8e\u4e94\u5c0f\u65f6')
    session = requests.Session()
    if fileI.exists():
        with fileI.open() as f:
            r = float(f.read())
            if r != 0 and time.time() - r < 18e3:
                quit()
    with open('Question-Banks.json', 'r', encoding='UTF-8') as file:
        questionBanks = json.load(file)

    cookies = input('键入 cookies, 形如: {"响应 Cookie":{...},"请求 Cookie":{"csrftoken":"123abc",'
                    '"Hm_lpvt_123":"1574858254","sessionid":"123abc"}}:\n')
    session.cookies.update(json.loads(cookies))

    examsUrl = input('键入在线测试页面 URL, 形如: https://www.yooc.me/group/123456/exams:\n')

    session.headers.update(headers)
    detailUrl = getDetailUrl(examsUrl, session)
    examHtml = session.get(detailUrl, headers={'Referer': examsUrl}).text
    with Path('log', 'detail-{}.html'.format(time.time())).open('w', encoding='UTF-8') as f:
        f.write(examHtml)
    startTime = time.time()
    examHtml = examHtml.replace('\n', '')
    print('\n开始答题\n\n')
    answers = []  # 要提交的答案

    for question in re.findall(r'question-board" id="question-([0-9]+?)">(.+?)</div>', examHtml):
        answer = []
        questionId = question[0]
        questionContent = question[1]
        if questionId in questionBanks['collected']:
            answers.append({questionId: {'1': questionBanks['collected'][questionId]}})
            continue
        questionContent = re.sub(r'q-cnt crt">[0-9]+、<span>\[[0-9]+分\]', '', questionContent)
        if '<input type="text">' in questionContent:
            # 填空题
            questionContent = re.sub(r'<.+?>', '``', questionContent, flags=re.S)
            questionContent = onlyKeepChineseChars(questionContent)
            questionContent = questionContent.replace('``', '_')
            addAnswer(questionContent)
        else:
            # 选择题/判断题
            questionI = re.search('q-cnt crt">(.+?)</p>', questionContent).group(1)
            questionI = re.sub(r'<.+?>', '', questionI, flags=re.S)
            questionI = onlyKeepChineseChars(questionI)
            options = []
            for option in re.findall('<li>(.+?)</li>', questionContent):
                option = re.sub(r'<.+?>', '', option, flags=re.S)
                option = onlyKeepChineseChars(option)
                option = re.sub('^[ABCDEFG][、.]', '', option)
                options.append(option)
            options.sort()
            key = '_'.join((questionI, *options))
            addAnswer(key)

    while True:
        try:
            print('\r已经开考 {} s, 键入 Ctrl + C 以提交'.format(round(time.time() - startTime)), end='', flush=True)
            time.sleep(1)
        except KeyboardInterrupt:
            print()
            break
    print(submitAnswer(session, detailUrl, answers).json()['message'])
    if r != 0:
        with fileI.open('w') as f:
            f.write(str(time.time()))
