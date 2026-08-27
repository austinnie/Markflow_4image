# Markflow_4image - 图片处理专用版本

这是 MarkFlow 的图片处理专用分支/版本，专门用于图像生成、编辑和转换等任务。

## 🎯 版本说明

此版本保留了 MarkFlow 的所有图片处理技能，包括：

- `sd_image_generator` - SD 图像生成
- `fantasy_character` - 奇幻角色转换
- `style_transfer` - 风格迁移
- `anime_to_real` / `real_to_anime` - 动漫/真实转换
- `old_photo_restore` - 老照片修复
- `controlnet` - ControlNet 控制
- 以及 30+ 其他图片处理技能

## 📦 包含技能

### 基础生成
- `sd_image_generator` - Stable Diffusion 图像生成

### 角色编辑
- `add_animal_ears` - 添加动物耳朵
- `add_glasses` - 添加眼镜
- `add_tattoo` - 添加纹身
- `change_expression` - 改变表情
- `change_eye_color` - 改变眼睛颜色
- `change_hair` - 改变发型
- `change_makeup` - 改变妆容
- `change_skin_tone` - 改变肤色
- `remove_clothes` - 去除衣物

### 风格转换
- `anime_to_real` - 动漫转真人
- `real_to_anime` - 真人转动漫
- `sketch_to_real` - 素描转真实
- `style_transfer` - 风格迁移
- `colorize_sketch` - 素描上色

### 环境变换
- `change_background` - 更换背景
- `change_lighting` - 改变光照
- `change_perspective` - 改变视角
- `day_night_transfer` - 日夜转换
- `season_transfer` - 季节转换
- `weather_transfer` - 天气转换

### 身体特征
- `change_age` - 改变年龄
- `change_body_type` - 改变体型
- `change_clothes` - 更换衣物
- `change_clothing_style` - 更换服装风格
- `change_gender` - 改变性别
- `change_nationality` - 改变国籍

### 对象操作
- `add_background_objects` - 添加背景物体
- `change_furniture` - 更换家具
- `remove_object` - 移除物体
- `replace_object` - 替换物体

### 奇幻角色
- `fantasy_character` - 奇幻角色转换（精灵/天使/恶魔等）

### 修复增强
- `old_photo_restore` - 老照片修复
- `photo_restorer` - 照片修复
- `photo_realistic` - 照片真实感增强

### 控制网络
- `controlnet` - ControlNet 基础控制

## 🚀 快速开始

### 使用技能

```python
from markflow import MarkFlow

# 创建实例
flow = MarkFlow()

# 奇幻角色转换
result = flow.run(
    skill="fantasy_character",
    image_path="photo.jpg",
    fantasy_type="elf"
)

# 图像生成
result = flow.run(
    skill="sd_image_generator",
    prompt="beautiful landscape, sunset, 4k"
)

# 风格迁移
result = flow.run(
    skill="style_transfer",
    image_path="photo.jpg",
    style="anime"
)
```

##  命令行使用
```bash
# 奇幻角色转换
python scripts/run.py fantasy_character --image photo.jpg --type elf

# 图像生成
python scripts/run.py sd_image_generator --prompt "beautiful landscape"

# 风格迁移
python scripts/run.py style_transfer --image photo.jpg --style anime
```python

##  🔧 环境配置

###  依赖安装

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装 PyTorch (CUDA 版本)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 安装 diffusers 和相关库
pip install diffusers transformers accelerate
```

###  模型配置
将 SD 模型放在 models/ 目录下：


📂 目录结构

```text
Markflow_4image/
├── markflow/              # 核心模块
│   ├── __init__.py
│   ├── core.py
│   └── ...
├── skills/                # 所有技能 (含图片处理)
│   ├── fantasy_character/
│   ├── sd_image_generator/
│   ├── style_transfer/
│   └── ... (30+ skills)
├── scripts/               # 工具脚本
├── models/                # 模型文件
├── output/                # 输出目录
├── .gitignore
└── README.md
```

###  ⚠️ 注意事项

模型文件: 需要自行下载 SD 模型到 models/ 目录

GPU 内存: 建议至少 8GB VRAM

首次运行: 首次运行会下载相关依赖模型

###  📄 许可证
MIT

###  🔗 相关项目

MarkFlow - 原版 MarkFlow，包含更多通用技能

此版本是 MarkFlow 的图片处理专用分支

### 3. 修改 .gitignore (可选)

如果想在 Markflow_4image 中单独管理，可以保持 .gitignore 不变，或者添加一些图片处理相关的忽略：

```.gitignore
# Markflow_4image 专用忽略

# 模型文件 (通常较大，不提交)
models/
*.safetensors
*.ckpt
*.pth
*.pt

# 输出文件
output/
*.png
*.jpg
*.jpeg
*.meta.json

# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/
.venv/
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# 日志
logs/
*.log

```