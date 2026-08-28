# markflow/core/quality.py
"""
代码质量检查模块 - 从 code_gen_from_md 迁移
"""

import ast
import re
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False

try:
    import pylint
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False


class CodeQualityChecker:
    """
    代码质量检查器
    提供语法检查、导入检查、文档字符串检查、命名检查等功能
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.review_dimensions = [
            "功能完整性",
            "代码可读性",
            "性能效率",
            "安全性",
            "可维护性",
            "测试覆盖",
            "错误处理",
            "文档完整",
        ]
        
    @property
    def ollama_url(self) -> str:
        """获取 Ollama URL"""
        return self.config.get('ollama_url', 'http://localhost:11434')
        
    # ==================== 语法检查 ====================
    
    def validate_python_syntax(self, code: str) -> Tuple[bool, str]:
        """检查 Python 语法"""
        if not code.strip():
            return False, "代码为空"
        
        try:
            ast.parse(code)
            return True, "语法检查通过"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def validate_imports(self, code: str, language: str = "python") -> Tuple[bool, str]:
        """检查导入语句"""
        if language != "python":
            return True, f"非 Python 语言，跳过导入检查"
        
        import_pattern = r'^(?:from|import)\s+\S+'
        imports = re.findall(import_pattern, code, re.MULTILINE)
        
        if not imports:
            return False, "没有检测到 import 语句，代码可能不完整"
        
        common_imports = ['os', 'sys', 'json', 're', 'pathlib', 'typing', 'datetime']
        found_common = [imp for imp in common_imports if any(imp in imp_str for imp_str in imports)]
        
        return True, f"检测到 {len(imports)} 个导入语句，其中 {len(found_common)} 个标准库"
    
    def validate_docstrings(self, code: str, language: str = "python") -> Tuple[bool, str]:
        """检查文档字符串"""
        if language != "python":
            return True, f"非 Python 语言，跳过文档检查"
        
        func_pattern = r'def\s+\w+\s*\([^)]*\)\s*->?[^:]*:\s*\n\s*"""[^"]*"""'
        funcs_with_doc = re.findall(func_pattern, code, re.DOTALL)
        funcs_total = len(re.findall(r'def\s+\w+\s*\(', code))
        
        class_pattern = r'class\s+\w+[^:]*:\s*\n\s*"""[^"]*"""'
        classes_with_doc = re.findall(class_pattern, code, re.DOTALL)
        classes_total = len(re.findall(r'class\s+\w+', code))
        
        issues = []
        if funcs_total > 0 and len(funcs_with_doc) < funcs_total:
            issues.append(f"有 {funcs_total - len(funcs_with_doc)} 个函数缺少 docstring")
        if classes_total > 0 and len(classes_with_doc) < classes_total:
            issues.append(f"有 {classes_total - len(classes_with_doc)} 个类缺少 docstring")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, f"文档字符串检查通过 (函数: {len(funcs_with_doc)}/{funcs_total}, 类: {len(classes_with_doc)}/{classes_total})"
    
    def validate_naming(self, code: str, language: str = "python") -> Tuple[bool, str]:
        """检查命名规范"""
        if language != "python":
            return True, f"非 Python 语言，跳过命名检查"
        
        issues = []
        
        class_pattern = r'class\s+([a-z][a-zA-Z0-9_]*)'
        invalid_classes = re.findall(class_pattern, code)
        if invalid_classes:
            issues.append(f"类名不符合 PascalCase: {', '.join(invalid_classes[:3])}")
        
        func_pattern = r'def\s+([A-Z][a-zA-Z0-9_]*)'
        invalid_funcs = re.findall(func_pattern, code)
        if invalid_funcs:
            issues.append(f"函数名不符合 snake_case: {', '.join(invalid_funcs[:3])}")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "命名检查通过"
    
    def validate_type_hints(self, code: str, language: str = "python") -> Tuple[bool, str]:
        """检查类型注解"""
        if language != "python":
            return True, f"非 Python 语言，跳过类型注解检查"
        
        func_without_hints = re.findall(r'def\s+\w+\s*\([^:)]*\)\s*:', code)
        func_with_hints = re.findall(r'def\s+\w+\s*\([^)]*:\s*\w+', code)
        
        total = len(func_without_hints) + len(func_with_hints)
        if total > 0:
            ratio = len(func_with_hints) / total
            if ratio < 0.3:
                return False, f"类型注解覆盖率较低: {int(ratio*100)}% ({len(func_with_hints)}/{total})"
            return True, f"类型注解覆盖率: {int(ratio*100)}% ({len(func_with_hints)}/{total})"
        
        return True, "未检测到函数定义"
    
    # ==================== 完整验证 ====================
    
    def validate_all(self, code: str, language: str = "python") -> Dict:
        """执行所有验证检查"""
        results = {
            "passed": True,
            "checks": [],
            "errors": [],
            "warnings": [],
            "score": 100,
        }
        
        checks = [
            ("syntax", self.validate_python_syntax if language == "python" else None),
            ("imports", self.validate_imports),
            ("docstrings", self.validate_docstrings),
            ("naming", self.validate_naming),
            ("type_hints", self.validate_type_hints),
        ]
        
        for name, func in checks:
            if func is None:
                continue
            
            try:
                passed, message = func(code, language)
                if passed:
                    results["checks"].append({"name": name, "status": "pass", "message": message})
                else:
                    if name in ["docstrings", "type_hints"]:
                        results["warnings"].append({"name": name, "message": message})
                        results["score"] -= 5
                    else:
                        results["errors"].append({"name": name, "message": message})
                        results["passed"] = False
                        results["score"] -= 20
            except Exception as e:
                results["checks"].append({"name": name, "status": "error", "message": str(e)})
                results["score"] -= 10
        
        results["score"] = max(0, min(100, results["score"]))
        
        return results
    
    # ==================== 代码格式化 ====================
    
    def format_code(self, code: str, language: str = "python") -> str:
        """格式化代码"""
        if language == "python" and BLACK_AVAILABLE:
            try:
                import black
                mode = black.Mode()
                return black.format_str(code, mode=mode)
            except Exception as e:
                logger.warning(f"Black 格式化失败: {e}")
                return code
        return code
    
    # ==================== 代码统计 ====================
    
    def analyze_code_stats(self, code: str, language: str = "python") -> Dict:
        """分析代码统计信息"""
        lines = code.split('\n')
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = 0
        code_lines = 0
        
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    comment_lines += 1
                    continue
                in_docstring = not in_docstring
                comment_lines += 1
                continue
            if in_docstring:
                comment_lines += 1
                continue
            if stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        functions = len(re.findall(r'def\s+\w+\s*\(', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "functions": functions,
            "classes": classes,
            "comment_ratio": comment_lines / max(1, code_lines + comment_lines),
        }
    
    # ==================== AI 审查 (需要 Ollama) ====================
    
    def review_code_with_ollama(self, code: str, language: str = "python", 
                                ollama_url: str = "http://localhost:11434",
                                model: str = "qwen2.5:7b") -> Dict:
        """使用 Ollama 进行 AI 代码审查"""
        import requests
        
        print(f"🔍 调用 Ollama: {ollama_url}, 模型: {model}")
        
        prompt = self._build_review_prompt(code, language)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2048  # 减少输出长度，加快响应
            }
        }
        
        try:
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=600  # 增加到 300 秒
            )
            print(f"📡 响应状态码: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            review_text = data.get("response", "").strip()
            
            if not review_text:
                return {
                    "score": 0,
                    "dimensions": {},
                    "issues": ["Ollama 返回空响应"],
                    "suggestions": [],
                    "summary": "无法完成 AI 审查"
                }
            
            return self._parse_review_response(review_text)
        except requests.exceptions.Timeout:
            logger.error("AI 审查超时")
            return {
                "score": 0,
                "dimensions": {},
                "issues": ["审查超时，请检查 Ollama 服务"],
                "suggestions": [],
                "summary": "无法完成 AI 审查"
            }
        except Exception as e:
            logger.error(f"AI 审查失败: {e}")
            return {
                "score": 0,
                "dimensions": {},
                "issues": [f"审查失败: {e}"],
                "suggestions": [],
                "summary": "无法完成 AI 审查"
            }
        
    def _build_review_prompt(self, code: str, language: str) -> str:
        """构建审查 Prompt - 精简版"""
        # 只取代码的前 2000 字符进行审查
        code_preview = code[:2000]
        if len(code) > 2000:
            code_preview += "\n... (代码已截断)"
        
        prompt = '请对以下 ' + language + ' 代码进行代码审查：\n\n'
        prompt += '代码：\n'
        prompt += '```' + language + '\n'
        prompt += code_preview + '\n'
        prompt += '```\n\n'
        prompt += '请从以下维度审查：\n'
        prompt += '1. 功能完整性\n'
        prompt += '2. 代码可读性\n'
        prompt += '3. 性能效率\n'
        prompt += '4. 安全性\n'
        prompt += '5. 可维护性\n'
        prompt += '6. 错误处理\n'
        prompt += '7. 文档完整\n\n'
        prompt += '请输出 JSON 格式的审查结果：\n'
        prompt += '{\n'
        prompt += '    "score": 0-100,\n'
        prompt += '    "dimensions": {\n'
        prompt += '        "功能完整性": 0-10,\n'
        prompt += '        "代码可读性": 0-10,\n'
        prompt += '        "性能效率": 0-10,\n'
        prompt += '        "安全性": 0-10,\n'
        prompt += '        "可维护性": 0-10,\n'
        prompt += '        "错误处理": 0-10,\n'
        prompt += '        "文档完整": 0-10\n'
        prompt += '    },\n'
        prompt += '    "issues": ["问题1", "问题2"],\n'
        prompt += '    "suggestions": ["建议1", "建议2"],\n'
        prompt += '    "summary": "总结"\n'
        prompt += '}'
        
        return prompt
    
    def _parse_review_response(self, response: str) -> Dict:
        """解析 AI 审查响应"""
        import json
        
        try:
            # 尝试提取 JSON 代码块
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            review = json.loads(response)
            return {
                "score": review.get("score", 0),
                "dimensions": review.get("dimensions", {}),
                "issues": review.get("issues", []),
                "suggestions": review.get("suggestions", []),
                "summary": review.get("summary", ""),
            }
        except json.JSONDecodeError:
            # 尝试提取分数
            score_match = re.search(r'"score":\s*(\d+)', response)
            score = int(score_match.group(1)) if score_match else 0
            
            issues = re.findall(r'"issues":\s*\[([^\]]+)\]', response, re.DOTALL)
            issues_list = []
            if issues:
                issues_list = [i.strip('"\'') for i in re.findall(r'"([^"]+)"', issues[0])]
            
            return {
                "score": score,
                "dimensions": {},
                "issues": issues_list if issues_list else ["无法解析审查结果"],
                "suggestions": [],
                "summary": response[:200] + "..." if len(response) > 200 else response,
            }
        
    def __repr__(self):
        return f"<CodeQualityChecker(black={BLACK_AVAILABLE}, pylint={PYLINT_AVAILABLE})>"