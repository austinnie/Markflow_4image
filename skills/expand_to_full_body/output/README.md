# expand_to_full_body

> 将人物半身/头像图扩展为全身图

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 9
- **函数数**: 2

## 支持的功能

| 功能 | 说明 |
|------|------|
| 🤖 AI 智能处理 | - |
| 📊 学习进度追踪 | 记录学习统计 |

## 依赖

```bash
pip install controlnet-aux
pip install Pillow
pip install diffusers
pip install ultralytics
pip install torch
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image_path` | string | `` | 输入图片路径 |
| `prompt` | string | `a person, beautiful, detailed` | 人物描述提示词 |
| `controlnet_type` | string | `openpose` | ControlNet 类型 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 生成的全身图路径 |

## 使用方法

```bash
python -m markflow.cli.commands execute expand_to_full_body [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute expand_to_full_body [参数]
```

## 输出位置

生成的输出保存在 `skills/expand_to_full_body/output/` 目录下。

---

*文档自动生成于 2026-08-30 16:04:36*