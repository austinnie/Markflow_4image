# HumanToRobot

> 将人物照片转换为机器人/机械风格。支持 OpenAI 滤镜重绘与本地 ControlNet AI 图生图。

## 技能描述

该技能利用 OpenCV 计算机视觉技术与 ControlNet 图生图引擎，将输入的人物照片快速转换为具有科幻感、机械感的机器人风格图像。默认使用轻量级的 OpenCV 赛博朋克滤镜进行快速处理；也可以开启 `ai_convert` 模式调用本地深度模型进行真正的“人变机器人”重绘，支持单张处理与目录批量处理。

## 核心功能

1. **赛博朋克滤镜模式** - 仅依赖 OpenCV 和 NumPy，无需显卡，几秒钟即可生成带有青色/洋红偏移、边缘高亮和电路纹理的机械感图片。
2. **AI 深度重绘模式** - 调用本地 ControlNet 引擎，基于原图姿态，重绘出具有真实金属光泽和机械结构的机器人图像。
3. **批量处理支持** - 自动检测输入路径是否为目录，若是则遍历所有常见图片格式，自动批量生成并保存到输出目录。
4. **多风格切换** - 支持 `cyberpunk_robot`（赛博朋克）、`mechanical`（机械）、`android`（仿生人）等多种重绘风格。

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| image_path | string | 是 | - | 输入图片路径或包含图片的目录（支持 jpg/png/bmp/webp） |
| output_path | string | 否 | - | 单张模式下的输出图片路径（必须为 .png） |
| ai_convert | boolean | 否 | False | 是否开启 ControlNet AI 重绘（开启需消耗大量显存，建议先关闭测试） |
| style | string | 否 | cyberpunk_robot | 机器人风格（cyberpunk_robot / mechanical / android） |
| save_result | boolean | 否 | True | 是否保存处理结果日志 |

## 输出

| 字段 | 说明 |
|------|------|
| status | 执行状态：success / error |
| result | 包含输出路径、风格、是否使用 AI 转换等信息的字典（批量模式下包含 items 列表） |
| metadata | 技能名称、版本、执行时间等元数据 |

## 步骤

1. 验证输入路径并加载默认配置。
2. 判断输入是否为目录：若为目录则提取所有有效格式图片，进入批量循环；否则直接处理单张。
3. 根据 `ai_convert` 参数决定处理方式：
   - 为 False 时，利用 OpenCV 提取边缘、进行颜色偏移、叠加网格纹理，生成机械滤镜图。
   - 为 True 时，调用本地 ControlNet 引擎，使用提取的姿态进行 AI 深度图生图。
4. 确保输出目录存在，保存结果为 PNG 格式。
5. 返回处理结果。

## 依赖

- opencv-python
- numpy
- pillow

## 示例

```python
from skills.human_to_robot.skill import HumanToRobot

# 初始化技能
skill = HumanToRobot()

# 快速滤镜处理
result = skill.execute(image_path="input/girl.jpg", ai_convert=False)

# 批量处理并启用 AI 重绘
batch_result = skill.execute(image_path="input/", ai_convert=True, style="mechanical")
print(batch_result)
```

## 使用示例

```bash
# 单张滤镜处理（快速、无显卡要求）
python -m markflow.cli.commands execute human_to_robot image_path="input/girl.jpg"

# 启用 AI 重绘（需配置好 ControlNet）
python -m markflow.cli.commands execute human_to_robot image_path="input/girl.jpg" ai_convert=True style="mechanical"

# 批量处理整个目录
python -m markflow.cli.commands execute human_to_robot image_path="input/" ai_convert=False
```