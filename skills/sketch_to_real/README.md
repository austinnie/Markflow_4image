# sketch_to_real

> sketch_to_real 技能

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 10
- **函数数**: 2

## 使用方法

```bash
python -m markflow.cli.commands execute sketch_to_real [参数]
```


## 🚀 使用命令
```bash
cd E:\SD_OpenVINO\Markflow_4image

# 1. 列出可用模型
python skills/sketch_to_real/skill.py --list-models

# 2. 列出可用风格
python skills/sketch_to_real/skill.py --list-styles

# 3. 基础用法（默认风格 realistic）
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/real.png

# 4. 指定风格
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/cinematic.png --style cinematic

# 5. 指定模型
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/real.png --model asianrealisticSdlife_v40.safetensors

# 6. 自定义提示词（覆盖风格默认）
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/real.png --prompt "a beautiful woman, photorealistic" --negative "ugly, cartoon"

# 7. 高质量输出
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/real.png --steps 50 --seed 42

# 8. 使用 GPU
python skills/sketch_to_real/skill.py --input sketch.jpg --output output/real.png --device cuda
```

## 📋 通过 MarkFlow CLI 调用
```bash
# 基础用法
python -m markflow.cli.commands execute sketch_to_real image_path="sketch.jpg" output_path="output/real.png"

# 指定风格
python -m markflow.cli.commands execute sketch_to_real image_path="sketch.jpg" output_path="output/cinematic.png" style=cinematic

# 指定模型
python -m markflow.cli.commands execute sketch_to_real image_path="sketch.jpg" output_path="output/real.png" model_name=asianrealisticSdlife_v40.safetensors

# 自定义提示词
python -m markflow.cli.commands execute sketch_to_real image_path="sketch.jpg" output_path="output/real.png" prompt="a beautiful woman, photorealistic" style=realistic

# 使用默认模型 anytimeRealistic_v10
python -m markflow.cli.commands execute sketch_to_real image_path="skills\sketch_to_real/test6.png" output_path="skills/sketch_to_real/output/cinematic.png" style=cinematic

# 使用亚洲写实模型
python -m markflow.cli.commands execute sketch_to_real image_path="skills\sketch_to_real/test6.png" output_path="skills/sketch_to_real/output/cinematic_asian.png" style=cinematic model_name=asianrealisticSdlife_v40.safetensors

# 使用 DreamShaper（艺术风格）
python -m markflow.cli.commands execute sketch_to_real image_path="skills\sketch_to_real/test6.png" output_path="skills/sketch_to_real/output/cinematic_art.png" style=cinematic model_name=DreamShaper_8_pruned.safetensors

```

## 输出位置

生成的输出保存在 `skills/sketch_to_real/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:57*