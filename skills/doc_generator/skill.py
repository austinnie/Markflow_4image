"""
doc_generator - 代码文档自动生成器，从 Python 代码自动生成 API 文档

目的: 自动化生成项目文档，支持 API 参考、README 和使用指南
"""

import os
import ast
import inspect
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DocGenerator:
    """
    代码文档自动生成器
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "doc_generator"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()

        logger.info("DocGenerator 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': './skills',
            'default_doc_type': 'all',
            'default_format': 'md',
            'exclude_patterns': ['__pycache__', '*.pyc', 'test_*', '*_test.py'],
            'include_patterns': ['*.py']
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        if 'code_path' not in kwargs or not kwargs['code_path']:
            raise ValueError("code_path 是必填参数")

        code_path = Path(kwargs['code_path'])
        if not code_path.exists():
            raise ValueError(f"代码路径不存在: {code_path}")

        doc_type = kwargs.get('doc_type', self.config.get('default_doc_type', 'all'))
        if doc_type not in ['api', 'readme', 'all']:
            raise ValueError(f"doc_type 必须为 api、readme 或 all，当前值: {doc_type}")

        output_format = kwargs.get('output_format', self.config.get('default_format', 'md'))
        if output_format not in ['md', 'html']:
            raise ValueError(f"output_format 必须为 md 或 html，当前值: {output_format}")

        return True

    def _should_include_file(self, file_path: Path) -> bool:
        """检查文件是否应该被包含"""
        exclude_patterns = self.config.get('exclude_patterns', ['__pycache__', '*.pyc'])
        for pattern in exclude_patterns:
            if file_path.match(pattern):
                return False

        include_patterns = self.config.get('include_patterns', ['*.py'])
        for pattern in include_patterns:
            if file_path.match(pattern):
                return True

        return False

    def _collect_python_files(self, code_path: Path) -> List[Path]:
        """收集所有 Python 文件"""
        files = []
        if code_path.is_file():
            if code_path.suffix == '.py' and self._should_include_file(code_path):
                files.append(code_path)
        else:
            for root, dirs, files_in_dir in os.walk(code_path):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', 'node_modules']]
                for file in files_in_dir:
                    file_path = Path(root) / file
                    if file_path.suffix == '.py' and self._should_include_file(file_path):
                        files.append(file_path)
        return files

    def _parse_python_file(self, file_path: Path) -> Dict[str, Any]:
        """解析 Python 文件 - 完整版"""
        result = {
            'file_path': str(file_path),
            'module_name': file_path.stem,
            'docstring': '',
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': [],
            'content': ''  # ✅ 新增这行
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result['content'] = content  # ✅ 新增这行，保存内容
            
            tree = ast.parse(content)

            module_doc = ast.get_docstring(tree)
            if module_doc:
                result['docstring'] = module_doc

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in result['imports']:
                            result['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ''
                    for alias in node.names:
                        full_name = f"{module_name}.{alias.name}" if module_name else alias.name
                        if full_name not in result['imports']:
                            result['imports'].append(full_name)
                elif isinstance(node, ast.ClassDef):
                    class_names = [c['name'] for c in result['classes']]
                    if node.name not in class_names:
                        class_info = self._parse_class(node, content)
                        result['classes'].append(class_info)
                elif isinstance(node, ast.FunctionDef):
                    func_names = [f['name'] for f in result['functions']]
                    if node.name not in func_names and not node.name.startswith('_'):
                        func_info = self._parse_function(node, content)
                        result['functions'].append(func_info)
                elif isinstance(node, ast.AsyncFunctionDef):
                    func_names = [f['name'] for f in result['functions']]
                    if node.name not in func_names and not node.name.startswith('_'):
                        func_info = self._parse_function(node, content)
                        result['functions'].append(func_info)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            const_names = [c['name'] for c in result['constants']]
                            if target.id not in const_names:
                                result['constants'].append({
                                    'name': target.id,
                                    'value': self._get_constant_value(node.value)
                                })

        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}")

        return result

    def _parse_class(self, node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """解析类"""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'bases': [self._get_name(base) for base in node.bases],
            'methods': [],
            'attributes': [],
            'class_variables': []
        }

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._parse_function(item, content)
                class_info['methods'].append(method_info)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_info = self._parse_function(item, content)
                class_info['methods'].append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info['class_variables'].append({
                            'name': target.id,
                            'value': self._get_constant_value(item.value)
                        })

        return class_info

    def _parse_function(self, node, content: str) -> Dict[str, Any]:
        """解析函数"""
        func_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'params': [],
            'return_type': '',
            'decorators': [],
            'line_number': node.lineno,
            'is_async': isinstance(node, ast.AsyncFunctionDef)
        }

        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': self._get_annotation(arg.annotation) if arg.annotation else 'Any',
                'default': None
            }
            func_info['params'].append(param_info)

        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                param_index = len(func_info['params']) - len(defaults) + i
                if param_index < len(func_info['params']):
                    func_info['params'][param_index]['default'] = self._get_constant_value(default)

        if node.returns:
            func_info['return_type'] = self._get_annotation(node.returns)

        for decorator in node.decorator_list:
            decorator_name = self._get_name(decorator)
            if decorator_name:
                func_info['decorators'].append(decorator_name)

        return func_info

    def _get_name(self, node) -> str:
        """获取 AST 节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        elif hasattr(node, 'id'):
            return node.id
        return str(node)[:50]

    def _get_annotation(self, node) -> str:
        """获取类型注解字符串"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
            return node.s
        elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant):
            return str(node.value)
        return str(node)[:50]

    def _get_constant_value(self, node) -> Any:
        """获取常量值"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return [self._get_constant_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            return {self._get_constant_value(k): self._get_constant_value(v) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.Tuple):
            return tuple(self._get_constant_value(elt) for elt in node.elts)
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
            return node.s
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return node.n
        elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant):
            return node.value
        return str(node)[:50]

    def _generate_api_doc_md(self, parsed_files: List[Dict], project_name: str, project_description: str) -> str:
        """生成 API 参考文档（Markdown 格式）"""
        lines = []

        lines.append(f"# {project_name} API 参考")
        lines.append("")
        lines.append(f"*{project_description}*")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for file_info in parsed_files:
            module_name = file_info['module_name']
            file_path = file_info['file_path']

            lines.append(f"## 模块: {module_name}")
            lines.append("")
            lines.append(f"**文件**: `{file_path}`")
            lines.append("")

            if file_info['docstring']:
                lines.append(file_info['docstring'])
                lines.append("")

            if file_info['imports']:
                lines.append("### 导入")
                lines.append("")
                for imp in file_info['imports'][:10]:
                    lines.append(f"- `{imp}`")
                if len(file_info['imports']) > 10:
                    lines.append(f"- ... 还有 {len(file_info['imports']) - 10} 个导入")
                lines.append("")

            if file_info['classes']:
                lines.append("### 类")
                lines.append("")
                for cls in file_info['classes']:
                    lines.append(f"#### `{cls['name']}`")
                    lines.append("")
                    if cls['bases']:
                        lines.append(f"- **基类**: {', '.join(cls['bases'])}")
                        lines.append("")
                    if cls['docstring']:
                        lines.append(f"- **说明**: {cls['docstring']}")
                        lines.append("")

                    if cls['class_variables']:
                        lines.append("**类变量**:")
                        lines.append("")
                        for var in cls['class_variables']:
                            lines.append(f"- `{var['name']}` = `{var['value']}`")
                        lines.append("")

                    if cls['methods']:
                        lines.append("**方法**:")
                        lines.append("")
                        for method in cls['methods']:
                            params_str = ', '.join([f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p.get('default') is not None else '') for p in method['params']])
                            lines.append(f"- `{method['name']}({params_str})` -> `{method['return_type']}`")
                            if method['docstring']:
                                lines.append(f"  - {method['docstring'][:100]}")
                            if method['decorators']:
                                lines.append(f"  - @{', @'.join(method['decorators'])}")
                        lines.append("")

            if file_info['functions']:
                lines.append("### 函数")
                lines.append("")
                for func in file_info['functions']:
                    params_str = ', '.join([f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p.get('default') is not None else '') for p in func['params']])
                    lines.append(f"- `{func['name']}({params_str})` -> `{func['return_type']}`")
                    if func['docstring']:
                        lines.append(f"  - {func['docstring'][:100]}")
                lines.append("")

        return '\n'.join(lines)

    def _extract_skill_features(self, parsed_files: List[Dict], project_name: str) -> Dict[str, Any]:
        """自动从代码中提取技能特征"""
        features = {
            'capabilities': [],
            'supported_langs': {},
            'data_sources': [],
            'categories': [],
            'features_table': [],
            'dependencies': [],
            'special_notes': []
        }
        
        # 收集所有代码内容（直接从文件读取）
        all_content = ""
        for f in parsed_files:
            file_path_str = f.get('file_path', '')
            if file_path_str:
                try:
                    with open(file_path_str, 'r', encoding='utf-8') as f_read:
                        content = f_read.read()
                        all_content += content + "\n"
                except Exception as e:
                    logger.warning(f"读取文件失败 {file_path_str}: {e}")
        
        if not all_content:
            # 降级：从 docstring 获取
            for f in parsed_files:
                docstring = f.get('docstring', '')
                if docstring:
                    all_content += docstring + "\n"
        
        # 1. 检测并提取功能列表（从 docstring 或注释中）
        for file_info in parsed_files:
            # 从模块 docstring 提取
            docstring = file_info.get('docstring', '')
            if docstring:
                lines = docstring.split('\n')
                for line in lines:
                    if any(kw in line.lower() for kw in ['功能', '特性', '支持', 'feature', 'capability']):
                        if line.strip() and not line.strip().startswith(('"""', "'''")):
                            features['capabilities'].append(line.strip())
            
            # 从类和方法中提取功能
            for cls in file_info.get('classes', []):
                cls_doc = cls.get('docstring', '')
                if cls_doc:
                    for line in cls_doc.split('\n'):
                        if '功能' in line or 'feature' in line.lower():
                            if line.strip() and not line.strip().startswith(('"""', "'''")):
                                features['capabilities'].append(line.strip())
                
                for method in cls.get('methods', []):
                    method_name = method.get('name', '')
                    if method_name.startswith(('play', 'search', 'download', 'generate', 'export', 'import', 
                                              'scan', 'analyze', 'translate', 'speak', 'quiz', 'flashcard')):
                        action = {
                            'play': '▶️ 播放/播放控制',
                            'search': '🔍 搜索功能',
                            'download': '📥 下载功能',
                            'generate': '✨ 生成功能',
                            'export': '💾 导出功能',
                            'import': '📂 导入功能',
                            'scan': '📁 扫描功能',
                            'analyze': '📊 分析功能',
                            'translate': '🌐 翻译功能',
                            'speak': '🔊 语音合成',
                            'quiz': '❓ 测验功能',
                            'flashcard': '🃏 闪卡学习',
                        }.get(method_name.split('_')[0], '')
                        if action and action not in features['capabilities']:
                            features['capabilities'].append(action)
        
        # 2. 提取支持的语言（从常量、配置或注释中）
        lang_patterns = [
            r'SUPPORTED_LANGUAGES\s*=\s*\{([^}]+)\}',
            r'LANGUAGES\s*=\s*\[([^\]]+)\]',
            r'SUPPORTED_LANG\w*\s*=\s*\[([^\]]+)\]',
            r'#\s*支持的语言[:：]\s*([^\n]+)',
            r'语言支持[:：]\s*([^\n]+)',
        ]
        
        for pattern in lang_patterns:
            match = re.search(pattern, all_content, re.IGNORECASE | re.DOTALL)
            if match:
                lang_str = match.group(1)
                lang_names = re.findall(r'["\'](\w+)["\']', lang_str)
                if lang_names:
                    lang_map = {
                        'en': '英语', 'es': '西班牙语', 'fr': '法语', 'de': '德语',
                        'it': '意大利语', 'pt': '葡萄牙语', 'nl': '荷兰语', 'pl': '波兰语',
                        'fi': '芬兰语', 'el': '希腊语', 'ar': '阿拉伯语', 'he': '希伯来语',
                        'th': '泰语', 'sv': '瑞典语', 'ja': '日语', 'zh': '中文',
                        'ko': '韩语', 'ru': '俄语', 'hi': '印地语', 'vi': '越南语',
                        'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java',
                        'cpp': 'C++', 'go': 'Go', 'rust': 'Rust'
                    }
                    for code in lang_names:
                        if code in lang_map:
                            features['supported_langs'][code] = lang_map[code]
                        else:
                            features['supported_langs'][code] = code
                    break
        
        # 3. 提取分类信息（从常量或注释中）
        category_patterns = [
            r'CATEGORIES\s*=\s*\{([^}]+)\}',
            r'#\s*分类[:：]\s*([^\n]+)',
            r'CATEGORY\w*\s*=\s*\[([^\]]+)\]',
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, all_content, re.IGNORECASE | re.DOTALL)
            if match:
                cat_str = match.group(1)
                categories = re.findall(r'["\'](\w+)["\']', cat_str)
                if categories:
                    features['categories'] = categories
                    break
        
        # 4. 检测特殊功能（从注释和字符串中）
        special_keywords = {
            'ai': '🤖 AI 智能处理',
            'ollama': '🤖 AI 摘要/生成',
            'rss': '📡 RSS 订阅',
            'playlist': '🎵 播放列表管理',
            'lyric': '📋 歌词显示',
            'progress': '📊 进度追踪',
            'review': '🔄 复习模式',
            'grammar': '📖 语法学习',
            'tts': '🔊 语音合成',
            'wordnet': '📚 WordNet 词典',
            'jamdict': '📚 Jamdict 日语词典',
            'jieba': '📚 Jieba 中文分词',
            'cedict': '📚 CEDICT 词典',
        }
        
        for keyword, label in special_keywords.items():
            if keyword in all_content.lower():
                if label not in features['capabilities']:
                    features['capabilities'].append(label)
        
        # 5. 提取数据源信息
        source_patterns = [
            r'数据源[:：]\s*([^\n]+)',
            r'source[s]?\s*=\s*["\']([^"\']+)["\']',
            r'from\s+["\']([^"\']+)["\']\s+import',
        ]
        
        for pattern in source_patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            if matches:
                for m in matches:
                    if m and m not in features['data_sources'] and len(m) > 3:
                        features['data_sources'].append(m)
        
        # 6. 检测特殊功能模块
        if any(kw in all_content.lower() for kw in ['flashcard', 'quiz', 'learn']):
            features['features_table'].append(('🃏 闪卡学习模式', '高效的单词记忆方式'))
            features['features_table'].append(('❓ 选择题测验', '检验学习成果'))
        
        if any(kw in all_content.lower() for kw in ['grammar', 'sentence']):
            features['features_table'].append(('📖 语法学习', '掌握语言规则'))
        
        if any(kw in all_content.lower() for kw in ['progress', 'track', 'stats']):
            features['features_table'].append(('📊 学习进度追踪', '记录学习统计'))
        
        if any(kw in all_content.lower() for kw in ['play', 'music', 'audio']):
            features['features_table'].append(('▶️ 播放音乐', '自动选择播放器'))
            features['features_table'].append(('🔊 音量控制', '调节播放音量'))
            features['features_table'].append(('📊 播放控制', '暂停/继续/停止'))
        
        # 7. 提取依赖（从 imports 或注释）
        for file_info in parsed_files:
            imports = file_info.get('imports', [])
            for imp in imports:
                if any(dep in imp for dep in ['nltk', 'jamdict', 'jieba', 'konlpy', 'edge_tts']):
                    features['dependencies'].append(imp.split('.')[0] if '.' in imp else imp)
        
        return features
    
    def _generate_readme_md(self, parsed_files: List[Dict], project_name: str,
                           project_description: str, author: str) -> str:
        """生成 README 文档 - 智能版"""
        lines = []
        
        # 标题和描述
        lines.append(f"# {project_name}")
        lines.append("")
        if project_description:
            lines.append(f"> {project_description}")
            lines.append("")
        
        if author:
            lines.append(f"**作者**: {author}")
            lines.append("")
        
        # 概览
        total_classes = 0
        total_methods = 0
        total_functions = 0
        
        for f in parsed_files:
            total_classes += len(f['classes'])
            total_functions += len(f['functions'])
            for cls in f['classes']:
                total_methods += len(cls['methods'])
        
        lines.append("## 概览")
        lines.append("")
        lines.append(f"- **文件数**: {len(parsed_files)}")
        lines.append(f"- **类数**: {total_classes}")
        lines.append(f"- **方法数**: {total_methods}")
        lines.append(f"- **函数数**: {total_functions}")
        lines.append("")
        
        # ============ 智能提取特征 ============
        features = self._extract_skill_features(parsed_files, project_name)
        
        # 支持的语言
        if features.get('supported_langs'):
            lines.append("## 支持的语言")
            lines.append("")
            lines.append("| 语言 | 代码 |")
            lines.append("|------|------|")
            for code, name in features['supported_langs'].items():
                lines.append(f"| {name} | `{code}` |")
            lines.append("")
        
        # 功能列表
        if features.get('capabilities') or features.get('features_table'):
            lines.append("## 支持的功能")
            lines.append("")
            lines.append("| 功能 | 说明 |")
            lines.append("|------|------|")
            
            # 去重
            all_features = set()
            for cap in features.get('capabilities', []):
                if cap and cap not in all_features:
                    all_features.add(cap)
                    # 尝试提取简短说明
                    parts = cap.split('：', 1) if '：' in cap else cap.split(':', 1)
                    if len(parts) == 2:
                        lines.append(f"| {parts[0].strip()} | {parts[1].strip()} |")
                    else:
                        lines.append(f"| {cap} | - |")
            
            for name, desc in features.get('features_table', []):
                if name not in all_features:
                    lines.append(f"| {name} | {desc} |")
                    all_features.add(name)
            lines.append("")
        
        # 数据源
        if features.get('data_sources'):
            lines.append("## 数据源")
            lines.append("")
            for source in features['data_sources']:
                lines.append(f"- {source}")
            lines.append("")
        
        # 分类
        if features.get('categories'):
            lines.append("## 支持的分类")
            lines.append("")
            lines.append("| 分类 | 说明 |")
            lines.append("|------|------|")
            for cat in features['categories']:
                lines.append(f"| `{cat}` | - |")
            lines.append("")
        
        # ============ 从 meta.json 读取 ============
        meta_file = Path(f"./skills/{project_name}/meta.json")
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                if meta.get('description') and not project_description:
                    lines.append("## 技能描述")
                    lines.append("")
                    lines.append(meta['description'])
                    lines.append("")
                
                # 依赖（合并自动提取的）
                all_deps = set(meta.get('dependencies', []))
                all_deps.update(features.get('dependencies', []))
                
                if all_deps:
                    lines.append("## 依赖")
                    lines.append("")
                    lines.append("```bash")
                    for dep in all_deps:
                        lines.append(f"pip install {dep}")
                    lines.append("```")
                    lines.append("")
                
                # 参数说明
                if meta.get('inputs'):
                    lines.append("## 参数说明")
                    lines.append("")
                    lines.append("| 参数 | 类型 | 默认值 | 说明 |")
                    lines.append("|------|------|--------|------|")
                    for inp in meta['inputs']:
                        name = inp.get('name', '')
                        dtype = inp.get('type', 'string')
                        default = inp.get('default', '')
                        desc = inp.get('description', '')
                        lines.append(f"| `{name}` | {dtype} | `{default}` | {desc} |")
                    lines.append("")
                
                if meta.get('outputs'):
                    lines.append("## 输出")
                    lines.append("")
                    lines.append("| 字段 | 说明 |")
                    lines.append("|------|------|")
                    for out in meta['outputs']:
                        name = out.get('name', '')
                        desc = out.get('description', '')
                        lines.append(f"| `{name}` | {desc} |")
                    lines.append("")
                    
            except Exception as e:
                logger.warning(f"读取 meta.json 失败: {e}")
        
        # ============ 使用方法 ============
        lines.append("## 使用方法")
        lines.append("")
        lines.append("```bash")
        lines.append(f"python -m markflow.cli.commands execute {project_name} [参数]")
        lines.append("```")
        lines.append("")
        
        # 示例
        lines.append("### 示例")
        lines.append("")
        lines.append("```bash")
        lines.append(f"python -m markflow.cli.commands execute {project_name} [参数]")
        lines.append("```")
        lines.append("")
        
        # 输出位置
        lines.append("## 输出位置")
        lines.append("")
        lines.append(f"生成的输出保存在 `skills/{project_name}/output/` 目录下。")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append(f"*文档自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)
    
    def _generate_readme_md_old(self, parsed_files: List[Dict], project_name: str,
                           project_description: str, author: str) -> str:
        """生成 README 文档 - 增强版"""
        lines = []

        # 标题
        lines.append(f"# {project_name}")
        lines.append("")
        lines.append(f"> {project_description}")
        lines.append("")

        if author:
            lines.append(f"**作者**: {author}")
            lines.append("")

        # 概览
        total_classes = 0
        total_methods = 0
        total_functions = 0

        for f in parsed_files:
            total_classes += len(f['classes'])
            total_functions += len(f['functions'])
            for cls in f['classes']:
                total_methods += len(cls['methods'])

        lines.append("## 概览")
        lines.append("")
        lines.append(f"- **文件数**: {len(parsed_files)}")
        lines.append(f"- **类数**: {total_classes}")
        lines.append(f"- **方法数**: {total_methods}")
        lines.append(f"- **函数数**: {total_functions}")
        lines.append("")

        # ============ 新增：提取多语言支持信息 ============
        if project_name == "code_reviewer":
            supported_langs = self._extract_supported_languages_from_code(parsed_files)
            if supported_langs:
                lines.append("## 支持的语言")
                lines.append("")
                lines.append("| 语言 | 检查工具 | 状态 |")
                lines.append("|------|----------|------|")
                for lang, tools in supported_langs.items():
                    tool_list = ", ".join(tools) if isinstance(tools, list) else str(tools)
                    # 检查工具是否已安装
                    installed = self._check_tools_installed(tools)
                    status_icon = "✅" if installed else "⚠️ 需安装"
                    lines.append(f"| {lang.upper()} | {tool_list} | {status_icon} |")
                lines.append("")
        # ============ 新增结束 ============
        
        # ============ music_player 特殊处理 ============
        if project_name == "music_player":
            lines.append("## 支持的功能")
            lines.append("")
            lines.append("| 功能 | 说明 |")
            lines.append("|------|------|")
            lines.append("| 🔍 搜索音乐 | 在线搜索 YouTube 音乐 |")
            lines.append("| ▶️ 播放音乐 | 自动选择播放器（Moo0/VLC/浏览器） |")
            lines.append("| 🎵 智能歌单 | 根据情绪生成播放列表 |")
            lines.append("| 💾 保存歌单 | 保存播放列表到本地 |")
            lines.append("| 📋 歌词显示 | 显示当前歌曲歌词 |")
            lines.append("| 📊 播放控制 | 暂停/继续/停止/上一首/下一首 |")
            lines.append("| 🔊 音量控制 | 调节播放音量 |")
            lines.append("| 📁 本地扫描 | 扫描本地音乐文件 |")
            lines.append("")
            
            lines.append("## 播放器支持")
            lines.append("")
            lines.append("| 播放器 | 本地文件 | 在线音乐 | 说明 |")
            lines.append("|--------|----------|----------|------|")
            lines.append("| Moo0 AudioPlayer | ✅ | ❌ | 轻量稳定，优先用于本地 |")
            lines.append("| 浏览器 | ❌ | ✅ | 在线音乐主要播放方式 |")
            lines.append("| VLC | ✅ | ⚠️ | 作为备选 |")
            lines.append("| 系统播放器 | ✅ | ❌ | 最后备选 |")
            lines.append("| mpv | ✅ | ✅ | 最后备选 |")
            lines.append("")        
        # ============ 新增结束 ============

        # ============ news_aggregator 特殊处理 ============
        if project_name == "news_aggregator":
            lines.append("## 支持的功能")
            lines.append("")
            lines.append("| 功能 | 说明 |")
            lines.append("|------|------|")
            lines.append("| 📡 RSS 抓取 | 自动抓取多个 RSS 源 |")
            lines.append("| 🤖 AI 摘要 | 使用 Ollama 生成智能摘要 |")
            lines.append("| 📂 分类聚合 | 科技/财经/国际/中国/美国/日本/韩国 |")
            lines.append("| 📰 每日简报 | 生成格式化的新闻简报 |")
            lines.append("| 🔗 来源去重 | 自动去重，减少重复内容 |")
            lines.append("| 📁 报告保存 | 保存为 TXT 格式 |")
            lines.append("")
            
            lines.append("## 支持的地区分类")
            lines.append("")
            lines.append("| 分类 | 说明 | 源数量 |")
            lines.append("|------|------|--------|")
            lines.append("| `tech` | 科技新闻（国际 + 中日韩） | 20+ |")
            lines.append("| `business` | 财经新闻（国际 + 中日韩） | 15+ |")
            lines.append("| `world` | 国际新闻 | 20+ |")
            lines.append("| `china` | 中国新闻 | 12 |")
            lines.append("| `usa` | 美国新闻 | 14 |")
            lines.append("| `japan` | 日本新闻 | 8 |")
            lines.append("| `korea` | 韩国新闻 | 6 |")
            lines.append("")
        # ============ 新增结束 ============

        # ============ language_learner 特殊处理 ============
        if project_name == "language_learner":
            lines.append("## 支持的语言")
            lines.append("")
            lines.append("| 语言 | 代码 | 词条数 | 数据源 |")
            lines.append("|------|------|--------|--------|")
            lines.append("| 英语 | en | 87,353 | WordNet (OMW) |")
            lines.append("| 西班牙语 | es | 90,851 | WordNet (OMW) |")
            lines.append("| 法语 | fr | 55,316 | WordNet (OMW) |")
            lines.append("| 意大利语 | it | 41,829 | WordNet (OMW) |")
            lines.append("| 葡萄牙语 | pt | 50,000 | WordNet (OMW) |")
            lines.append("| 荷兰语 | nl | 43,066 | WordNet (OMW) |")
            lines.append("| 波兰语 | pl | 45,342 | WordNet (OMW) |")
            lines.append("| 芬兰语 | fi | 50,000 | WordNet (OMW) |")
            lines.append("| 希腊语 | el | 18,216 | WordNet (OMW) |")
            lines.append("| 阿拉伯语 | ar | 17,772 | WordNet (OMW) |")
            lines.append("| 希伯来语 | he | 5,325 | WordNet (OMW) |")
            lines.append("| 泰语 | th | 50,000 | WordNet (OMW) |")
            lines.append("| 瑞典语 | sv | 5,823 | WordNet (OMW) |")
            lines.append("| 日语 | ja | 15,012 | Jamdict |")
            lines.append("| 中文 | zh | 10,000 | CEDICT + Jieba |")
            lines.append("| 德语 | de | 230 | OpenThesaurus + 内置 |")
            lines.append("| 韩语 | ko | 132 | 内置词库 |")
            lines.append("")
            lines.append("**总计：~580,000+ 词汇量**")
            lines.append("")
            
            lines.append("## 支持的功能")
            lines.append("")
            lines.append("| 功能 | 说明 |")
            lines.append("|------|------|")
            lines.append("| 🃏 闪卡学习模式 | 高效的单词记忆方式 |")
            lines.append("| ❓ 选择题测验 | 检验学习成果 |")
            lines.append("| 💬 句子练习 | 学习实际应用场景 |")
            lines.append("| 📖 语法学习 | 掌握语言规则 |")
            lines.append("| 🔄 复习模式 | 巩固已学知识 |")
            lines.append("| 🔊 语音合成 | 支持多语言发音 (Edge TTS) |")
            lines.append("| 📊 学习进度追踪 | 记录学习统计 |")
            lines.append("| 📥 完整词典下载 | 一键下载各语言词典 |")
            lines.append("| 📚 知识库管理 | 添加/导入/导出单词和句子 |")
            lines.append("")
            
            lines.append("## 词典数据源说明")
            lines.append("")
            lines.append("| 语言 | 数据源 | 说明 |")
            lines.append("|------|--------|------|")
            lines.append("| en, es, fr, it, pt, nl, pl, fi, el, ar, he, th, sv | WordNet (OMW) | NLTK Open Multilingual WordNet |")
            lines.append("| ja | Jamdict | JMdict 日语词典 |")
            lines.append("| zh | CEDICT + Jieba | 中文-英语词典 + Jieba 词库 |")
            lines.append("| de | OpenThesaurus + 内置 | 开源德语同义词词典 |")
            lines.append("| ko | 内置词库 | 韩语常用词汇 |")
            lines.append("")
            
        # 从 meta.json 读取参数说明
        meta_file = Path(f"./skills/{project_name}/meta.json")
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                if meta.get('description'):
                    lines.append("## 技能描述")
                    lines.append("")
                    lines.append(meta['description'])
                    lines.append("")

                # 依赖
                if meta.get('dependencies'):
                    lines.append("## 依赖")
                    lines.append("")
                    lines.append("```bash")
                    for dep in meta['dependencies']:
                        lines.append(f"pip install {dep}")
                    lines.append("```")
                    lines.append("")

                # ============ 新增：各语言依赖安装 ============
                if project_name == "code_reviewer":
                    lang_deps = self._get_language_install_commands()
                    if lang_deps:
                        lines.append("## 各语言依赖安装")
                        lines.append("")
                        for lang, cmds in lang_deps.items():
                            if lang == "python":
                                continue
                            lines.append(f"### {lang.upper()}")
                            lines.append("")
                            lines.append("```bash")
                            for cmd in cmds:
                                lines.append(cmd)
                            lines.append("```")
                            lines.append("")
                # ============ 新增结束 ============

                # 参数说明
                if meta.get('inputs'):
                    lines.append("## 参数说明")
                    lines.append("")
                    lines.append("| 参数 | 类型 | 默认值 | 说明 |")
                    lines.append("|------|------|--------|------|")
                    for inp in meta['inputs']:
                        name = inp.get('name', '')
                        dtype = inp.get('type', 'string')
                        default = inp.get('default', '')
                        desc = inp.get('description', '')
                        lines.append(f"| `{name}` | {dtype} | `{default}` | {desc} |")
                    lines.append("")

                # 输出
                if meta.get('outputs'):
                    lines.append("## 输出")
                    lines.append("")
                    lines.append("| 字段 | 说明 |")
                    lines.append("|------|------|")
                    for out in meta['outputs']:
                        name = out.get('name', '')
                        desc = out.get('description', '')
                        lines.append(f"| `{name}` | {desc} |")
                    lines.append("")

            except Exception as e:
                logger.warning(f"读取 meta.json 失败: {e}")

        # 使用方法
        lines.append("## 使用方法")
        lines.append("")
        lines.append("```bash")
        lines.append(f"python -m markflow.cli.commands execute {project_name} [参数]")
        lines.append("```")
        lines.append("")

        # 示例
        lines.append("### 示例")
        lines.append("")
        lines.append("```bash")

        if project_name == "code_reviewer":
            lines.append(f"# 自动检测并审查所有代码")
            lines.append(f"python -m markflow.cli.commands execute {project_name} code_path=\"./project\"")
            lines.append("")
            lines.append(f"# 审查 Python 代码")
            lines.append(f"python -m markflow.cli.commands execute {project_name} code_path=\"./markflow\"")
            lines.append("")
            lines.append(f"# 只检查安全问题")
            lines.append(f"python -m markflow.cli.commands execute {project_name} code_path=\"./markflow\" focus=\"security\"")
            lines.append("")
            lines.append(f"# 指定 JavaScript 语言")
            lines.append(f"python -m markflow.cli.commands execute {project_name} code_path=\"./project\" language=\"javascript\"")
            lines.append("")
            lines.append(f"# 深度审查")
            lines.append(f"python -m markflow.cli.commands execute {project_name} code_path=\"./project\" review_level=\"deep\"")

        elif project_name == "music_player":
            lines.append(f"# 搜索并播放音乐")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"play\" query=\"周杰伦 稻香\"")
            lines.append("")
            lines.append(f"# 生成开心歌单")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"playlist\" mood=\"happy\" count=5")
            lines.append("")
            lines.append(f"# 保存歌单")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"playlist\" mood=\"relax\" save=true")
            lines.append("")
            lines.append(f"# 扫描本地音乐")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"scan\"")
            lines.append("")
            lines.append(f"# 查看播放状态")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"info\"")

        elif project_name == "news_aggregator":
            lines.append(f"# 抓取科技新闻（5条）")
            lines.append(f"python -m markflow.cli.commands execute {project_name} category=\"tech\" top_n=5")
            lines.append("")
            lines.append(f"# 抓取中国新闻（10条）")
            lines.append(f"python -m markflow.cli.commands execute {project_name} category=\"china\" top_n=10")
            lines.append("")
            lines.append(f"# 抓取财经新闻")
            lines.append(f"python -m markflow.cli.commands execute {project_name} category=\"business\" top_n=5")
            lines.append("")
            lines.append(f"# 自定义源")
            lines.append(f"python -m markflow.cli.commands execute {project_name} sources=\"TechCrunch,BBC\"")
            lines.append("")
            lines.append(f"# 语音播报新闻（配合 voice_assistant）")
            lines.append(f"python scripts/news_voice_broadcast.py --category tech --top 5 --play")

        # ============ language_learner 依赖 ============
        elif project_name == "language_learner":
            lines.append("## 依赖安装")
            lines.append("")
            lines.append("```bash")
            lines.append("# 基础依赖")
            lines.append("pip install nltk edge-tts requests")
            lines.append("")
            lines.append("# 日语词典")
            lines.append("pip install jamdict")
            lines.append("")
            lines.append("# 中文分词")
            lines.append("pip install jieba")
            lines.append("")
            lines.append("# 韩语 (可选)")
            lines.append("pip install konlpy")
            lines.append("```")
            lines.append("")
            lines.append("### NLTK 数据下载")
            lines.append("")
            lines.append("```python")
            lines.append("import nltk")
            lines.append("nltk.download('wordnet')")
            lines.append("nltk.download('omw-2.0')")
            lines.append("```")
            lines.append("")
            lines.append("### Jamdict 数据下载（日语）")
            lines.append("")
            lines.append("```bash")
            lines.append("# 下载 JMdict 词典文件")
            lines.append("python -c \"from jamdict import Jamdict; jmd=Jamdict(); jmd.import_data()\"")
            lines.append("```")
            lines.append("")
                    
        else:
            meta_file = Path(f"./skills/{project_name}/meta.json")
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    inputs = meta.get('inputs', [])
                    required = [inp for inp in inputs if inp.get('required', False)]
                    if required:
                        params_str = ' '.join([f"{inp['name']}=\"your_{inp['name']}\"" for inp in required])
                        lines.append(f"python -m markflow.cli.commands execute {project_name} {params_str}")
                    else:
                        lines.append(f"python -m markflow.cli.commands execute {project_name}")
                except:
                    lines.append(f"python -m markflow.cli.commands execute {project_name}")
            else:
                lines.append(f"python -m markflow.cli.commands execute {project_name}")

        lines.append("```")
        lines.append("")

        lines.append("查看完整参数说明：")
        lines.append("")
        lines.append("```bash")
        lines.append(f"python -m markflow.cli.commands info {project_name}")
        lines.append("```")
        lines.append("")

        # 查看报告
        if project_name == "code_reviewer":
            lines.append("### 查看报告")
            lines.append("")
            lines.append("```bash")
            lines.append("python -c \"")
            lines.append("import json")
            lines.append("from pathlib import Path")
            lines.append("reports = list(Path('skills/code_reviewer/output').glob('review_*.json'))")
            lines.append("if reports:")
            lines.append("    latest = max(reports, key=lambda p: p.stat().st_mtime)")
            lines.append("    data = json.load(open(latest))")
            lines.append("    result = data.get('result', data)")
            lines.append("    print(f'评分: {result.get(\\\"overall_score\\\", 0)}/100')")
            lines.append("    print(f'问题: {result.get(\\\"issues_count\\\", 0)} 个')")
            lines.append("\"")
            lines.append("```")
            lines.append("")
            
        elif project_name == "music_player":
            lines.append("### 查看播放列表")
            lines.append("")
            lines.append("```bash")
            lines.append(f"python -m markflow.cli.commands execute {project_name} action=\"info\"")
            lines.append("```")
            lines.append("")

        elif project_name == "news_aggregator":
            lines.append("### 查看报告")
            lines.append("")
            lines.append("```bash")
            lines.append(f"cat skills/news_aggregator/output/news_*.txt")
            lines.append("```")
            lines.append("")
            lines.append("### 语音播报")
            lines.append("")
            lines.append("```bash")
            lines.append(f"# 科技新闻播报")
            lines.append(f"python scripts/news_voice_broadcast.py --category tech --top 5 --play")
            lines.append("")
            lines.append(f"# 中国新闻播报")
            lines.append(f"python scripts/news_voice_broadcast.py --category china --top 5 --play")
            lines.append("```")
            lines.append("")


        elif project_name == "language_learner":
            lines.append("```bash")
            lines.append("# 查看所有可用语言")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"list\"")
            lines.append("")
            lines.append("# 下载英语词典")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_download_full_dict\" language=\"en\" source=\"wordnet\"")
            lines.append("")
            lines.append("# 下载日语词典")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_download_full_dict\" language=\"ja\" source=\"jamdict\"")
            lines.append("")
            lines.append("# 下载中文词典")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_download_full_dict\" language=\"zh\" source=\"jieba\"")
            lines.append("")
            lines.append("# 闪卡模式 - 学习 10 个新单词")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"flashcard\" language=\"it\" count=10")
            lines.append("")
            lines.append("# 选择题测验 - 5 道题")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"quiz\" language=\"es\" count=5")
            lines.append("")
            lines.append("# 切换语言")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"set_language\" language=\"ja\"")
            lines.append("")
            lines.append("# 语音合成")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"speak\" language=\"ja\" text=\"こんにちは\"")
            lines.append("")
            lines.append("# 查看学习统计")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"stats\" language=\"it\"")
            lines.append("```")
            lines.append("")
            lines.append("### 知识库管理")
            lines.append("")
            lines.append("```bash")
            lines.append("# 添加单词")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_add_word\" language=\"it\" word=\"ciao\" meaning=\"你好\"")
            lines.append("")
            lines.append("# 添加句子")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_add_sentence\" language=\"it\" original=\"Come stai?\" translation=\"你好吗？\"")
            lines.append("")
            lines.append("# 批量导入")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_import_text\" language=\"it\" text=\"ciao:你好\\ngrazie:谢谢\"")
            lines.append("")
            lines.append("# 导出知识库")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_export\" language=\"it\" format=\"json\"")
            lines.append("```")
            lines.append("")
            lines.append("### 查看报告")
            lines.append("")
            lines.append("```bash")
            lines.append("# 查看知识库统计")
            lines.append("py -3.14 -m markflow.cli.commands execute language_learner action=\"kb_stats\" language=\"it\"")
            lines.append("```")
            lines.append("")
            
        # 输出位置
        lines.append("## 输出位置")
        lines.append("")
        lines.append(f"生成的输出保存在 `skills/{project_name}/output/` 目录下。")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*文档自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return '\n'.join(lines)
        
    def _extract_supported_languages_from_code(self, parsed_files: List[Dict]) -> Dict:
        """从 code_reviewer/skill.py 中提取 SUPPORTED_LANGUAGES"""
        import re
        result = {}
        
        for file_info in parsed_files:
            content = file_info.get('content', '')
            
            # 方法1: 匹配 SUPPORTED_LANGUAGES = { ... } 整个字典
            pattern = r'SUPPORTED_LANGUAGES\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                block = match.group(1)
                # 匹配每个语言条目: "python": {"extensions": [...], "tools": [...]}
                lang_pattern = r'"(\w+)"\s*:\s*\{[^}]*"tools"\s*:\s*\[([^\]]+)\]'
                for m in re.finditer(lang_pattern, block):
                    lang = m.group(1)
                    tools_raw = m.group(2)
                    # 解析工具列表，去掉引号和空格
                    tools = [t.strip().strip('"').strip("'") for t in tools_raw.split(',') if t.strip()]
                    result[lang] = tools
                return result
            
            # 方法2: 如果上面的正则没匹配到，尝试更宽松的匹配
            # 先找到 SUPPORTED_LANGUAGES 的位置
            start_idx = content.find('SUPPORTED_LANGUAGES = {')
            if start_idx == -1:
                start_idx = content.find('SUPPORTED_LANGUAGES={')
            if start_idx != -1:
                # 从 SUPPORTED_LANGUAGES = { 开始，找到匹配的 }
                brace_count = 0
                in_string = False
                escape = False
                end_idx = start_idx
                for i, ch in enumerate(content[start_idx:], start_idx):
                    if escape:
                        escape = False
                        continue
                    if ch == '\\':
                        escape = True
                        continue
                    if ch == '"' or ch == "'":
                        if not in_string:
                            in_string = ch
                        elif in_string == ch:
                            in_string = False
                        continue
                    if in_string:
                        continue
                    if ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break
                
                if brace_count == 0:
                    dict_str = content[start_idx:end_idx+1]
                    # 提取每个语言
                    lang_pattern = r'"(\w+)"\s*:\s*\{[^}]*"tools"\s*:\s*\[([^\]]+)\]'
                    for m in re.finditer(lang_pattern, dict_str):
                        lang = m.group(1)
                        tools_raw = m.group(2)
                        tools = [t.strip().strip('"').strip("'") for t in tools_raw.split(',') if t.strip()]
                        result[lang] = tools
                    return result
        
        return result
        

    def _check_tools_installed(self, tools: List[str]) -> bool:
        """检查工具是否已安装（只检查 Python 工具）"""
        import shutil
        # 只有 Python 工具才真正检查
        python_tools = ['pylint', 'flake8', 'bandit', 'radon']
        for tool in tools:
            if tool in python_tools:
                if shutil.which(tool):
                    return True
        # 非 Python 工具默认返回 False（表示需安装）
        return False
        
    def _get_language_install_commands(self) -> Dict:
        """获取各语言的依赖安装命令"""
        return {
            "javascript": [
                "npm install -g eslint"
            ],
            "java": [
                "# 下载 checkstyle.jar 放到 lib/ 目录",
                "curl -L -o lib/checkstyle.jar https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.0/checkstyle-10.12.0-all.jar",
                "",
                "# 下载 spotbugs.jar 放到 lib/ 目录",
                "curl -L -o lib/spotbugs.jar https://github.com/spotbugs/spotbugs/releases/download/4.8.3/spotbugs-4.8.3.jar"
            ],
            "cpp": [
                "# Windows",
                "choco install cppcheck",
                "",
                "# Linux",
                "sudo apt install cppcheck clang-tidy",
                "",
                "# macOS",
                "brew install cppcheck"
            ],
            "go": [
                "go install golang.org/x/lint/golint@latest",
                "go install honnef.co/go/tools/cmd/staticcheck@latest"
            ],
            "rust": [
                "rustup component add clippy"
            ],
            "android": [
                "# 配置 ANDROID_HOME 环境变量",
                "# 使用 Android Studio 自带的 lint 工具",
                "",
                "# 安装 ktlint (macOS)",
                "brew install ktlint"
            ]
        }
        
    def _generate_usage_examples(self, parsed_files: List[Dict], project_name: str) -> str:
        """生成使用示例"""
        lines = []

        lines.append(f"# {project_name} 使用示例")
        lines.append("")
        lines.append("以下是从代码中提取的使用示例：")
        lines.append("")

        for file_info in parsed_files:
            module_name = file_info['module_name']
            lines.append(f"## {module_name}")
            lines.append("")

            for cls in file_info['classes']:
                lines.append(f"### {cls['name']}")
                lines.append("")

                init_method = None
                for method in cls['methods']:
                    if method['name'] == '__init__':
                        init_method = method
                        break

                if init_method:
                    params = [p for p in init_method['params'] if p['name'] != 'self']
                    if params:
                        param_str = ', '.join([f"{p['name']}={repr(p['default'])}" if p.get('default') is not None else p['name'] for p in params])
                        lines.append("```python")
                        lines.append(f"# 创建实例")
                        lines.append(f"obj = {cls['name']}({param_str})")
                        lines.append("```")
                        lines.append("")

                methods = [m for m in cls['methods'] if m['name'] not in ['__init__', '__repr__']]
                if methods:
                    lines.append("```python")
                    for method in methods[:3]:
                        params = [p for p in method['params'] if p['name'] != 'self']
                        param_str = ', '.join([f"{p['name']}={repr(p['default'])}" if p.get('default') is not None else p['name'] for p in params])
                        if param_str:
                            lines.append(f"result = obj.{method['name']}({param_str})")
                        else:
                            lines.append(f"result = obj.{method['name']}()")
                        if method['docstring']:
                            lines.append(f"# {method['docstring'][:60]}")
                    lines.append("```")
                lines.append("")

        return '\n'.join(lines)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行文档生成"""
        start_time = datetime.now()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            self._validate_inputs(**kwargs)

            code_path = Path(kwargs.get('code_path'))
            doc_type = kwargs.get('doc_type', self.config.get('default_doc_type', 'all'))
            output_format = kwargs.get('output_format', self.config.get('default_format', 'md'))
            project_name = kwargs.get('project_name', code_path.name)
            project_description = kwargs.get('project_description', '')
            author = kwargs.get('author', '')
            include_tests = kwargs.get('include_tests', False)
            extract_classes = kwargs.get('extract_classes', True)
            extract_functions = kwargs.get('extract_functions', True)
            generate_examples = kwargs.get('generate_examples', True)

            # 获取技能名称（用于确定输出位置）
            skill_name = kwargs.get('skill_name_param', project_name)

            # 如果指定了技能名称，输出到该技能的 output 目录
            if skill_name:
                output_dir = Path("./skills") / skill_name / "output"
            else:
                output_dir = Path(self.config.get('output_dir', './skills'))

            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"扫描代码目录: {code_path}")
            files = self._collect_python_files(code_path)

            if not files:
                return {
                    "status": "error",
                    "error": f"未找到任何 Python 文件: {code_path}"
                }

            logger.info(f"找到 {len(files)} 个 Python 文件")

            parsed_files = []
            for file_path in files:
                logger.info(f"  解析: {file_path}")
                parsed = self._parse_python_file(file_path)
                parsed_files.append(parsed)

            results = {}
            saved_paths = []

            if doc_type in ['api', 'all']:
                api_doc = self._generate_api_doc_md(parsed_files, project_name, project_description)
                api_path = output_dir / f"{project_name}_api_reference.{output_format}"
                with open(api_path, 'w', encoding='utf-8') as f:
                    f.write(api_doc)
                saved_paths.append(str(api_path))
                results['api_reference'] = api_doc

            if doc_type in ['readme', 'all']:
                readme_doc = self._generate_readme_md(parsed_files, project_name, project_description, author)
                readme_path = output_dir / f"README.{output_format}"
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_doc)
                saved_paths.append(str(readme_path))
                results['readme'] = readme_doc

                # 同时复制一份到技能根目录
                target_readme = Path("./skills") / skill_name / "README.md"
                if target_readme.parent.exists():
                    with open(target_readme, 'w', encoding='utf-8') as f:
                        f.write(readme_doc)
                    saved_paths.append(str(target_readme))
                    logger.info(f"   README 已复制到: {target_readme}")

            if generate_examples:
                examples_doc = self._generate_usage_examples(parsed_files, project_name)
                examples_path = output_dir / f"{project_name}_examples.md"
                with open(examples_path, 'w', encoding='utf-8') as f:
                    f.write(examples_doc)
                saved_paths.append(str(examples_path))
                results['usage_examples'] = examples_doc

            generation_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"文档生成完成! 保存位置: {output_dir}")
            logger.info(f"  耗时: {generation_time:.2f}s")

            return {
                "status": "success",
                "result": {
                    "doc_path": str(output_dir),
                    "saved_files": saved_paths,
                    "api_reference": results.get('api_reference', ''),
                    "readme": results.get('readme', ''),
                    "usage_examples": results.get('usage_examples', ''),
                    "modules_summary": {
                        "total_files": len(parsed_files),
                        "total_classes": sum(len(f['classes']) for f in parsed_files),
                        "total_functions": sum(len(f['functions']) for f in parsed_files)
                    },
                    "generated_at": datetime.now().isoformat(),
                    "generation_time": f"{generation_time:.2f}s"
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<DocGenerator(name={self.name}, version={self.version})>"
        
# 在 skill.py 文件末尾添加
if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='代码文档自动生成器 - 从 Python 代码自动生成 API 文档',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成 README
  python skill.py --code_path="./skills/sd_image_generator/skill.py" --doc_type="readme" --project_name="sd_image_generator"
  
  # 生成所有文档
  python skill.py --code_path="./skills/sd_image_generator" --doc_type="all"
  
  # 生成 API 参考文档（HTML格式）
  python skill.py --code_path="./my_project" --doc_type="api" --output_format="html"
        """
    )
    
    parser.add_argument(
        '--code_path', 
        required=True, 
        help='要分析的 Python 代码路径（文件或目录）'
    )
    parser.add_argument(
        '--project_name', 
        help='项目名称（默认使用路径名）'
    )
    parser.add_argument(
        '--doc_type', 
        default='all', 
        choices=['api', 'readme', 'all'],
        help='文档类型: api=API参考, readme=README, all=全部（默认: all）'
    )
    parser.add_argument(
        '--output_format', 
        default='md', 
        choices=['md', 'html'],
        help='输出格式: md=Markdown, html=HTML（默认: md）'
    )
    parser.add_argument(
        '--project_description', 
        default='',
        help='项目描述'
    )
    parser.add_argument(
        '--author', 
        default='',
        help='作者名称'
    )
    parser.add_argument(
        '--skill_name',
        help='技能名称（输出目录名，默认使用 project_name）'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 确定项目名称
    code_path_obj = Path(args.code_path)
    if not args.project_name:
        if code_path_obj.is_file():
            args.project_name = code_path_obj.stem
        else:
            args.project_name = code_path_obj.name
    
    # 配置日志级别
    config = {}
    if args.verbose:
        config['log_level'] = 'DEBUG'
    else:
        config['log_level'] = 'INFO'
    
    # 创建生成器
    generator = DocGenerator(config)
    
    # 执行
    print(f"🚀 开始生成文档...")
    print(f"📂 代码路径: {args.code_path}")
    print(f"📝 项目名称: {args.project_name}")
    print(f"📄 文档类型: {args.doc_type}")
    print(f"📁 输出格式: {args.output_format}")
    print("-" * 50)
    
    result = generator.execute(
        code_path=args.code_path,
        project_name=args.project_name,
        doc_type=args.doc_type,
        output_format=args.output_format,
        project_description=args.project_description,
        author=args.author,
        skill_name_param=args.skill_name or args.project_name
    )
    
    print("-" * 50)
    
    if result['status'] == 'success':
        print(f"✅ 文档生成成功！")
        print(f"📁 保存位置: {result['result']['doc_path']}")
        print(f"📄 生成文件:")
        for f in result['result']['saved_files']:
            print(f"   - {f}")
        
        if args.verbose:
            print(f"\n📊 统计信息:")
            summary = result['result']['modules_summary']
            print(f"   - 文件数: {summary['total_files']}")
            print(f"   - 类数: {summary['total_classes']}")
            print(f"   - 函数数: {summary['total_functions']}")
        
        print(f"\n⏱️  耗时: {result['result']['generation_time']}")
    else:
        print(f"❌ 文档生成失败!")
        print(f"错误: {result.get('error', '未知错误')}")
        sys.exit(1)        