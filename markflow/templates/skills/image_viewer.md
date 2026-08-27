# image_viewer

## 描述
功能完整的图片查看器和管理器，替代 Windows 自带图片查看器

## 目的
提供一站式图片浏览、管理和编辑能力

## 输入
- action: string: 操作类型 (browse/view/info/edit/manage/slideshow/search/export/print)
- source_dir: string: 图片目录路径
- file: string: 单个图片文件路径
- view_mode: string: 查看模式 (grid/list/single)，默认 grid
- sort_by: string: 排序方式 (name/date/size/type)，默认 name
- sort_order: string: 排序顺序 (asc/desc)，默认 asc
- filter: string: 过滤条件 (all/images/videos/starred)，默认 all
- thumbnail_size: integer: 缩略图大小，默认 200
- slideshow_interval: integer: 幻灯片间隔(秒)，默认 3
- fullscreen: boolean: 是否全屏，默认 false
- tags: string: 标签列表，逗号分隔
- star: integer: 星标 0-5
- rename_pattern: string: 重命名模式
- export_format: string: 导出格式 (jpg/png/webp)
- export_quality: integer: 导出质量 1-100，默认 85
- export_size: string: 导出尺寸，如 800x600

## 输出
- files: 文件列表
- current_file: 当前查看的文件
- file_info: 文件详细信息
- thumbnails: 缩略图列表
- stats: 统计信息
- export_path: 导出路径
- message: 操作结果消息

## 步骤
1. 验证输入参数
2. 扫描目录获取文件列表
3. 根据操作执行相应功能
4. 返回结果

## 依赖
- Pillow
- tkinter (可选，用于GUI)
- pyexiv2 (可选，用于EXIF)
- watchdog (可选，用于文件监控)

## 示例
```python
viewer = ImageViewer()
# 浏览目录
result = viewer.execute(action="browse", source_dir="./images")
# 查看图片信息
result = viewer.execute(action="info", file="./images/photo.jpg")
# 幻灯片播放
result = viewer.execute(action="slideshow", source_dir="./images", slideshow_interval=5)
# 导出图片
result = viewer.execute(action="export", source_dir="./images", export_format="webp", export_quality=80)