# SDImageGenerator

## 描述
使用本地 Stable Diffusion 模型生成图片的技能

## 目的


## 输入
- **prompt**: 图片描述提示词 (必填)
- **negative_prompt**: 负面提示词，描述不想出现的内容 (可选)
- **model_name**: 使用的模型文件名，默认 sd-v1-5-tiny.safetensors
- **width**: 生成图片宽度，默认 512，范围 256-1024
- **height**: 生成图片高度，默认 512，范围 256-1024
- **steps**: 采样步数，默认 20，范围 10-50
- **cfg_scale**: 提示词引导强度，默认 7.0，范围 1.0-20.0
- **seed**: 随机种子，-1表示随机，默认 -1
- **output_dir**: 输出目录，默认 ./generated_images
- **batch_size**: 一次生成数量，默认 1，范围 1-4
- **scheduler**: 采样调度器，可选 ddim, pndm, lms, euler, euler_a, dpm

## 输出
- **image_paths**: 生成的图片路径列表
- **parameters**: 使用的生成参数
- **model_used**: 使用的模型名称
- **generation_time**: 生成耗时
- **generated_at**: 生成时间

## 步骤
无

## 依赖
- diffusers
- torch
- transformers
- accelerate
- safetensors
- Pillow

## 版本
1.0.0
