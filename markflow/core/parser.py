# markflow/core/parser.py
"""
Markdown解析器 - 从Markdown提取技能规格
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
            "version": self.version
        }


class MarkdownParser:
    """Markdown解析器"""
    
    def __init__(self):
        self.section_patterns = {
            'description': r'##\s*(?:描述|Description)',
            'purpose': r'##\s*(?:目的|Purpose)',
            'inputs': r'##\s*(?:输入|Inputs|参数|Parameters)',
            'outputs': r'##\s*(?:输出|Outputs|返回|Returns)',
            'steps': r'##\s*(?:步骤|Steps|流程|Workflow)',
            'dependencies': r'##\s*(?:依赖|Dependencies|安装|Install)',
            'examples': r'##\s*(?:示例|Examples|使用|Usage)',
            'config': r'##\s*(?:配置|Config|设置|Settings)',
            'tags': r'##\s*(?:标签|Tags|分类|Categories)'
        }
    
    def parse(self, content: str) -> SkillSpec:
        """解析Markdown内容"""
        lines = content.split('\n')
        
        # 提取标题
        name = self._extract_title(lines)
        
        # 提取各章节
        sections = self._extract_sections(lines)
        
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
            tags=self._parse_tags(self._extract_section_content(sections, 'tags'))
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
            # 检查是否匹配某个章节标题
            matched = False
            for key, pattern in self.section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    current_section = key
                    matched = True
                    break
            
            if matched:
                continue
            
            # 如果当前在某个章节中
            if current_section and line.strip():
                # 检查是否是新的章节
                if line.startswith('##'):
                    current_section = None
                    continue
                sections[current_section] += line + '\n'
        
        return sections
    
    def _extract_section_content(self, sections: Dict[str, str], key: str) -> str:
        """提取章节内容"""
        content = sections.get(key, '').strip()
        # 移除代码块标记
        content = re.sub(r'```.*?\n', '', content)
        content = re.sub(r'```', '', content)
        return content.strip()
        

    def _parse_inputs(self, content: str) -> List[Dict[str, str]]:
        """解析输入参数"""
        inputs = []
        if not content:
            return inputs
        
        # 按行分割
        lines = content.split('\n')
        
        # 遍历每一行
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配格式: - name: type: description
            pattern = r'^-\s*(\w+)\s*[:：]\s*(\w+)\s*[:：]\s*(.+)'
            match = re.match(pattern, line)
            if match:
                name = match.group(1)
                type_str = match.group(2)
                description = match.group(3).strip()
                
                # 检查是否可选
                is_optional = ('可选' in description or 
                              'optional' in description.lower() or
                              '默认' in description)
                
                inputs.append({
                    'name': name,
                    'type': type_str,
                    'description': description,
                    'required': not is_optional
                })
                continue
            
            # 匹配格式: - name: description (不带类型)
            pattern2 = r'^-\s*(\w+)\s*[:：]\s*(.+)'
            match = re.match(pattern2, line)
            if match:
                name = match.group(1)
                description = match.group(2).strip()
                
                is_optional = ('可选' in description or 
                              'optional' in description.lower() or
                              '默认' in description)
                
                inputs.append({
                    'name': name,
                    'type': 'string',
                    'description': description,
                    'required': not is_optional
                })
        
        return inputs
    

    def _parse_outputs(self, content: str) -> List[Dict[str, str]]:
        """解析输出"""
        outputs = []
        if not content:
            return outputs
        
        pattern = r'-\s*(\w+)\s*[:：]\s*(.+)'
        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                outputs.append({
                    'name': match.group(1),
                    'description': match.group(2).strip()
                })
        
        return outputs
    
    def _parse_steps(self, content: str) -> List[str]:
        """解析步骤"""
        steps = []
        if not content:
            return steps
        
        # 匹配数字列表或项目符号
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 数字列表: 1. 步骤
            match = re.match(r'^\d+\.\s*(.+)', line)
            if match:
                steps.append(match.group(1).strip())
                continue
            
            # 项目符号: - 步骤
            match = re.match(r'^[-*]\s*(.+)', line)
            if match:
                steps.append(match.group(1).strip())
        
        return steps
    
    def _parse_dependencies(self, content: str) -> List[str]:
        """解析依赖"""
        deps = []
        if not content:
            return deps
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 提取包名
            match = re.match(r'[-*]\s*([a-zA-Z0-9_\-]+)', line)
            if match:
                deps.append(match.group(1))
            else:
                # 尝试直接匹配
                match = re.search(r'([a-zA-Z0-9_\-]+)', line)
                if match:
                    deps.append(match.group(1))
        
        return deps
    
    def _parse_examples(self, content: str) -> List[str]:
        """解析示例"""
        examples = []
        if not content:
            return examples
        
        # 提取代码块
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
            
            # 解析键值对
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 尝试解析值类型
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
            
            # 匹配标签: - tag1, tag2, tag3
            if line.startswith('-'):
                line = line[1:].strip()
            
            # 按逗号或空格分割
            for tag in re.split(r'[,，\s]+', line):
                tag = tag.strip()
                if tag:
                    tags.append(tag)
        
        return tags