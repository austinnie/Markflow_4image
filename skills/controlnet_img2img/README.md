# ControlNet Img2Img 技能（方案1：通用底层引擎）

> 利用 `controlnet_aux` 精准提取线稿/边缘/深度等预处理图，再结合底层 `ControlNet` 模型进行高度保真的图生图二次重绘。这是整个项目实现“结构保持”的通用核心底座。

## ✨ 功能特性

- **精准控制**：通过提取图像的 **HED（软边缘）、Canny（硬边缘）、MLSD（直线）、OpenPose（姿态）** 等特征，让重绘完全遵循原图的构图、线条和人物姿态。
- **单文件底模兼容**：完美支持从 `WebUI/ComfyUI` 下载的 `.safetensors` 或 `.ckpt` 单文件底模加载（`from_single_file`），无需强制转换目录。
- **本地离线运行**：自动对接本地 `hf_cache` 和 `models/controlnet` 目录，无需额外联网下载大模型。
- **参数灵活**：可动态调整 `strength`（重绘幅度）和 `controlnet_conditioning_scale`（控制网权重），兼顾细节还原与创意发挥。

---

## 📦 前置依赖

### 1. 核心 Python 依赖
```bash
pip install diffusers transformers accelerate controlnet-aux safetensors
```

### 2. 本地模型目录要求

| 资源 | 路径说明 |
| :--- | :--- |
| **预处理模型 (controlnet_aux)** | 存放于 `E:\SD_OpenVINO\hf_cache\.cache\controlnet_aux` (包含 `ControlNetHED.pth`, `mlsd_large_512_fp32.pth` 等) |
| **ControlNet 基础模型** | 存放于 `E:\SD_OpenVINO\models\controlnet` (如 `models--lllyasviel--sd-controlnet-canny` 等) |
| **SD 底模** | 存放于 `E:\SD_OpenVINO\models\sd-v1-5\` (如 `aiiiiii01_v10.safetensors` 单文件) |

> **注意**：请确保在 `markflow/utils/controlnet_config.py` 中已正确配置上述路径。


## 🚀 使用方法
该技能遵循标准的 Markflow 执行机制，可以通过命令行或 GUI 调用。
1. 命令行直接调用
```bash

python -m markflow.cli.commands execute controlnet_img2img \
    input_image_path="path/to/your/image.jpg" \
    prompt="a beautiful realistic portrait, masterpiece" \
    negative_prompt="lowres, bad anatomy, blurry" \
    preprocessor_type="HED" \
    controlnet_model="canny" \
    strength=0.7 \
    output_path="./output/controlnet_result.png"
```

## 📋 参数说明

### 必填参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `input_image_path` | string | 输入图片路径 |
| `prompt` | string | 正向提示词 |

### 常用可选参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `negative_prompt` | string | "" | 负面提示词 |
| `controlnet_type` | string | canny | canny/openpose/depth/hed/mlsd/lineart |
| `strength` | float | 0.6 | 重绘强度 (0.0-1.0) |
| `steps` | integer | 25 | 迭代步数 |
| `cfg_scale` | float | 7.0 | 引导强度 |
| `seed` | integer | -1 | 随机种子 |
| `output_path` | string | 自动生成 | 输出路径 |
| `width` | integer | 原图尺寸 | 输出宽度 |
| `height` | integer | 原图尺寸 | 输出高度 |
| `scheduler` | string | DDIM | DDIM/DPM/UniPC/Euler |
| `model_name` | string | 默认 | 底模名称 |
| `preset` | string | - | 预设模板 (beach/forest/city/...) |

### 高级参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `controlnet_strength` | float | 1.0 | ControlNet 权重 |
| `controlnet_guidance_start` | float | 0.0 | 起始步数比例 |
| `controlnet_guidance_end` | float | 1.0 | 结束步数比例 |
| `resize_mode` | string | crop | crop/fit/stretch |
| `batch_size` | integer | 1 | 批次大小 |
| `save_mask` | boolean | false | 保存遮罩 |
| `lora_weights` | json | {} | LoRA 配置 |


## 🧠 底层逻辑说明

1. **预处理 (`_preprocess`)**：读取原图，使用 `controlnet_aux` 库提取特征图（如线稿图、姿态图）。
2. **模型加载 (`_load_base_pipeline`)**：使用 `diffusers` 库加载底模（自动识别单文件/文件夹）和 ControlNet 模型。
3. **推理 (`execute`)**：将原图和控制图同时输入 `StableDiffusionControlNetImg2ImgPipeline`，结合 `strength` 和 `controlnet_conditioning_scale` 进行最终生成。



## 🧩 扩展与集成

- **作为底层引擎接入批量脚本**：可在 `scripts/generate_images.py` 中通过传入 `input_image` 触发，实现批量图生图。
- **作为上游工具接驳高级 Skills**：可为 `change_clothes`, `add_glasses` 等 39 个技能提供“强制保形”的底层能力。



## ⚠️ 常见问题 (FAQ)

| 问题 | 解决方案 |
| :--- | :--- |
| **Q: 运行时提示 `float16 cannot run with cpu`？** | **A:** 如果未启用 NVIDIA 显卡或 CUDA，请将 `skill.py` 中的 `torch_dtype=torch.float16` 修改为 `torch_dtype=torch.float32`。 |
| **Q: 提取线稿时报错 `Repo id must use alphanumeric chars...`？** | **A:** 请确保 `skill.py` 中调用 `controlnet_aux` 时传入的是标准 HF ID (如 `"lllyasviel/Annotators"`)，而不是本地绝对路径。 |
| **Q: 模型加载时提示缺少 `config.json`？** | **A:** 请确认 `models/controlnet` 下的模型目录是完整的 HF 缓存结构（包含 `snapshots` 文件夹）。如果是自行下载的权重，请使用 `diffusers` 转存为标准目录结构。 |