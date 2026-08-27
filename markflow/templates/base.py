"""
模板管理器 - 管理技能模板
"""

from typing import Dict, Any, List, Optional
from pathlib import Path


class TemplateManager:
    """模板管理器"""
    
    TEMPLATES = {
        "basic": {
            "name": "基础技能",
            "description": "适用于大多数场景的基础技能模板",
            "tags": ["basic", "通用"],
            "markdown": '# {name}\n\n## 描述\n{description}\n\n## 目的\n{purpose}\n\n## 输入\n{inputs}\n\n## 输出\n{outputs}\n\n## 步骤\n{steps}\n\n## 依赖\n{dependencies}\n\n## 示例\n```python\nskill = {class_name}()\nresult = skill.execute({example_params})\n```'
        },
        "data_pipeline": {
            "name": "数据处理流水线",
            "description": "适用于ETL和数据处理场景",
            "tags": ["data", "etl", "processing"],
            "markdown": '# {name}\n\n## 描述\n{description}\n\n## 目的\n构建数据处理流水线\n\n## 输入\n- source: string: 数据源路径\n- transformations: json: 转换配置\n- output: string: 输出路径\n\n## 输出\n- data: 处理后的数据\n- pipeline_info: 流水线信息\n\n## 步骤\n1. 读取源数据\n2. 应用转换规则\n3. 数据验证\n4. 生成输出\n5. 记录日志\n\n## 依赖\n- pandas\n- numpy\n\n## 示例\n```python\npipeline = {class_name}()\nresult = pipeline.execute(\n    source="data.csv",\n    transformations=\'{"clean": true, "normalize": true}\',\n    output="processed.csv"\n)\n```'
        },
        "web_scraper": {
            "name": "网页爬虫",
            "description": "适用于网页数据采集场景",
            "tags": ["web", "scraping", "crawler"],
            "markdown": '# {name}\n\n## 描述\n{description}\n\n## 目的\n从网页采集数据\n\n## 输入\n- urls: list: 目标URL列表\n- selectors: json: CSS选择器配置\n- output: string: 输出路径\n\n## 输出\n- scraped_data: 采集的数据\n- stats: 采集统计\n\n## 步骤\n1. 设置请求头\n2. 遍历URL列表\n3. 提取数据\n4. 数据清洗\n5. 保存结果\n\n## 依赖\n- requests\n- beautifulsoup4\n\n## 示例\n```python\nscraper = {class_name}()\nresult = scraper.execute(\n    urls=["https://example.com"],\n    selectors=\'{"title": "h1", "content": ".content"}\',\n    output="data.json"\n)\n```'
        }
    }
    
    def __init__(self, template_dir: Path = None):
        self.template_dir = template_dir or Path("./templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._templates = self.TEMPLATES.copy()
        self._load_custom_templates()
    
    def _load_custom_templates(self):
        """加载自定义模板"""
        for md_file in self.template_dir.glob("*.md"):
            name = md_file.stem
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata = self._extract_metadata(content)
            self._templates[name] = {
                "name": metadata.get('name', name),
                "description": metadata.get('description', f"{name} 自定义模板"),
                "tags": metadata.get('tags', ['custom']),
                "markdown": content
            }
    
    def _extract_metadata(self, content: str) -> Dict:
        """提取元数据"""
        metadata = {}
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):
            if line.startswith('# '):
                metadata['name'] = line[2:].strip()
            elif line.startswith('## 描述') or line.startswith('## Description'):
                if i + 1 < len(lines):
                    metadata['description'] = lines[i + 1].strip()
            elif line.startswith('## 标签') or line.startswith('## Tags'):
                if i + 1 < len(lines):
                    tag_line = lines[i + 1].strip()
                    if tag_line:
                        metadata['tags'] = [t.strip() for t in tag_line.split(',')]
        return metadata
    
    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        return [
            {
                "id": name,
                "name": info["name"],
                "description": info["description"],
                "tags": info.get("tags", [])
            }
            for name, info in self._templates.items()
        ]
    
    def get_template(self, name: str) -> Optional[Dict]:
        """获取模板"""
        return self._templates.get(name)
    
    def render(self, name: str, params: Dict) -> str:
        """渲染模板"""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"模板不存在: {name}")
        
        # 使用format而不是Template，避免花括号转义问题
        markdown = template['markdown']
        
        defaults = {
            'name': 'unnamed_skill',
            'description': '技能描述',
            'purpose': '执行特定功能',
            'inputs': '- input_data: string: 输入数据',
            'outputs': '- result: 执行结果',
            'steps': '1. 处理输入\n2. 执行功能\n3. 返回结果',
            'dependencies': '- 无',
            'class_name': 'UnnamedSkill',
            'example_params': 'input_data="test"'
        }
        
        for key, value in defaults.items():
            if key not in params:
                params[key] = value
        
        # 使用format替换占位符
        try:
            return markdown.format(**params)
        except KeyError as e:
            # 如果缺少某个键，补充默认值后重试
            for key in list(defaults.keys()):
                if key not in params:
                    params[key] = defaults[key]
            return markdown.format(**params)
    
    def add_template(self, name: str, template: Dict):
        """添加自定义模板"""
        self._templates[name] = template
        self._save_template(name, template)
    
    def _save_template(self, name: str, template: Dict):
        """保存模板到文件"""
        file_path = self.template_dir / f"{name}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template['markdown'])