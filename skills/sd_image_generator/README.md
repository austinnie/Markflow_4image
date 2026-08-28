# sd_image_generator

> 使用本地 Stable Diffusion 模型生成图片

**作者**: MarkFlow Team

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 8
- **函数数**: 1

## 支持的功能

| 功能 | 说明 |
|------|------|
| 🤖 AI 智能处理 | - |

## 依赖

```bash
pip install accelerate
pip install diffusers
pip install Pillow
pip install transformers
pip install torch
pip install safetensors
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | string | `` | 图片描述提示词 |
| `negative_prompt` | string | `` | 负面提示词 |
| `model_name` | string | `sd-v1-5-tiny.safetensors` | 使用的模型文件名 |
| `width` | integer | `512` | 生成图片宽度，范围 256-1024 |
| `height` | integer | `512` | 生成图片高度，范围 256-1024 |
| `steps` | integer | `20` | 采样步数，范围 10-50 |
| `cfg_scale` | float | `7.0` | 提示词引导强度，范围 1.0-20.0 |
| `seed` | integer | `-1` | 随机种子，-1 表示随机 |
| `output_dir` | string | `./generated_images` | 输出目录 |
| `batch_size` | integer | `1` | 一次生成数量，范围 1-4 |
| `scheduler` | string | `ddim` | 采样调度器 |

## 输出

| 字段 | 说明 |
|------|------|
| `image_paths` | 生成的图片路径列表 |
| `parameters` | 使用的生成参数 |
| `model_used` | 使用的模型名称 |
| `generation_time` | 生成耗时(秒) |
| `generated_at` | 生成时间 |

## 使用方法

```bash
python -m markflow.cli.commands execute sd_image_generator [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute sd_image_generator [参数]
```

## 输出位置

生成的输出保存在 `skills/sd_image_generator/output/` 目录下。

---

*文档自动生成于 2026-08-28 19:04:23*