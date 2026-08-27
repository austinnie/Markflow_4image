# ControlNet

> 提供姿态检测和 ControlNet 控制能力，支持 10 种 ControlNet 类型，Pipeline 生图，批量处理

## 📋 版本信息

| 版本 | 更新内容 |
|------|----------|
| **v2.0.0** | 新增 Segmentation/Scribble 类型、Pipeline 生图、Gradio UI、批量处理 |
| v1.0.0 | 基础 ControlNet 检测功能 |

## 🎯 功能概览

| 功能 | 说明 |
|------|------|
| 🔍 **检测控制图** | 从图片提取 ControlNet 控制图（姿态/边缘/深度等） |
| ✨ **生成图片** | 一步到位：检测 + ControlNet + SD 生成 |
| 📦 **批量检测** | 批量处理多张图片，提取控制图 |
| 📦 **批量生成** | 批量生成图片 |
| 🖥️ **Gradio UI** | Web 图形界面，可视化操作 |
| 🔌 **Pipeline 缓存** | 自动缓存 Pipeline，重复使用无需重复加载 |

## 📦 支持的 ControlNet 类型

### 原有类型 (8 种)

| 类型 | 名称 | 说明 |
|------|------|------|
| `canny` | Canny (边缘) | 边缘轮廓控制，适合保持构图 |
| `hed` | HED (软边缘) | 软边缘检测，更灵活 |
| `lineart` | Lineart (线稿) | 线稿提取，适合二次元 |
| `depth` | Depth (深度) | 深度图控制，适合保持空间结构 |
| `normal` | Normal (法线) | 法线图控制，适合保持光影 |
| `mlsd` | MLSD (直线) | 直线检测，适合建筑 |
| `openpose` | OpenPose (姿态) | 人体姿态骨架，适合换装 |
| `openpose_full` | OpenPose Full (完整姿态) | 全身姿态 + 手指 + 面部表情 |

### 新增类型 (v2.0.0)

| 类型 | 名称 | 说明 |
|------|------|------|
| `seg` | Segmentation (语义分割) | 语义分割控制，适合换背景、场景转换 |
| `scribble` | Scribble (涂鸦) | 涂鸦控制，适合手绘控制 |

## 🚀 快速开始

### 依赖安装

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或单独安装
pip install diffusers controlnet-aux opencv-python-headless torch Pillow numpy gradio
```

##  ControlNet 模型
ControlNet 技能需要下载 ControlNet 模型，首次运行时会自动从 HuggingFace 下载。

### 自动下载（推荐）：

运行以下命令会自动下载模型：

```bash
# 查看状态（会自动检查并下载缺失的模型）
python -m markflow.cli.commands execute controlnet action=status

# 或直接检测姿态
python -m markflow.cli.commands execute controlnet action=detect_pose image="test.jpg"
```

### 手动下载：

如果自动下载失败，可以运行下载脚本：

```bash
# 直接下载
python scripts/download_controlnet.py

