# news_aggregator

> RSS 新闻抓取 + AI 摘要生成

## 技能描述

自动抓取 RSS 新闻源，使用 AI 生成智能摘要，支持多分类聚合和每日简报

## 核心功能

1. RSS 抓取 - 自动抓取多个 RSS 源
2. AI 摘要 - 使用 Ollama 生成智能摘要
3. 分类聚合 - 支持科技/财经/国际/中国/美国/日本/韩国分类
4. 每日简报 - 生成格式化的新闻简报
5. 来源去重 - 自动去重，减少重复内容

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| sources | string | 否 | - | RSS 源列表 |
| category | string | 否 | tech | 新闻分类 (tech/business/world/china/usa/japan/korea) |
| top_n | integer | 否 | 10 | 提取 Top N 条新闻 |
| summary_length | integer | 否 | 100 | 摘要长度 |

## 输出

| 字段 | 说明 |
|------|------|
| news | 新闻列表 |
| summaries | AI 摘要 |
| daily_report | 每日简报 |

## 步骤

1. 验证输入参数
2. 根据分类获取 RSS 源
3. 抓取 RSS 内容
4. 去重处理
5. 使用 AI 生成摘要
6. 生成每日简报
7. 返回结果

## 依赖

- feedparser
- requests
- ollama

## 示例

```python
aggregator = NewsAggregator()

# 抓取科技新闻
result = aggregator.execute(
    category="tech",
    top_n=5
)

# 抓取中国新闻
result = aggregator.execute(
    category="china",
    top_n=10
)
```

## 使用示例

```bash
python -m markflow.cli.commands execute news_aggregator category="tech" top_n=5

python -m markflow.cli.commands execute news_aggregator category="china" top_n=10

python -m markflow.cli.commands execute news_aggregator sources="TechCrunch,BBC"
```