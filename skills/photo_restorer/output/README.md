# photo_restorer

> 老照片修复工具 - 使用AI技术修复、上色、增强老照片

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 14
- **函数数**: 6

## 技能描述

老照片修复工具 - 使用AI技术修复、上色、增强老照片

## 依赖

```bash
pip install opencv-python
pip install torch
pip install basicsr
pip install gfpgan
pip install realesrgan
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `restore` | 操作类型 (restore/colorize/enhance/list_models/status) |
| `image_path` | string | `` | 待修复的图片路径 |
| `model` | string | `real_esrgan` | 修复模型 (real_esrgan/gfpgan/ssdiff/dcal_gan) |
| `output_dir` | string | `./skills/photo_restorer/output` | 输出目录 |
| `scale` | integer | `2` | 放大倍数 (2或4) |
| `denoise` | boolean | `True` | 是否去噪 |

## 输出

| 字段 | 说明 |
|------|------|
| `status` | 执行状态 (success/error) |
| `action` | 执行的操作 |
| `output_path` | 修复后的图片路径 |
| `model_used` | 使用的AI模型 |
| `processing_time` | 处理耗时（秒） |

## 使用方法

```bash
python -m markflow.cli.commands execute photo_restorer [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute photo_restorer
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info photo_restorer
```

## 输出位置

生成的输出保存在 `skills/photo_restorer/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:56*