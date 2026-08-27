# ChangeBackground

> 保持人物不变，替换图片背景

## 功能特性

- **自动检测人物**：使用 YOLO 自动分割人物区域
- **深度图控制**：使用 Depth ControlNet 保持空间结构
- **预设背景**：20+ 种预设背景快速切换
- **自定义描述**：支持自定义背景提示词
- **批量处理**：支持目录批量处理

## 预设背景

| 预设 | 说明 |
|------|------|
| `beach` | 海滩 |
| `forest` | 森林 |
| `mountain` | 雪山 |
| `city` | 城市 |
| `space` | 太空 |
| `underwater` | 海底 |
| `sakura` | 樱花 |
| `autumn` | 秋叶 |
| `snow` | 雪景 |
| `desert` | 沙漠 |
| `library` | 图书馆 |
| `cafe` | 咖啡馆 |
| `temple` | 寺庙 |
| `sunset` | 日落 |
| `aurora` | 极光 |
| `waterfall` | 瀑布 |
| `castle` | 城堡 |
| `cyberpunk` | 赛博朋克 |
| `studio` | 影棚 |
| `gradient` | 渐变 |

## 使用方法

```bash
# 使用预设背景
python -m markflow.cli.commands execute change_background image_path="person.jpg" preset=beach

# 自定义背景描述
python -m markflow.cli.commands execute change_background image_path="person.jpg" background_prompt="sunny meadow with wildflowers, blue sky"

# 调整参数
python -m markflow.cli.commands execute change_background image_path="person.jpg" preset=city strength=0.8 steps=35

# 禁用 ControlNet
python -m markflow.cli.commands execute change_background image_path="person.jpg" preset=forest no_controlnet=True

# 批量处理
python skills/change_background/skill.py --input ./images/ --preset studio --batch -o ./output/
```

## 输出位置
```text
skills/change_background/output/
```