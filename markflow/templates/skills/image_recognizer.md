# ImageRecognizer

> 使用 Ollama 多模态模型识别图片内容，支持多语言翻译

## 技能描述

ImageRecognizer 是一个基于 Ollama 多模态模型的图片识别技能。它可以识别图片中的物体、场景、人物、文字等内容，并支持将识别结果翻译成 14 种不同的语言。适用于图片内容分析、OCR 文字提取、多语言场景理解等任务。

## 核心功能

1. **图片内容识别** - 识别图片中的物体、场景、人物、文字、颜色、氛围等
2. **多语言输出** - 支持 14 种语言的识别结果输出（中文、英文、日语、韩语、法语等）
3. **翻译功能** - 将识别结果翻译成指定的目标语言
4. **多级详细程度** - 支持简洁、标准、详细、标签、JSON 五种输出模式
5. **结果自动保存** - 识别结果自动保存为 JSON 和 TXT 文件

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| image_path | string | 是 | - | 图片文件路径（支持 jpg/png/webp/gif/bmp） |
| language | string | 否 | zh | 输出语言代码（zh/en/ja/ko/fr/de/es/it/pt/ru/ar/th/vi/id/hi） |
| detail_level | string | 否 | standard | 详细程度（brief/standard/detailed/tags/json） |
| translate_to | string | 否 | - | 翻译目标语言代码 |
| save_result | boolean | 否 | true | 是否保存结果到文件 |

### 语言代码说明

| 代码 | 语言 |
|------|------|
| zh | 中文 |
| en | English |
| ja | 日本語 |
| ko | 한국어 |
| fr | Français |
| de | Deutsch |
| es | Español |
| it | Italiano |
| pt | Português |
| ru | Русский |
| ar | العربية |
| th | ภาษาไทย |
| vi | Tiếng Việt |
| id | Bahasa Indonesia |
| hi | हिन्दी |

### 详细程度说明

| 级别 | 说明 |
|------|------|
| brief | 简洁描述（50字以内） |
| standard | 标准详细描述（默认） |
| detailed | 非常详细的分析（构图、光影、色彩等） |
| tags | 生成 5-10 个标签关键词 |
| json | JSON 格式输出结构化数据 |

## 输出

| 字段 | 说明 |
|------|------|
| recognition | 图片识别结果文本 |
| translated_result | 翻译后的结果（如果指定了 translate_to） |
| saved_to | 结果文件保存路径（JSON 格式） |
| image_name | 图片文件名 |
| executed_at | 执行时间 |

## 步骤

1. 验证输入参数（图片路径是否存在、格式是否支持）
2. 将图片编码为 Base64 格式
3. 根据语言和详细程度构建提示词
4. 调用 Ollama 多模态模型进行识别
5. 如指定翻译，调用 Ollama 进行翻译
6. 保存结果到文件（JSON 和 TXT 格式）
7. 返回识别结果

## 依赖

- requests
- Ollama（需安装多模态模型）

### Ollama 模型要求

需要安装支持视觉的多模态模型，推荐：

```bash
ollama pull qwen2.5-vl:7b   # 推荐
ollama pull qwen2.5-vl:3b   # 轻量版
ollama pull llava:7b        # 备选
```

## 示例

### Python 调用

```python
skill = ImageRecognizer()
result = skill.execute(
    image_path="./photo.jpg",
    language="zh",
    detail_level="detailed",
    translate_to="en"
)
print(result["result"]["recognition"])
```

### 命令行调用
```bash
# 基础识别（中文）
python -m markflow.cli.commands execute image_recognizer image_path="./photo.jpg"

# 英文输出
python -m markflow.cli.commands execute image_recognizer image_path="./photo.jpg" language="en"

# 详细分析并翻译成日语
python -m markflow.cli.commands execute image_recognizer image_path="./photo.jpg" detail_level="detailed" translate_to="ja"

# 只生成标签
python -m markflow.cli.commands execute image_recognizer image_path="./photo.jpg" detail_level="tags"

# 生成 JSON 格式输出
python -m markflow.cli.commands execute image_recognizer image_path="./photo.jpg" detail_level="json"
```

## 使用场景

- 📷 **照片内容分析** - 识别旅行照片中的景点、人物、食物等
- 🖼️ **艺术画作解读** - 分析画作的风格、构图、色彩和主题
- 📄 **截图文字提取** - 从截图或扫描件中提取文字信息
- 🌍 **多语言图片理解** - 用不同语言描述同一张图片
- 🏷️ **图片自动打标签** - 为图片生成关键词标签，便于分类管理
- 📊 **图片数据批量处理** - 批量识别多张图片内容，生成结构化数据

## 注意事项

- ⚠️ 需要 **Ollama 服务** 正在运行：`ollama serve`
- ⚠️ 需要安装**多模态模型**：`ollama pull qwen2.5-vl:7b`
- ⚠️ **首次调用**可能需要较长时间加载模型（约 30-60 秒）
- ⚠️ **大图片**建议压缩后再识别，以提高响应速度
- ⚠️ 确保图片格式为支持格式（jpg/png/webp/gif/bmp）



### 🚀 使用方式

将这个文件保存为 `image_recognizer.md`，然后运行：

```bash
python -m markflow.cli.commands build image_recognizer.md
```
MarkFlow 会自动解析这个 Markdown 文件，生成完整的 skill.py 代码，并保存到 skills/image_recognizer/ 目录下。

### 预期生成的文件结构
```text
skills/image_recognizer/
├── skill.py          # 自动生成的代码
├── meta.json         # 自动生成的元数据
├── skill.md          # 技能文档
├── README.md         # 自动生成的 README
├── requirements.txt  # 依赖列表
├── output/           # 输出目录
└── tests/
    └── test_skill.py # 自动生成的测试
```
	
你可以直接使用 MarkFlow 的 build 命令一键生成所有文件，非常方便！

## 验证技能
构建完成后，列出所有技能确认是否成功加载：

```bash
python -m markflow.cli.commands list
```

应该能看到 image_recognizer 在列表中。

### 测试运行
找一个本地图片测试：

```bash
python -m markflow.cli.commands execute image_recognizer image_path="D:/test.jpg"
```

### 可能遇到的问题

1.  Ollama 未运行：确保 ollama serve 在后台运行
2. 模型未安装：运行 ollama pull qwen2.5-vl:7b
3. 图片路径错误：使用绝对路径，如 D:/photos/test.jpg