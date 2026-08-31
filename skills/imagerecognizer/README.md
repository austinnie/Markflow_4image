# ImageRecognizer

> ImageRecognizer 是一个基于 Ollama 多模态模型的图片识别技能。它可以识别图片中的物体、场景、人物、文字等内容，并支持将识别结果翻译成 14 种不同的语言。适用于图片内容分析、OCR 文字提取、多语言场景理解等任务。

## 描述

ImageRecognizer 是一个基于 Ollama 多模态模型的图片识别技能。它可以识别图片中的物体、场景、人物、文字等内容，并支持将识别结果翻译成 14 种不同的语言。适用于图片内容分析、OCR 文字提取、多语言场景理解等任务。

## 核心功能

1. **图片内容识别** - 识别图片中的物体、场景、人物、文字、颜色、氛围等
2. **多语言输出** - 支持 14 种语言的识别结果输出（中文、英文、日语、韩语、法语等）
3. **翻译功能** - 将识别结果翻译成指定的目标语言
4. **多级详细程度** - 支持简洁、标准、详细、标签、JSON 五种输出模式
5. **结果自动保存** - 识别结果自动保存为 JSON 和 TXT 文件

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `image_path` | string | 是 |  | 图片文件路径（支持 jpg/png/webp/gif/bmp） |
| `language` | string | 否 | zh | 输出语言代码（zh/en/ja/ko/fr/de/es/it/pt/ru/ar/th/vi/id/hi） |
| `detail_level` | string | 否 | standard | 详细程度（brief/standard/detailed/tags/json） |
| `translate_to` | string | 否 |  | 翻译目标语言代码 |
| `save_result` | boolean | 否 | true | 是否保存结果到文件 |

## 输出

| 字段 | 说明 |
|------|------|
| `recognition` | 图片识别结果文本 |
| `translated_result` | 翻译后的结果（如果指定了 translate_to） |
| `saved_to` | 结果文件保存路径（JSON 格式） |
| `image_name` | 图片文件名 |
| `executed_at` | 执行时间 |

## 使用方法

```bash
python -m markflow.cli.commands execute ImageRecognizer [参数]
```

## 依赖安装

```bash
pip install requests
pip install Ollama
```

---

*文档生成于 2026-08-31 22:27:54*