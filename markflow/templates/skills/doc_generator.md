# doc_generator

> 代码文档自动生成器，从 Python 代码自动生成 API 文档

## 技能描述

自动化生成项目文档，支持 API 参考、README 和使用指南

## 核心功能

1. 📄 **API 文档生成** - 从代码自动生成 API 参考文档
2. 📖 **README 生成** - 自动生成项目 README 文档
3. 📝 **使用示例生成** - 从代码中提取使用示例
4. 🔍 **代码解析** - 解析 Python 文件，提取类、函数、模块信息
5. 📊 **模块摘要** - 生成代码模块结构摘要

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `code_path` | string | 是 | - | 代码目录或文件路径 |
| `doc_type` | string | 否 | all | 文档类型 (api/readme/all) |
| `output_format` | string | 否 | md | 输出格式 (md/html) |
| `project_name` | string | 否 | - | 项目名称，默认从目录名获取 |
| `project_description` | string | 否 | - | 项目描述 |
| `author` | string | 否 | - | 作者信息 |
| `include_tests` | boolean | 否 | false | 是否包含测试用例信息 |
| `extract_classes` | boolean | 否 | true | 是否提取类结构 |
| `extract_functions` | boolean | 否 | true | 是否提取函数签名 |
| `generate_examples` | boolean | 否 | true | 是否生成使用示例 |

## 输出

| 字段 | 说明 |
|------|------|
| `doc_path` | 文档保存路径 |
| `api_reference` | API 参考文档内容 |
| `modules_summary` | 模块摘要 |
| `classes_summary` | 类结构摘要 |
| `functions_summary` | 函数摘要 |
| `usage_examples` | 使用示例 |

## 步骤

1. 验证输入参数
2. 扫描代码目录，收集所有 Python 文件
3. 解析 Python 文件，提取模块、类、函数信息
4. 解析 docstring，提取文档注释
5. 生成 API 参考文档
6. 生成 README 文档
7. 生成使用示例
8. 输出文档并返回结果

## 依赖

- ast
- inspect
- pydoc
- jinja2 (可选，用于模板渲染)
- markdown (可选，用于格式转换)

## 示例

```python
generator = DocGenerator()
result = generator.execute(
    code_path="./markflow",
    doc_type="all",
    output_format="md",
    project_name="MarkFlow",
    project_description="从 Markdown 到可执行技能的工作流引擎",
    author="MarkFlow Team"
)
print(f"文档已生成: {result['doc_path']}")
```

## 使用示例

```bash
python -m markflow.cli.commands execute doc_generator code_path="./markflow" doc_type="all"
```