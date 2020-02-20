import json
import os
import re


def parseQuestionsFromTxt(questions):
    questions = re.sub('([ABCDEFG])\t', r'\1、', questions)
    questions = onlyKeepChineseWords(questions)
    questions = re.split(r'\n+?[0-9]+、', questions)  # 分割题目
    del questions[0]
    # 保证所有选项独立成行
    # answers = re.sub(r'([^\na-zA-Z0-9])([ABCDEFG]、)', r'\1\n\2', answers)
    _questions = {}
    for question in questions:
        question = question.replace('\n', '')  # 题目+选项+答案
        problem = None  # 题目
        options = []  # 选项
        answers = None  # 答案
        if re.search(r'A[、.].+?B[、.]', question) is None:
            # 判断题
            parts = re.search(r'(.+?)([对错]$)', question)
            _questions[parts.group(1)] = ['0' if parts.group(2) == '对' else '1']
        else:
            # 选择题
            # ABCDEFG
            for i in range(6):
                parts = re.split('{}[、.]'.format(chr(65 + i)), question)
                if len(parts) == 1 and i < 4:  # ABCD
                    parts = question.split('{}\t'.format(chr(65 + i)))
                if len(parts) == 1:  # 循环到不存在的选项
                    lastParts = re.search('(.+?)(参考)?答案(A?B?C?D?E?F?G?)', question)
                    if lastParts is None:
                        options.append(parts[0])
                    else:
                        # 答案在尾部
                        answers = lastParts.group(3)
                        options.append(lastParts.group(1))
                    break
                question = parts[1]
                if i == 0:
                    problem = parts[0]
                    continue
                options.append(parts[0])
            if answers is None:
                problemParts = re.search(r'(.+?)(A?B?C?D?E?F?G?)$', problem)
                problem = problemParts.group(1)
                answers = problemParts.group(2)
            options.sort()  # 保证统一
            # {'题目_选项': ['0', '1', '2']}                      # ord('A') - ord('0') = 17
            _questions['_'.join((problem, *options))] = [chr(ord(i) - 17) for i in answers]
    return _questions


def parseQuestionsFromHtml(questions):
    questions = re.split(r'<div style=".+?" class="cls_003"><span class="cls_003">'
                         r'[0-9]+</span><span[\n\s]+?class="cls_002">、', questions)
    del questions[0]
    del questions[-1]
    _questions = {}
    for question in questions:
        # 答案标签 class
        answers = re.findall(r'<span[\n\s]+class="cls_005">(.+?)</span>'
                             r'([\n\s]*<span[\n\s]+class="cls_007">(.+?)</span>)?', question)
        # 合并
        answers = [answer[0] + answer[2] for answer in answers]
        # 移除空白填空
        # answers = list(filter(lambda item: not item.isspace(), answers))
        question = re.sub(r'<span[\n\s]+class="cls_00[57]">.+?</span>', '', question)
        question = re.sub(r'<.+?>', '', question, flags=re.S)
        # 只保留汉字,数字,字母等字符, 适用于填空题
        question = re.sub(r'[^\u4e00-\u9fa5、.a-zA-Z0-9]', '', question)
        _questions[question] = answers
        # questions = []
        # soup = BeautifulSoup(file, "lxml")
        # for i in soup.find_all(class_='cls_003'):
        #     i.getText()
        # for tag in soup.find_all(getBlankTag):
        #     tag.string.replace_with('___')
    return _questions


def onlyKeepChineseWords(string):
    # 只保留汉字,数字,字母,换行等字符, 不适用于填空题
    return re.sub(r'[^\u4e00-\u9fa5、.a-zA-Z0-9\n]', '', string)


questionsBank = {}

with os.scandir('QuestionsBank') as files:
    for entry in files:
        with open(entry) as file:
            if file.name.endswith('.html'):
                questionsBank = {**questionsBank, **parseQuestionsFromHtml(file.read())}
            else:
                questionsBank = {**questionsBank, **parseQuestionsFromTxt(file.read())}

with open('./QuestionsBank.json', 'w') as file:
    json.dump(questionsBank, file, indent=4, ensure_ascii=False)