# 使用镜像加速（国内用户）
set HF_ENDPOINT=https://hf-mirror.com
python scripts/download_controlnet.py
```

### 模型列表

| 模型 | 大小 | 用途 |
|------|------|------|
| `lllyasviel/control_v11p_sd15_openpose` | ~1.5 GB | OpenPose 姿态检测 |
| `lllyasviel/sd-controlnet-canny` | ~1.5 GB | Canny 边缘检测 |
| `lllyasviel/sd-controlnet-depth` | ~1.5 GB | Depth 深度检测 |
| `lllyasviel/sd-controlnet-hed` | ~1.5 GB | HED 软边缘检测 |
| `lllyasviel/control_v11p_sd15_lineart` | ~1.5 GB | Lineart 线稿提取 |
| `lllyasviel/sd-controlnet-normal` | ~1.5 GB | Normal 法线检测 |
| `lllyasviel/sd-controlnet-mlsd` | ~1.5 GB | MLSD 直线检测 |

> **注**：首次运行 `detect_pose` 时会自动下载对应的 ControlNet 模型。


### 缓存位置：

模型默认下载到 HuggingFace 缓存目录：

```text
C:\Users\用户名\.cache\huggingface\hub\
```

或自定义缓存位置：

```bash
set HF_HOME=E:\hf_cache\.cache
python -m markflow.cli.commands execute controlnet action=detect_pose image="test.jpg"
```


## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `status` | 操作类型: status, list_types, detect_pose, load_pipeline |
| `image` | string | - | 输入图片路径 (detect_pose 操作) |
| `image_path` | string | - | 输入图片路径 (detect_pose 操作, 同 image) |
| `output_path` | string | - | 输出图片路径 (detect_pose 操作) |
| `model_path` | string | - | SD 模型路径 (load_pipeline 操作) |
| `controlnet_type` | string | `openpose` | ControlNet 类型: openpose, openpose_full, dwpose, canny, hed, lineart, depth, normal, mlsd |
| `device` | string | `cpu` | 设备: cpu 或 cuda |


## 输出

| 字段 | 说明 |
|------|------|
| `status` | 执行状态: success 或 error |
| `output_path` | 生成的 ControlNet 控制图路径 (detect_pose 操作) |
| `controlnet_type` | 使用的 ControlNet 类型 |
| `types` | 所有支持的 ControlNet 类型列表 (list_types 操作) |
| `dependencies` | 依赖检查状态 (status 操作) |


## 使用方法

### 方式一：通过 CLI 调用
```bash
python -m markflow.cli.commands execute controlnet [参数]
```

## 示例

```bash
# 查看状态
python -m markflow.cli.commands execute controlnet action=status

# 列出支持的 ControlNet 类型
python -m markflow.cli.commands execute controlnet action=list_types

# 检测姿态（生成控制图）
python -m markflow.cli.commands execute controlnet action=detect_pose image="test.jpg" output_path="pose.png"

# 使用不同 ControlNet 类型
python -m markflow.cli.commands execute controlnet action=detect_pose image="test.jpg" controlnet_type=canny output_path="canny.png"

# 加载 ControlNet Pipeline
python -m markflow.cli.commands execute controlnet action=load_pipeline model_path="E:/SD_OpenVINO/models/sd-v1-5/zenityXmix.inpainting.safetensors" controlnet_type=openpose
```

### 方式二：直接运行 skill.py

```bash
python skills/controlnet/skill.py [参数]
```

## 示例

```bash
# 查看状态
python skills/controlnet/skill.py --action status

# 检测姿态
python skills/controlnet/skill.py --action detect_pose --image test.jpg --output-path pose.png

# 使用不同 ControlNet 类型
python skills/controlnet/skill.py --action detect_pose --image test.jpg --controlnet-type canny --output-path canny.png

# 加载 ControlNet Pipeline
python skills/controlnet/skill.py --action load_pipeline --model-path "E:/SD_OpenVINO/models/sd-v1-5/zenityXmix.inpainting.safetensors" --controlnet-type openpose
```
## 输出位置

生成的输出保存在 skills/controlnet/output/ 目录下。


### 方式三：Gradio UI（推荐新手）

```bash
python skills/controlnet/skill.py --action gui --port 7860
或
python skills/controlnet/gradio_app.py
```

## 📖 命令示例

### 1. 查看状态

```bash
python skills/controlnet/skill.py --action status
```

### 2. 列出支持的 ControlNet 类型

```bash
python skills/controlnet/skill.py --action list_types
```

### 3. 检测控制图

```bash
# 使用 OpenPose 检测姿态
python skills/controlnet/skill.py --action detect_pose --image photo.jpg --controlnet-type openpose

# 使用 Canny 边缘检测
python skills/controlnet/skill.py --action detect_pose --image photo.jpg --controlnet-type canny --output-path canny.png

