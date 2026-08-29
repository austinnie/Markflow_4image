# controlnet

> 提供姿态检测和 ControlNet 控制能力，支持 OpenPose、Canny、Depth 等多种 ControlNet 类型

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 10
- **函数数**: 5

## 技能描述

提供姿态检测和 ControlNet 控制能力，支持 OpenPose、Canny、Depth 等多种 ControlNet 类型

## 依赖

```bash
pip install diffusers
pip install controlnet-aux
pip install opencv-python-headless
pip install torch
pip install Pillow
pip install numpy
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `status` | 操作类型: status, list_types, detect_pose, load_pipeline |
| `image` | string | `` | 输入图片路径 (detect_pose 操作) |
| `image_path` | string | `` | 输入图片路径 (detect_pose 操作, 同 image) |
| `output_path` | string | `` | 输出图片路径 (detect_pose 操作) |
| `model_path` | string | `` | SD 模型路径 (load_pipeline 操作) |
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

```bash
python -m markflow.cli.commands execute controlnet [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute controlnet
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info controlnet
```

## 输出位置

生成的输出保存在 `skills/controlnet/output/` 目录下。

---

*文档自动生成于 2026-08-27 23:41:53*