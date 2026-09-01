# ChangePose

> 改变图片中人物的姿态，支持站立、坐姿、躺姿、侧躺、跪姿等多种预设

## 描述

基于 ControlNet OpenPose，在保持人物身份特征的前提下，将人物姿态转换为目标姿势。支持预设姿态和自定义姿态参考图。

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| image_path | string | 是 | - | 输入图片路径 |
| pose | string | 否 | standing | 目标姿态 (standing/sitting/lying/side_lying/kneeling/walking/running/dancing/squatting/jumping) |
| strength | float | 否 | 0.65 | 变化强度 (0.0-1.0) |
| steps | integer | 否 | 30 | 迭代步数 |
| seed | integer | 否 | -1 | 随机种子 |
| controlnet_type | string | 否 | openpose | ControlNet 类型 |

## 输出

| 字段 | 说明 |
|------|------|
| output_path | 生成的图片路径 |
| pose | 应用的姿态 |
| generation_time | 生成耗时 |

## 依赖

- PIL
- torch
- controlnet_img2img

## 示例

```python
skill = ChangePose()
result = skill.execute(
    image_path="input/person.jpg",
    pose="lying",
    strength=0.65
)
print(result['output_path'])
```
## 使用示例
```bash
python -m markflow.cli.commands execute change_pose image_path="input/person.jpg" pose="lying"

python -m markflow.cli.commands execute change_pose image_path="input/person.jpg" pose="sitting" strength=0.7
```