# 使用深度图检测
python skills/controlnet/skill.py --action detect_pose --image photo.jpg --controlnet-type depth
```

### 4. 生成图片（一步到位）⭐ 新增
```bash
# 基本用法
python skills/controlnet/skill.py --action generate \
    --image photo.jpg \
    --prompt "a beautiful girl, detailed face, masterpiece" \
    --model-path "E:/SD_OpenVINO/models/sd-v1-5/zenityXmix.inpainting.safetensors" \
    --controlnet-type openpose

# 指定参数
python skills/controlnet/skill.py --action generate \
    --image photo.jpg \
    --prompt "cyberpunk city, neon lights, futuristic" \
    --model-path "E:/SD_OpenVINO/models/sd-v1-5/xxx.safetensors" \
    --controlnet-type canny \
    --steps 30 \
    --cfg-scale 7.5 \
    --seed 42 \
    --output-path result.png
```

### 5. 批量检测 ⭐ 新增

```bash
# 批量检测多张图片
python skills/controlnet/skill.py --action batch_detect \
    --images "img1.jpg,img2.jpg,img3.jpg" \
    --controlnet-type openpose \
    --output-dir ./output/batch
```

### 6. 批量生成 ⭐ 新增

```bash
# 批量生成（提示词用 || 分隔）
python skills/controlnet/skill.py --action batch_generate \
    --images "img1.jpg,img2.jpg" \
    --prompts "a beautiful girl||a handsome man" \
    --model-path "E:/SD_OpenVINO/models/sd-v1-5/xxx.safetensors" \
    --controlnet-type openpose \
    --output-dir ./output/batch_gen
```

###  7. 启动 Gradio UI ⭐ 新增

```bash
# 默认端口 7860
python skills/controlnet/skill.py --action gui

# 指定端口和公开链接
python skills/controlnet/skill.py --action gui --port 8080 --share

# 使用独立脚本
python skills/controlnet/gradio_app.py
```

### 🔧 参数说明

#### 通用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--action` | string | `status` | 操作类型: status, list_types, detect_pose, load_pipeline, generate, batch_detect, batch_generate, gui |
| `--controlnet-type` | string | `openpose` | ControlNet 类型: openpose, openpose_full, canny, hed, depth, normal, mlsd, lineart, seg, scribble |
| `--device` | string | `cpu` | 设备: cpu 或 cuda |

#### detect_pose 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--image` | 路径 | - | 输入图片路径 |
| `--output-path` | 路径 | 自动生成 | 输出图片路径 |

#### generate 参数 ⭐ 新增

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--image` | 路径 | - | 输入图片路径（控制源） |
| `--prompt` | 字符串 | - | 生成提示词（必填） |
| `--model-path` | 路径 | - | SD 模型路径（必填） |
| `--negative-prompt` | 字符串 | `""` | 负面提示词 |
| `--steps` | 整数 | `20` | 推理步数 (10-50) |
| `--cfg-scale` | 浮点数 | `7.5` | CFG 尺度 (1.0-20.0) |
| `--seed` | 整数 | `-1` | 随机种子 (-1 随机) |
| `--controlnet-strength` | 浮点数 | `1.0` | ControlNet 控制强度 (0.0-1.0) |
| `--output-path` | 路径 | 自动生成 | 输出图片路径 |

#### batch_detect 参数 ⭐ 新增

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--images` | 字符串 | - | 图片路径列表，逗号分隔 |
| `--output-dir` | 路径 | 自动生成 | 输出目录 |

#### batch_generate 参数 ⭐ 新增

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--images` | 字符串 | - | 图片路径列表，逗号分隔 |
| `--prompts` | 字符串 | - | 提示词列表，用 `\|\|` 分隔 |
| `--model-path` | 路径 | - | SD 模型路径 |
| `--output-dir` | 路径 | 自动生成 | 输出目录 |

#### gui 参数 ⭐ 新增

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--port` | 整数 | `7860` | 服务端口 |
| `--share` | 标志 | `False` | 生成公开链接 |


### 📤 输出说明
#### detect_pose 输出

