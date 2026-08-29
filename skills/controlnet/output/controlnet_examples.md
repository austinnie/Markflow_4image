# controlnet 使用示例

以下是从代码中提取的使用示例：

## skill

### Controlnet

```python
# 创建实例
obj = Controlnet(config)
```

```python
result = obj._setup_logging()
# 设置日志
result = obj._setup_config()
# 设置配置默认值
result = obj._get_detector(controlnet_type)
# 获取或创建检测器
```
