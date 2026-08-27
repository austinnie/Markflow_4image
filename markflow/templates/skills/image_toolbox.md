# ImageToolbox

## 描述
图片批量处理工具箱

## 目的
批量处理图片，支持格式转换、尺寸调整、压缩、水印、裁剪等操作

## 输入
- source_dir: string: 源图片目录路径 (必填)
- output_dir: string: 输出目录路径，默认 ./processed_images
- operations: string: 操作类型，多个操作用逗号分隔 (resize,compress,convert,watermark,crop,rotate,color,thumbnail,grid)
- target_format: string: 目标格式 (jpg/png/webp/bmp/tiff)，默认保持原格式
- width: integer: 目标宽度
- height: integer: 目标高度
- quality: integer: 压缩质量 1-100，默认 85
- watermark_text: string: 水印文字内容
- watermark_position: string: 水印位置 (center/top-left/top-right/bottom-left/bottom-right)，默认 bottom-right
- watermark_opacity: float: 水印透明度 0-1，默认 0.7
- crop_x: integer: 裁剪起始 X 坐标
- crop_y: integer: 裁剪起始 Y 坐标
- crop_width: integer: 裁剪宽度
- crop_height: integer: 裁剪高度
- rotate_angle: integer: 旋转角度 (90/180/270)
- flip_direction: string: 翻转方向 (horizontal/vertical)
- brightness: float: 亮度调整 (-1.0 到 1.0)
- contrast: float: 对比度调整 (-1.0 到 1.0)
- saturation: float: 饱和度调整 (-1.0 到 1.0)
- thumbnail_size: integer: 缩略图尺寸，默认 200
- grid_cols: integer: 图册列数，默认 3
- recursive: boolean: 是否递归处理子目录，默认 true
- pattern: string: 文件匹配模式，默认 *.jpg,*.jpeg,*.png,*.webp,*.bmp,*.tiff
- dry_run: boolean: 预览模式，只显示处理计划不实际处理，默认 false

## 输出
- processed_count: 成功处理文件数
- failed_count: 失败文件数
- output_dir: 输出目录路径
- size_reduction: 文件大小变化百分比
- processing_time: 处理耗时

## 步骤
1. 验证输入参数
2. 扫描源目录，收集符合条件的图片文件
3. 创建输出目录
4. 遍历图片文件，依次执行操作
5. 保存处理后的图片
6. 生成处理报告
7. 返回处理结果

## 依赖
- Pillow
- opencv-python
- numpy

## 示例
```python
toolbox = ImageToolbox()
result = toolbox.execute(
    source_dir="./images",
    operations="resize,compress,watermark",
    width=800,
    quality=85,
    watermark_text="Copyright 2024",
    output_dir="./processed_images"
)
print(result)