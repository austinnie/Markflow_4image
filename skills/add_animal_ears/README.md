# add_animal_ears

> 为人物添加动物耳朵，支持猫耳、狗耳、狐耳、狼耳、兔耳、熊耳。使用 ControlNet 保持人物面部不变。

## 描述

为人物添加动物耳朵，支持猫耳、狗耳、狐耳、狼耳、兔耳、熊耳。使用 ControlNet 保持人物面部不变。

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `image_path` | string | 是 |  | 输入图片路径 |
| `animal` | string | 否 | cat | 动物类型 (cat/dog/fox/wolf/bunny/bear) |
| `strength` | float | 否 | 0.55 | 变化强度 (0.0-1.0) |
| `steps` | integer | 否 | 30 | 迭代步数 |
| `seed` | integer | 否 | -1 | 随机种子 |

## 输出

| 字段 | 说明 |
|------|------|
| `output_path` | 生成的图片路径 |
| `animal` | 应用的动物类型 |
| `generation_time` | 生成耗时 |

## 使用方法

```bash
python -m markflow.cli.commands execute add_animal_ears [参数]
```

## 依赖安装

```bash
pip install PIL
pip install torch
```

---

*文档生成于 2026-09-01 16:15:57*