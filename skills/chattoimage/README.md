# ChatToImage

> 通过自然语言对话生成和编辑图片。支持文生图、换装、换背景、换表情、换发型、加配饰、风格转换等多种图片操作。支持多轮对话记忆上下文。

## 描述

通过自然语言对话生成和编辑图片。支持文生图、换装、换背景、换表情、换发型、加配饰、风格转换等多种图片操作。支持多轮对话记忆上下文。

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `message` | string | 是 |  | 用户的自然语言描述 |
| `image_path` | string | 否 |  | 输入图片路径（用于图生图操作） |
| `model` | string | 否 | qwen2.5:7b | LLM 模型名称 |
| `api_type` | string | 否 | ollama | LLM API 类型 (ollama/openai) |
| `api_base` | string | 否 | http://localhost:11434 | API 地址 |
| `api_key` | string | 否 |  | API Key（OpenAI 等需要） |
| `stream` | boolean | 否 | false | 是否流式输出 |

## 输出

| 字段 | 说明 |
|------|------|
| `response` | AI 的回复内容 |
| `image_paths` | 生成的图片路径列表 |
| `intent` | 识别到的意图类型 |
| `skill_used` | 实际调用的技能名称 |
| `params` | 传递给子技能的参数 |
| `conversation_id` | 会话 ID（用于多轮对话） |

## 使用方法

```bash
python -m markflow.cli.commands execute ChatToImage [参数]
```

## 依赖安装

```bash
pip install requests
pip install json
pip install logging
pip install pathlib
```

---

*文档生成于 2026-09-01 14:38:06*