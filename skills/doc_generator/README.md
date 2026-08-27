# doc_generator

> 代码文档自动生成器，从 Python 代码自动生成 API 文档

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 17
- **函数数**: 1

## 技能描述

代码文档自动生成器，从 Python 代码自动生成 API 文档

## 依赖

```bash
pip install ast
pip install inspect
pip install pydoc
pip install jinja2
pip install markdown
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code_path` | string | `` | 代码目录或文件路径 (必填) |
| `doc_type` | string | `` | 文档类型 (api/readme/all)，默认 all |
| `output_format` | string | `` | 输出格式 (md/html)，默认 md |
| `project_name` | string | `` | 项目名称，默认从目录名获取 |
| `project_description` | string | `` | 项目描述 |
| `author` | string | `` | 作者信息 |
| `include_tests` | boolean | `` | 是否包含测试用例信息，默认 false |
| `extract_classes` | boolean | `` | 是否提取类结构，默认 true |
| `extract_functions` | boolean | `` | 是否提取函数签名，默认 true |
| `generate_examples` | boolean | `` | 是否生成使用示例，默认 true |

## 输出

| 字段 | 说明 |
|------|------|
| `doc_path` | 文档保存路径 |
| `api_reference` | API 参考文档内容 |
| `modules_summary` | 模块摘要 |
| `classes_summary` | 类结构摘要 |
| `functions_summary` | 函数摘要 |
| `usage_examples` | 使用示例 |

## 使用方法

```bash
python -m markflow.cli.commands execute doc_generator [参数]
```

### 示例

```bash
# 生成 README
python -m markflow.cli.commands execute doc_generator code_path="./skills/sd_image_generator/skill.py" doc_type="readme" project_name="sd_image_generator"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info doc_generator
```

## 输出位置

生成的输出保存在 `skills/doc_generator/output/` 目录下。

---

*文档自动生成于 2026-08-23 17:13:22*