# change_background

> 保持人物不变，替换图片背景，支持预设背景和自定义描述

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 16
- **函数数**: 3

## 技能描述

保持人物不变，替换图片背景，支持预设背景和自定义描述

## 依赖

```bash
pip install torch
pip install diffusers
pip install transformers
pip install accelerate
pip install Pillow
pip install opencv-python
pip install ultralytics
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | string | `` | 输入图片路径 |
| `preset` | string | `` | 预设背景名称: beach, forest, mountain, city, space, underwater, sakura, autumn, snow, desert, library, cafe, temple, sunset, aurora, waterfall, castle, cyberpunk, studio, gradient |
| `background_prompt` | string | `` | 自定义背景描述提示词 |
| `strength` | float | `0.7` | 重绘强度 (0.0-1.0) |
| `steps` | integer | `30` | 迭代步数 |
| `controlnet_type` | string | `depth` | ControlNet 类型 (depth/canny/hed/lineart) |
| `save_mask` | boolean | `False` | 是否保存遮罩 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 生成图片路径 |
| `parameters` | 使用的参数 |

## 使用方法

```bash
python -m markflow.cli.commands execute change_background [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute change_background image_path="your_image_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info change_background
```

## 输出位置

生成的输出保存在 `skills/change_background/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:47*