# language_learner

> 多语言学习助手，支持 17 种语言的单词、语法、句子学习，集成语音发音和完整的词典管理

## 技能描述

提供多语言学习能力，包括闪卡记忆、选择题测验、句子练习、语法学习、复习模式，以及完整的词典下载和管理功能

## 核心功能

1. 闪卡学习模式 - 高效的单词记忆方式
2. 选择题测验 - 检验学习成果
3. 句子练习 - 学习实际应用场景
4. 语法学习 - 掌握语言规则
5. 复习模式 - 巩固已学知识
6. 语音合成 - 支持多语言发音 (Edge TTS)
7. 学习进度追踪 - 记录学习统计
8. 完整词典下载 - 一键下载各语言词典
9. 知识库管理 - 添加/导入/导出单词和句子

## 支持的语言

| 语言 | 代码 | 词条数 | 数据源 |
|------|------|--------|--------|
| 英语 | en | 87,353 | WordNet (OMW) |
| 西班牙语 | es | 90,851 | WordNet (OMW) |
| 法语 | fr | 55,316 | WordNet (OMW) |
| 意大利语 | it | 41,829 | WordNet (OMW) |
| 葡萄牙语 | pt | 50,000 | WordNet (OMW) |
| 荷兰语 | nl | 43,066 | WordNet (OMW) |
| 波兰语 | pl | 45,342 | WordNet (OMW) |
| 芬兰语 | fi | 50,000 | WordNet (OMW) |
| 希腊语 | el | 18,216 | WordNet (OMW) |
| 阿拉伯语 | ar | 17,772 | WordNet (OMW) |
| 希伯来语 | he | 5,325 | WordNet (OMW) |
| 泰语 | th | 50,000 | WordNet (OMW) |
| 瑞典语 | sv | 5,823 | WordNet (OMW) |
| 日语 | ja | 15,012 | Jamdict |
| 中文 | zh | 10,000 | CEDICT + Jieba |
| 德语 | de | 230 | OpenThesaurus + 内置 |
| 韩语 | ko | 132 | 内置词库 |

## 输入

| 参数          | 类型      | 必填  | 默认值     | 描述                                                                                                                                                                           |
| ----------- | ------- | --- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| action      | string  | 是   | -       | 操作类型 (list/set_language/flashcard/quiz/sentence/grammar/review/speak/stats/kb_download_full_dict/kb_stats/kb_add_word/kb_add_sentence/kb_import_text/kb_export/mark_learned) |
| language    | string  | 否   | en      | 目标语言 (en/ja/ko/fr/de/es/zh/it/pt/nl/pl/fi/el/ar/he/th/sv)                                                                                                                    |
| text        | string  | 否   | -       | 要发音或翻译的文本                                                                                                                                                                    |
| word        | string  | 否   | -       | 单词                                                                                                                                                                           |
| meaning     | string  | 否   | -       | 释义                                                                                                                                                                           |
| example     | string  | 否   | -       | 例句                                                                                                                                                                           |
| source      | string  | 否   | wordnet | 词典源 (wordnet/jamdict/jieba/korean)                                                                                                                                           |
| count       | integer | 否   | 10      | 学习数量                                                                                                                                                                         |
| format      | string  | 否   | json    | 导出格式 (json/csv)                                                                                                                                                              |
| original    | string  | 否   | -       | 句子原文                                                                                                                                                                         |
| translation | string  | 否   | -       | 句子翻译                                                                                                                                                                         |
| title       | string  | 否   | -       | 语法标题                                                                                                                                                                         |
| rule        | string  | 否   | -       | 语法规则                                                                                                                                                                         |
| type        | string  | 否   | word    | 标记类型 (word/sentence/grammar)                                                                                                                                                 |

## 输出

| 字段          | 描述                   |
| ----------- | -------------------- |
| result      | 执行结果，包含学习的单词/语法/句子等  |
| status      | 执行状态 (success/error) |
| word        | 学习的单词                |
| meaning     | 单词含义                 |
| example     | 例句                   |
| audio_path  | 语音文件路径               |
| grammar     | 语法规则                 |
| sentence    | 练习句子                 |
| translation | 翻译结果                 |
| stats       | 学习统计                 |

## 步骤

1. 验证输入参数
2. 根据 action 类型执行对应操作
3. 返回处理结果

## 依赖

- nltk
- edge-tts
- requests
- jamdict
- jieba
- konlpy (可选)

### NLTK 数据下载

```python
import nltk
nltk.download('wordnet')
nltk.download('omw-2.0')
```

### Jamdict 数据下载（日语）

```bash
python -c "from jamdict import Jamdict; jmd=Jamdict(); jmd.import_data()"
```

### 示例

```python
learner = LanguageLearner()

# 查看所有可用语言
result = learner.execute(action="list")

# 下载英语词典
result = learner.execute(
    action="kb_download_full_dict",
    language="en",
    source="wordnet"
)

# 下载日语词典
result = learner.execute(
    action="kb_download_full_dict",
    language="ja",
    source="jamdict"
)

# 闪卡模式 - 学习 10 个新单词
result = learner.execute(
    action="flashcard",
    language="it",
    count=10
)

# 选择题测验 - 5 道题
result = learner.execute(
    action="quiz",
    language="es",
    count=5
)

# 句子练习
result = learner.execute(
    action="sentence",
    language="ja"
)

# 语法学习
result = learner.execute(
    action="grammar",
    language="ja"
)

# 复习已学单词
result = learner.execute(
    action="review",
    language="it",
    count=10
)

# 切换语言
result = learner.execute(
    action="set_language",
    language="ja"
)

# 语音合成
result = learner.execute(
    action="speak",
    language="ja",
    text="こんにちは"
)

# 查看学习统计
result = learner.execute(
    action="stats",
    language="it"
)

# 添加单词
result = learner.execute(
    action="kb_add_word",
    language="it",
    word="ciao",
    meaning="你好"
)

# 添加句子
result = learner.execute(
    action="kb_add_sentence",
    language="it",
    original="Come stai?",
    translation="你好吗？"
)

# 批量导入
result = learner.execute(
    action="kb_import_text",
    language="it",
    text="ciao:你好\ngrazie:谢谢"
)

# 导出知识库
result = learner.execute(
    action="kb_export",
    language="it",
    format="json"
)

# 标记已学习
result = learner.execute(
    action="mark_learned",
    language="it",
    word="ciao",
    type="word"
)
```

## 输出位置

|路径    |说明|
|------|------|
|skills/language_learner/knowledge/{lang}.json    |各语言知识库文件|
|skills/language_learner/progress.json    |学习进度|
|skills/language_learner/output/audio/    |语音合成文件|
|skills/language_learner/output/export/    |导出的知识库|

## 词典数据目录

| 路径 | 说明 |
|------|------|
| skills/language_learner/knowledge/nltk_data/ | NLTK WordNet/OMW 数据 |
| skills/language_learner/knowledge/jamdict_data/ | Jamdict 日语词典数据 |
| skills/language_learner/knowledge/chinese_data/ | CEDICT 中文词典数据 |

## 使用示例
```bash
python -m markflow.cli.commands execute language_learner action="list"

python -m markflow.cli.commands execute language_learner action="flashcard" language="it" count=10

python -m markflow.cli.commands execute language_learner action="speak" language="ja" text="こんにちは"

```