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

## 🖼️ 批量图片生成器
scripts/generate_images.py 是一个强大的批量图片生成工具，支持从分层 Prompt 配置自动组合生成大量图片。

工作原理
自动扫描 scripts/configs/prompts/ 目录下的所有 .py 文件

解析风格：每个文件定义了一个 STYLE 字典，包含 subjects（主题）、styles（风格）、moods（情绪）

自动组合：将三层组合生成完整的 Prompt

调用 sd_image_generator 技能生成图片


## 当前配置

| 统计项 | 数量 |
|--------|------|
| 风格文件 | 94 个 |
| 生成方案 | 13,810 种 |
| 覆盖类型 | 国画、动漫、机甲、线稿、生肖、珠宝、白描、人物、动物、城市、军事等 |

---

## 风格分类详情

| 分类 | 风格数量 | 代表风格 |
|------|----------|----------|
| 国画/水墨 | 12 | `chinese_ink_animals`、`chinese_landscape_master`、`chinese_ink_bird` |
| 白描线稿 | 10 | `classical_chinese_lineart`、`countryside_ink_lineart`、`hermit_ink_lineart` |
| 动漫/二次元 | 6 | `anime_figure_girl`、`anime_greyscale_portrait`、`autumn_anime_portrait` |
| 机甲/机械 | 18 | `mecha_sketch`、`gundam_sketch`、`mecha_girl_ultra_expansion`、`transformers_sketch` |
| 动物线稿 | 12 | `bird_sketch`、`cat_sketch`、`dragon_sketch`、`tiger_sketch`、`horse_sketch` |
| 十二生肖 | 8 | `rat_sketch`、`ox_sketch`、`tiger_sketch`、`rabbit_sketch`、`dragon_sketch` 等 |
| 人像/人物 | 8 | `human_portrait_sketch`、`sketch_fashion_designer`、`pencil_sketch_02_anatomy` |
| 铅笔素描 | 9 | `pencil_sketch_01_fashion`、`pencil_sketch_04_atmosphere`、`pencil_sketch_05_minimal` |
| 设计/蓝图 | 6 | `watch_blueprint`、`jewelry_blueprint`、`bag_blueprint`、`mecha_blueprint` |
| 风景/环境 | 5 | `city_sketch`、`beach_resort_swimwear`、`nature_outdoor_girl` |
| 其他 | 10 | `calligraphy_art`、`gallery_elegant`、`nuclear_01_sketch`、`transformers_optimus_prime` |
| **合计** | **94** | |

---

## 组合生成说明

每个风格文件包含三层组合：

| 层级 | 说明 | 示例 |
|------|------|------|
| **Subjects** | 主题/主体 | `flying swallow, dynamic wings` |
| **Styles** | 风格/画风 | `minimalist line art`、`sketch style` |
| **Moods** | 情绪/氛围 | `peaceful, calm`、`dramatic, intense` |

**组合公式**：`Subjects × Styles × Moods = 生成方案数`

例如 `bird_sketch`：10 × 3 × 4 = **120 种方案**


