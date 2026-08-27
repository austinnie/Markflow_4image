# sd_image_generator

> 使用本地 Stable Diffusion 模型生成图片的技能

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 8
- **函数数**: 1

## 技能描述

使用本地 Stable Diffusion 模型生成图片的技能

## 依赖

```bash
pip install diffusers
pip install torch
pip install transformers
pip install accelerate
pip install safetensors
pip install Pillow
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | string | `` | 图片描述提示词 (必填) |
| `negative_prompt` | string | `` | 负面提示词，描述不想出现的内容 (可选) |
| `model_name` | string | `` | 使用的模型文件名，默认 sd-v1-5-tiny.safetensors |
| `width` | integer | `` | 生成图片宽度，默认 512，范围 256-1024 |
| `height` | integer | `` | 生成图片高度，默认 512，范围 256-1024 |
| `steps` | integer | `` | 采样步数，默认 20，范围 10-50 |
| `cfg_scale` | float | `` | 提示词引导强度，默认 7.0，范围 1.0-20.0 |
| `seed` | integer | `` | 随机种子，-1表示随机，默认 -1 |
| `output_dir` | string | `` | 输出目录，默认 ./generated_images |
| `batch_size` | integer | `` | 一次生成数量，默认 1，范围 1-4 |
| `scheduler` | string | `` | 采样调度器，可选 ddim, pndm, lms, euler, euler_a, dpm |

## 输出

| 字段 | 说明 |
|------|------|
| `image_paths` | 生成的图片路径列表 |
| `parameters` | 使用的生成参数 |
| `model_used` | 使用的模型名称 |
| `generation_time` | 生成耗时 |
| `generated_at` | 生成时间 |

## 使用方法

```bash
python -m markflow.cli.commands execute sd_image_generator [参数]
```

### 示例

```bash
# 生成图片
python -m markflow.cli.commands execute sd_image_generator prompt="a beautiful sunset" model_name="sd-v1-5-tiny.safetensors"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info sd_image_generator
```

## 输出位置

生成的输出保存在 `skills/sd_image_generator/output/` 目录下。

---

*文档自动生成于 2026-08-23 17:13:23*