# -*- coding: UTF-8 -*-
import re
from pathlib import Path

import yaml


def parseQuestionsFromTxt(questionBanksI):
    questionBanksI = questionBanksI.replace('（', '(')
    questionBanksI = questionBanksI.replace('）', ')')
    questionBanksI = re.sub(r'((?<!^[(\[]) )|( (?![)\]]))', '', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'^\t+', '', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'[^\u4e00-\u9fa5、. ()\[\]a-zA-Z0-9\t\n]', '', questionBanksI)
    questionBanksI = re.sub(r'(?<=[^\n]\n)([ABCDEFG])[\t、.]+', r'\n`\1`', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'(?<=[^\n]\n)[(\[]([Xx ])[)\]]', r'`\1`', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'(参考)?答案?(?P<answer>[ABCDEFG对错]+)$', r'`!\g<answer>`!', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'\((?P<answer>[ABCDEFG对错]+)\)$', r'`!\g<answer>`!', questionBanksI, flags=re.M)
    questionBanksI = re.sub(r'[\[\]()\t、]', '', questionBanksI)
    while '\n\n\n' in questionBanksI:
        questionBanksI = questionBanksI.replace('\n\n\n', '\n\n')
    questionBanksI = re.sub(r'\n+$', '', questionBanksI)
    questionsBanksDict = {}

    for questionBank in questionBanksI.split('\n\n'):
        question = None  # 题目
        options = None  # 选项
        answers = None  # 答案
        lines = questionBank.split('\n')
        searchQuestion = re.search(r'(.+)`!(.+)`!', lines[0])
        searchAnswer = re.search(r'`!(.+)`!', lines[-1])
        if searchQuestion is not None:
            question = searchQuestion.group(1)
            answers = searchQuestion.group(2)
        else:
            question = lines[0]
            if searchAnswer is not None:
                answers = searchAnswer.group(1)
        if searchAnswer is not None:
            options = lines[1:-1]
        else:
            options = lines[1:]
        if answers is None:
            answers = []
            for option, line in enumerate(options):
                searchOption = re.search(r'^`(.)`', line)
                if searchOption is not None:
                    if searchOption.group(1) != ' ':
                        answers.append(str(option))  # 0, 1, 2
        for index, option in enumerate(options):
            options[index] = re.sub(r'^`.`', '', option)
        if answers == '对':
            answers = ['0']
        elif answers == '错':
            answers = ['1']
        elif re.search(r'[0-9]', answers[0]) is None:
            # ord('A') - ord('0') = 17
            answers = [chr(ord(i) - 17) for i in answers]
        options.sort()  # 保证统一
        # {'题目_选项': ['0', '1', '2']}
        questionsBanksDict['_'.join((question, *options))] = answers

    return questionsBanksDict


def parseQuestionsFromHtml(questions):
    questions = re.split(r'<div style=".+?" class="cls_003"><span class="cls_003">'
                         r'[0-9]+</span><span[\n\s]+?class="cls_002">、', questions)
    del questions[0]
    del questions[-1]
    questions = {}
    for question in questions:
        # 答案标签 class
        answers = re.findall(r'<span[\n\s]+class="cls_005">(.+?)</span>'
                             r'([\n\s]*<span[\n\s]+class="cls_007">(.+?)</span>)?', question)
        # 合并
        answers = [answer[0] + answer[2] for answer in answers]
        # 移除空白填空
        question = re.sub(r'<span[\n\s]+class="cls_00[57]">.+?</span>', '', question)
        question = re.sub(r'<.+?>', '', question, flags=re.S)
        # 只保留汉字,数字,字母等字符, 适用于填空题
        question = re.sub(r'[^\u4e00-\u9fa5.a-zA-Z0-9]', '', question)
        questions[question] = answers
    return questions


questionBanks = {}
for file in Path('Question-Banks').iterdir():
    with file.open('r', encoding='UTF-8') as stream:
        if file.suffix == '.html':
            questionBanks = {**questionBanks, **parseQuestionsFromHtml(stream.read())}
        else:
            questionBanks = {**questionBanks, **parseQuestionsFromTxt(stream.read())}
path = Path('Question-Banks.yaml')
if not path.exists():
    path.touch()
with path.open('r+', encoding='UTF-8') as file:
    questionBanksO = yaml.safe_load(file)
    if questionBanksO is None:
        questionBanksO = {'collected': {}}
    questionBanksO['parsed'] = questionBanks
    file.seek(0)
    yaml.safe_dump(questionBanksO, file, indent=4, allow_unicode=True)
