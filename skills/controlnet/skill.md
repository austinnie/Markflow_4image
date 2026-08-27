# ControlNet

## 描述
提供姿态检测和 ControlNet 控制能力，支持 OpenPose、Canny、Depth 等多种 ControlNet 类型

## 目的
为其他技能（如 remove_clothes）提供 ControlNet 姿态检测和生成能力，保持人物姿态不变

## 输入
- **action**: 操作类型: status, list_types, detect_pose, load_pipeline
- **image**: 输入图片路径 (detect_pose 操作)
- **image_path**: 输入图片路径 (detect_pose 操作, 同 image)
- **output_path**: 输出图片路径 (detect_pose 操作)
- **model_path**: SD 模型路径 (load_pipeline 操作)
- **controlnet_type**: ControlNet 类型: openpose, openpose_full, dwpose, canny, hed, lineart, depth, normal, mlsd
- **device**: 设备: cpu 或 cuda

## 输出
- **status**: 执行状态: success 或 error
- **output_path**: 生成的 ControlNet 控制图路径 (detect_pose 操作)
- **controlnet_type**: 使用的 ControlNet 类型
- **types**: 所有支持的 ControlNet 类型列表 (list_types 操作)
- **dependencies**: 依赖检查状态 (status 操作)

## 步骤
无

## 依赖
- diffusers
- controlnet-aux
- opencv-python-headless
- torch
- Pillow
- numpy

## 版本
1.0.0