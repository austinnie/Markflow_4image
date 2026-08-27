# NewsAggregator

## 描述
RSS 新闻抓取 + AI 摘要生成

## 输入
- sources: string: RSS 源列表 (可选)
- category: string: 新闻分类 (tech/business/world) (可选)
- top_n: integer: 提取 Top N 条新闻 (可选)
- summary_length: integer: 摘要长度 (可选)

## 输出
- news: 新闻列表
- summaries: AI 摘要
- daily_report: 每日简报

## 依赖
- feedparser
- requests
- ollama

## 状态
待实现