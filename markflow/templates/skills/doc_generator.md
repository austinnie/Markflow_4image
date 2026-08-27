# doc_generator

## 描述
代码文档自动生成器，从 Python 代码自动生成 API 文档

## 目的
自动化生成项目文档，支持 API 参考、README 和使用指南

## 输入
- code_path: string: 代码目录或文件路径 (必填)
- doc_type: string: 文档类型 (api/readme/all)，默认 all
- output_format: string: 输出格式 (md/html)，默认 md
- project_name: string: 项目名称，默认从目录名获取
- project_description: string: 项目描述
- author: string: 作者信息
- include_tests: boolean: 是否包含测试用例信息，默认 false
- extract_classes: boolean: 是否提取类结构，默认 true
- extract_functions: boolean: 是否提取函数签名，默认 true
- generate_examples: boolean: 是否生成使用示例，默认 true

## 输出
- doc_path: 文档保存路径
- api_reference: API 参考文档内容
- modules_summary: 模块摘要
- classes_summary: 类结构摘要
- functions_summary: 函数摘要
- usage_examples: 使用示例

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
print(f"API 参考: {result['api_reference'][:200]}...")