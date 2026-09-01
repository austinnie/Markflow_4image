# Bedroom Lingerie - 卧室唯美内衣

## 描述
基于参考图，生成一张在床上穿着唯美内衣的人物正面全身图

## 输入
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| image_path | string | 是 | - | 参考图路径 |
| outfit | string | 否 | white lace | 内衣风格 (white lace/black silk/pink satin/red velvet) |
| pose | string | 否 | lying | 姿态 (lying/sitting/kneeling) |
| strength | float | 否 | 0.7 | 变化强度 |

## 输出
| 字段 | 说明 |
|------|------|
| output_path | 生成的图片路径 |

## 示例
```bash
python -m markflow.cli.commands execute bedroom_lingerie image_path="input/person.jpg" outfit="white lace" pose="lying"
```