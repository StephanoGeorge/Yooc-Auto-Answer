# -*- coding: utf-8 -*-
import atexit
import yaml
import re
import time
from random import random
from threading import Thread

import requests

import answer


def repeatExam(config):
    examsUrl = config['examsUrl']
    sess = requests.Session()
    sess.cookies.update(config['cookies'])
    sess.headers.update(answer.headers)
    while True:
        if config['questionBanksAmount'] != 0 and len(questionBanks['1']) >= config['questionBanksAmount']:
            print('题库收集完毕')
            break
        detailUrl = answer.getDetailUrl(examsUrl, sess)
        examHtml = sess.get(detailUrl).text
        questionIds = re.findall(r'<div class="question-board" id="question-([0-9]+?)">', examHtml)
        time.sleep(5 + random() * 5)  # 睡眠 [5, 10]s
        answers = [{questionId: {'1': '0'}} for questionId in questionIds]
        answer.submitAnswer(sess, detailUrl, answers)
        time.sleep(2 + random() * 3)  # 睡眠 [2, 3]s

        examHtml = sess.get(detailUrl).text
        examHtml = examHtml.replace('\n', '')
        for question in re.findall(r'question-board" id="question-([0-9]+?)">(.+?)</div>', examHtml):
            questionId = question[0]
            questionContent = question[1]
            try:
                _answer = re.search(r'<p>正确答案：(.+?)</p>', questionContent).group(1)
            except AttributeError:
                print(examHtml)
                return
            if '<span class="ans"' in questionContent:
                # 填空题
                questionBanks['1'][questionId] = [_answer]
            else:
                _answer = _answer.replace('、', '')
                order = re.findall('data-question-value="([0-9])"', questionContent)
                #                                #  ord('A') = 65
                questionBanks['1'][questionId] = [order[ord(i) - 65] for i in _answer]
        time.sleep(5 + random() * 5)  # 睡眠 [5, 10]s


def saveConfig():
    with open('QuestionBanks.yaml', 'w', encoding='UTF-8') as _file:
        yaml.safe_dump(questionBanks, _file, indent=4, allow_unicode=True)


with open('config.yaml', 'r', encoding='UTF-8') as file:
    config = yaml.safe_load(file)
with open('QuestionBanks.yaml', 'r', encoding='UTF-8') as file:
    questionBanks = yaml.safe_load(file)

for account in config['accounts']:
    Thread(target=repeatExam, args=(account,)).start()

atexit.register(saveConfig)
