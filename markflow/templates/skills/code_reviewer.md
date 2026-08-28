# code_reviewer

> AI 代码审查，发现问题和安全风险

## 技能描述

使用 AI 对代码进行多维度审查，发现问题、安全风险和性能瓶颈，提供改进建议

## 核心功能

1. 代码质量检查 - 检查代码规范、可读性和可维护性
2. 安全漏洞扫描 - 识别潜在的安全风险
3. 性能分析 - 发现性能瓶颈和优化机会
4. AI 改进建议 - 基于 AI 提供代码改进建议
5. 质量评分 - 生成代码质量评分报告

## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| code_path | string | 是 | - | 代码文件或目录路径 |
| language | string | 否 | python | 编程语言 (python/js/go) |
| review_level | string | 否 | basic | 审查深度 (basic/deep) |
| focus | string | 否 | security | 审查重点 (security/performance/style) |

## 输出

| 字段 | 说明 |
|------|------|
| issues | 发现的问题列表 |
| suggestions | 改进建议 |
| security_risks | 安全风险警告 |
| code_score | 代码质量评分 (0-100) |

## 步骤

1. 验证输入参数
2. 扫描代码文件
3. 执行静态代码分析
4. 执行安全扫描
5. 生成 AI 审查报告
6. 返回审查结果

## 依赖

- pylint
- flake8
- radon
- ollama

## 示例

```python
reviewer = CodeReviewer()
result = reviewer.execute(
    code_path="./markflow",
    language="python",
    review_level="deep",
    focus="security"
)
print(f"评分: {result['code_score']}/100")
print(f"问题: {len(result['issues'])} 个")
```

## 使用示例
```bash
python -m markflow.cli.commands execute code_reviewer code_path="./markflow"

python -m markflow.cli.commands execute code_reviewer code_path="./markflow" review_level="deep"

python -m markflow.cli.commands execute code_reviewer code_path="./markflow" focus="security"
```