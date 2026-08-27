# meta_cleaner

> 清除图片中的 AI 生成痕迹，移除元数据

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 7
- **函数数**: 3

## 技能描述

清除图片中的 AI 生成痕迹，移除元数据

## 依赖

```bash
pip install Pillow
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | string | `` | 输入图片路径 |
| `method` | string | `auto` | 清理方法 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 输出图片路径 |
| `method` | 使用的方法 |

## 使用方法

```bash
python -m markflow.cli.commands execute meta_cleaner [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute meta_cleaner image_path="your_image_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info meta_cleaner
```

## 输出位置

生成的输出保存在 `skills/meta_cleaner/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:55*