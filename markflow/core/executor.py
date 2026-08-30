# markflow/core/executor.py
"""
技能执行器 - 执行和管理技能
"""

from typing import Dict, Any, Optional, List, Set
from pathlib import Path
import logging
from .registry import SkillRegistry
from .generator import CodeGenerator
from .parser import MarkdownParser, SkillSpec
from .quality import CodeQualityChecker  # 新增导入
from .project_builder import ProjectBuilder  # 新增导入

logger = logging.getLogger(__name__)

from .project_builder import ProjectBuilder  # 新增导入
import json  

class SkillExecutor:
    """技能执行器"""
    
    def __init__(self, registry: SkillRegistry = None):
        self.registry = registry or SkillRegistry()
        self.parser = MarkdownParser()
        self.generator = CodeGenerator()
        self.project_builder = ProjectBuilder()  # 新增
        self.quality_checker = CodeQualityChecker()  # 新增
        self._executed_skills = set()  # 新增：记录已执行的技能

    # ==================== 新增配置处理方法 ====================
    
    def apply_config_defaults(
        self,
        user_config: Dict[str, Any],
        defaults: Dict[str, Any],
        extra_valid_keys: Set[str] = None,
        skill_name: str = None
    ) -> Dict[str, Any]:
        """
        应用配置默认值，过滤未知键
        
        Args:
            user_config: 用户传入的配置
            defaults: 默认配置
            extra_valid_keys: 额外允许的有效键（如 log_level）
            skill_name: 技能名称（用于日志）
        
        Returns:
            合并后的配置
        """
        valid_keys = set(defaults.keys())
        if extra_valid_keys:
            valid_keys |= set(extra_valid_keys)
        
        # 过滤用户配置，只保留有效键
        filtered_config = {k: v for k, v in user_config.items() if k in valid_keys}
        
        # 记录被忽略的键
        ignored_keys = set(user_config.keys()) - valid_keys
        if ignored_keys:
            name = skill_name or "Unknown"
            logger.warning(f"[{name}] 忽略未知配置键: {', '.join(ignored_keys)}")
        
        # 合并默认值
        result = defaults.copy()
        result.update(filtered_config)
        
        return result
    
    def get_skill_default_config(self, skill_name: str) -> Dict[str, Any]:
        """
        从技能的 meta.json 获取默认配置
        
        Args:
            skill_name: 技能名称
        
        Returns:
            默认配置字典
        """
        skill_dir = self.registry.storage_dir / skill_name
        meta_file = skill_dir / "meta.json"
        
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                return meta.get('config', {})
            except Exception as e:
                logger.warning(f"读取 {skill_name} 的 meta.json 失败: {e}")
        
        return {}
        
    def build_from_markdown(self, markdown_content: str, save: bool = True,
                            quality_check: bool = True, format_code: bool = True,
                            generate_tests: bool = True, review: bool = False,
                            model: str = "qwen2.5:7b") -> Dict[str, Any]:
        """
        从Markdown构建技能
        
        Args:
            markdown_content: Markdown内容
            save: 是否保存到文件
            quality_check: 是否执行质量检查
            format_code: 是否格式化代码
            generate_tests: 是否生成测试
            review: 是否执行AI审查
            model: Ollama模型名称
            
        Returns:
            构建结果
        """
        import json
        
        spec = self.parser.parse(markdown_content)
        
        # 生成代码
        result = self.generator.generate(
            spec, 
            quality_check=quality_check,
            format_code=format_code,
            generate_tests=generate_tests
        )
        
        # 注册技能
        self._register_generated_skill(result)
        
        # 执行AI审查
        if review:
            logger.info("执行AI代码审查...")
            quality_checker = CodeQualityChecker()
            review_result = quality_checker.review_code_with_ollama(
                result['code'], 
                "python",
                model=model
            )
            result['review'] = review_result
        
        # 保存到文件（使用新格式）
        if save:
            skill_name = result['class_name'].lower()
            skill_dir = self.registry.storage_dir / skill_name
            
            # 生成完整项目结构
            project_files = self.project_builder.generate_project(
                spec,
                result['code'],
                result.get('tests', ''),
                result.get('quality'),
                result.get('trace')
            )
            
            saved_paths = self.project_builder.save_project(project_files, self.registry.storage_dir)
            logger.info(f"项目已保存: {skill_dir} ({len(saved_paths)} 个文件)")
            
            # 更新结果
            result['saved_files'] = [str(p) for p in saved_paths]
            result['project_dir'] = str(skill_dir)
        
        return result

    def build_from_markdown_with_auto_fix(
        self,
        markdown_content: str,
        save: bool = True,
        quality_check: bool = True,
        format_code: bool = True,
        generate_tests: bool = True,
        review: bool = True,
        auto_fix: bool = False,
        iterations: int = 1,
        model: str = "qwen2.5:7b"
    ) -> Dict[str, Any]:
        """
        从Markdown构建技能，支持AI自动修复
        """
        import json
        import re
        
        # 第一轮：生成
        result = self.build_from_markdown(
            markdown_content,
            save=False,
            quality_check=quality_check,
            format_code=format_code,
            generate_tests=generate_tests,
            review=False
        )
        
        if not auto_fix:
            if review:
                review_result = self.quality_checker.review_code_with_ollama(
                    result['code'], "python", model=model
                )
                result['review'] = review_result
                result['final_score'] = review_result.get('score', 0)
            return result
        
        # ===== 自动修复模式 =====
        iteration_history = []
        current_code = result['code']
        current_spec = self.parser.parse(markdown_content)
        
        for i in range(iterations):
            print(f"\n🔄 迭代 {i+1}/{iterations}")
            
            # 执行 AI 审查
            print("📋 执行 AI 审查...")
            try:
                review_result = self.quality_checker.review_code_with_ollama(
                    current_code, "python", model=model
                )
            except Exception as e:
                print(f"   ⚠️ 审查异常: {e}")
                review_result = {"score": 0, "issues": [f"审查异常: {e}"], "suggestions": []}
            
            score = review_result.get("score", 0)
            issues = review_result.get("issues", [])
            suggestions = review_result.get("suggestions", [])
            
            print(f"   评分: {score}/100")
            print(f"   问题: {len(issues)} 个")
            print(f"   建议: {len(suggestions)} 个")
            
            iteration_history.append({
                "iteration": i + 1,
                "score": score,
                "issues": issues,
                "suggestions": suggestions
            })
            
            # 如果评分 >= 80，停止迭代
            if score >= 80:
                print(f"✅ 评分 {score}/100，达到目标，停止迭代")
                result['final_score'] = score
                break
            
            # 如果是最后一轮，停止（不修复）
            if i == iterations - 1:
                print(f"⚠️ 达到最大迭代次数 {iterations}")
                result['final_score'] = score
                break
            
            # ===== 执行修复 =====
            print("🔧 AI 正在根据审查结果修复代码...")
            fixed_code = self._fix_code_with_ai(
                current_code,
                review_result,
                current_spec,
                model
            )
            
            if fixed_code and fixed_code != current_code and len(fixed_code) > 100:
                current_code = fixed_code
                print(f"   ✅ 代码已修复，长度: {len(current_code)} 字符")
                
                if format_code:
                    current_code = self.quality_checker.format_code(current_code, "python")
            else:
                print("   ⚠️ 修复未产生变化，停止迭代")
                result['final_score'] = score
                break
        
        # 更新结果
        result['code'] = current_code
        result['iteration_history'] = iteration_history
        result['auto_fixed'] = True
        
        # 如果 final_score 没有设置，用最后一次的评分
        if 'final_score' not in result:
            result['final_score'] = iteration_history[-1].get('score', 0) if iteration_history else 0
        
        # 保存到文件
        if save:
            spec = current_spec
            class_name = result['class_name']
            skill_name = class_name.lower()
            skill_dir = self.registry.storage_dir / skill_name
            
            project_files = self.project_builder.generate_project(
                spec,
                current_code,
                result.get('tests', ''),
                result.get('quality'),
                result.get('trace')
            )
            
            saved_paths = self.project_builder.save_project(project_files, self.registry.storage_dir)
            result['saved_files'] = [str(p) for p in saved_paths]
            result['project_dir'] = str(skill_dir)
            
            logger.info(f"项目已保存: {skill_dir} ({len(saved_paths)} 个文件)")
        
        return result


    def _fix_code_with_ai(
        self,
        code: str,
        review_result: Dict,
        spec,
        model: str = "qwen2.5:7b"
    ) -> str:
        """使用 AI 根据审查结果修复代码"""
        import requests
        import re
        
        issues = review_result.get("issues", [])
        suggestions = review_result.get("suggestions", [])
        
        if not issues and not suggestions:
            return code
        
        # 构建输入参数信息
        inputs_str = ', '.join([inp.get('name', '') for inp in spec.inputs]) if hasattr(spec, 'inputs') else ''
        outputs_str = ', '.join([out.get('name', '') for out in spec.outputs]) if hasattr(spec, 'outputs') else ''
        
        # 构建修复提示 - 使用字符串拼接，避免 f-string 花括号冲突
        prompt = '请根据以下审查结果优化这段 Python 代码。\n\n'
        prompt += '## 技能信息\n'
        prompt += '名称: ' + spec.name + '\n'
        prompt += '描述: ' + spec.description + '\n'
        prompt += '输入参数: ' + inputs_str + '\n'
        prompt += '输出: ' + outputs_str + '\n\n'
        prompt += '## 当前代码\n'
        prompt += '```python\n'
        prompt += code + '\n'
        prompt += '```\n\n'
        prompt += '## 审查发现的问题\n'
        for issue in issues:
            prompt += '- ' + issue + '\n'
        prompt += '\n'
        prompt += '## 改进建议\n'
        for suggestion in suggestions:
            prompt += '- ' + suggestion + '\n'
        prompt += '\n'
        prompt += '## 要求\n'
        prompt += '1. 修复所有问题，实现建议的改进\n'
        prompt += '2. 保持代码结构不变，只修改有问题的部分\n'
        prompt += '3. 添加必要的错误处理\n'
        prompt += '4. 确保代码完整可运行\n'
        prompt += '5. 只输出修复后的完整 Python 代码，不要其他解释\n\n'
        prompt += '请输出完整的 Python 代码：'
        
        try:
            response = requests.post(
                f"{self.quality_checker.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 4096
                    }
                },
                timeout=600
            )
            response.raise_for_status()
            data = response.json()
            result_text = data.get("response", "").strip()
            
            # 提取代码块
            code_match = re.search(r'```python\s*\n(.*?)\n```', result_text, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            # 尝试提取任何代码块
            code_match = re.search(r'```\s*\n(.*?)\n```', result_text, re.DOTALL)
            if code_match:
                return code_match.group(1)
            
            # 如果没有代码块，检查是否直接是代码
            if 'def ' in result_text or 'class ' in result_text:
                return result_text
            
            return code
            
        except Exception as e:
            logger.error(f"AI 修复失败: {e}")
            return code
        
        
    def execute(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_name: 技能名称
            **kwargs: 执行参数
        
        Returns:
            执行结果
        """
        try:
            instance = self.registry.get_instance(skill_name)

            # 记录执行的技能
            self._executed_skills.add(skill_name)            
            
            # ✅ 自动应用配置默认值到 instance.config
            if hasattr(instance, 'config') and hasattr(instance, 'name'):
                # 获取技能内置默认配置（如果有 _get_default_config 方法）
                if hasattr(instance, '_get_default_config'):
                    defaults = instance._get_default_config()
                else:
                    # 从 meta.json 获取
                    defaults = self.get_skill_default_config(instance.name)
                
                if defaults:
                    instance.config = self.apply_config_defaults(
                        instance.config,
                        defaults,
                        extra_valid_keys={'log_level'},
                        skill_name=instance.name
                    )
            
            return instance.execute(**kwargs)

            # ========== 新增：执行后清理 ==========
            # 如果技能有 pipeline 属性，尝试清理（如果是 SD 技能）
            if hasattr(instance, 'pipeline'):
                try:
                    # 将 pipeline 移到 CPU 并清空缓存（不强制卸载）
                    if hasattr(instance.pipeline, 'to'):
                        instance.pipeline.to('cpu')
                    # 记录需要清理
                    self._executed_skills.add(skill_name)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"执行技能失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": skill_name
            }

    def clear_model_cache(self, skill_name: str = None):
        """清理模型缓存"""
        if skill_name:
            if skill_name in self._executed_skills:
                self._executed_skills.remove(skill_name)
                logger.info(f"已清理技能缓存: {skill_name}")
        else:
            self._executed_skills.clear()
            logger.info("已清理所有技能缓存")
            
    def execute_from_markdown(self, markdown_content: str, **kwargs) -> Dict[str, Any]:
        """
        从Markdown执行技能
        
        Args:
            markdown_content: Markdown内容
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        # 解析Markdown
        spec = self.parser.parse(markdown_content)
        
        # 生成代码
        result = self.generator.generate(spec)
        
        # 注册技能
        self._register_generated_skill(result)
        
        # 执行技能
        return self.execute(result['class_name'], **kwargs)
    

    
    def build_from_file(self, markdown_path: Path, save: bool = True) -> Dict[str, Any]:
        """
        从Markdown文件构建技能
        
        Args:
            markdown_path: Markdown文件路径
            save: 是否保存到文件
            
        Returns:
            构建结果
        """
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.build_from_markdown(content, save)
    
    def _register_generated_skill(self, result: Dict[str, Any]):
        """注册生成的技能"""
        # 动态执行代码创建类
        namespace = {}
        exec(result['code'], namespace)
        skill_class = namespace.get(result['class_name'])
        
        if skill_class:
            self.registry.register(skill_class, result['metadata'])
        else:
            raise ValueError(f"生成技能类失败: {result['class_name']}")
    
    def list_skills(self) -> Dict[str, Dict]:
        """列出所有技能"""
        return self.registry.list()
    
    def get_skill_info(self, skill_name: str) -> Dict:
        """获取技能信息"""
        if skill_name in self.registry._metadata:
            return self.registry._metadata[skill_name]
        return {}
    
    def reload_skill(self, skill_name: str) -> bool:
        """重新加载技能"""
        # 注销
        self.registry.unregister(skill_name)
        
        # 从文件重新加载
        code_file = self.registry.storage_dir / f"{skill_name}.py"
        if code_file.exists():
            skill_class = self.registry.load_from_file(code_file)
            return skill_class is not None
        
        return False