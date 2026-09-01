# BedroomNude

## 描述
基于参考图，生成一张在床上裸露的人物正面全身图

## 目的
一键生成卧室裸体照，无需多步处理

## 输入
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| image_path | string | 是 | - | 参考图路径 |
| pose | string | 否 | lying | 姿态 (lying/sitting/kneeling/standing) |
| strength | float | 否 | 0.7 | 变化强度 |
| steps | integer | 否 | 30 | 迭代步数 |
| seed | integer | 否 | -1 | 随机种子 |

## 输出
| 字段 | 说明 |
|------|------|
| output_path | 生成的图片路径 |

## 依赖
- controlnet_img2img

## 示例
```bash
python -m markflow.cli.commands execute bedroom_nude image_path="input/person.jpg" pose="lying"
```