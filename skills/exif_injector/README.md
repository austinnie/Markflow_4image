# exif_injector

> 为图片添加相机 EXIF 元数据，让 AI 图片更像真实照片

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 8
- **函数数**: 3

## 技能描述

为图片添加相机 EXIF 元数据，让 AI 图片更像真实照片

## 依赖

```bash
pip install Pillow
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | string | `` | 输入图片路径 |
| `camera` | string | `sony_a7iv` | 相机预设 |
| `style` | string | `portrait` | 照片风格 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 输出图片路径 |
| `exif_params` | 注入的 EXIF 参数 |

## 使用方法

```bash
python -m markflow.cli.commands execute exif_injector [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute exif_injector image_path="your_image_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info exif_injector
```

## 输出位置

生成的输出保存在 `skills/exif_injector/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:54*