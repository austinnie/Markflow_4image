# ChatToImage

## 描述
通过自然语言对话生成和编辑图片。支持文生图、换装、换背景、换表情、换发型、加配饰、风格转换等多种图片操作。支持多轮对话记忆上下文。

## 目的
让用户通过对话式交互完成图片生成和编辑任务，无需手动填写参数。

## 输入
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| message | string | 是 | - | 用户的自然语言描述 |
| image_path | string | 否 | - | 输入图片路径（用于图生图操作） |
| model | string | 否 | qwen2.5:7b | LLM 模型名称 |
| api_type | string | 否 | ollama | LLM API 类型 (ollama/openai) |
| api_base | string | 否 | http://localhost:11434 | API 地址 |
| api_key | string | 否 | - | API Key（OpenAI 等需要） |
| stream | boolean | 否 | false | 是否流式输出 |

## 输出
| 字段 | 说明 |
|------|------|
| response | AI 的回复内容 |
| image_paths | 生成的图片路径列表 |
| intent | 识别到的意图类型 |
| skill_used | 实际调用的技能名称 |
| params | 传递给子技能的参数 |
| conversation_id | 会话 ID（用于多轮对话） |

## 步骤
1. 接收用户输入
2. 加载对话上下文
3. 使用 LLM 分析意图和提取参数
4. 根据意图调用对应的技能
5. 返回生成结果并更新上下文

## 依赖
- requests
- json
- logging
- pathlib

## 示例

### 基础用法
```python
skill = ChatToImage()
result = skill.execute(message="生成一张日落海滩风景")
print(result['image_paths'])
```

### 带图片的图生图
```bash
python -m markflow.cli.commands execute ChatToImage message="把这个人换成红裙子" image_path="./input/person.jpg"
```

### 多轮对话（使用相同的 conversation_id）
```bash
python -m markflow.cli.commands execute ChatToImage message="一个女孩在沙滩上" conversation_id="session_1"
python -m markflow.cli.commands execute ChatToImage message="给她换一件红裙子" conversation_id="session_1"
python -m markflow.cli.commands execute ChatToImage message="换成日落背景" conversation_id="session_1"
```

### 使用 OpenAI 模型
```bash
python -m markflow.cli.commands execute ChatToImage message="生成一张赛博朋克城市" api_type="openai" api_key="sk-xxx" model="gpt-4o"
```

### Python 调用
```python
from markflow.core.executor import SkillExecutor

executor = SkillExecutor()
result = executor.execute(
    "ChatToImage",
    message="生成一张美丽的女孩，穿白色连衣裙，在花园里"
)

# 多轮对话
result2 = executor.execute(
    "ChatToImage",
    message="给她加一副墨镜",
    image_path=result["image_paths"][0],
    conversation_id="my_session"
)
print(result2["image_paths"])
```




## 🚀 使用方法

### 1. 构建技能
```bash
python -m markflow.cli.commands build chat_to_image.md
```

### 2. 执行技能
```bash
# 文生图
python -m markflow.cli.commands execute ChatToImage message="生成一张日落海滩风景"

# 换装（需要图片）
python -m markflow.cli.commands execute ChatToImage message="换一件红裙子" image_path="./input/person.jpg"

# 多轮对话
python -m markflow.cli.commands execute ChatToImage message="一个女孩在樱花树下" conversation_id="session_1"
python -m markflow.cli.commands execute ChatToImage message="换成古装" conversation_id="session_1"
```

3. 使用不同 LLM
```bash
# 使用 OpenAI
python -m markflow.cli.commands execute ChatToImage message="生成一张星空" api_type="openai" api_key="sk-xxx" model="gpt-4o"

# 使用其他 Ollama 模型
python -m markflow.cli.commands execute ChatToImage message="生成一张星空" model="qwen2.5:14b"
```

## 📋 支持的意图与子技能映射

| 用户意图 | 目标 Skill | 示例 |
|---------|-----------|------|
| 文生图 | `sd_image_generator` | "生成一张日落" |
| 换装 | `change_clothes` | "换成红裙子" |
| 换背景 | `change_background` | "换成海滩背景" |
| 换表情 | `change_expression` | "让她笑起来" |
| 换发型/发色 | `change_hair` | "染成粉色头发" |
| 加眼镜 | `add_glasses` | "加一副圆框眼镜" |
| 加兽耳 | `add_animal_ears` | "加猫耳" |
| 风格转换 | `style_transfer` | "转成油画风格" |
| 二次元转写实 | `anime_to_real` | "转成写实风格" |
| 扩展为全身 | `expand_to_full_body` | "扩展为全身图" |

## 🔧 后续扩展
1. GUI 集成：可以在 markflow.gui 中添加对话式交互界面

2. 更多子技能：在 INTENT_MAP 中添加新意图映射

3. 更多 LLM 支持：在 _call_llm 中添加更多 API 类型

4. Function Calling：支持更复杂的工具调用
