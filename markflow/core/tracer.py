# markflow/core/tracer.py
"""
需求追溯模块 - 建立需求到代码的映射
"""

import re
from typing import Dict, List, Set, Any


class RequirementTracer:
    """需求追溯器"""
    
    def __init__(self):
        self.trace_map: Dict[str, Dict] = {}
    
    def trace(self, spec, code: str) -> Dict[str, Any]:
        """
        追溯需求到代码的映射
        
        Args:
            spec: SkillSpec 对象
            code: 生成的代码
            
        Returns:
            追溯结果
        """
        result = {
            "total_requirements": 0,
            "implemented": 0,
            "coverage": 0.0,
            "details": {},
            "unimplemented": []
        }
        
        # 收集所有需求（从 features + steps 中提取）
        requirements = []
        if hasattr(spec, 'features') and spec.features:
            requirements.extend(spec.features)
        if hasattr(spec, 'steps') and spec.steps:
            requirements.extend(spec.steps)
        
        # 去重
        requirements = list(dict.fromkeys(requirements))
        result["total_requirements"] = len(requirements)
        
        for req in requirements:
            trace_detail = self._trace_single(req, code)
            result["details"][req] = trace_detail
            
            if trace_detail["implemented"]:
                result["implemented"] += 1
            else:
                result["unimplemented"].append(req)
        
        result["coverage"] = result["implemented"] / max(1, result["total_requirements"])
        
        return result
    
    def _trace_single(self, requirement: str, code: str) -> Dict:
        """追溯单个需求"""
        keywords = self._extract_keywords(requirement)
        
        found_locations = []
        lines = code.split('\n')
        
        for keyword in keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(code)
            
            for match in matches:
                char_pos = match.start()
                line_num = code[:char_pos].count('\n') + 1
                found_locations.append({
                    "keyword": keyword,
                    "line": line_num,
                    "context": lines[line_num-1].strip() if line_num <= len(lines) else ""
                })
        
        # 去重
        unique_locations = []
        seen = set()
        for loc in found_locations:
            key = (loc["line"], loc["keyword"])
            if key not in seen:
                seen.add(key)
                unique_locations.append(loc)
        
        return {
            "implemented": len(unique_locations) > 0,
            "matches": unique_locations,
            "keywords": keywords
        }
    
    def _extract_keywords(self, requirement: str) -> List[str]:
        """从需求中提取关键词"""
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '至', '把', '让', '被', '从', '到', '对', '于', '与', '或', '等'}
        
        # 提取中文词
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', requirement)
        # 提取英文词
        english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', requirement)
        
        keywords = []
        for word in chinese_words + english_words:
            if word not in stopwords and len(word) > 1:
                keywords.append(word)
        
        # 如果关键词太少，尝试拆分
        if len(keywords) < 2:
            parts = re.split(r'[、，,，.。\s]+', requirement)
            for part in parts:
                part = part.strip()
                if part and len(part) > 1 and part not in stopwords:
                    keywords.append(part)
        
        return list(dict.fromkeys(keywords))
    
    def generate_report(self, trace_result: Dict) -> str:
        """生成追溯报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("📋 需求追溯报告")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"总需求数: {trace_result['total_requirements']}")
        lines.append(f"已实现: {trace_result['implemented']}")
        lines.append(f"未实现: {len(trace_result['unimplemented'])}")
        lines.append(f"覆盖率: {trace_result['coverage']*100:.1f}%")
        lines.append("")
        
        if trace_result['unimplemented']:
            lines.append("❌ 未实现的需求:")
            for req in trace_result['unimplemented']:
                lines.append(f"  - {req}")
            lines.append("")
        
        lines.append("📝 详细追溯:")
        for req, detail in trace_result['details'].items():
            status = "✅" if detail['implemented'] else "❌"
            lines.append(f"  {status} {req}")
            if detail['matches']:
                for match in detail['matches'][:3]:
                    lines.append(f"      → 行 {match['line']}: {match['context'][:50]}")
            lines.append("")
        
        lines.append("=" * 60)
        return '\n'.join(lines)