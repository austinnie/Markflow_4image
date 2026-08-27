# doc_generator

## 描述
代码文档自动生成器，从 Python 代码自动生成 API 文档

## 目的


## 输入
- **code_path**: 代码目录或文件路径 (必填)
- **doc_type**: 文档类型 (api/readme/all)，默认 all
- **output_format**: 输出格式 (md/html)，默认 md
- **project_name**: 项目名称，默认从目录名获取
- **project_description**: 项目描述
- **author**: 作者信息
- **include_tests**: 是否包含测试用例信息，默认 false
- **extract_classes**: 是否提取类结构，默认 true
- **extract_functions**: 是否提取函数签名，默认 true
- **generate_examples**: 是否生成使用示例，默认 true

## 输出
- **doc_path**: 文档保存路径
- **api_reference**: API 参考文档内容
- **modules_summary**: 模块摘要
- **classes_summary**: 类结构摘要
- **functions_summary**: 函数摘要
- **usage_examples**: 使用示例

## 步骤
无

## 依赖
- ast
- inspect
- pydoc
- jinja2
- markdown

## 版本
1.0.0
