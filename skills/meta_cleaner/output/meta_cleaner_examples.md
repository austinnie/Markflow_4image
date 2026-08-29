# meta_cleaner 使用示例

以下是从代码中提取的使用示例：

## skill

### MetaCleaner

```python
# 创建实例
obj = MetaCleaner(config)
```

```python
result = obj._setup_logging()
result = obj._setup_config()
result = obj.clean_metadata(image_path, output_path, method='auto', jpg_quality=92)
# 清理图片元数据

Args:
    image_path: 输入图片路径
    output_path: 输出路径

```
