#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SD 图片批量生成器 - 支持 JSON + Python 配置
"""

import sys
import os
import json
import argparse
import time
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Set

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
from markflow.utils.model_config import get_model_config


def get_sd_config():
    """获取 SD 配置"""
    cfg = get_model_config()
    return {
        "model_path": cfg.get("model_path"),
        "model_name": cfg.get("model_name"),
        "device": cfg.get("device", "cpu"),
        "steps": cfg.get("default_steps", 25),
        "cfg_scale": cfg.get("default_cfg", 7.5),
        "loras": cfg.get("loras", []),
        "model_type": cfg.get("model_type", "sd15"),
    }


class PromptLoader:
    """Prompt 加载器 - 支持 JSON 和 Python 配置"""
    
    EXCLUDED_FILES: Set[str] = {
        "dynamic_prompt.py",
        "__init__.py",
    }
    
    @staticmethod
    def find_prompts_dir(source: str = None) -> Optional[Path]:
        """查找 prompts 目录"""
        script_dir = Path(__file__).parent
        
        if source:
            source = source.strip().rstrip('/\\')
            source_path = Path(source)
            
            if source_path.is_absolute():
                if source_path.exists() and source_path.is_dir():
                    return source_path.absolute()
                if source_path.exists() and source_path.is_file():
                    return source_path.parent.absolute()
            
            cwd_path = Path.cwd() / source
            if cwd_path.exists():
                return cwd_path.absolute()
            
            script_path = script_dir / source
            if script_path.exists():
                return script_path.absolute()
            
            project_path = project_root / source
            if project_path.exists():
                return project_path.absolute()
        
        candidates = [
            script_dir / "configs" / "prompts",
            script_dir / "configs" / "prompts_new",
            project_root / "scripts" / "configs" / "prompts",
            project_root / "scripts" / "configs" / "prompts_new",
            project_root / "configs" / "prompts",
            project_root / "configs" / "prompts_new",
            project_root / "tools" / "prompts",
            project_root / "tools" / "prompts_new",
            project_root / "prompts",
            project_root / "prompts_new",
        ]
        
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate.absolute()
        
        return None
    
    @staticmethod
    def resolve_source(source: str) -> Optional[Path]:
        """解析 source 参数，返回实际路径"""
        source = source.strip().rstrip('/\\')
        source_path = Path(source)
        script_dir = Path(__file__).parent
        
        if source_path.is_absolute():
            if source_path.exists():
                return source_path.absolute()
            return None
        
        cwd_path = Path.cwd() / source
        if cwd_path.exists():
            return cwd_path.absolute()
        
        script_path = script_dir / source
        if script_path.exists():
            return script_path.absolute()
        
        project_path = project_root / source
        if project_path.exists():
            return project_path.absolute()
        
        prompts_dir = PromptLoader.find_prompts_dir()
        if prompts_dir:
            file_path = prompts_dir / f"{source}.py"
            if file_path.exists():
                return file_path.absolute()
            
            sub_dir = prompts_dir / source
            if sub_dir.exists() and sub_dir.is_dir():
                return sub_dir.absolute()
            
            for py_file in prompts_dir.rglob('*.py'):
                if py_file.stem == source and not py_file.name.startswith('_'):
                    return py_file.absolute()
        
        if source_path.exists():
            return source_path.absolute()
        
        return None
    
    @staticmethod
    def load_json(config_path: Path) -> List[Dict]:
        """加载 JSON 配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schemes = []
        default_params = data.get('default_params', {})
        
        for scheme in data.get('schemes', []):
            schemes.append({
                'id': scheme.get('id', len(schemes) + 1),
                'name': scheme.get('name', f'scheme_{scheme["id"]}'),
                'prompts': [scheme.get('prompt', '')],
                'negative_prompt': scheme.get('negative_prompt', ''),
                'params': {
                    'width': scheme.get('width', default_params.get('width', 512)),
                    'height': scheme.get('height', default_params.get('height', 768)),
                    'steps': scheme.get('steps', default_params.get('steps', 30)),
                    'cfg_scale': scheme.get('cfg_scale', default_params.get('cfg_scale', 7.5)),
                    'seed': scheme.get('seed', default_params.get('seed', -1)),
                    'batch_size': scheme.get('batch_size', default_params.get('batch_size', 1)),
                    'model': scheme.get('model', default_params.get('model', None))
                },
                'source': 'json'
            })
        
        return schemes
    
    @staticmethod
    def is_excluded(file_path: Path) -> bool:
        """检查文件是否应该被排除"""
        return file_path.name in PromptLoader.EXCLUDED_FILES
    
    @staticmethod
    def load_python_file(file_path: Path) -> Dict:
        """加载 Python prompt 文件"""
        try:
            spec = importlib.util.spec_from_file_location("style_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'STYLE'):
                return getattr(module, 'STYLE')
            return {}
        except Exception as e:
            return {}
    
    @staticmethod
    def load_python_directory(dir_path: Path, recursive: bool = True, 
                              style_filter: str = None, folder_filter: str = None) -> Dict[str, Dict]:
        """加载目录下所有 Python prompt 文件，支持过滤"""
        all_styles = {}
        
        if recursive:
            py_files = list(dir_path.rglob('*.py'))
        else:
            py_files = list(dir_path.glob('*.py'))
        
        py_files = [f for f in py_files if not PromptLoader.is_excluded(f)]
        
        if not py_files:
            print(f"⚠️ 在 {dir_path} 中未找到任何 .py 文件")
            return all_styles
        
        loaded_count = 0
        
        for py_file in py_files:
            try:
                styles = PromptLoader.load_python_file(py_file)
                if styles:
                    for style_name, style_data in styles.items():
                        if style_filter and style_filter not in style_name:
                            continue
                        if folder_filter and folder_filter not in style_data.get('folder', ''):
                            continue
                        all_styles[style_name] = style_data
                        loaded_count += 1
                        if loaded_count <= 5:
                            try:
                                rel_path = py_file.relative_to(dir_path)
                                print(f"  ✓ {rel_path} -> {style_name}")
                            except ValueError:
                                print(f"  ✓ {py_file.name} -> {style_name}")
                        elif loaded_count == 6:
                            print(f"  ... 还有更多文件加载成功")
            except Exception as e:
                pass
        
        if loaded_count > 5:
            print(f"  ✓ 共加载 {loaded_count} 个风格")
        
        return all_styles
    
    @staticmethod
    def expand_style(style_name: str, style_data: Dict, limit: int = None) -> List[Dict]:
        """将 STYLE 字典展开为 schemes 列表，支持限制组合数"""
        schemes = []
        subjects = style_data.get('subjects', [''])
        styles = style_data.get('styles', [''])
        moods = style_data.get('moods', [''])
        
        if not subjects:
            subjects = ['']
        
        if len(subjects) == 1 and "placeholder" in subjects[0].lower():
            return []
        
        combo_id = 0
        for subject in subjects:
            if not subject or "placeholder" in subject.lower():
                continue
            
            if styles and moods:
                for style_item in styles:
                    for mood in moods:
                        combo_id += 1
                        if limit and combo_id > limit:
                            break
                        
                        prompt_parts = [subject, style_item, mood]
                        full_prompt = ', '.join(prompt_parts)
                        
                        schemes.append({
                            'id': combo_id,
                            'name': f"{style_name}_{combo_id}",
                            'prompts': [full_prompt],
                            'negative_prompt': '',
                            'params': {
                                'width': 512,
                                'height': 768,
                                'steps': 30,
                                'cfg_scale': 7.5,
                                'seed': -1,
                                'batch_size': 1,
                                'model': None  # 使用统一配置
                            },
                            'source': 'python',
                            'style_name': style_name,
                            'folder': style_data.get('folder', style_name),
                            'subject': subject,
                            'style': style_item,
                            'mood': mood
                        })
                    if limit and combo_id >= limit:
                        break
            else:
                combo_id += 1
                if limit and combo_id > limit:
                    break
                
                prompt_parts = [subject]
                if styles:
                    prompt_parts.append(', '.join(styles))
                if moods:
                    prompt_parts.append(', '.join(moods))
                full_prompt = ', '.join(prompt_parts)
                
                schemes.append({
                    'id': combo_id,
                    'name': f"{style_name}_{combo_id}",
                    'prompts': [full_prompt],
                    'negative_prompt': '',
                    'params': {
                        'width': 512,
                        'height': 768,
                        'steps': 30,
                        'cfg_scale': 7.5,
                        'seed': -1,
                        'batch_size': 1,
                        'model': None  # 使用统一配置
                    },
                    'source': 'python',
                    'style_name': style_name,
                    'folder': style_data.get('folder', style_name)
                })
        
        return schemes


class PromptCombinator:
    """Prompt 组合器"""
    
    @staticmethod
    def combine_prompts(schemes: List[Dict]) -> List[Dict]:
        """扩展每个 scheme 的 prompts 字段"""
        expanded = []
        for scheme in schemes:
            prompts = scheme.get('prompts', [''])
            if isinstance(prompts, str):
                prompts = [prompts]
            
            for i, prompt in enumerate(prompts):
                if not prompt or "placeholder" in prompt.lower():
                    continue
                new_scheme = scheme.copy()
                new_scheme['id'] = f"{scheme['id']}_{i+1}" if len(prompts) > 1 else scheme['id']
                new_scheme['name'] = f"{scheme['name']}_{i+1}" if len(prompts) > 1 else scheme['name']
                new_scheme['prompt'] = prompt
                expanded.append(new_scheme)
        
        return expanded


class SDImageGenerator:
    def __init__(self, config_path: str = None, source: str = None, auto_load: bool = True,
                 style_filter: str = None, folder_filter: str = None, limit: int = None,
                 model_name: str = None, lora_config: str = None, max_size: int = None):  # 新增 max_size
        self.base_dir = Path(__file__).parent.parent
        self.schemes = []
        self.output_dir = None
        self.loader_source = None
        self.source_path = None
        self.style_filter = style_filter
        self.folder_filter = folder_filter
        self.limit = limit
        self._call_count = 0

        # ========== 新增：模型覆盖 ==========
        self._override_model = model_name
        if model_name:
            print(f"📌 临时使用模型: {model_name}")
        
        # ========== 新增：LoRA 覆盖 ==========
        self._lora_weights = {}
        if lora_config:
            for item in lora_config.split(','):
                item = item.strip()
                if ':' in item:
                    name, weight = item.split(':')
                    self._lora_weights[name.strip()] = float(weight.strip())
                else:
                    self._lora_weights[item] = 0.8
            if self._lora_weights:
                print(f"📌 临时使用 LoRA: {self._lora_weights}")

        # ========== 新增：最大尺寸限制 ==========
        self._max_size = max_size
        if max_size:
            print(f"📐 限制最大尺寸: {max_size}px")
        
        # ✅ 加载统一配置
        self.sd_config = get_sd_config()
        print(f"📁 使用模型: {self.sd_config.get('model_name', '未设置')}")
        print(f"💻 设备: {self.sd_config.get('device', 'cpu')}")
        print(f"📦 LoRA: {len(self.sd_config.get('loras', []))} 个")
        print()
        
        if config_path:
            self._load_from_json(config_path)
            self.loader_source = 'json'
        elif source:
            self._load_from_python(source)
            self.loader_source = 'python'
        elif auto_load:
            self._auto_load()
        else:
            self.loader_source = None
            return
        
        if self.schemes:
            if self.schemes[0].get('source') == 'python':
                self.output_dir = Path("./output/python_generated")
            else:
                self.output_dir = Path("./output/json_generated")
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _auto_load(self):
        """自动加载 prompts 目录"""
        prompts_dir = PromptLoader.find_prompts_dir()
        if prompts_dir:
            print(f"🔍 自动发现 prompts 目录: {prompts_dir}")
            self.source_path = prompts_dir
            self._load_python_directory(prompts_dir)
            self.loader_source = 'python'
        else:
            self.loader_source = None
    
    def _load_from_json(self, config_path):
        """从 JSON 加载"""
        config_path = Path(config_path)
        if not config_path.exists():
            config_path = project_root / config_path
            if not config_path.exists():
                config_path = Path(__file__).parent / config_path
                if not config_path.exists():
                    print(f"❌ 配置文件不存在: {config_path}")
                    sys.exit(1)
        
        self.schemes = PromptLoader.load_json(config_path)
        print(f"✅ 从 JSON 加载了 {len(self.schemes)} 个方案")
    
    def _load_from_python(self, source):
        """从 Python 文件/目录加载"""
        resolved_path = PromptLoader.resolve_source(source)
        
        if resolved_path is None:
            prompts_dir = PromptLoader.find_prompts_dir(source)
            if prompts_dir:
                print(f"💡 自动发现 prompts 目录: {prompts_dir}")
                self.source_path = prompts_dir
                self._load_python_directory(prompts_dir)
                return
            else:
                print(f"❌ 无法解析源路径: {source}")
                sys.exit(1)
            return
        
        self.source_path = resolved_path
        
        if resolved_path.is_file() and resolved_path.suffix == '.py':
            styles = PromptLoader.load_python_file(resolved_path)
            if styles:
                print(f"✅ 从 Python 文件加载了 {len(styles)} 个风格")
            else:
                print(f"⚠️ 文件中未找到 STYLE 字典: {resolved_path}")
                sys.exit(1)
        elif resolved_path.is_dir():
            self._load_python_directory(resolved_path)
            return
        else:
            print(f"❌ 无效的源: {source} -> {resolved_path}")
            sys.exit(1)
        
        all_schemes = []
        for style_name, style_data in styles.items():
            schemes = PromptLoader.expand_style(style_name, style_data, self.limit)
            all_schemes.extend(schemes)
        
        self.schemes = PromptCombinator.combine_prompts(all_schemes)
        print(f"✅ 展开为 {len(self.schemes)} 个生成方案")
    
    def _load_python_directory(self, dir_path: Path):
        """加载 Python 目录（递归搜索所有子目录）"""
        print(f"📂 扫描目录: {dir_path}")
        
        if self.style_filter:
            print(f"   🎯 风格过滤: {self.style_filter}")
        if self.folder_filter:
            print(f"   📁 文件夹过滤: {self.folder_filter}")
        if self.limit:
            print(f"   📊 每个风格限制: {self.limit} 个组合")
        
        styles = PromptLoader.load_python_directory(
            dir_path, recursive=True,
            style_filter=self.style_filter,
            folder_filter=self.folder_filter
        )
        
        if not styles:
            print(f"❌ 在 {dir_path} 中未加载到任何风格")
            if self.style_filter or self.folder_filter:
                print("   请检查过滤条件是否正确")
            sys.exit(1)
        
        print(f"\n📋 加载的风格列表 ({len(styles)} 个):")
        for idx, (name, data) in enumerate(sorted(styles.items()), 1):
            folder = data.get('folder', '未知文件夹')
            subjects_count = len(data.get('subjects', []))
            styles_count = len(data.get('styles', []))
            moods_count = len(data.get('moods', []))
            total = subjects_count * (styles_count if styles_count else 1) * (moods_count if moods_count else 1)
            actual = min(total, self.limit) if self.limit else total
            print(f"  {idx:3}. {name}")
            print(f"      文件夹: {folder} | 主题: {subjects_count} | 风格: {styles_count} | 情绪: {moods_count} | 组合: {actual}/{total}")
        
        self._save_styles_list(styles)
        
        all_schemes = []
        for style_name, style_data in styles.items():
            schemes = PromptLoader.expand_style(style_name, style_data, self.limit)
            all_schemes.extend(schemes)
        
        self.schemes = PromptCombinator.combine_prompts(all_schemes)
        print(f"\n✅ 从目录加载了 {len(styles)} 个风格，展开为 {len(self.schemes)} 个生成方案")
    
    def _save_styles_list(self, styles: Dict):
        """保存风格列表到文件"""
        output_file = Path("./output/styles_list.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("  加载的 Prompt 风格列表\n")
            f.write("="*80 + "\n\n")
            
            if self.style_filter:
                f.write(f"风格过滤: {self.style_filter}\n")
            if self.folder_filter:
                f.write(f"文件夹过滤: {self.folder_filter}\n")
            if self.limit:
                f.write(f"每个风格限制: {self.limit} 个组合\n")
            
            f.write(f"总计: {len(styles)} 个风格\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("-"*80 + "\n\n")
            
            for idx, (name, data) in enumerate(sorted(styles.items()), 1):
                folder = data.get('folder', '未知文件夹')
                subjects = data.get('subjects', [])
                styles_list = data.get('styles', [])
                moods = data.get('moods', [])
                
                subjects_count = len(subjects)
                styles_count = len(styles_list)
                moods_count = len(moods)
                total = subjects_count * (styles_count if styles_count else 1) * (moods_count if moods_count else 1)
                actual = min(total, self.limit) if self.limit else total
                
                f.write(f"[{idx}] {name}\n")
                f.write(f"    文件夹: {folder}\n")
                f.write(f"    主题数: {subjects_count}\n")
                f.write(f"    风格数: {styles_count}\n")
                f.write(f"    情绪数: {moods_count}\n")
                f.write(f"    组合数: {actual}/{total}\n")
                
                if subjects:
                    f.write(f"    主题示例: {subjects[0][:60]}...\n" if len(subjects[0]) > 60 else f"    主题示例: {subjects[0]}\n")
                if styles_list:
                    f.write(f"    风格示例: {styles_list[0]}\n")
                if moods:
                    f.write(f"    情绪示例: {moods[0]}\n")
                f.write("\n")
            
            f.write("="*80 + "\n")
            f.write(f"总计: {len(styles)} 个风格\n")
        
        print(f"\n💾 风格列表已保存到: {output_file}")
    
    # ==================== ✅ 新增：获取配置的方法 ====================
    
    def _get_model_name(self, scheme_model: Optional[str] = None) -> str:
        """
        获取模型名称
        优先级: 命令行指定 > scheme 中指定 > 统一配置 > 回退值
        """
        # 如果命令行指定了模型，优先使用
        if self._override_model:
            return self._override_model
        
        # 如果 scheme 指定了模型，使用它
        if scheme_model:
            return scheme_model
        
        # 否则使用统一配置的模型
        model_name = self.sd_config.get('model_name')
        if model_name:
            return model_name
        
        # 回退
        return 'sd-v1-5-tiny.safetensors'
    
    def _get_steps(self, scheme_steps: Optional[int] = None) -> int:
        """获取步数"""
        if scheme_steps:
            return scheme_steps
        return self.sd_config.get('default_steps', 25)
    
    def _get_cfg_scale(self, scheme_cfg: Optional[float] = None) -> float:
        """获取 CFG Scale"""
        if scheme_cfg:
            return scheme_cfg
        return self.sd_config.get('default_cfg', 7.5)
    

    def _apply_max_size(self, width: int, height: int) -> tuple:
        """应用最大尺寸限制（保持宽高比）"""
        if not self._max_size:
            return width, height
        
        # 如果已经小于最大尺寸，不处理
        if width <= self._max_size and height <= self._max_size:
            return width, height
        
        # 计算缩放比例
        if width > height:
            scale = self._max_size / width
        else:
            scale = self._max_size / height
        
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        # 对齐到 64 的倍数
        new_w = ((new_w + 31) // 64) * 64
        new_h = ((new_h + 31) // 64) * 64
        
        return new_w, new_h
        
    # ==================== 生成方法 ====================
    
    def generate_one(self, scheme, index: int = None, total: int = None):
        """生成单张图片"""
        self._call_count += 1
        
        if total is None:
            total = len(self.schemes)
        
        if index is not None:
            print(f"\n{'='*60}")
            print(f"   🔥 第 {self._call_count} 次调用 generate_one")
            print(f"   [{index}/{total}] {scheme['name']}")
            print('='*60)
        else:
            print(f"\n{'='*60}")
            print(f"   🔥 第 {self._call_count} 次调用 generate_one")
            print(f"   {scheme['name']}")
            print('='*60)
        
        params = scheme.get('params', {})
        prompt = scheme.get('prompt', '')
        negative_prompt = scheme.get('negative_prompt', '')
        
        if not prompt:
            print("❌ 无 prompt 内容")
            return False
        
        seed = params.get('seed', -1)
        if isinstance(seed, str):
            try:
                seed = int(seed)
            except:
                seed = -1
        
        # ✅ 从统一配置获取参数
        model_name = self._get_model_name(params.get('model'))
        steps = self._get_steps(params.get('steps'))
        cfg_scale = self._get_cfg_scale(params.get('cfg_scale'))
        
        # ========== 新增：应用最大尺寸限制 ==========
        width = params.get('width', 512)
        height = params.get('height', 768)
        width, height = self._apply_max_size(width, height)
        
        print(f"📦 使用模型: {model_name}")
        print(f"⚙️  步数: {steps}, CFG: {cfg_scale}")
        print(f"📐 尺寸: {width}x{height}")
        print(f"📝 提示词: {prompt[:80]}...")
        
        try:
            result = execute_skill(
                "sd_image_generator",
                prompt=prompt,
                negative_prompt=negative_prompt,
                model_name=model_name,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                batch_size=params.get('batch_size', 1)
            )
            
            # ✅ 检查返回值
            if result is None:
                print("❌ 执行失败: 返回值为 None")
                return False
            
            # ✅ 如果 result 是字典，检查 status
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    print(f"✅ 生成成功!")
                    image_paths = result.get('image_paths', [])
                    if image_paths:
                        for path in image_paths:
                            print(f"   📁 {path}")
                    return True
                else:
                    error = result.get('error', '未知错误')
                    print(f"❌ 执行失败: {error}")
                    return False
            
            # ✅ 如果 result 是布尔值
            if isinstance(result, bool):
                return result
            
            print(f"⚠️ 未知返回值类型: {type(result)}")
            return False
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def list_schemes(self):
        """列出所有方案"""
        if not self.schemes:
            print("❌ 没有加载任何方案")
            print("\n💡 提示: 请确保 prompts 目录存在且包含 .py 文件")
            return
        
        print("\n" + "="*90)
        print("   📸 SD 图片生成方案列表")
        print("="*90)
        print()
        print(f"{'ID':<8} {'名称':<35} {'风格':<20} {'尺寸':<12}")
        print("-"*90)
        
        for idx, s in enumerate(self.schemes[:50], 1):
            w = s.get('params', {}).get('width', 512)
            h = s.get('params', {}).get('height', 768)
            style_name = s.get('style_name', 'unknown')
            print(f"{idx:<8} {s['name'][:34]:<35} {style_name[:19]:<20} {w}x{h}")
        
        if len(self.schemes) > 50:
            print(f"... 还有 {len(self.schemes) - 50} 个方案未显示")
        print()
        print(f"共 {len(self.schemes)} 个方案")
        print(f"源目录: {self.source_path}")
        print(f"输出目录: {self.output_dir}")
        print(f"📦 当前模型: {self.sd_config.get('model_name', '未设置')}")
    
    def generate_by_id(self, ids):
        """根据 ID 生成（ID 从 1 开始）"""
        if not self.schemes:
            print("❌ 没有加载任何方案")
            return
        
        if isinstance(ids, int):
            ids = [ids]
        elif isinstance(ids, str):
            ids = [int(x.strip()) for x in ids.split(',')]
        elif not isinstance(ids, list):
            ids = list(ids)
        
        ids = [int(i) for i in ids]
        
        print(f"🔍 查找 ID: {ids}")
        print(f"📊 总方案数: {len(self.schemes)}")
        
        found = []
        for idx, s in enumerate(self.schemes, 1):
            if idx in ids:
                found.append((idx, s))
                print(f"  ✓ 找到 ID {idx}: {s['name']}")
        
        if not found:
            print(f"❌ 未找到 ID: {ids}")
            print(f"   可用 ID 范围: 1-{len(self.schemes)}")
            return
        
        print(f"\n🎯 将生成 {len(found)} 个方案")
        
        for idx, s in found:
            self.generate_one(s, idx)
            time.sleep(0.5)
    
    def generate_all(self):
        """生成所有"""
        if not self.schemes:
            print("❌ 没有加载任何方案")
            return
        
        total = len(self.schemes)
        success = 0
        for idx, s in enumerate(self.schemes, 1):
            print(f"\n进度: {idx}/{total}")
            if self.generate_one(s, idx):
                success += 1
            time.sleep(0.5)
        print(f"\n✅ 完成！成功 {success}/{total} 张")
    
    # ========== 衣服移除模式 ==========
    def remove_clothes_mode(self, args):
        """执行衣服移除"""
        print("\n" + "="*60)
        print("   👕 衣服移除模式")
        print("="*60)
        
        input_path = args.input
        output_path = args.output
        batch = args.batch
        
        if not input_path:
            print("❌ 请指定输入路径: --input <图片路径或目录>")
            return
        
        if not os.path.exists(input_path):
            print(f"❌ 路径不存在: {input_path}")
            return
        
        if batch:
            # 批量模式
            if not os.path.isdir(input_path):
                print(f"❌ 批量模式需要目录: {input_path}")
                return
            
            print(f"📁 批量处理目录: {input_path}")
            if output_path:
                print(f"📂 输出目录: {output_path}")
            else:
                output_path = os.path.join(input_path, "nude_output")
                print(f"📂 输出目录: {output_path} (默认)")
            
            # 收集所有图片
            extensions = ('.png', '.jpg', '.jpeg', '.webp')
            files = [os.path.join(input_path, f) for f in os.listdir(input_path) 
                     if f.lower().endswith(extensions)]
            files = sorted(files)
            
            if not files:
                print(f"❌ 未找到图片: {input_path}")
                return
            
            print(f"\n📊 找到 {len(files)} 个图片")
            print("="*60)
            
            os.makedirs(output_path, exist_ok=True)
            
            success_count = 0
            for i, file_path in enumerate(files, 1):
                filename = os.path.basename(file_path)
                out_file = os.path.join(output_path, filename)
                print(f"\n[{i}/{len(files)}] {filename}")
                
                try:
                    result = execute_skill(
                        "remove_clothes",
                        input_path=file_path,
                        output_path=out_file,
                        prompt=args.prompt,
                        negative_prompt=args.negative,
                        strength=args.strength,
                        steps=args.steps,
                        seed=args.seed,
                        device=args.device,
                        save_mask=args.save_mask
                    )
                    if result:
                        success_count += 1
                except Exception as e:
                    print(f"   ❌ 失败: {e}")
            
            print(f"\n✅ 完成: {success_count}/{len(files)} 张")
            
        else:
            # 单张模式
            if not os.path.isfile(input_path):
                print(f"❌ 文件不存在: {input_path}")
                return
            
            print(f"📷 处理单张图片: {input_path}")
            
            try:
                result = execute_skill(
                    "remove_clothes",
                    input_path=input_path,
                    output_path=output_path,
                    prompt=args.prompt,
                    negative_prompt=args.negative,
                    strength=args.strength,
                    steps=args.steps,
                    seed=args.seed,
                    device=args.device,
                    save_mask=args.save_mask
                )
                if result:
                    print("\n✅ 完成！")
            except Exception as e:
                print(f"❌ 执行失败: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        prompts_dir = PromptLoader.find_prompts_dir()
        if prompts_dir:
            prompts_path = str(prompts_dir) + "/"
        else:
            prompts_path = "configs/prompts/"
        
        # 获取当前模型信息
        sd_config = get_sd_config()
        current_model = sd_config.get('model_name', '未设置')
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    SD 图片批量生成器                             ║
║                    支持 JSON + Python 配置                      ║
╚══════════════════════════════════════════════════════════════════╝

📦 当前模型: {current_model}
💻 设备: {sd_config.get('device', 'cpu')}

📖 图片生成用法:

  1. 自动加载所有风格
     python generate_images.py --list          # 列出所有方案
     python generate_images.py --all           # 生成所有方案
     python generate_images.py --id 1          # 生成第 1 个方案

  2. 按风格名称筛选
     python generate_images.py --style bird_sketch --list
     python generate_images.py --style bird_sketch --id 1

  3. 按文件夹名称筛选
     python generate_images.py --folder 极简飞鸟线稿 --list
     python generate_images.py --folder 极简飞鸟线稿 --all

  4. 限制每个风格的组合数
     python generate_images.py --limit 10 --list
     python generate_images.py --limit 5 --style bird_sketch --all

  5. 组合使用
     python generate_images.py --style bird_sketch --limit 5 --all

  6. 使用 JSON 配置文件
     python generate_images.py --config configs/girls_config.json

👕 衣服移除用法:

  7. 单张图片移除衣服
     python generate_images.py --remove-clothes --input image.jpg
     python generate_images.py --remove-clothes --input image.jpg -o output.jpg

  8. 批量处理
     python generate_images.py --remove-clothes --input ./images/ --batch
     python generate_images.py --remove-clothes --input ./images/ --batch -o ./output/

  9. 衣服移除高级参数
     python generate_images.py --remove-clothes --input image.jpg \\
         --prompt "nude, beautiful skin" --strength 0.85 --steps 30 --device cpu

📂 自动发现路径:
  - scripts/configs/prompts
  - configs/prompts
  - tools/prompts_new
  - prompts_new

⏭️ 自动排除文件:
  - dynamic_prompt.py (触发器文件)
  - __init__.py

🔧 参数:
  --help              显示此帮助信息
  --list              列出所有已加载的方案
  --all               生成所有方案
  --id N              生成指定 ID 的方案
  --ids N,N           生成多个方案
  --style NAME        只加载指定风格
  --folder NAME       只加载指定文件夹
  --limit N           每个风格最多生成 N 个组合
  --total N           总共生成 N 张图片（取前 N 个）
  --config PATH       使用 JSON 配置文件
  --source PATH       指定 Python prompt 目录

👕 衣服移除参数:
  --remove-clothes    进入衣服移除模式
  --input PATH        输入图片路径或目录
  -o, --output PATH   输出路径（单张）或输出目录（批量）
  --batch             批量模式
  --prompt TEXT       生成提示词 (默认: nude, naked body...)
  --negative TEXT     负面提示词 (默认: clothes, fabric, ugly...)
  --strength FLOAT    重绘强度 (0.0-1.0, 默认: 0.85)
  --steps N           迭代步数 (默认: 30)
  --seed N            随机种子
  --device DEVICE     设备 (cpu/cuda, 默认: cpu)
  --save-mask         保存遮罩
""")
    
    def run(self, args):
        # ========== 衣服移除模式 ==========
        if args.remove_clothes:
            self.remove_clothes_mode(args)
            return
        
        if args.help or (not args.config and not args.source and not args.list and 
                         args.id is None and args.ids is None and not args.all):
            self.show_help()
            return
        
        if args.list:
            self.list_schemes()
            return
        
        if args.id is not None:
            self.generate_by_id([args.id])
            return
        
        if args.ids:
            ids = [int(x.strip()) for x in args.ids.split(',')]
            self.generate_by_id(ids)
            return
        
        if args.total and not args.all:
            total = min(args.total, len(self.schemes))
            print(f"\n📊 共 {len(self.schemes)} 个方案，将生成前 {total} 个")
            print("="*60)
            success = 0
            for idx, s in enumerate(self.schemes[:total], 1):
                print(f"\n进度: {idx}/{total}")
                if self.generate_one(s, idx, total):
                    success += 1
                time.sleep(0.5)
            print(f"\n✅ 完成！成功 {success}/{total} 张")
            return

        if args.all:
            if args.total:
                total = min(args.total, len(self.schemes))
                print(f"\n📊 共 {len(self.schemes)} 个方案，将生成前 {total} 个")
                print("="*60)
                success = 0
                for idx, s in enumerate(self.schemes[:total], 1):
                    print(f"\n进度: {idx}/{total}")
                    if self.generate_one(s, idx, total):
                        success += 1
                    time.sleep(0.5)
                print(f"\n✅ 完成！成功 {success}/{total} 张")
            else:
                self.generate_all()
            return


def main():
    parser = argparse.ArgumentParser(
        description="SD 图片批量生成器 - 支持 JSON + Python 配置 + 衣服移除",
        add_help=False,
        epilog="示例：python generate_images.py --style bird_sketch --limit 10 --list"
    )
    
    # ========== 图片生成参数 ==========
    parser.add_argument("--config", type=str, help="使用 JSON 配置文件")
    parser.add_argument("--source", type=str, help="加载 Python prompt 文件/目录/风格名称")
    parser.add_argument("--list", action="store_true", help="列出所有方案")
    parser.add_argument("--id", type=int, help="生成指定 ID 的方案")
    parser.add_argument("--ids", type=str, help="生成多个方案，用逗号分隔，如 1,3,5")
    parser.add_argument("--all", action="store_true", help="生成所有方案")
    parser.add_argument("--help", action="store_true", help="显示帮助信息")
    parser.add_argument("--style", type=str, help="只加载指定风格（如 bird_sketch）")
    parser.add_argument("--folder", type=str, help="只加载指定文件夹（如 极简飞鸟线稿）")
    parser.add_argument("--limit", type=int, help="每个风格最多生成 N 个组合")
    parser.add_argument("--total", type=int, help="总共生成 N 张图片（取前 N 个）")
    
    # ========== 新增：模型管理参数 ==========
    parser.add_argument("--model", type=str, help="指定底模名称（临时覆盖配置）")
    parser.add_argument("--lora", type=str, help="指定 LoRA 名称，如 'lora_000004:0.7,aesthetic_anime:0.9'")
    
    # ========== 新增：尺寸限制参数 ==========
    parser.add_argument("--max-size", type=int, default=768, 
                       help="限制最大边长 (默认: 768, 推荐 512-768)")
    
    # ========== 衣服移除参数 ==========
    parser.add_argument("--remove-clothes", action="store_true", help="进入衣服移除模式")
    parser.add_argument("--input", type=str, help="输入图片路径或目录")
    parser.add_argument("-o", "--output", type=str, help="输出路径（单张）或输出目录（批量）")
    parser.add_argument("--batch", action="store_true", help="批量模式")
    parser.add_argument("--prompt", type=str, 
                        default="nude, naked body, beautiful skin, realistic body, masterpiece, best quality",
                        help="生成提示词")
    parser.add_argument("--negative", type=str,
                        default="clothes, fabric, ugly, deformed, bad anatomy, cropped, low quality",
                        help="负面提示词")
    parser.add_argument("--strength", type=float, default=0.85, help="重绘强度 (0.0-1.0)")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        args.help = True
    
    generator = SDImageGenerator(
        args.config, args.source, auto_load=True,
        style_filter=args.style,
        folder_filter=args.folder,
        limit=args.limit,
        model_name=args.model,      # 新增
        lora_config=args.lora,      # 新增
        max_size=args.max_size      # 新增
    )
    generator.run(args)
    

if __name__ == "__main__":
    main()