cd Markflow_4image
```bash
# 1. 列出所有方案（查看可用风格和组合数）
python scripts/generate_images.py --list
python scripts/generate_images.py --folder 极简飞鸟线稿 --list
python scripts/generate_images.py --style bird_sketch --list

# 2. 生成所有方案（谨慎！13810 张）
python scripts/generate_images.py --all

# 3. 生成指定 ID 的方案
python scripts/generate_images.py --id 1
python scripts/generate_images.py --ids 1,3,5,10


# 4. 按风格名称筛选
python scripts/generate_images.py --style bird_sketch --all
python scripts/generate_images.py --style bird_sketch --id 1

# 5. 按文件夹名称筛选生成
python scripts/generate_images.py --folder 极简飞鸟线稿 --all

# 6. 限制每个风格的组合数
python scripts/generate_images.py --limit 10 --list
python scripts/generate_images.py --style bird_sketch --limit 5 --all

# 7. 限制总生成数量（取前 N 个方案）
python scripts/generate_images.py --total 10 --all
python scripts/generate_images.py --folder 极简飞鸟线稿 --total 5 --all

# 8. 组合使用
python scripts/generate_images.py --style bird_sketch --limit 5 --total 10 --all

# 执行的效果：
python scripts/generate_images.py --folder 极简飞鸟线稿 --all
🔍 自动发现 prompts 目录: E:\SD_OpenVINO\Markflow_4image\scripts\configs\prompts
📂 扫描目录: E:\SD_OpenVINO\Markflow_4image\scripts\configs\prompts
   📁 文件夹过滤: 极简飞鸟线稿
  ✓ animals\bird_sketch.py -> bird_sketch
  ✓ sketch\bird_sketch.py -> bird_sketch

📋 加载的风格列表 (1 个):
    1. bird_sketch
      文件夹: 极简飞鸟线稿 | 主题: 10 | 风格: 3 | 情绪: 4 | 组合: 120/120

💾 风格列表已保存到: output\styles_list.txt

✅ 从目录加载了 1 个风格，展开为 120 个生成方案

进度: 1/120

============================================================
   🔥 第 1 次调用 generate_one
   [1/120] bird_sketch_1
============================================================
```

### 🔧 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--config` | 路径 | 使用 JSON 配置文件 | `--config configs/girls_config.json` |
| `--source` | 路径 | 指定 Python prompt 文件/目录 | `--source configs/prompts/animals` |
| `--list` | 标志 | 列出所有已加载的方案（不生成） | `--list` |
| `--all` | 标志 | **触发生成**，生成所有方案 | `--all` |
| `--total` | 数字 | **配合 `--all` 使用**，限制总生成数量，取前 N 个方案 | `--total 5` |
| `--id` | 数字 | 生成指定 ID 的方案 | `--id 1` |
| `--ids` | 字符串 | 生成多个方案，用逗号分隔 | `--ids 1,3,5` |
| `--style` | 名称 | 只加载指定风格 | `--style bird_sketch` |
| `--folder` | 名称 | 只加载指定文件夹 | `--folder 极简飞鸟线稿` |
| `--limit` | 数字 | **限制每个风格**最多生成 N 个组合 | `--limit 10` |
| `--help` | 标志 | 显示帮助信息 | `--help` |

### 📌 参数组合说明

| 组合命令 | 效果 |
|----------|------|
| `--all` | 生成所有方案（如 13,810 张） |
| `--all --total 10` | 生成前 10 张 |
| `--limit 5 --all` | 每个风格最多生成 5 张，生成所有风格 |
| `--limit 5 --all --total 10` | 每个风格最多 5 张，但总共只取前 10 张 |
| `--folder 极简飞鸟线稿 --all` | 生成该文件夹下所有风格的所有方案 |
| `--folder 极简飞鸟线稿 --limit 3 --all` | 该文件夹下每个风格生成 3 张 |
| `--folder 极简飞鸟线稿 --limit 3 --all --total 5` | 该文件夹下每个风格最多 3 张，总共取前 5 张 |

### ⚠️ 重要说明

| 参数 | 是否触发生成 | 说明 |
|------|-------------|------|
| `--all` | ✅ **是** | 生成所有方案 |
| `--id` / `--ids` | ✅ **是** | 生成指定方案 |
| `--total` | ❌ **否** | **必须配合 `--all` 使用**，单独使用无效 |
| `--limit` | ❌ **否** | **必须配合 `--all` 使用**，单独使用无效 |
| `--list` | ❌ **否** | 只列出方案，不生成 |
| `--style` / `--folder` | ❌ **否** | 只做筛选，需配合 `--all` 或 `--id` 使用 |

**正确用法：**