```json
{
  "status": "success",
  "output_path": "output/pose_openpose_20260828_120000.png",
  "controlnet_type": "openpose",
  "processing_time": "0.85s",
  "size": [512, 512],
  "timestamp": "2026-08-28T12:00:00"
}
```

#### generate 输出 ⭐ 新增

```json
{
  "status": "success",
  "output_path": "output/generated_openpose_20260828_120000.png",
  "control_path": "output/pose_openpose_20260828_115959.png",
  "controlnet_type": "openpose",
  "prompt": "a beautiful girl",
  "seed": 42,
  "processing_time": "8.50s",
  "timestamp": "2026-08-28T12:00:00"
}
```

#### batch_detect 输出 ⭐ 新增

```json
{
  "status": "success",
  "total": 10,
  "success": 8,
  "failed": 2,
  "output_dir": "output/batch",
  "processing_time": "12.30s",
  "timestamp": "2026-08-28T12:00:00"
}
```


### 📂 目录结构

```text
skills/controlnet/
├── skill.py                   # ⭐ 核心实现 (v2.0.0)
├── gradio_app.py              # ⭐ 新增 Gradio UI 独立启动
├── test_controlnet.py         # 测试脚本
├── download_controlnet.py     # 模型下载
├── README.md                  # 本文档
├── skill.md                   # 技能描述
├── meta.json                  # 技能元数据
├── requirements.txt           # 依赖列表
├── install.sh / install.bat   # 安装脚本
├── generate_snapshot.py       # 代码快照工具
├── output/                    # 输出目录
│   ├── *.png                  # 控制图/生成图
│   ├── batch/                 # 批量检测输出
│   └── batch_generated/       # 批量生成输出
└── cache/                     # 模型缓存
```

## 🔄 配合其他技能使用

| 配合技能 | 效果 |
|----------|------|
| `sd_image_generator` | 从零生成图片 |
| `remove_clothes` | 换衣服（锁定姿态） |
| `photo_restorer` | 修复老照片 |
| `fantasy_character` | 奇幻角色转换（保持姿态） |
| `style_transfer` | 风格迁移（保持构图） |

## 🖥️ Gradio UI 界面

启动后访问 `http://127.0.0.1:7860`

### 功能标签

| 标签 | 功能 |
|------|------|
| **🔍 检测控制图** | 上传图片 → 选择类型 → 提取控制图 |
| **✨ 生成图片** | 上传图片 → 输入提示词 → 生成图片 |
| **📋 帮助** | 使用说明和示例 |

### UI 界面预览

```text
┌─────────────────────────────────────────────────────────────────┐
│                    🎨 ControlNet 技能                          │
│              基于 ControlNet 的图片控制与生成                   │
├─────────────────────────────────────────────────────────────────┤
│  [🔍 检测控制图]  [✨ 生成图片]  [📋 帮助]                    │
├─────────────────────────────────────────────────────────────────┤
│  上传图片: [📁 选择文件]   ControlNet 类型: [openpose ▼]     │
│  最大尺寸: [==========o=========] 512                         │
│  [🚀 提取控制图]                                              │
├─────────────────────────────────────────────────────────────────┤
│  控制图:                                                       │
│  [ 图片预览区域 ]                                              │
├─────────────────────────────────────────────────────────────────┤
│  状态: ✅ 成功！耗时: 0.85s                                   │
└─────────────────────────────────────────────────────────────────┘
```

## ⚠️ 注意事项

| 事项 | 说明 |
|------|------|
| **模型路径** | 使用 `generate` 前需要指定有效的 SD 模型路径 |
| **GPU 内存** | 建议至少 8GB VRAM（使用 GPU 时） |
| **首次运行** | 会自动从 HuggingFace 下载 ControlNet 模型（约 1.5GB） |
| **缓存位置** | 模型缓存默认在 `cache/` 目录 |
| **批量处理** | 建议单次不超过 50 张图片，避免 GPU 过载 |

	
## ControlNet 控制能力

ControlNet 的作用是：**在保持原图某些特征（姿态、轮廓、深度等）不变的前提下，用 AI 重绘图片内容。**

