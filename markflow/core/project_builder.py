# markflow/core/project_builder.py
"""
项目结构生成器 - 生成完整的技能目录
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class ProjectBuilder:
    """项目结构生成器"""
    
    def __init__(self):
        self.gitignore_template = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Output
output/
logs/
"""
    
    def generate_project(self, spec, code: str, tests: str = "", 
                         quality_result: Dict = None, trace_result: Dict = None) -> Dict[str, str]:
        """
        生成完整的技能项目文件
        
        Args:
            spec: SkillSpec 对象
            code: 技能代码
            tests: 测试代码
            quality_result: 质量检查结果
            trace_result: 追溯结果
            
        Returns:
            Dict[str, str]: 文件路径 -> 文件内容
        """
        skill_name = spec.name.lower().replace(' ', '_')
        class_name = self._generate_class_name(spec.name)
        
        files = {}
        
        # 1. skill.py
        files[f"{skill_name}/skill.py"] = code
        
        # 2. __init__.py
        files[f"{skill_name}/__init__.py"] = self._generate_init(skill_name, class_name)
        
        # 3. meta.json
        files[f"{skill_name}/meta.json"] = self._generate_meta(spec, quality_result, trace_result)
        
        # 4. README.md
        files[f"{skill_name}/README.md"] = self._generate_readme(spec)
        
        # 5. requirements.txt
        files[f"{skill_name}/requirements.txt"] = self._generate_requirements(spec.dependencies)
        
        # 6. .gitignore
        files[f"{skill_name}/.gitignore"] = self.gitignore_template
        
        # 7. tests/test_skill.py
        if tests:
            files[f"{skill_name}/tests/test_skill.py"] = tests
        else:
            files[f"{skill_name}/tests/test_skill.py"] = self._generate_empty_test(skill_name, class_name)
        
        # 8. tests/__init__.py
        files[f"{skill_name}/tests/__init__.py"] = '"""测试模块"""\n'
        
        # 9. output/.gitkeep
        files[f"{skill_name}/output/.gitkeep"] = "# 输出目录\n"
        
        # 10. config.yaml (如果有配置)
        if spec.config:
            files[f"{skill_name}/config.yaml"] = self._generate_config(spec.config)
        
        return files
    
    def _generate_class_name(self, name: str) -> str:
        """生成类名"""
        words = name.replace('-', '_').replace(' ', '_').split('_')
        return ''.join(word.capitalize() for word in words)
    
    def _generate_init(self, skill_name: str, class_name: str) -> str:
        """生成 __init__.py"""
        return f'''"""
{skill_name} 技能包
"""

from .skill import {class_name}

__all__ = ["{class_name}"]
'''
    
    def _generate_meta(self, spec, quality_result: Dict = None, trace_result: Dict = None) -> str:
        """生成 meta.json"""
        meta = {
            "name": spec.name,
            "display_name": spec.name,
            "description": spec.description,
            "version": spec.version,
            "inputs": spec.inputs,
            "outputs": spec.outputs,
            "dependencies": spec.dependencies,
            "tags": spec.tags,
            "features": spec.features if hasattr(spec, 'features') else [],
            "generated_at": datetime.now().isoformat()
        }
        
        if quality_result:
            meta["quality"] = {
                "score": quality_result.get('score', 0),
                "passed": quality_result.get('passed', False),
                "checks_count": len(quality_result.get('checks', [])),
                "errors_count": len(quality_result.get('errors', []))
            }
        
        if trace_result:
            meta["trace"] = {
                "coverage": trace_result.get('coverage', 0),
                "total_requirements": trace_result.get('total_requirements', 0),
                "implemented": trace_result.get('implemented', 0)
            }
        
        return json.dumps(meta, ensure_ascii=False, indent=2)
    
    def _generate_readme(self, spec) -> str:
        """生成 README.md"""
        lines = []
        lines.append(f"# {spec.name}")
        lines.append("")
        lines.append(f"> {spec.description}")
        lines.append("")
        lines.append("## 描述")
        lines.append("")
        lines.append(spec.description)
        lines.append("")
        
        if hasattr(spec, 'features') and spec.features:
            lines.append("## 核心功能")
            lines.append("")
            for i, feature in enumerate(spec.features, 1):
                lines.append(f"{i}. {feature}")
            lines.append("")
        
        if spec.inputs:
            lines.append("## 输入参数")
            lines.append("")
            lines.append("| 参数 | 类型 | 必填 | 默认值 | 描述 |")
            lines.append("|------|------|------|--------|------|")
            for inp in spec.inputs:
                required = "是" if inp.get('required', False) else "否"
                default = inp.get('default', '-')
                lines.append(f"| `{inp['name']}` | {inp.get('type', 'string')} | {required} | {default} | {inp.get('description', '')} |")
            lines.append("")
        
        if spec.outputs:
            lines.append("## 输出")
            lines.append("")
            lines.append("| 字段 | 说明 |")
            lines.append("|------|------|")
            for out in spec.outputs:
                lines.append(f"| `{out['name']}` | {out.get('description', '')} |")
            lines.append("")
        
        lines.append("## 使用方法")
        lines.append("")
        lines.append("```bash")
        lines.append(f"python -m markflow.cli.commands execute {spec.name} [参数]")
        lines.append("```")
        lines.append("")
        
        lines.append("## 依赖安装")
        lines.append("")
        if spec.dependencies:
            lines.append("```bash")
            for dep in spec.dependencies:
                lines.append(f"pip install {dep}")
            lines.append("```")
        else:
            lines.append("无特殊依赖")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append(f"*文档生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)
    
    def _generate_requirements(self, dependencies: List[str]) -> str:
        """生成 requirements.txt"""
        if not dependencies:
            return "# 无依赖\n"
        
        lines = []
        for dep in dependencies:
            lines.append(dep)
        return '\n'.join(lines) + '\n'
    
    def _generate_empty_test(self, skill_name: str, class_name: str) -> str:
        """生成空测试文件"""
        return f'''"""
{skill_name} 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.{skill_name}.skill import {class_name}


class Test{class_name}(unittest.TestCase):
    """{class_name} 测试类"""
    
    def setUp(self):
        self.skill = {class_name}()
    
    def test_skill_initialization(self):
        """测试技能初始化"""
        self.assertEqual(self.skill.name, "{skill_name}")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()
'''
    
    def _generate_config(self, config: Dict) -> str:
        """生成 config.yaml"""
        import yaml
        return yaml.dump(config, allow_unicode=True, default_flow_style=False)
    
    def save_project(self, files: Dict[str, str], base_dir: Path) -> List[Path]:
        """
        保存项目文件到磁盘
        
        Args:
            files: 文件路径 -> 文件内容
            base_dir: 基础目录
            
        Returns:
            List[Path]: 保存的文件路径列表
        """
        saved = []
        for file_path, content in files.items():
            full_path = base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            saved.append(full_path)
        return saved