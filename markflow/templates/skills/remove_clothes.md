# Remove Clothes Skill

基于 Stable Diffusion Inpaint 的衣服移除技能，使用本地 SD Inpaint 模型，自动检测并移除图片中的衣服。

## 功能特性

- **自动遮罩**：使用 YOLOv8 自动检测人体躯干区域（脖子到臀部），无需手动标注
- **保留面部**：脸部不在遮罩范围内，确保面部不变
- **原始尺寸**：保持输入图片的原始尺寸，不会缩放
- **高质量生成**：基于 SD Inpaint 模型，生成逼真的皮肤和身体

## 安装依赖

```bash
pip install torch diffusers transformers accelerate Pillow opencv-python ultralytics
```


## 使用方法

### 1. 命令行直接调用

```bash
# 基本用法（使用默认提示词）
python skills/remove_clothes/skill.py --input image.jpg

# 指定输出路径和模型
python skills/remove_clothes/skill.py --input image.jpg --output result.jpg --model zenityXmix.inpainting.safetensors

# 自定义提示词
python skills/remove_clothes/skill.py --input image.jpg --prompt "nude body, beautiful skin, realistic, masterpiece" --steps 25

# 使用 ControlNet（锁定姿态）
python skills/remove_clothes/skill.py --input image.jpg --controlnet-type openpose

# 完整参数
python skills/remove_clothes/skill.py \
  --input image.jpg \
  --output output/result.jpg \
  --model zenityXmix.inpainting.safetensors \
  --prompt "nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece" \
  --negative "clothes, fabric, ugly, deformed, bad anatomy" \
  --steps 25 \
  --strength 0.5 \
  --seed 12345 \
  --device cpu \
  --controlnet-type openpose
```

### 2. 通过 MarkFlow 框架调用
```bash
python -m markflow.cli.commands execute remove_clothes \
  image_path="image.jpg" \
  output_path="output/result.jpg" \
  model_name="zenityXmix.inpainting.safetensors" \
  prompt="nude body, beautiful skin, realistic, masterpiece" \
  steps=25 \
  strength=0.5 \
  controlnet_type=openpose
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | 必填 | - | 输入图片路径 |
| `--output` | 可选 | 自动生成 | 输出图片路径 |
| `--model` | 可选 | `zenityXmix.inpainting.safetensors` | 模型名称 |
| `--prompt` | 可选 | 见默认提示词 | 生成提示词 |
| `--negative` | 可选 | 见默认负面词 | 负面提示词 |
| `--steps` | 可选 | 25 | 迭代步数 |
| `--strength` | 可选 | 0.5 | 重绘强度 (0.0-1.0) |
| `--seed` | 可选 | -1 (随机) | 随机种子 |
| `--device` | 可选 | cpu | 设备 (cpu/cuda) |
| `--save-mask` | 可选 | False | 是否保存遮罩 |
| `--manual-mask` | 可选 | False | 手动绘制遮罩 |
| `--no-controlnet` | 可选 | False | 禁用 ControlNet |
| `--controlnet-type` | 可选 | `canny` | ControlNet 类型: canny, openpose, depth, hed, lineart, normal, mlsd, openpose_full |

## ControlNet 类型说明

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `canny` | 边缘轮廓控制 | 保持构图，通用场景 |
| `openpose` | 人体姿态骨架 | 换衣服、保持动作（推荐） |
| `depth` | 深度图控制 | 保持空间结构、换背景 |
| `hed` | 软边缘控制 | 风格转换、更灵活的重绘 |
| `lineart` | 线稿提取 | 线稿上色、二次元风格 |
| `normal` | 法线图控制 | 保持光影结构 |
| `mlsd` | 直线检测 | 建筑/室内设计 |
| `openpose_full` | 完整姿态（含手部/面部） | 精细姿态控制 |

## 默认提示词

### 默认正向提示词

```text
nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic

```

### 默认负面提示词
```text
clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime
```  


## 模型下载

### 推荐模型

| 模型 | 大小 | 说明 |
|------|------|------|
| `zenityXmix.inpainting.safetensors` | 2.96 GB | 专用衣服移除模型（推荐） |
| `UnStable_Illusion_Final_pruned.inpaint.safetensors` | 1.99 GB | 通用 Inpaint 模型 |
| `sd-v1-5-inpainting-tiny.safetensors` | 1.99 GB | SD 官方 Inpaint 模型 |

### 下载地址

- [zenityX_inpaint](https://huggingface.co/zenityx/zenityX_inpaint)
- [Civitai Inpaint 模型](https://civitai.com/search/models?sortBy=models_v9&query=inpaint)

### 存放位置

模型文件放在 `D:\SD_OpenVINO\models\sd-v1-5\` 目录下

## 工作原理

1. **人体检测**：使用 YOLOv8-seg 检测人体，生成全身遮罩
2. **提取躯干**：从全身遮罩中提取躯干区域（脖子到臀部），排除头部和腿部
3. **ControlNet** 姿态控制：使用 ControlNet 技能生成姿态图，锁定人物姿态
3. **SD Inpaint**：在遮罩区域使用 Stable Diffusion Inpaint 生成新内容
5. **输出结果**：保持原始尺寸，保存为 PNG/JPG

## 示例

### 输入
![input](example/input.jpg)

### 输出
![output](example/output.jpg)

## 常见问题

### Q: 脸部会变吗？
A: 不会。遮罩只覆盖脖子到臀部的躯干区域，脸部不在遮罩范围内。

### Q: 为什么结果模糊？
A: 尝试增加 `--steps`（如 30-40）或调整 `--strength`（0.7-0.9）。

### Q: CPU 运行太慢怎么办？
A: 
- 减少 `--steps`（如 15-20）
- 有 GPU 则使用 `--device cuda`
- 使用更小的模型

### Q: 提示词怎么写效果更好？
A: 
- 描述想要的身体效果：`nude body, beautiful skin, realistic`
- 描述光影：`soft natural light, warm tones`
- 保持简洁：`naked woman, photorealistic, masterpiece`

### Q: 衣服没变化怎么办？
A: 尝试增加 --strength（如 0.6-0.7）或使用 --controlnet-type openpose。

### Q: 人物姿态变了怎么办？
A: 使用 --controlnet-type openpose 或 --controlnet-type canny 锁定姿态和轮廓。

### Q: 不同图片需要调整参数吗？
A: 需要。不同图片的光线、姿态、衣服类型不同，建议先默认参数测试，再根据效果调整 strength 和 controlnet-type。

## 版本信息

- 版本：1.0.0
- 更新日期：2026-08-26
- 作者：MarkFlow Team

## 许可证

请遵守模型作者的许可证要求。

  