### ControlNet 类型说明

| 类型 | 锁定的内容 | 应用场景 |
|------|-----------|----------|
| `openpose` | 人体姿态骨架 | 换衣服、换装、保持动作不变 |
| `canny` | 边缘轮廓 | 保持构图、换风格 |
| `depth` | 空间深度结构 | 换背景、保持场景布局 |
| `hed` | 软边缘 | 风格转换、更灵活的重绘 |
| `lineart` | 线稿 | 线稿上色、二次元风格转换 |
| `normal` | 法线图 | 保持光影结构 |
| `mlsd` | 直线 | 建筑/室内设计风格转换 |
| `openpose_full` | 完整姿态（含手部/面部） | 精细姿态控制 |

### 实际应用场景

#### 1. 换衣服
- **输入**：有人物的照片
- **操作**：用 `openpose` 锁定姿态，用 Inpaint 遮罩衣服区域
- **输出**：同一个人，同样的姿势，衣服被替换

#### 2. 风格转换
- **输入**：一张照片
- **操作**：用 `canny` 或 `hed` 锁定轮廓，改变提示词
- **输出**：同一构图，变成油画/水彩/动漫风格

#### 3. 换背景
- **输入**：一张人像
- **操作**：用 `depth` 锁定深度结构，改变背景描述
- **输出**：同一个人，姿态不变，背景完全改变

#### 4. 线稿上色
- **输入**：一张线稿
- **操作**：用 `lineart` 锁定线稿，添加颜色提示词
- **输出**：上色后的完整图片

#### 5. 图片修复/扩展
- **输入**：破损或裁剪过的图片
- **操作**：用 `canny` 锁定现有边缘，用 Inpaint 填充缺失部分
- **输出**：修复后的完整图片

#### 6. 保持姿态的角色生成
- **输入**：一张参考姿势图
- **操作**：用 `openpose` 提取姿态，改变人物描述
- **输出**：不同角色、相同姿势

#### 7. 建筑/室内设计
- **输入**：建筑或室内照片
- **操作**：用 `mlsd` 锁定直线结构
- **输出**：保持建筑结构，改变材质/风格

### 命令示例

```bash
# 1. 换衣服（锁定姿态）
python -m markflow.cli.commands execute remove_clothes image_path="person.jpg" controlnet_type=openpose

# 2. 风格转换（锁定边缘）
python -m markflow.cli.commands execute controlnet action=detect_pose image="photo.jpg" controlnet_type=canny

# 3. 换背景（锁定深度）
python -m markflow.cli.commands execute controlnet action=detect_pose image="photo.jpg" controlnet_type=depth

# 4. 线稿上色
python -m markflow.cli.commands execute controlnet action=detect_pose image="sketch.jpg" controlnet_type=lineart
```

### 与其他技能配合

| 配合技能 | 效果 |
|----------|------|
| `sd_image_generator` | 从零生成图片 |
| `remove_clothes` | 换衣服 |
| `photo_restorer` | 修复老照片 |
| 自建技能 | 根据需求定制 |

### ControlNet 能力总结

| 能力 | 说明 |
|------|------|
| 锁定姿态 | 保持人物动作不变 |
| 锁定轮廓 | 保持构图不变 |
| 锁定深度 | 保持空间结构不变 |
| 锁定线稿 | 保持线条不变 |
| 保持光影 | 保持光照结构不变 |
| 任意组合 | 8 种类型，按需选择 |

## 🔗 相关项目

| 项目 | 说明 |
|------|------|
| [MarkFlow](https://github.com/austinnie/Markflow) | 原版 MarkFlow，包含更多通用技能 |
| [ControlNet 官方](https://github.com/lllyasviel/ControlNet) | ControlNet 官方完整实现 |
| [controlnet-aux](https://github.com/huggingface/controlnet_aux) | ControlNet 辅助检测器库 |
| [diffusers](https://github.com/huggingface/diffusers) | HuggingFace 扩散模型库 |