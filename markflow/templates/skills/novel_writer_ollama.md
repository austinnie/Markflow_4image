# novel_writer_ollama

> 使用本地 Ollama 大模型自动写小说

## 技能描述

根据大纲和设定，利用本地大模型自动生成小说章节

## 核心功能

1. 小说生成 - 根据大纲自动生成完整小说
2. 章节控制 - 支持自定义章节数量和每章字数
3. 风格选择 - 支持多种写作风格
4. 角色设定 - 支持自定义角色设定
5. 本地模型 - 使用本地 Ollama 模型，无需联网

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| genre | string | 是 | - | 小说类型 (科幻/奇幻/言情/悬疑/武侠/都市) |
| title | string | 是 | - | 小说标题 |
| outline | string | 是 | - | 故事大纲 |
| characters | string | 否 | - | 主要角色设定 |
| chapter_count | integer | 否 | 3 | 要生成的章节数量，范围 1-10 |
| words_per_chapter | integer | 否 | 500 | 每章目标字数，范围 200-2000 |
| style | string | 否 | 细腻 | 写作风格 (简洁/细腻/幽默/严肃) |
| temperature | float | 否 | 0.85 | 创意程度，范围 0-1 |
| model | string | 否 | qwen2.5:7b | 使用的模型 |
| ollama_url | string | 否 | http://localhost:11434 | Ollama 服务地址 |

## 输出

| 字段 | 说明 |
|------|------|
| title | 小说标题 |
| genre | 小说类型 |
| chapters | 所有章节列表 |
| summary | 小说简介 |
| total_words | 总字数 |
| model_used | 使用的模型名称 |
| generated_at | 生成时间 |

## 步骤

1. 验证输入参数
2. 检查 Ollama 服务是否可用
3. 构建小说生成系统提示词
4. 生成小说简介
5. 逐章生成小说内容
6. 整理和统计结果
7. 返回完整小说数据



## 依赖
- requests
- json

## 示例
```python
writer = NovelWriterOllama()
result = writer.execute(
    genre="科幻",
    title="星际行者",
    outline="一个普通少年意外获得星际航行能力，在宇宙中探索未知文明",
    characters="主角：阿星，16岁，好奇心强；AI助手：小智，幽默风趣",
    chapter_count=3,
    words_per_chapter=600,
    model="qwen2.5:7b"
)
print(f"生成了 {len(result['chapters'])} 章，共 {result['total_words']} 字")
for chapter in result['chapters']:
    print(f"第{chapter['index']}章: {chapter['title']}")
```	

## 使用示例
```bash
python -m markflow.cli.commands execute novel_writer_ollama genre="科幻" title="星际行者" outline="探索宇宙" chapter_count=3

python -m markflow.cli.commands execute novel_writer_ollama genre="武侠" title="江湖风云" outline="少年闯江湖" style="细腻"
```
