# novel_writer_ollama

## 描述
使用本地 Ollama 大模型自动写小说

## 目的
根据大纲和设定，利用本地大模型自动生成小说章节

## 输入
- genre: string: 小说类型 (科幻/奇幻/言情/悬疑/武侠/都市)
- title: string: 小说标题
- outline: string: 故事大纲，描述主要情节
- characters: string: 主要角色设定
- chapter_count: integer: 要生成的章节数量，默认 3，范围 1-10
- words_per_chapter: integer: 每章目标字数，默认 500，范围 200-2000
- style: string: 写作风格 (简洁/细腻/幽默/严肃)，默认 细腻
- temperature: float: 创意程度 0-1，默认 0.85
- model: string: 使用的模型，默认 qwen2.5:7b
- ollama_url: string: Ollama 服务地址，默认 http://localhost:11434

## 输出
- title: 小说标题
- genre: 小说类型
- chapters: 所有章节列表，每章包含标题和内容
- summary: 小说简介
- total_words: 总字数
- model_used: 使用的模型名称
- generated_at: 生成时间

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