# markflow/core/generator.py
"""
代码生成器 - 从SkillSpec生成可执行代码（增强版）
"""

from typing import Dict, Any, List, Optional
from .parser import SkillSpec
from .quality import CodeQualityChecker
import re
import logging

logger = logging.getLogger(__name__)


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        self.templates = {}
        self.quality_checker = CodeQualityChecker()
    
    def generate(self, spec: SkillSpec, quality_check: bool = True, 
                 format_code: bool = True, generate_tests: bool = True) -> Dict[str, Any]:
        """生成技能代码"""
        from .tracer import RequirementTracer
        
        class_name = self._generate_class_name(spec.name)
        code = self._generate_class_code(spec, class_name)
        
        # 质量检查
        quality_result = None
        if quality_check:
            logger.info("执行代码质量检查...")
            quality_result = self.quality_checker.validate_all(code, "python")
            if quality_result.get("score", 0) < 60:
                logger.warning(f"质量评分较低: {quality_result['score']}/100")
            else:
                logger.info(f"质量评分: {quality_result['score']}/100")
        
        # 格式化
        if format_code:
            logger.info("格式化代码...")
            code = self.quality_checker.format_code(code, "python")
        
        # 生成测试
        tests = ""
        if generate_tests:
            logger.info("生成单元测试...")
            tests = self._generate_tests(spec, code)
        
        # 需求追溯
        tracer = RequirementTracer()
        trace_result = tracer.trace(spec, code)
        
        metadata = self._generate_metadata(spec)
        if quality_result:
            metadata['quality'] = {
                'score': quality_result.get('score', 0),
                'passed': quality_result.get('passed', False),
                'errors_count': len(quality_result.get('errors', [])),
                'warnings_count': len(quality_result.get('warnings', []))
            }
        if trace_result:
            metadata['trace'] = {
                'coverage': trace_result['coverage'],
                'total_requirements': trace_result['total_requirements'],
                'implemented': trace_result['implemented']
            }
        
        stats = self.quality_checker.analyze_code_stats(code, "python")
        
        return {
            'name': spec.name,
            'class_name': class_name,
            'code': code,
            'tests': tests,
            'metadata': metadata,
            'quality': quality_result,
            'stats': stats,
            'trace': trace_result
        }
    
    def _generate_class_name(self, name: str) -> str:
        """生成类名"""
        words = name.replace('-', '_').replace(' ', '_').split('_')
        return ''.join(word.capitalize() for word in words)
    
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
    
    # ==================== 阶段1：优化参数验证生成 ====================
    
    def _generate_validate_inputs(self, spec: SkillSpec) -> List[str]:
        """生成参数验证代码"""
        lines = []
        lines.append('    def _validate_inputs(self, **kwargs) -> bool:')
        lines.append('        """')
        lines.append('        验证输入参数')
        lines.append('        ')
        lines.append('        Args:')
        lines.append('            **kwargs: 输入参数')
        lines.append('            ')
        lines.append('        Returns:')
        lines.append('            验证是否通过')
        lines.append('        """')
        
        # 收集必填参数
        required = [inp for inp in spec.inputs if inp.get('required', False)]
        optional = [inp for inp in spec.inputs if not inp.get('required', False)]
        
        # 检查必填参数是否存在
        if required:
            lines.append('        # 检查必填参数')
            lines.append('        required_params = [' + ', '.join([f'"{inp["name"]}"' for inp in required]) + ']')
            lines.append('        for param in required_params:')
            lines.append('            if param not in kwargs or kwargs[param] is None or kwargs[param] == "":')
            lines.append('                raise ValueError(f"缺少必需参数: {param}")')
            lines.append('')
        
        # 根据参数类型生成验证
        if spec.inputs:
            lines.append('        # 类型验证')
            for inp in spec.inputs:
                name = inp.get('name', '')
                type_str = inp.get('type', 'string')
                default = inp.get('default', '')
                
                if type_str in ['integer', 'int']:
                    lines.append(f'        if "{name}" in kwargs and kwargs["{name}"] is not None:')
                    lines.append(f'            try:')
                    lines.append(f'                kwargs["{name}"] = int(kwargs["{name}"])')
                    lines.append(f'            except (ValueError, TypeError):')
                    lines.append(f'                raise ValueError(f"参数 {name} 必须是整数")')
                elif type_str in ['float', 'number']:
                    lines.append(f'        if "{name}" in kwargs and kwargs["{name}"] is not None:')
                    lines.append(f'            try:')
                    lines.append(f'                kwargs["{name}"] = float(kwargs["{name}"])')
                    lines.append(f'            except (ValueError, TypeError):')
                    lines.append(f'                raise ValueError(f"参数 {name} 必须是数字")')
                elif type_str in ['boolean', 'bool']:
                    lines.append(f'        if "{name}" in kwargs and kwargs["{name}"] is not None:')
                    lines.append(f'            if isinstance(kwargs["{name}"], str):')
                    lines.append(f'                kwargs["{name}"] = kwargs["{name}"].lower() in ["true", "1", "yes", "on"]')
                elif type_str in ['list', 'array', 'json']:
                    lines.append(f'        if "{name}" in kwargs and kwargs["{name}"] is not None:')
                    lines.append(f'            if isinstance(kwargs["{name}"], str):')
                    lines.append(f'                try:')
                    lines.append(f'                    import json')
                    lines.append(f'                    kwargs["{name}"] = json.loads(kwargs["{name}"])')
                    lines.append(f'                except json.JSONDecodeError:')
                    lines.append(f'                    raise ValueError(f"参数 {name} 必须是有效的 JSON")')
        
        # 设置默认值（只在参数未提供或为空时设置）
        if optional:
            lines.append('')
            lines.append('        # 设置默认值')
            for inp in optional:
                name = inp.get('name', '')
                default = inp.get('default', '')
                if default and default != '-':
                    # 对于字符串类型，用引号包裹
                    if isinstance(default, str) and not default.startswith(('"', "'")):
                        default_repr = repr(default)
                    else:
                        default_repr = repr(default)
                    lines.append(f'        if "{name}" not in kwargs or kwargs["{name}"] is None:')
                    lines.append(f'            kwargs["{name}"] = {default_repr}')
                elif default == '-':
                    # '-' 表示无默认值，使用空字符串
                    lines.append(f'        if "{name}" not in kwargs or kwargs["{name}"] is None:')
                    lines.append(f'            kwargs["{name}"] = ""')
        
        lines.append('')
        lines.append('        return True')
        
        return lines
    
    # ==================== 阶段2：优化步骤方法生成 ====================
    
    def _generate_steps_methods(self, spec: SkillSpec, has_steps: bool) -> List[str]:
        """生成步骤方法"""
        methods = []
        
        if not has_steps:
            return methods
        
        for i, step in enumerate(spec.steps):
            method_name = self._step_to_method_name(step, i)
            method_code = self._generate_step_method_by_type(method_name, step, i, spec)
            methods.append(method_code)
        
        return methods
    
    def _generate_step_method_by_type(self, method_name: str, step: str, index: int, spec: SkillSpec) -> str:
        """根据步骤类型生成不同的实现"""
        
        step_lower = step.lower()
        
        # 检测步骤类型并生成对应实现
        if any(kw in step_lower for kw in ['读取', 'load', '加载']):
            return self._generate_load_step(method_name, step)
        elif any(kw in step_lower for kw in ['保存', 'save', '存储', '导出']):
            return self._generate_save_step(method_name, step)
        elif any(kw in step_lower for kw in ['处理', 'process', '转换', 'transform']):
            return self._generate_process_step(method_name, step)
        elif any(kw in step_lower for kw in ['分析', 'analyze', '统计', '计算']):
            return self._generate_analyze_step(method_name, step)
        elif any(kw in step_lower for kw in ['验证', 'validate', '检查', 'check']):
            return self._generate_validate_step(method_name, step)
        elif any(kw in step_lower for kw in ['生成', 'generate', '创建', 'create']):
            return self._generate_generate_step(method_name, step)
        else:
            return self._generate_generic_step(method_name, step)
    
    def _generate_load_step(self, method_name: str, step: str) -> str:
        """生成加载步骤"""
        return f'''    def {method_name}(self, **kwargs):
            """
            {step}
            """
            logger.info(f"执行步骤: {step}")
            
            # 获取数据源
            source = kwargs.get("source") or kwargs.get("file_path") or kwargs.get("data_source")
            if not source:
                for key in ["md_file", "file", "path", "input"]:
                    if key in kwargs and kwargs[key]:
                        source = kwargs[key]
                        break
            
            if not source:
                raise ValueError("未指定数据源")
            
            try:
                data = self._load_data(source, **kwargs)
                kwargs["data"] = data
                logger.info(f"数据加载成功: {{source}}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据加载失败: {{e}}")
                raise
            
            return kwargs'''
        
    def _generate_save_step(self, method_name: str, step: str) -> str:
        """生成保存步骤"""
        return f'''    def {method_name}(self, **kwargs):
            """
            {step}
            """
            logger.info(f"执行步骤: {step}")
            
            data = kwargs.get("data") or kwargs.get("result")
            destination = kwargs.get("destination") or kwargs.get("output") or kwargs.get("output_path")
            
            if not destination:
                for key in ["output_file", "save_path", "path"]:
                    if key in kwargs and kwargs[key]:
                        destination = kwargs[key]
                        break
            
            if not destination:
                raise ValueError("未指定保存路径")
            
            if data is None:
                raise ValueError("没有数据可保存")
            
            try:
                self._save_data(data, destination, **kwargs)
                kwargs["saved_path"] = destination
                logger.info(f"数据保存成功: {{destination}}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据保存失败: {{e}}")
                raise
            
            return kwargs'''
        
    def _generate_process_step(self, method_name: str, step: str) -> str:
        """生成处理步骤"""
        return f'''    def {method_name}(self, **kwargs):
        """
        {step}
        """
        logger.info(f"执行步骤: {step}")
        
        # 获取要处理的数据
        data = kwargs.get("data") or kwargs.get("input_data")
        if data is None:
            # 尝试从其他参数获取
            for key in ["content", "text", "input"]:
                if key in kwargs and kwargs[key]:
                    data = kwargs[key]
                    break
        
        if data is None:
            raise ValueError("没有数据可处理")
        
        # 处理数据
        try:
            processed = self._process_data(data, **kwargs)
            kwargs["processed_data"] = processed
            kwargs["data"] = processed
            logger.info(f"数据处理完成")
        except Exception as e:
            logger.error(f"数据处理失败: {{e}}")
            raise
        
        return kwargs'''
    
    def _generate_analyze_step(self, method_name: str, step: str) -> str:
        """生成分析步骤"""
        return f'''    def {method_name}(self, **kwargs):
        """
        {step}
        """
        logger.info(f"执行步骤: {step}")
        
        # 获取要分析的数据
        data = kwargs.get("data") or kwargs.get("input_data")
        if data is None:
            for key in ["content", "text", "result"]:
                if key in kwargs and kwargs[key]:
                    data = kwargs[key]
                    break
        
        if data is None:
            raise ValueError("没有数据可分析")
        
        # 分析数据
        try:
            analysis_result = self._analyze_data(data, **kwargs)
            kwargs["analysis"] = analysis_result
            logger.info("数据分析完成: %s 字符" % len(str(analysis_result)))
        except Exception as e:
            logger.error(f"数据分析失败: {{e}}")
            raise
        
        return kwargs'''
    
    def _generate_validate_step(self, method_name: str, step: str) -> str:
        """生成验证步骤"""
        return f'''    def {method_name}(self, **kwargs):
            """
            {step}
            """
            logger.info(f"执行步骤: {step}")
            
            # 获取要验证的数据
            data = kwargs.get("data") or kwargs.get("input_data")
            if data is None:
                for key in ["content", "text", "result"]:
                    if key in kwargs and kwargs[key]:
                        data = kwargs[key]
                        break
            
            if data is None:
                raise ValueError("没有数据可验证")
            
            # 验证数据
            try:
                is_valid = self._validate_data(data, **kwargs)
                if not is_valid:
                    raise ValueError("数据验证失败")
                kwargs["validated"] = True
                logger.info(f"数据验证通过")
            except Exception as e:
                logger.error(f"数据验证失败: {{e}}")
                raise
            
            return kwargs'''
    
    def _generate_generate_step(self, method_name: str, step: str) -> str:
        """生成生成步骤"""
        return f'''    def {method_name}(self, **kwargs):
            """
            {step}
            """
            logger.info(f"执行步骤: {step}")
            
            params = {{k: v for k, v in kwargs.items() if k not in ["self"]}}
            
            try:
                result = self._generate_result(params, **kwargs)
                kwargs["generated"] = result
                logger.info(f"生成完成")
            except Exception as e:
                logger.error(f"生成失败: {{e}}")
                raise
            
            return kwargs'''
        
    def _generate_generic_step(self, method_name: str, step: str) -> str:
        """生成通用步骤"""
        return f'''    def {method_name}(self, **kwargs):
            """
            {step}
            """
            logger.info(f"执行步骤: {step}")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {{len(input_data)}} 项")
                else:
                    logger.info(f"处理数据: {{type(input_data).__name__}}")
                kwargs["processed"] = input_data
            
            return kwargs'''
        
    # ==================== 阶段3：优化辅助方法 ====================
    
    def _generate_helper_methods(self, spec: SkillSpec, has_steps: bool) -> str:
        """生成辅助方法"""
        helpers = []
        
        # 始终包含基础辅助方法
        helpers.append(self._generate_base_helpers())
        
        # 只有有步骤时才生成具体辅助方法
        if has_steps:
            step_text = ' '.join(spec.steps)
            
            if any(kw in step_text.lower() for kw in ['读取', 'load', '加载']):
                helpers.append(self._generate_load_helper())
            
            if any(kw in step_text.lower() for kw in ['保存', 'save', '存储', '导出']):
                helpers.append(self._generate_save_helper())
            
            if any(kw in step_text.lower() for kw in ['处理', 'process', '转换']):
                helpers.append(self._generate_process_helper())
            
            if any(kw in step_text.lower() for kw in ['分析', 'analyze', '统计']):
                helpers.append(self._generate_analyze_helper())
            
            if any(kw in step_text.lower() for kw in ['验证', 'validate', '检查']):
                helpers.append(self._generate_validate_helper())
            
            if any(kw in step_text.lower() for kw in ['生成', 'generate', '创建']):
                helpers.append(self._generate_generate_helper())
        
        return '\n'.join(helpers) if helpers else ''
    
    def _generate_base_helpers(self) -> str:
        """生成基础辅助方法"""
        return '''
    def _handle_error(self, error: Exception, context: str = "") -> Dict:
        """处理错误"""
        logger.error(f"{context}: {error}")
        return {
            "status": "error",
            "error": str(error),
            "context": context
        }
    
    def _log_step(self, step_name: str, **kwargs):
        """记录步骤日志"""
        logger.info(f"步骤: {step_name}")
'''
    
    def _generate_load_helper(self) -> str:
        """生成加载辅助方法"""
        return '''
    def _load_data(self, source: str, **kwargs) -> Any:
        """加载数据"""
        import json
        from pathlib import Path
        
        if source.startswith(('http://', 'https://')):
            import requests
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type:
                return response.json()
            elif 'text' in content_type:
                return response.text
            else:
                return response.content
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {source}")
            
            if source.endswith(('.csv', '.tsv')):
                import pandas as pd
                return pd.read_csv(source)
            elif source.endswith('.json'):
                with open(source, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif source.endswith(('.yaml', '.yml')):
                import yaml
                with open(source, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    return f.read()
'''
    
    def _generate_save_helper(self) -> str:
        """生成保存辅助方法"""
        return '''
    def _save_data(self, data: Any, destination: str, **kwargs) -> bool:
        """保存数据"""
        import json
        from pathlib import Path
        
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        if destination.endswith('.json'):
            with open(destination, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif destination.endswith('.csv'):
            import pandas as pd
            if isinstance(data, (list, dict)):
                pd.DataFrame(data).to_csv(destination, index=False)
            else:
                pd.DataFrame([data]).to_csv(destination, index=False)
        elif destination.endswith(('.yaml', '.yml')):
            import yaml
            with open(destination, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        else:
            with open(destination, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        logger.info(f"数据已保存: {destination}")
        return True
'''
    
    def _generate_process_helper(self) -> str:
        """生成处理辅助方法"""
        return '''
    def _process_data(self, data: Any, **kwargs) -> Any:
        """处理数据"""
        if isinstance(data, list):
            return [self._process_item(item, **kwargs) for item in data]
        elif isinstance(data, dict):
            return {k: self._process_item(v, **kwargs) for k, v in data.items()}
        else:
            return self._process_item(data, **kwargs)
    
    def _process_item(self, item: Any, **kwargs) -> Any:
        """处理单个数据项"""
        # 默认返回原值
        return item
'''
    
    def _generate_analyze_helper(self) -> str:
        """生成分析辅助方法"""
        return '''
    def _analyze_data(self, data: Any, **kwargs) -> Dict:
        """分析数据"""
        result = {
            "type": type(data).__name__,
            "size": 0,
            "summary": {}
        }
        
        if isinstance(data, list):
            result["size"] = len(data)
            if data:
                result["first_item"] = data[0] if not isinstance(data[0], (list, dict)) else str(data[0])[:100]
        elif isinstance(data, dict):
            result["size"] = len(data)
            result["keys"] = list(data.keys())[:20]
        elif isinstance(data, str):
            result["size"] = len(data)
            result["words"] = len(data.split())
        elif isinstance(data, (int, float)):
            result["value"] = data
        
        return result
'''
    
    def _generate_validate_helper(self) -> str:
        """生成验证辅助方法"""
        return '''
    def _validate_data(self, data: Any, **kwargs) -> bool:
        """验证数据"""
        if data is None:
            logger.warning("数据为空")
            return False
        
        if isinstance(data, (list, dict)) and not data:
            logger.warning("数据为空容器")
            return False
        
        if isinstance(data, str) and not data.strip():
            logger.warning("数据为空字符串")
            return False
        
        logger.info(f"数据验证通过: 类型={type(data).__name__}")
        return True
'''
    
    def _generate_generate_helper(self) -> str:
        """生成生成辅助方法"""
        return '''
    def _generate_result(self, params: Dict, **kwargs) -> Dict:
        """生成结果"""
        from datetime import datetime
        
        return {
            "status": "success",
            "generated_at": datetime.now().isoformat(),
            "params": params,
            "result": params
        }
'''
    
    # ==================== 主类代码生成 ====================
    
    def _generate_class_code(self, spec: SkillSpec, class_name: str) -> str:
        """生成类代码"""
        imports = self._generate_imports(spec.dependencies)
        
        # 判断是否有步骤
        has_steps = len(spec.steps) > 0
        
        # 生成各部分
        validate_method = self._generate_validate_inputs(spec)
        step_methods = self._generate_steps_methods(spec, has_steps)
        helper_methods = self._generate_helper_methods(spec, has_steps)
        
        code_lines = []
        
        # 文件头
        code_lines.append('"""')
        code_lines.append(f'{spec.name} - {spec.description}')
        code_lines.append('')
        code_lines.append(self._format_docstring(spec))
        code_lines.append('"""')
        code_lines.append('')
        code_lines.append(imports)
        code_lines.append('')
        code_lines.append('import logging')
        code_lines.append('from typing import Dict, Any, Optional, List')
        code_lines.append('from pathlib import Path')
        code_lines.append('from datetime import datetime')
        code_lines.append('import json')
        code_lines.append('')
        code_lines.append('logger = logging.getLogger(__name__)')
        code_lines.append('')
        code_lines.append('')
        code_lines.append(f'class {class_name}:')
        code_lines.append('    """')
        code_lines.append(f'    {spec.description}')
        code_lines.append('    ')
        code_lines.append(f'    {self._format_purpose(spec.purpose)}')
        code_lines.append('    """')
        code_lines.append('    ')
        code_lines.append('    def __init__(self, config: Dict[str, Any] = None):')
        code_lines.append('        """')
        code_lines.append('        初始化技能')
        code_lines.append('        ')
        code_lines.append('        Args:')
        code_lines.append('            config: 配置参数字典')
        code_lines.append('        """')
        code_lines.append('        self.config = config or {}')
        code_lines.append(f'        self.name = "{spec.name}"')
        code_lines.append(f'        self.version = "{spec.version}"')
        code_lines.append('        self._setup_logging()')
        code_lines.append('        self._setup_config()')
        code_lines.append('    ')
        code_lines.append('    def _setup_logging(self):')
        code_lines.append('        """设置日志"""')
        code_lines.append('        log_level = self.config.get(\'log_level\', \'INFO\')')
        code_lines.append('        logging.basicConfig(')
        code_lines.append('            level=getattr(logging, log_level.upper()),')
        code_lines.append('            format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'')
        code_lines.append('        )')
        code_lines.append('    ')
        code_lines.append('    def _setup_config(self):')
        code_lines.append('        """设置配置"""')
        code_lines.append('        defaults = {}')
        for key, value in spec.config.items():
            if isinstance(value, str):
                code_lines.append(f'        defaults["{key}"] = "{value}"')
            else:
                code_lines.append(f'        defaults["{key}"] = {repr(value)}')
        code_lines.append('        for key, value in defaults.items():')
        code_lines.append('            if key not in self.config:')
        code_lines.append('                self.config[key] = value')
        code_lines.append('    ')
        
        # 添加验证方法
        for line in validate_method:
            code_lines.append(line)
        code_lines.append('    ')
        
        # 执行方法
        code_lines.append('    def execute(self, **kwargs) -> Dict[str, Any]:')
        code_lines.append('        """')
        code_lines.append('        执行技能')
        code_lines.append('        ')
        code_lines.append('        Args:')
        code_lines.append('            **kwargs: 输入参数')
        code_lines.append('            ')
        code_lines.append('        Returns:')
        code_lines.append('            执行结果')
        code_lines.append('        """')
        code_lines.append('        logger.info(f"执行技能: {self.name} (v{self.version})")')
        code_lines.append('        ')
        code_lines.append('        try:')
        code_lines.append('            self._validate_inputs(**kwargs)')
        code_lines.append('            ')
        
        if has_steps:
            code_lines.append('            # 执行步骤')
            for i, step in enumerate(spec.steps):
                method_name = self._step_to_method_name(step, i)
                code_lines.append(f'            kwargs = self.{method_name}(**kwargs)')
            code_lines.append('            ')
            code_lines.append('            result_data = kwargs')
        else:
            code_lines.append('            # 没有定义步骤，直接返回参数')
            code_lines.append('            result_data = kwargs')
        
        code_lines.append('            ')
        code_lines.append('            result = {')
        code_lines.append('                "status": "success",')
        code_lines.append('                "result": result_data,')
        code_lines.append('                "metadata": {')
        code_lines.append('                    "skill": self.name,')
        code_lines.append('                    "version": self.version,')
        code_lines.append('                    "executed_at": datetime.now().isoformat()')
        code_lines.append('                }')
        code_lines.append('            }')
        code_lines.append('            ')
        code_lines.append('            logger.info(f"技能执行成功: {self.name}")')
        code_lines.append('            return result')
        code_lines.append('            ')
        code_lines.append('        except Exception as e:')
        code_lines.append('            logger.error(f"技能执行失败: {e}")')
        code_lines.append('            return {')
        code_lines.append('                "status": "error",')
        code_lines.append('                "error": str(e),')
        code_lines.append('                "skill": self.name,')
        code_lines.append('                "timestamp": datetime.now().isoformat()')
        code_lines.append('            }')
        code_lines.append('    ')
        
        # 添加步骤方法
        if step_methods:
            for method in step_methods:
                for line in method.split('\n'):
                    code_lines.append(line)
                code_lines.append('')
        
        # 添加辅助方法
        if helper_methods:
            for line in helper_methods.split('\n'):
                code_lines.append(line)
        
        code_lines.append('    def __repr__(self):')
        code_lines.append(f'        return f"<{class_name}(name={{self.name}}, version={{self.version}})>"')
        
        return '\n'.join(code_lines)
    
    # ==================== 其他方法 ====================
    
    def _generate_imports(self, dependencies: List[str]) -> str:
        """生成导入语句"""
        import_map = {
            'pandas': 'import pandas as pd',
            'numpy': 'import numpy as np',
            'requests': 'import requests',
            'yaml': 'import yaml',
            'json': 'import json',
        }
        
        imports = ['import os', 'import sys', 'import re', 'import time', 'import random', 'import json']
        
        for dep in dependencies:
            if dep in import_map:
                imports.append(import_map[dep])
            elif dep:
                imports.append(f'# import {dep}  # 可选依赖')
        
        return '\n'.join(list(set(imports)))
    
    def _step_to_method_name(self, step: str, index: int) -> str:
        """将步骤转换为方法名"""
        verbs = ['load', 'process', 'validate', 'transform', 'analyze', 
                'generate', 'save', 'export', 'import', 'convert', 'check']
        
        step_lower = step.lower()
        for verb in verbs:
            if verb in step_lower:
                parts = step_lower.split(verb, 1)
                if len(parts) > 1:
                    keywords = parts[1].strip()
                    words = re.findall(r'\w+', keywords)
                    if words:
                        return f"_{verb}_{'_'.join(words[:2])}"
                return f"_{verb}_data"
        
        return f"_step_{index + 1}"
    
    def _generate_metadata(self, spec: SkillSpec) -> Dict:
        """生成元数据"""
        cleaned_inputs = []
        for inp in spec.inputs:
            cleaned = inp.copy()
            cleaned['name'] = self._clean_name(inp.get('name', ''))
            cleaned_inputs.append(cleaned)
        
        cleaned_outputs = []
        for out in spec.outputs:
            cleaned = out.copy()
            cleaned['name'] = self._clean_name(out.get('name', ''))
            name = cleaned['name']
            if name in ['路径', '说明', '------', '---']:
                continue
            if '/' in name or '{' in name or '.ext' in name:
                continue
            cleaned_outputs.append(cleaned)
        
        return {
            "name": spec.name,
            "version": spec.version,
            "description": spec.description,
            "tags": spec.tags,
            "dependencies": spec.dependencies,
            "inputs": cleaned_inputs,
            "outputs": cleaned_outputs,
            "config": spec.config
        }
    
    def _format_docstring(self, spec: SkillSpec) -> str:
        """格式化文档字符串"""
        parts = []
        if spec.purpose:
            parts.append(f"目的: {spec.purpose}")
        if spec.inputs:
            parts.append("")
            parts.append("输入参数:")
            for inp in spec.inputs:
                name = self._clean_name(inp.get('name', ''))
                parts.append(f"  - {name} ({inp.get('type', 'string')}): {inp.get('description', '')}")
        if spec.outputs:
            parts.append("")
            parts.append("输出:")
            for out in spec.outputs:
                name = self._clean_name(out.get('name', ''))
                if name in ['路径', '说明', '------', '---']:
                    continue
                if '/' in name or '{' in name or '.ext' in name:
                    continue
                parts.append(f"  - {name}: {out.get('description', '')}")
        if spec.steps:
            parts.append("")
            parts.append("执行步骤:")
            for i, step in enumerate(spec.steps, 1):
                parts.append(f"  {i}. {step}")
        return '\n'.join(parts)
    
    def _format_purpose(self, purpose: str) -> str:
        """格式化目的"""
        if purpose:
            return purpose.strip()
        return "执行技能功能"
    
    def _generate_tests(self, spec: SkillSpec, code: str) -> str:
        """生成单元测试"""
        class_name = self._generate_class_name(spec.name)
        skill_name = spec.name.lower().replace(' ', '_')
        
        test_lines = []
        test_lines.append('"""')
        test_lines.append(f'{spec.name} 单元测试')
        test_lines.append('"""')
        test_lines.append('')
        test_lines.append('import unittest')
        test_lines.append('import sys')
        test_lines.append('from pathlib import Path')
        test_lines.append('')
        test_lines.append('sys.path.insert(0, str(Path(__file__).parent.parent))')
        test_lines.append('')
        test_lines.append(f'from skills.{skill_name}.skill import {class_name}')
        test_lines.append('')
        test_lines.append('')
        test_lines.append(f'class Test{class_name}(unittest.TestCase):')
        test_lines.append('    """')
        test_lines.append(f'    {class_name} 测试类')
        test_lines.append('    """')
        test_lines.append('')
        test_lines.append('    def setUp(self):')
        test_lines.append('        """测试前准备"""')
        test_lines.append(f'        self.skill = {class_name}()')
        test_lines.append('')
        
        if spec.inputs:
            test_lines.append('    def test_execute_with_valid_params(self):')
            test_lines.append('        """测试正常执行"""')
            
            params = []
            for inp in spec.inputs:
                name = self._clean_name(inp.get('name', ''))
                if not name:
                    continue
                default = inp.get('default', '')
                if default and default != '-':
                    params.append(f'{name}={repr(default)}')
                else:
                    params.append(f'{name}=""')
            
            if params:
                params_str = ', '.join(params)
                test_lines.append(f'        result = self.skill.execute({params_str})')
            else:
                test_lines.append('        result = self.skill.execute()')
            
            test_lines.append('        self.assertEqual(result.get("status"), "success")')
            test_lines.append('        self.assertIn("result", result)')
            test_lines.append('')
        
        test_lines.append('    def test_skill_metadata(self):')
        test_lines.append('        """测试技能元数据"""')
        test_lines.append(f'        self.assertEqual(self.skill.name, "{spec.name}")')
        test_lines.append('        self.assertIsInstance(self.skill.version, str)')
        test_lines.append('')
        
        test_lines.append('')
        test_lines.append('if __name__ == "__main__":')
        test_lines.append('    unittest.main()')
        
        return '\n'.join(test_lines)