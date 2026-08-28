# markflow/core/parser.py
"""
Markdown解析器 - 从Markdown提取技能规格（增强版）
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class SkillSpec:
    """技能规格"""
    name: str
    description: str = ""
    purpose: str = ""
    inputs: List[Dict[str, str]] = field(default_factory=list)
    outputs: List[Dict[str, str]] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "examples": self.examples,
            "config": self.config,
            "tags": self.tags,
            "version": self.version,
            "features": self.features,
        }


class MarkdownParser:
    """Markdown解析器"""
    
    def __init__(self):
        self.section_patterns = {
            'description': r'##\s*(?:描述|Description|技能描述)',
            'features': r'#{2,3}\s*(?:核心功能|功能|Core Features|Features|功能特性)',
            'purpose': r'##\s*(?:目的|Purpose)',
            'inputs': r'##\s*(?:输入|Inputs|参数|Parameters)',
            'outputs': r'##\s*(?:输出|Outputs|返回|Returns)',
            'steps': r'##\s*(?:步骤|Steps|流程|Workflow)',
            'dependencies': r'##\s*(?:依赖|Dependencies|安装|Install)',
            'examples': r'##\s*(?:示例|Examples|使用|Usage)',
            'config': r'##\s*(?:配置|Config|设置|Settings)',
            'tags': r'##\s*(?:标签|Tags|分类|Categories)',            
        }
    
    def parse(self, content: str) -> SkillSpec:
        """解析Markdown内容"""
        lines = content.split('\n')
        
        name = self._extract_title(lines)
        sections = self._extract_sections(lines)
        
        features_content = self._extract_section_content(sections, 'features')
        
        return SkillSpec(
            name=name,
            description=self._extract_section_content(sections, 'description'),
            purpose=self._extract_section_content(sections, 'purpose'),
            inputs=self._parse_inputs(self._extract_section_content(sections, 'inputs')),
            outputs=self._parse_outputs(self._extract_section_content(sections, 'outputs')),
            steps=self._parse_steps(self._extract_section_content(sections, 'steps')),
            dependencies=self._parse_dependencies(self._extract_section_content(sections, 'dependencies')),
            examples=self._parse_examples(self._extract_section_content(sections, 'examples')),
            config=self._parse_config(self._extract_section_content(sections, 'config')),
            tags=self._parse_tags(self._extract_section_content(sections, 'tags')),
            features=self._parse_features(features_content),
        )
    
    def parse_file(self, file_path: Path) -> SkillSpec:
        """从文件解析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)
    
    def _extract_title(self, lines: List[str]) -> str:
        """提取标题"""
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('#') and not line.startswith('##'):
                return line[1:].strip()
        return "UnnamedSkill"
    
    def _extract_sections(self, lines: List[str]) -> Dict[str, str]:
        """提取所有章节"""
        sections = {key: "" for key in self.section_patterns}
        current_section = None
        
        for line in lines:
            matched = False
            for key, pattern in self.section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    current_section = key
                    matched = True
                    break
            
            if matched:
                continue
            
            if current_section and line.strip():
                if line.startswith('##'):
                    current_section = None
                    continue
                sections[current_section] += line + '\n'
        
        return sections
    
    def _extract_section_content(self, sections: Dict[str, str], key: str) -> str:
        """提取章节内容"""
        content = sections.get(key, '').strip()
        # 只有 dependencies 和 examples 需要移除代码块标记
        if key in ['dependencies', 'examples']:
            content = re.sub(r'```.*?\n', '', content)
            content = re.sub(r'```', '', content)
        return content.strip()
    
    # ==================== 辅助方法 ====================
    
    def _clean_name(self, name: str) -> str:
        """清理名称，移除反引号和多余空格"""
        if not name:
            return ''
        name = name.strip()
        if name.startswith('`') and name.endswith('`'):
            name = name[1:-1]
        if (name.startswith('"') and name.endswith('"')) or \
           (name.startswith("'") and name.endswith("'")):
            name = name[1:-1]
        return name.strip()
    
    # ==================== 表格解析 ====================
    
    def _parse_table(self, content: str) -> List[Dict[str, str]]:
        """解析 Markdown 表格"""
        lines = content.strip().split('\n')
        if len(lines) < 3:
            return []
        
        if not re.match(r'^[\s\|:-]+$', lines[1].strip()):
            return []
        
        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        if not headers:
            return []
        
        rows = []
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^[\s\|:-]+$', line):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) >= len(headers):
                row = {}
                for i, header in enumerate(headers):
                    row[header] = cells[i] if i < len(cells) else ''
                rows.append(row)
        
        return rows
    
    # ==================== 解析方法 ====================
    
    def _parse_inputs(self, content: str) -> List[Dict[str, str]]:
        """解析输入参数"""
        inputs = []
        if not content:
            return inputs
        
        table_rows = self._parse_table(content)
        if table_rows:
            for row in table_rows:
                name = row.get('参数') or row.get('name') or row.get('Name') or ''
                name = self._clean_name(name)
                if not name:
                    continue
                # 跳过分隔行
                if name in ['------', '---'] or name.startswith('---'):
                    continue
                
                type_str = row.get('类型') or row.get('type') or row.get('Type') or 'string'
                type_str = type_str.strip()
                
                required_str = row.get('必填') or row.get('required') or row.get('Required') or ''
                required_str = required_str.strip()
                
                default = row.get('默认值') or row.get('default') or row.get('Default') or ''
                default = default.strip()
                if default == '-' or default == '':
                    default = ''
                
                description = row.get('描述') or row.get('description') or row.get('Description') or ''
                description = description.strip()
                
                is_required = required_str.lower() in ['是', 'true', 'yes', '必填']
                
                inputs.append({
                    'name': name,
                    'type': type_str,
                    'description': description,
                    'required': is_required,
                    'default': default
                })
            return inputs
        
        # 列表格式
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            pattern = r'^-\s*(\w+)\s*[:：]\s*(\w+)\s*[:：]\s*(.+)'
            match = re.match(pattern, line)
            if match:
                name = self._clean_name(match.group(1))
                type_str = match.group(2).strip()
                description = match.group(3).strip()
                is_optional = ('可选' in description or 'optional' in description.lower() or '默认' in description)
                inputs.append({
                    'name': name,
                    'type': type_str,
                    'description': description,
                    'required': not is_optional,
                    'default': ''
                })
                continue
            
            pattern2 = r'^-\s*(\w+)\s*[:：]\s*(.+)'
            match = re.match(pattern2, line)
            if match:
                name = self._clean_name(match.group(1))
                description = match.group(2).strip()
                is_optional = ('可选' in description or 'optional' in description.lower() or '默认' in description)
                inputs.append({
                    'name': name,
                    'type': 'string',
                    'description': description,
                    'required': not is_optional,
                    'default': ''
                })
        
        return inputs
    
    def _parse_outputs(self, content: str) -> List[Dict[str, str]]:
        """解析输出"""
        outputs = []
        if not content:
            return outputs
        
        table_rows = self._parse_table(content)
        if table_rows:
            for row in table_rows:
                name = row.get('字段') or row.get('name') or row.get('Name') or ''
                name = self._clean_name(name)
                if not name:
                    continue
                
                # 过滤无效输出
                if name.lower() in ['字段', '说明', 'name', 'description', '路径']:
                    continue
                if name in ['------', '---'] or name.startswith('---'):
                    continue
                if '/' in name or '{' in name or '.ext' in name:
                    continue
                
                description = row.get('说明') or row.get('description') or row.get('Description') or ''
                description = description.strip()
                
                outputs.append({
                    'name': name,
                    'description': description
                })
            return outputs
        
        # 列表格式...
        return outputs
    
    def _parse_features(self, content: str) -> List[str]:
        """解析核心功能列表"""
        features = []
        if not content:
            return features
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'^\d+\.\s*(.+)', line)
            if match:
                features.append(match.group(1).strip())
                continue
            
            match = re.match(r'^[-*]\s*(.+)', line)
            if match:
                features.append(match.group(1).strip())
        
        return features
    
    def _parse_steps(self, content: str) -> List[str]:
        """解析步骤"""
        steps = []
        if not content:
            return steps
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'^\d+\.\s*(.+)', line)
            if match:
                steps.append(match.group(1).strip())
                continue
            
            match = re.match(r'^[-*]\s*(.+)', line)
            if match:
                steps.append(match.group(1).strip())
        
        return steps
    
    def _parse_dependencies(self, content: str) -> List[str]:
        """解析依赖 - 从 pip install 命令中提取包名"""
        deps = []
        if not content:
            return deps
        
        # 无效依赖过滤
        invalid_deps = {
            'pip', 'python', 'python3', 'setuptools', 'wheel', 'none',
            '-r', '--upgrade', 'install', '--', '---', '------',
            'requirements', 'txt', 'freeze', 'list', 'show',
            'from', 'import', 'as', 'with', 'for', 'to', 'of', 'and',
            'a', 'an', 'the', 'is', 'are', 'was', 'were'
        }
        
        date_pattern = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}')
        version_pattern = re.compile(r'^\d+\.\d+(\.\d+)?$')
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 跳过注释行
            if line.startswith('#'):
                continue
            
            # 跳过 pip 开头的行（不是 install 命令）
            if line.startswith('pip') and 'install' not in line:
                continue
            
            # 跳过日期和版本号
            if date_pattern.match(line):
                continue
            if version_pattern.match(line):
                continue
            if re.match(r'^[-*_]{3,}$', line):
                continue
            
            # ===== 处理 pip install 命令 =====
            if 'pip install' in line:
                # 提取 pip install 后面的包名
                parts = line.split()
                for i, part in enumerate(parts):
                    # 跳过 pip, install, 和选项
                    if part in ['pip', 'install']:
                        continue
                    if part.startswith('-'):
                        continue
                    # 移除版本号后缀 (>=, ==, <, >)
                    pkg = re.sub(r'[<>=!].*$', '', part).strip()
                    pkg = re.sub(r'^#.*$', '', pkg).strip()  # 移除行尾注释
                    if pkg and pkg not in invalid_deps and not date_pattern.match(pkg):
                        if not version_pattern.match(pkg) and len(pkg) >= 2:
                            deps.append(pkg)
                continue
            
            # ===== 列表格式: - package =====
            match = re.match(r'[-*]\s*([a-zA-Z0-9_\-]+)', line)
            if match:
                pkg = match.group(1)
                if pkg and pkg not in invalid_deps and not date_pattern.match(pkg):
                    if not version_pattern.match(pkg) and len(pkg) >= 2:
                        deps.append(pkg)
                continue
            
            # ===== 普通文本中的包名 =====
            matches = re.findall(r'([a-zA-Z][a-zA-Z0-9_\-]{1,})', line)
            for pkg in matches:
                if pkg.lower() in invalid_deps:
                    continue
                if date_pattern.match(pkg):
                    continue
                if version_pattern.match(pkg):
                    continue
                if pkg.isdigit():
                    continue
                if len(pkg) < 2:
                    continue
                # 过滤常见停用词
                if pkg.lower() in invalid_deps:
                    continue
                deps.append(pkg)
        
        # 去重并过滤
        deps = [d for d in deps if d and len(d) >= 2]
        return list(dict.fromkeys(deps))
    
    def _parse_examples(self, content: str) -> List[str]:
        """解析示例"""
        examples = []
        if not content:
            return examples
        
        in_code = False
        current_example = []
        
        for line in content.split('\n'):
            if line.strip().startswith('```'):
                in_code = not in_code
                if not in_code and current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                continue
            
            if in_code:
                current_example.append(line)
        
        return examples
    
    def _parse_config(self, content: str) -> Dict[str, Any]:
        """解析配置"""
        config = {}
        if not content:
            return config
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                
                config[key] = value
        
        return config
    
    def _parse_tags(self, content: str) -> List[str]:
        """解析标签"""
        tags = []
        if not content:
            return tags
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('-'):
                line = line[1:].strip()
            
            for tag in re.split(r'[,，\s]+', line):
                tag = tag.strip()
                if tag:
                    tags.append(tag)
        
        return tags