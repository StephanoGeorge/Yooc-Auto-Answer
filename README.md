# 优课 (yooc.me) 自动答题

# 使用方法

**执行所有操作前需要保证帐号不在考试中**

### 运行 `parseQuestionsBankToJson.py` 可以整理 `txt`,`html` 格式题库为 `json` 格式

> 在此之前, 将题库转换为 `txt` 格式置于 `QuestionsBank` 文件夹中
>
> > 可以接受的题库格式包括:
> >
> > ```
> > 23、问题(ABC)
> > A、选项
> > B、选项
> > ...
> > ```
> > ```
> > 23、问题
> > A、选项
> > B、选项
> > ...
> > 答案: ABC
> > ```
> 
> 对于填空题, 因为 `txt` 格式不能展示, 所以要使用工具将 `docx`,`pdf` 格式转换为 `html`, 再整理, 如果整理失败, 需要修改代码以匹配当前的 `html`

### 运行 `repeatExamToGetQuestionsBank.py` 可以重复测试以向 `json` 中增加题库

> 在此之前, 将 `configTemplate.json` 文件更名为 `config.json`, 并配置, 其中将题库数量指定为 0 可以禁用数量检测

### 运行 `answer.py` 以自动答题

> 在网页中使用开发者工具, 复制其中任一网络请求的 cookies, 处理 cookies 适配 firefox, 若失败需要修改代码

# 说明

- 需要题库或者考试可以反复测试