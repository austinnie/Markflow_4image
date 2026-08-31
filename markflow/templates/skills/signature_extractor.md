# SignatureExtractor

## 技能描述

> 从带有签名的图片中，提取纯黑字迹并去除背景，自动裁剪生成透明背景的签名图片，可直接插入到文档中。

## 技能描述

该技能利用 OpenCV 计算机视觉技术，对包含手写签名或印章的图片进行预处理。通过自适应阈值化、连通域面积过滤和形态学平滑，精准提取出签名笔迹，去除纸张底色、噪点和无关背景，并自动裁剪出签名的主体区域。最终输出带有 Alpha 通道的透明背景 PNG 图片，可直接无缝插入到 PDF 或 Word 文档中。

## 核心功能

1. **自适应提取** - 利用 cv2.adaptiveThreshold 自动适应光照不均、纸张纹理复杂的图片。
2. **智能降噪** - 基于连通域面积（min_area）过滤，精准剔除微小噪点，保留真实笔迹。
3. **自动边缘裁剪** - 自动计算签名包围盒，去除空白边缘，并留有适当Padding以保证视觉效果。
4. **透明背景输出** - 输出 RGBA 格式的 PNG，仅保留纯黑笔迹，背景全透明，兼容任何文档底色。

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 包含签名的原图片路径 (支持 .jpg, .png, .bmp) |
| output_path | string | 是 | - | 提取后透明背景签名图片的保存路径 (必须为 .png) |
| min_area | integer | 否 | 30 | 过滤噪点的最小像素面积，可根据图片分辨率微调 |
| save_result | boolean | 否 | True | 是否将提取参数和结果信息保存为日志文件 |

## 输出

| 字段 | 说明 |
|------|------|
| status | 执行状态：success / error |
| result | 包含提取结果详情、保存路径和图片尺寸等信息的字典 |
| metadata | 技能名称、版本、执行时间等元数据 |

## 步骤

1. 使用 OpenCV 将输入图片读取为灰度图。
2. 使用自适应高斯阈值反转为黑字白底（THRESH_BINARY_INV）。
3. 遍历连通域，删除面积小于 min_area 的孤立噪点。
4. 寻找笔迹边界框，添加 Padding 并进行裁剪。
5. 构建 RGBA 图像，将笔迹设置为纯黑且不透明，背景设为全透明。
6. 将结果保存为 PNG 格式，并返回执行结果。

## 依赖

- opencv-python
- numpy

## 示例

```python
from SignatureExtractor import SignatureExtractor

# 初始化技能
skill = SignatureExtractor()

# 执行提取
result = skill.execute(input_path="scanned_doc.jpg", output_path="signature.png")
print(result)
```

##使用示例
```bash
python -m markflow.cli.commands execute signature_extractor input_path="scanned_doc.jpg" output_path="signature.png"

def generate_md():
    filename = "README.md"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(README_TEMPLATE)
        print(f"✅ 成功生成 {filename}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")

if __name__ == "__main__":
    generate_md()
```	