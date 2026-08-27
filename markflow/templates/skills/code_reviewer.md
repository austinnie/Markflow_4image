# CodeReviewer

## 描述
AI 代码审查，发现问题和安全风险

## 输入
- code_path: string: 代码文件或目录路径 (必填)
- language: string: 编程语言 (python/js/go) (可选)
- review_level: string: 审查深度 (basic/deep) (可选)
- focus: string: 审查重点 (security/performance/style) (可选)

## 输出
- issues: 发现的问题列表
- suggestions: 改进建议
- security_risks: 安全风险警告
- code_score: 代码质量评分

## 依赖
- pylint
- flake8
- radon
- ollama

## 状态
待实现