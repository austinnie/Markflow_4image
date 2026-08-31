# MechaGenerator

> 高端机甲少女/机器人生成器：支持文生图、图生图、本地分层提示词自由组合，以及自动识别参考图。

## 技能描述

MechaGenerator 是基于 MarkFlow 框架开发的高级图像生成技能。它深度整合了项目内的 `sd_image_generator`（底层大模型）、`controlnet_img2img`（姿态控制）以及 `markflow.utils.model_config`（全局模型配置管理）。

本技能最大的特色是**“分层提示词”**：你可以将本地 12 个风格提示词文件（`mecha_glow.py`、`mecha_blueprint.py` 等）直接放入技能目录。每次执行时，技能会从对应文件的 `subjects`、`styles`、`moods` 三个维度中随机提取并进行组合，实现“盲盒式”的高质量出图。

## 核心功能

1. **纯文生图 (txt2img)** - 通过提示词直接生成高精度机甲少女。
2. **图生图 (img2img)** - 结合 ControlNet 提取原图姿态，将真人/普通图片转换成赛博机械风格。
3. **分层提示词自动组合** - 自动读取技能目录下的 `.py` 风格文件，随机抽取并拼接提示词。
4. **自动识别参考图** - 在 `img2img` 模式下，如果没有传 `input_image`，会自动读取当前目录下第一张 `Gemini_Generated_Image*.png`。
5. **全局模型自适应** - 自动读取 `markflow/utils/model_config.py` 中用户配置的全局底模，无需在参数中重复指定。

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| mode | string | 是 | - | 生成模式：`txt2img` (文生图) 或 `img2img` (图生图) |
| prompt | string | 视模式 | - | 正面提示词。`txt2img` 必填，`img2img` 为增强提示词 |
| negative_prompt | string | 否 | 内建 | 负面提示词 |
| style | string | 否 | none | 对应本地风格文件名（如 `mecha_glow`、`mecha_girl`），不填则纯靠 prompt |
| input_image | string | 视模式 | 自动 | `img2img` 模式下的输入参考图路径，不填会抓取目录下第一张参考图 |
| width | integer | 否 | 768 | 生成图片宽度 |
| height | integer | 否 | 1024 | 生成图片高度 |
| steps | integer | 否 | 30 | 采样迭代步数 |
| cfg_scale | float | 否 | 7.5 | 提示词引导系数（越大越贴近提示词） |
| seed | integer | 否 | -1 | 随机种子（-1 表示随机生成） |
| model_name | string | 否 | 全局配置 | 底层模型名称。不填时自动读取全局配置 |
| controlnet_type | string | 否 | canny | `img2img` 模式下的 ControlNet 预处理器（`openpose`/`canny`/`depth` 等） |
| strength | float | 否 | 0.75 | `img2img` 模式下的重绘强度（0.0-1.0） |

## 输出

| 字段 | 说明 |
|------|------|
| status | 执行状态：success / error |
| result | 包含 `mode`、`image_paths`（图片路径）、`elapsed_time`（耗时）、`prompt_used`（最终使用提示词）等 |
| metadata | 技能名称、版本、执行时间戳 |

## 步骤

1. 解析输入参数与模式。
2. 如果指定了 `style`，自动调用 `_load_prompts_from_library()` 读取技能目录下的 `.py` 文件。
3. 从读取到的分层数据中分别随机抽取 `subjects`、`styles`、`moods` 并组合为完整提示词。
4. 根据模式执行：
   - `txt2img` 调用 `Sdimagegenerator` 主引擎。
   - `img2img` 调用 `ControlNetImg2Img` 提取姿态并生成。
5. 保存结果，返回生成路径和耗时。

## 依赖

- opencv-python
- numpy
- pillow
- (可选) 项目内自带的 `skills/sd_image_generator` 和 `skills/controlnet_img2img` 底层引擎。

## 示例

### 1. 纯文生图（盲盒模式）
直接让系统从本地风格文件中随机抽取提示词：
```bash
python -m markflow.cli.commands execute mecha_generator mode="txt2img" style="mecha_glow"
```
### 2. 纯文生图 + 自定义提示词叠加
在本地风格的基础上，加上你的专属词：
```bash
python -m markflow.cli.commands execute mecha_generator mode="txt2img" prompt="1girl, long white hair, detailed face" style="mecha_girl_warfare" width=1024 height=1536 steps=40
```

### 3. 图生图（自动识别参考图）
只要你的参考图命名为 Gemini_Generated_Image*.png 并放在 skills/mecha_generator/ 目录下，运行以下命令即可自动转换：

```bash
python -m markflow.cli.commands execute mecha_generator mode="img2img" prompt="convert to a white mecha android with glowing blue core" style="mecha_blueprint" controlnet_type="canny" strength=0.7
```

### 4. 图生图（手动指定参考图）
```bash
python -m markflow.cli.commands execute mecha_generator mode="img2img" input_image="input/girl.jpg" prompt="sci-fi android, mechanical joints" style="mecha_thunder_cyberpunk" controlnet_type="openpose" strength=0.65
```

### 5. 指定底层大模型
如果你知道具体底模的名字，可以直接指定，跳过全局配置：

```bash
python -m markflow.cli.commands execute mecha_generator mode="txt2img" prompt="beautiful android" model_name="prg_sdxl.safetensors" style="mecha_girl_doll_kit"
```


## 使用示例 (Python 调用)
```ython
from skills.mecha_generator.skill import Mechagenerator

skill = Mechagenerator()

# 文生图
result = skill.execute(mode="txt2img", style="mecha_glow", width=768, height=1024)

# 图生图
result = skill.execute(
    mode="img2img",
    input_image="skills/mecha_generator/Gemini_Generated_Image.png",
    style="mecha_blueprint",
    controlnet_type="canny"
)
print(result)
```

## 本地风格文件说明

在 `skills/mecha_generator/` 目录下，你可以放置任意 `.py` 文件。文件里定义了一个 `STYLE` 字典：

- `subjects`: 具体形象主体（如：不同的机甲少女站姿/动作）。
- `styles`: 风格变化（如：3D 白模、科幻蓝图、赛博朋克配色）。
- `moods`: 情绪/氛围（如：静谧、战斗准备、极简、霓虹）。

执行时，技能会从这三个维度中各抽取一句，组合成一个完整的提示词。

> 你的 12 个提示词文件（`mecha_glow.py`、`mecha_blueprint.py` 等）符合上述标准，可直接放置并调用。

## 常见问题

**Q: 为什么我运行 txt2img 报错找不到模型？**
A: 技能会自动读取全局配置的模型。请确保你已通过 `python scripts/generate_images.py --set 你的模型名` 设置了模型，或者在执行时手动传入 `model_name="你的模型名.safetensors"`。

**Q: 图生图时，控制台提示找不到 `input_image`？**
A: 请确保你的参考图被重命名为 `Gemini_Generated_Image.png`（或 `Gemini_Generated_Image_1.png` 等），并位于 `skills/mecha_generator/` 根目录下。