```bash
# ✅ 正确：生成前 5 张
python scripts/generate_images.py --folder 极简飞鸟线稿 --limit 10 --all --total 5

# ❌ 错误：只加载方案，不生成（缺少 --all）
python scripts/generate_images.py --folder 极简飞鸟线稿 --limit 10 --total 5

# ✅ 正确：生成所有方案
python scripts/generate_images.py --folder 极简飞鸟线稿 --all

# ✅ 正确：生成指定 ID
python scripts/generate_images.py --folder 极简飞鸟线稿 --id 1


# 风格文件示例
scripts/configs/prompts/animals/bird_sketch.py:
```

##  提示词的分层结构

```python
STYLE = {
    "bird_sketch": {
        "folder": "极简飞鸟线稿",
        "subjects": [
            "flying swallow, dynamic wings",
            "eagle perched, majestic gaze",
            "flock of sparrows, chaotic flight",
            # ... 更多主题
        ],
        "styles": [
            "minimalist line art",
            "sketch style",
            "pencil drawing",
        ],
        "moods": [
            "peaceful, calm",
            "dramatic, intense",
            "dreamy, ethereal",
        ]
    }
}
```

## 重要说明
和其他skill组合使用 （如remove_clothes这个SKILLS， 其他SKILLS也可以加到代码中，
或者图片处理完成后再用次图片作为其他SKILLS的输入）

### 👕 衣服移除参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--remove-clothes` | 标志 | 进入衣服移除模式 | `--remove-clothes` |
| `--input` | 路径 | 输入图片路径或目录 | `--input image.jpg` |
| `-o, --output` | 路径 | 输出路径（单张）或输出目录（批量） | `-o output.jpg` |
| `--batch` | 标志 | 批量模式 | `--batch` |
| `--prompt` | 文本 | 生成提示词 | `--prompt "nude, beautiful skin"` |
| `--negative` | 文本 | 负面提示词 | `--negative "clothes, ugly"` |
| `--strength` | 浮点数 | 重绘强度 (0.0-1.0, 默认: 0.85) | `--strength 0.85` |
| `--steps` | 数字 | 迭代步数 (默认: 30) | `--steps 30` |
| `--seed` | 数字 | 随机种子 | `--seed 42` |
| `--device` | 设备 | 设备 (cpu/cuda, 默认: cpu) | `--device cuda` |
| `--save-mask` | 标志 | 保存遮罩 | `--save-mask` |

## 👕 衣服移除用法示例

```bash
# 单张图片移除衣服
python scripts/generate_images.py --remove-clothes --input image.jpg

# 指定输出路径
python scripts/generate_images.py --remove-clothes --input image.jpg -o output.jpg

# 批量处理目录
python scripts/generate_images.py --remove-clothes --input ./images/ --batch

# 批量处理并指定输出目录
python scripts/generate_images.py --remove-clothes --input ./images/ --batch -o ./output/

# 高级参数
python scripts/generate_images.py --remove-clothes --input image.jpg \
    --prompt "nude, beautiful skin" --strength 0.85 --steps 30 --device cuda
```


## 🎯 独立使用方式

每个技能都可以独立运行，无需依赖 MarkFlow 框架。每个技能目录下都包含独立的 `skill.py` 文件，包含完整的实现逻辑和命令行入口。

### 方式一：直接运行 skill.py

每个 skill 目录下的 `skill.py` 都包含 `if __name__ == "__main__":` 入口，可以直接运行：

```bash
## 🎯 独立使用方式

每个技能都可以独立运行，无需依赖 MarkFlow 框架。每个技能目录下都包含独立的 `skill.py` 文件，包含完整的实现逻辑和命令行入口。

### 方式一：直接运行 skill.py（不进入目录）

每个 skill 目录下的 `skill.py` 都包含 `if __name__ == "__main__":` 入口，可以直接从项目根目录运行：

```bash
# 从项目根目录直接运行（推荐）
python skills/sd_image_generator/skill.py --prompt "beautiful landscape"

