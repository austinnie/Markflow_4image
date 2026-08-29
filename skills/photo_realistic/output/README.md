# photo_realistic

> 让 AI 图片看起来像真实相机照片，所有功能默认关闭

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 10
- **函数数**: 4

## 技能描述

让 AI 图片看起来像真实相机照片，所有功能默认关闭

## 依赖

```bash
pip install Pillow
pip install opencv-python
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | string | `` | 输入图片路径 |
| `enable_noise` | boolean | `False` | 添加噪点 |
| `enable_vignette` | boolean | `False` | 添加暗角 |
| `enable_sharpen` | boolean | `False` | 锐化 |
| `enable_exif` | boolean | `False` | 注入 EXIF |
| `camera` | string | `sony_a7iv` | 相机预设 |
| `style` | string | `portrait` | 照片风格 |
| `strength` | string | `medium` | 强度 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 输出图片路径 |
| `applied` | 已应用的功能列表 |

## 使用方法

```bash
python -m markflow.cli.commands execute photo_realistic [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute photo_realistic image_path="your_image_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info photo_realistic
```

## 输出位置

生成的输出保存在 `skills/photo_realistic/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:56*