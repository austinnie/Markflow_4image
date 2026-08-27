# SDImageGenerator

## 描述
使用本地 Stable Diffusion 模型生成图片的技能

## 目的
利用 `E:/SD_OpenVINO/models` 目录下的模型文件，根据文本描述生成高质量图片

## 输入
- prompt: string: 图片描述提示词 (必填)
- negative_prompt: string: 负面提示词，描述不想出现的内容 (可选)
- model_name: string: 使用的模型文件名，默认 sd-v1-5-tiny.safetensors
- width: integer: 生成图片宽度，默认 512，范围 256-1024
- height: integer: 生成图片高度，默认 512，范围 256-1024
- steps: integer: 采样步数，默认 20，范围 10-50
- cfg_scale: float: 提示词引导强度，默认 7.0，范围 1.0-20.0
- seed: integer: 随机种子，-1表示随机，默认 -1
- output_dir: string: 输出目录，默认 ./generated_images
- batch_size: integer: 一次生成数量，默认 1，范围 1-4
- scheduler: string: 采样调度器，可选 ddim, pndm, lms, euler, euler_a, dpm

## 输出
- image_paths: 生成的图片路径列表
- parameters: 使用的生成参数
- model_used: 使用的模型名称
- generation_time: 生成耗时
- generated_at: 生成时间

## 步骤
1. 验证输入参数
2. 检查模型文件是否存在
3. 加载选定的模型
4. 设置随机种子
5. 执行图片生成
6. 保存生成的图片
7. 返回生成结果信息

## 依赖
- diffusers
- torch
- transformers
- accelerate
- safetensors
- Pillow

## 示例
```python
generator = SDImageGenerator()
result = generator.execute(
    prompt="a beautiful sunset over mountains, digital art",
    model_name="realisticmix_iiv12Version12.safetensors",
    width=768,
    height=512,
    steps=30,
    cfg_scale=7.5,
    batch_size=2
)
print(f"生成了 {len(result['image_paths'])} 张图片")
print(f"图片保存在: {result['image_paths']}")