# change_clothes

> 将人物衣服替换为指定款式

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 17
- **函数数**: 3

## 技能描述

将人物衣服替换为指定款式

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
| `prompt` | string | `wearing a beautiful dress, elegant, fashionable, high quality, detailed, masterpiece` | 服装描述，如: wearing a red dress, elegant |
| `strength` | float | `0.6` | 重绘强度 (0.0-1.0) |
| `controlnet_type` | string | `openpose` | ControlNet 类型 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 生成图片路径 |
| `parameters` | 使用的参数 |

## 使用方法

```bash
python -m markflow.cli.commands execute change_clothes [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute change_clothes image_path="your_image_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info change_clothes
```

## 输出位置

生成的输出保存在 `skills/change_clothes/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:48*