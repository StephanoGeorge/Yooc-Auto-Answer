import json
import logging
import os
import re
import time
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


def getPostHeaders(refererUrl, sess):
    return {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.yooc.me',
            'Referer': refererUrl,
            'X-CSRFToken': sess.cookies.get('csrftoken', domain=''),
            'X-Requested-With': 'XMLHttpRequest'}


def getDetailUrl(examsUrl, sess):
    _examHtml = sess.get(examsUrl).text
    time.sleep(0 + random() * 1)  # 睡眠 [0, 1]s
    repeatUrl = re.search(r'repeat-url="(.+?)">重做试卷', _examHtml)
    if repeatUrl is not None:
        try:
            resp = sess.post(repeatUrl.group(1),
                             headers={**getPostHeaders(examsUrl, sess),
                                      'Content-Type': 'application/json; charset=utf-8'},
                             data={'csrfmiddlewaretoken': sess.cookies.get('csrftoken', domain='')})
            return resp.json()['url']
        except JSONDecodeError:
            logging.warning(resp.text)
    else:
        print(_examHtml)
        return re.search(r'href="(.+?)" id="start-exam" class="start-exam" target="_blank">'
                         r'开始考试', _examHtml).group(1)


def addAnswer(_key):
    if _key in questionsBank['0']:
        answers.append({questionId: {'1': questionsBank['0'][_key]}})
    else:
        # 模糊匹配
        possibleKey = process.extractOne(_key, questionsBank['0'].keys())
        print('key: {}\npossibleKey: {}'.format(_key, possibleKey), end='\n\n')
        answers.append({questionId: {'1': questionsBank['0'][possibleKey[0]]}})


def submitAnswer(sess, detailUrl, answers):
    return sess.post(detailUrl.replace('detail', 'answer/submit'),
                     headers=getPostHeaders(detailUrl, sess),
                     data={
                         'csrfmiddlewaretoken': sess.cookies.get('csrftoken', domain=''),
                         'answers': json.dumps(answers),
                         'type': '0',
                         'auto': '0'
                     })


if __name__ == '__main__':
    fileName = os.path.expanduser('~/.config/.yoocAutoAnswer')
    print('\u4e3a\u9632\u6b62\u5546\u7528,'
          '\u4f7f\u7528\u95f4\u9694\u5fc5\u987b'
          '\u5927\u4e8e\u4e94\u5c0f\u65f6')
    sess = requests.Session()
    if os.path.exists(fileName):
        with open(fileName) as f:
            r = f.read()
            if float(r) != 0 and time.time() - float(r) < 18e6:
                os._exit(0)
    with open('QuestionBanks.json') as file:
        questionsBank = json.load(file)

    cookies = input('键入 cookies, 形如: {"响应 Cookie":{...},"请求 Cookie":{"csrftoken":"123abc",'
                    '"Hm_lpvt_123":"1574858254","sessionid":"123abc"}}:\n')
    cookies = json.loads(re.search(r'"请求 Cookie":(.+?)\}$', cookies).group(1))
    sess.cookies.update(cookies)

    examsUrl = input('键入知识竞赛页面 URL, 形如: https://www.yooc.me/group/123456/exams:\n')

    sess.headers.update(headers)
    detailUrl = getDetailUrl(examsUrl, sess)
    examHtml = sess.get(detailUrl, headers={'Referer': examsUrl}).text
    ###############################################
    with open('./log/detail.html', 'w') as f:
        f.write(examHtml)
    startTime = time.time()
    examHtml = examHtml.replace('\n', '')
    print('\n开始答题\n\n')
    answers = []  # 要提交的答案

    for question in re.findall(r'question-board" id="question-([0-9]+?)">(.+?)</div>', examHtml):
        answer = []
        questionId = question[0]
        questionContent = question[1]
        if questionId in questionsBank['1']:
            answers.append({questionId: {'1': questionsBank['1'][questionId]}})
            continue
        questionContent = re.sub(r'q-cnt crt">[0-9]+、<span>\[[0-9]+分\]', '', questionContent)
        if '<input type="text">' in questionContent:
            # 填空题
            questionContent = re.sub(r'<.+?>', '', questionContent, flags=re.S)
            questionContent = re.sub(r'[^\u4e00-\u9fa5、.a-zA-Z0-9]', '', questionContent)
            addAnswer(questionContent)
        else:
            problem = re.search('q-cnt crt">(.+?)</p>', questionContent).group(1)
            problem = re.sub(r'<.+?>', '', problem, flags=re.S)
            problem = re.sub(r'[^\u4e00-\u9fa5、.a-zA-Z0-9]', '', problem)
            if '<ol class="true-or-false">' in questionContent:
                # 判断题
                addAnswer(problem)
            else:
                # 选择题
                options = []
                for option in re.findall('<li>(.+?)</li>', questionContent):
                    option = re.sub(r'<.+?>', '', option, flags=re.S)
                    option = re.sub(r'[^\u4e00-\u9fa5、.a-zA-Z0-9]', '', option)
                    option = re.sub('^[ABCDEFG][、.]', '', option)
                    options.append(option)
                options.sort()
                key = '_'.join((problem, *options))
                addAnswer(key)

    print('睡眠...\n')
    finishTime = time.time()
    time.sleep(20 + random() * 5 - (finishTime - startTime) / 1000)  # 睡眠 [20, 25]s
    print(submitAnswer(sess, detailUrl, answers).json()['message'])
    with open(fileName, 'w') as f:
        f.write(str(time.time()))
