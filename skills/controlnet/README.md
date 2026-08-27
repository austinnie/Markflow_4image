# ControlNet

> 提供姿态检测和 ControlNet 控制能力

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 6

## 技能描述

提供姿态检测和 ControlNet 生成能力，支持 OpenPose、Canny、Depth、HED、Lineart、Normal、MLSD 等多种 ControlNet 类型。

## 依赖

```bash
pip install diffusers
pip install controlnet-aux
pip install opencv-python-headless
pip install torch
pip install Pillow
pip install numpy
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