# 奇幻角色转换
python skills/fantasy_character/skill.py --image photo.jpg --type elf

# 风格迁移
python skills/style_transfer/skill.py --image photo.jpg --style anime

# 移除衣服
python skills/remove_clothes/skill.py --input image.jpg

# ControlNet 姿态检测
python skills/controlnet/skill.py --action detect_pose --image photo.jpg

# 老照片修复
python skills/old_photo_restore/skill.py --image old_photo.jpg

# 动漫转真人
python skills/anime_to_real/skill.py --image anime.jpg

# 真人转动漫
python skills/real_to_anime/skill.py --image photo.jpg
```

### 方式二：作为模块导入

```bash
# 直接导入 skill 类使用
import sys
from pathlib import Path

# 添加技能目录到路径
skill_path = Path("skills/sd_image_generator")
sys.path.insert(0, str(skill_path))

from skill import Sdimagegenerator

# 创建实例并执行
generator = Sdimagegenerator()
result = generator.execute(
    prompt="beautiful landscape",
    model_name="xxx.safetensors",
    width=768,
    height=768
)
print(result)
```

### 方式三：通过 MarkFlow 框架（统一接口）

```bash
from markflow import MarkFlow

flow = MarkFlow()
result = flow.run(
    skill="sd_image_generator",
    prompt="beautiful landscape"
)
```


## 📌 各技能独立运行命令

| 技能 | 独立运行命令 |
|------|-------------|
| `sd_image_generator` | `python skills/sd_image_generator/skill.py -p "prompt"` |
| `fantasy_character` | `python skills/fantasy_character/skill.py --image photo.jpg --type elf` |
| `style_transfer` | `python skills/style_transfer/skill.py --image photo.jpg --style anime` |
| `remove_clothes` | `python skills/remove_clothes/skill.py --input image.jpg` |
| `controlnet` | `python skills/controlnet/skill.py --action detect_pose --image photo.jpg` |
| `old_photo_restore` | `python skills/old_photo_restore/skill.py --image old_photo.jpg` |
| `anime_to_real` | `python skills/anime_to_real/skill.py --image anime.jpg` |
| `real_to_anime` | `python skills/real_to_anime/skill.py --image photo.jpg` |
| `change_background` | `python skills/change_background/skill.py --image photo.jpg --background beach` |
| `day_night_transfer` | `python skills/day_night_transfer/skill.py --image photo.jpg --target night` |

## ✅ 独立使用的优点

| 优点 | 说明 |
|------|------|
| **轻量** | 不需要加载整个 MarkFlow 框架 |
| **快速测试** | 直接调试单个技能，无需进入目录 |
| **灵活集成** | 可以集成到其他项目 |
| **减少依赖** | 只加载该技能需要的依赖 |
| **脚本化** | 可以写成独立脚本定时运行 |

## ⚠️ 注意事项

| 事项 | 说明 |
|------|------|
| **模型路径** | 独立运行时需要确保 `models_dir` 配置正确 |
| **Python 路径** | 某些技能可能依赖 `markflow` 模块，需要设置 `PYTHONPATH` |
| **依赖安装** | 确保已安装该技能所需的依赖包 |
| **工作目录** | 建议在项目根目录执行，确保相对路径正确 |


##  🔧 环境配置

###  依赖安装 （每个skills单独有依赖，可以按提示安装，都安装到系统里，这样就所有skills共用一个环境，而不是venv）

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
│   ├── anytimeRealistic_v10.safetensors
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
│   ├── generate_images.py # ⭐ 批量图片生成器
│   ├── configs/
│   │   └── prompts/       # ⭐ 94 个风格配置文件
│   │       ├── animals/
│   │       ├── anime/
│   │       ├── chinese/
│   │       ├── mecha/
│   │       └── ...
│   └── markflow_gui.py
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

