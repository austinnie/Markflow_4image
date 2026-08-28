# code_gen_from_md

> 从 Markdown 需求文档自动生成高质量代码，包含语法检查、代码优化、单元测试和质量审查


## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 18
- **函数数**: 0


## 技能描述

代码生成器，从 Markdown 需求文档自动生成高质量代码。支持 Python、JavaScript、Java、Go、Rust 等多种语言，内置语法检查、代码优化、单元测试生成和 AI 代码审查。

### 核心功能

- 📝 **Markdown 解析** - 自动解析需求文档中的标题、描述、需求列表和代码示例
- 🤖 **AI 代码生成** - 使用 Ollama 生成高质量代码
- ✅ **语法检查** - 自动检查 Python 语法、导入语句、文档字符串、命名规范
- 🔧 **代码优化** - 自动修复代码问题，格式化代码
- 🧪 **单元测试生成** - 自动生成 Python 单元测试
- 📊 **代码审查** - AI 多维度审查代码质量并评分
- 🌐 **多语言支持** - Python、JavaScript、TypeScript、Java、Go、Rust、C++、HTML、CSS、Bash、SQL 等


## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `md_file` | string | 否* | - | Markdown 需求文件路径 |
| `md_content` | string | 否* | - | Markdown 需求内容（直接传入） |
| `language` | string | 否 | python | 目标语言（从 Markdown 自动检测） |
| `model` | string | 否 | qwen2.5:7b | Ollama 模型 |
| `mode` | string | 否 | full | 生成模式 (full/step) |


> *`md_file` 和 `md_content` 至少提供一个


## 输出

| 字段 | 说明 |
|------|------|
| `title` | 项目名称 |
| `language` | 目标语言 |
| `saved_files` | 生成的文件列表 |
| `quality_score` | 质量评分 (0-100) |
| `validations_passed` | 是否通过校验 |
| `optimized` | 是否经过优化 |
| `generated_at` | 生成时间 |


## 使用示例

```bash
# 从 Markdown 文件生成代码
python -m markflow.cli.commands execute code_gen_from_md md_file="./requirements.md"

# 指定模型
python -m markflow.cli.commands execute code_gen_from_md md_file="./requirements.md" model="qwen2.5:3b"

# 分步生成模式（适合复杂需求）
python -m markflow.cli.commands execute code_gen_from_md md_file="./requirements.md" mode="step" model="qwen2.5:3b"

# 直接传入 Markdown 内容
python -m markflow.cli.commands execute code_gen_from_md md_content="# 项目名称\n\n## 需求\n..."
```



### 字段说明

| 字段 | 说明 |
|------|------|
| `# 标题` | 项目名称 |
| `## 语言` | 目标语言 (python/javascript/java/go/rust/...) |
| `## 需求` | 需求列表，每个 `###` 为一个功能点 |
| `## 代码示例` | 可选的参考代码 |


## 输出示例

### 生成代码

```python
"""
文件处理工具 - 文件读写和统计
"""

import os
from pathlib import Path
from typing import Optional


def read_file(file_path: str, encoding: str = "utf-8") -> Optional[str]:
    """
    读取文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认 utf-8

    Returns:
        文件内容，失败返回 None
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {file_path}")
        return None
    except Exception as e:
        print(f"错误: 读取文件失败 - {e}")
        return None


def write_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认 utf-8

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        return False


def count_words(text: str) -> int:
    """统计文本中的单词数"""
    return len(text.split())


if __name__ == "__main__":
    # 示例用法
    content = read_file("example.txt")
    if content:
        print(f"文件内容: {content[:100]}...")
        print(f"单词数: {count_words(content)}")		
```

## 质量报告

```json
{
  "file": "文件处理工具_20260825_120000.py",
  "language": "python",
  "quality_score": 85,
  "validations": {
    "passed": true,
    "checks": [
      {"name": "syntax", "status": "pass", "message": "语法检查通过"},
      {"name": "imports", "status": "pass", "message": "检测到 3 个导入语句"},
      {"name": "docstrings", "status": "pass", "message": "文档字符串检查通过"},
      {"name": "naming", "status": "pass", "message": "命名检查通过"}
    ],
    "errors": [],
    "warnings": []
  },
  "has_tests": true,
  "optimized": true
}
```

## 生成模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `full` | 一次性生成完整代码 | 小型需求（< 5 个功能点） |
| `step` | 按需求逐个生成，最后合并 | 复杂需求（> 5 个功能点） |


##  依赖安装

```bash
# 基础依赖
pip install requests

# 代码格式化 (Python)
pip install black

# 代码检查 (Python)
pip install pylint
```


## 输出位置

生成的报告保存在 `skills/code_gen_from_md/output/` 目录下。

| 路径 | 说明 |
|------|------|
| `skills/code_gen_from_md/output/{title}_{timestamp}.{ext}` | 生成的代码文件 |
| `skills/code_gen_from_md/output/{title}_{timestamp}_quality.json` | 质量报告 |


## 适用场景

- **快速原型开发** - 从需求文档生成代码原型
- **代码脚手架** - 生成项目基础代码结构
- **学习示例生成** - 根据需求生成教学示例
- **代码标准化** - 确保生成的代码符合规范


## 相关技能

| 技能 | 说明 |
|------|------|
| `doc_generator` | 从代码生成 API 文档 |
| `code_relations_presents` | 代码关系分析报告 |

---

*文档版本: 1.0.0 | 生成于 2026-08-25*