# Markflow_4image - 图片处理专用版本

这是 MarkFlow 的图片处理专用分支，专门用于图像生成、编辑和转换等任务。

## 🎯 版本说明

此版本包含了 MarkFlow 的所有图片处理技能，共 **38** 个：

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
- `add_background_objects` - 添加背景物体
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

### 元数据处理
- `exif_injector` - 注入 EXIF 信息
- `meta_cleaner` - 清除图片元数据

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
# 列出所有可用技能
python -m markflow.cli.commands list

# 查看技能详情
python -m markflow.cli.commands info fantasy_character

# 奇幻角色转换
python -m markflow.cli.commands execute fantasy_character image_path="photo.jpg" fantasy_type="elf"

# 图像生成
python -m markflow.cli.commands execute sd_image_generator prompt="beautiful landscape" negative_prompt="ugly, blurry"

# 风格迁移
python -m markflow.cli.commands execute style_transfer image_path="photo.jpg" style="anime"

# 动漫转真人
python -m markflow.cli.commands execute anime_to_real image_path="anime.jpg"

# 真人转动漫
python -m markflow.cli.commands execute real_to_anime image_path="photo.jpg"

# 老照片修复
python -m markflow.cli.commands execute old_photo_restore image_path="old_photo.jpg"

# 更换背景
python -m markflow.cli.commands execute change_background image_path="photo.jpg" background="beach"

# 换脸
python -m markflow.cli.commands execute change_face source_image="person.jpg" target_image="photo.jpg"

# 日夜转换
python -m markflow.cli.commands execute day_night_transfer image_path="photo.jpg" target="night"

# 季节转换
python -m markflow.cli.commands execute season_transfer image_path="photo.jpg" season="winter"

# 天气转换
python -m markflow.cli.commands execute weather_transfer image_path="photo.jpg" weather="rainy"

# 注入 EXIF 信息
python -m markflow.cli.commands execute exif_injector image_path="photo.jpg" author="John" description="My photo"

# 清除元数据
python -m markflow.cli.commands execute meta_cleaner image_path="photo.jpg"
```


# GUI 图形界面
```bash
# 启动 GUI

python scripts/markflow_gui.py

或

python -m markflow.gui
```

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

将 SD 模型放在 models/ 目录下,和Markflow_4image同一个级别：
```text
Markflow_4image
models/
├── sd-v1-5/
│   ├── zenityXmix.inpainting.safetensors
│   └── ...
├── controlnet/
│   └── ...
└── ...
```


### 📂 目录结构

```text
Markflow_4image/
├── markflow/              # 核心模块
│   ├── __init__.py
│   ├── core/
│   ├── cli/
│   ├── gui/
│   └── ...
├── skills/                # 所有技能 (38个图片处理技能)
│   ├── add_animal_ears/
│   ├── add_background_objects/
│   ├── add_glasses/
│   ├── add_tattoo/
│   ├── anime_to_real/
│   ├── change_age/
│   ├── change_background/
│   ├── change_body_type/
│   ├── change_clothes/
│   ├── change_clothing_style/
│   ├── change_expression/
│   ├── change_eye_color/
│   ├── change_face/
│   ├── change_furniture/
│   ├── change_gender/
│   ├── change_hair/
│   ├── change_lighting/
│   ├── change_makeup/
│   ├── change_nationality/
│   ├── change_perspective/
│   ├── change_skin_tone/
│   ├── colorize_sketch/
│   ├── controlnet/
│   ├── day_night_transfer/
│   ├── exif_injector/
│   ├── fantasy_character/
│   ├── meta_cleaner/
│   ├── old_photo_restore/
│   ├── photo_realistic/
│   ├── photo_restorer/
│   ├── real_to_anime/
│   ├── remove_clothes/
│   ├── remove_object/
│   ├── replace_object/
│   ├── sd_image_generator/
│   ├── season_transfer/
│   ├── sketch_to_real/
│   ├── style_transfer/
│   └── weather_transfer/
├── scripts/               # 工具脚本
├── output/                # 输出目录
├── .gitignore
└── README.md
```

###  ⚠️ 注意事项

模型文件: 需要自行下载 SD 模型到 models/ 目录

GPU 内存: 建议至少 8GB VRAM

首次运行: 首次运行会下载相关依赖模型

参数格式: 命令行参数使用 key="value" 或 key=value 格式

###  📄 许可证
MIT

###  🔗 相关项目

MarkFlow - 原版 MarkFlow，包含更多通用技能

此版本是 MarkFlow 的图片处理专用分支

