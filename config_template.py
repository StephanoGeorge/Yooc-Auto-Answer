class Account:
    def __init__(self, cookies, examsUrl):
        self.cookies = cookies
        self.examsUrl = examsUrl


# 账户列表
accounts = [
    Account({'csrftoken': '123', 'sessionid': 'abc'}, 'https://www.yooc.me/group/123456/exams'),
    Account({'csrftoken': '456', 'sessionid': 'def'}, 'https://www.yooc.me/group/123456/exams'),
]
# 题库数量, 指定为 0 可以禁用数量检测
questionBanksAmount: 300
