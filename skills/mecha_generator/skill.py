"""
MechaGenerator - 机甲少女/机器人高端文生图与图生图生成器

输入参数:
  - mode (string): 生成模式 ("txt2img" 文生图 / "img2img" 图生图)
  - prompt (string): 正面提示词 (必填, txt2img)
  - negative_prompt (string): 负面提示词
  - input_image (string): 图生图的输入图片路径 (img2img模式下必填)
  - output_path (string): 输出路径 (可选，默认自动生成)
  - width (int): 宽度 (默认 768)
  - height (int): 高度 (默认 1024)
  - steps (int): 迭代步数 (默认 30)
  - cfg_scale (float): 提示词引导系数 (默认 7.5)
  - seed (int): 随机种子 (默认 -1 随机)
  - model_name (string): 使用哪个底模 (默认读取用户全局配置)
  - style (string): 预设风格 (对应本地提示词文件，如 mecha_glow / mecha_girl / none)
  - controlnet_type (string): img2img模式下的姿态控制 ("openpose", "canny", "depth" 等)
  - strength (float): 图生图重绘强度 (0.0-1.0，默认 0.75)

输出:
  - status: 执行状态
  - image_paths: 生成图片的路径列表
  - used_model: 实际使用的底模名称
"""

import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# 导入框架内部组件
try:
    from markflow.utils.model_config import get_models, get_loras, get_model_config, resolve_model_path
    from markflow.cli.commands import execute_skill
    MODEL_UTILS_AVAILABLE = True
except ImportError:
    MODEL_UTILS_AVAILABLE = False
    logger.warning("未能导入 Markflow 模型配置工具")

# 尝试导入 ControlNet
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False

# 尝试导入 SD 图像生成主引擎
try:
    from skills.sd_image_generator.skill import Sdimagegenerator
    SD_ENGINE_AVAILABLE = True
except ImportError:
    SD_ENGINE_AVAILABLE = False
    logger.warning("未能导入 SD 主引擎，尝试寻找其他引擎")


class Mechagenerator:
    """机甲少女生成器：支持文生图、图生图和分层提示词组合"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "mecha_generator"
        self.version = "1.0.0"
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self._setup_config()
        self._init_engine()
        
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_width': 768,
            'default_height': 1024,
            'default_steps': 30,
            'default_cfg': 7.5,
            'default_strength': 0.75,
            'default_style': 'none',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _init_engine(self):
        """初始化底层生成引擎"""
        self.sd_engine = None
        if SD_ENGINE_AVAILABLE:
            try:
                self.sd_engine = Sdimagegenerator(config={'device': self.config.get('device', 'cpu')})
                logger.info("SD 主引擎加载成功")
            except Exception as e:
                logger.warning(f"SD 主引擎初始化失败: {e}")

        # 如果主引擎不可用，尝试寻找其他底层
        if not self.sd_engine:
            # 尝试导入项目中的 generate_images 生成器
            try:
                sys.path.insert(0, str(project_root / "scripts"))
                from generate_images import SDImageGenerator
                self.script_generator = SDImageGenerator()
                logger.info("Scripts 目录下的图片生成器加载成功")
            except Exception as e:
                logger.warning(f"Scripts 生成器加载失败: {e}")

    def _apply_style_preset(self, style: str, prompt: str) -> str:
        """根据预设风格提取提示词增强 (当本地无此文件时的回退机制)"""
        style_presets = {
            "cyber_android_sdxl": "cyber android, translucent polymer skin, intricate blue energy circuits, glossy white mechanical skeleton",
            "mecha_girl": "mecha girl, metallic joints, sleek white and grey armor, exposed wiring, sci-fi weapon",
            "mecha_blueprint": "white mechanical android, blueprint lines, glowing blue core, uncolored 3D render, engineering diagram style",
            "mecha_glow": "biomechanical android, semi-transparent shell, glowing inner mechanical parts, ethereal pale lighting, 8k",
        }
        
        if style in style_presets:
            return f"{prompt}, {style_presets[style]}"
        return prompt

    def _load_prompts_from_library(self, style_name: str) -> Dict:
        """从当前技能目录加载提示词库（自动适配本地文件）"""
        local_py_files = list(self.skill_dir.glob("*.py"))
        
        for py_file in local_py_files:
            if py_file.name == "skill.py":
                continue
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"style_module_{py_file.stem}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 核心：自动寻找文件里的 STYLE 字典，并匹配关键字
                if hasattr(module, 'STYLE'):
                    styles = module.STYLE
                    # 匹配文件名的关键词，或者字典里的 key
                    for key in styles.keys():
                        if style_name in key or style_name in py_file.stem:
                            return styles[key]
            except Exception as e:
                logger.warning(f"加载提示词文件 {py_file.name} 失败: {e}")
        
        return {}
        
    def _generate_text_to_image(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, cfg: float, seed: int, model_name: Optional[str]) -> Dict:
        """执行文生图"""
        
        # ===== 核心修改：动态获取用户配置的模型 =====
        # 从 model_config.py 中拿到当前用户选定的模型
        try:
            from markflow.utils.model_config import get_model_config
            global_sd_config = get_model_config()
            if not model_name and global_sd_config.get('model_path'):
                model_name = global_sd_config.get('model_name')  # 获取配置的模型名
        except Exception as e:
            logger.warning(f"获取全局模型配置失败: {e}")

        if self.sd_engine:
            try:
                result = self.sd_engine.execute(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg_scale=cfg,
                    seed=seed,
                    model_name=model_name,
                    batch_size=1
                )
                if result.get('status') == 'success':
                    return result
                return {"status": "error", "error": result.get('error', 'SD引擎失败')}
            except Exception as e:
                logger.error(f"SD引擎异常: {e}")
                return {"status": "error", "error": str(e)}

        # 回退到脚本生成器
        if hasattr(self, 'script_generator') and self.script_generator:
            try:
                scheme = {
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'params': {
                        'width': width, 'height': height, 'steps': steps,
                        'cfg_scale': cfg, 'seed': seed, 'model': model_name
                    }
                }
                success = self.script_generator.generate_one(scheme)
                if success:
                    out_dir = Path("./output/python_generated")
                    latest = sorted(out_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
                    return {"status": "success", "image_paths": [str(latest)], "using": "script_generator"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "未找到任何可用的底层生成引擎，请检查 skills/sd_image_generator"}

    def _generate_image_to_image(self, input_image: str, prompt: str, negative_prompt: str, controlnet_type: str, strength: float, output_path: str) -> Dict:
        """执行图生图，调用 ControlNet"""
        if not CONTROLNET_AVAILABLE:
            return {"status": "error", "error": "未找到 ControlNet 引擎 (skills/controlnet_img2img)"}
        
        try:
            cn_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
            result = cn_engine.execute(
                input_image_path=input_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type=controlnet_type,
                controlnet_model=controlnet_type,
                strength=strength,
                output_path=output_path
            )
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行技能"""
        logger.info(f"执行技能: {self.name} (v{self.version})")
        start_time = time.time()

        try:
            # 1. 解析基本参数
            mode = kwargs.get('mode', 'txt2img')
            prompt = kwargs.get('prompt', '')
            negative_prompt = kwargs.get('negative_prompt', 
                'worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature')
            style = kwargs.get('style', self.config.get('default_style', 'none'))
            
            # 2. 应用预设风格（支持从本地提示词库加载）
            if style and style != 'none':
                # 尝试加载本地同目录下的 .py 提示词文件
                local_style = self._load_prompts_from_library(style)
                if local_style:
                    subjects = local_style.get('subjects', [])
                    local_styles = local_style.get('styles', [])
                    local_moods = local_style.get('moods', [])
                    
                    prompt_parts = []
                    if subjects:
                        prompt_parts.append(random.choice(subjects))
                    if local_styles:
                        prompt_parts.append(random.choice(local_styles))
                    if local_moods:
                        prompt_parts.append(random.choice(local_moods))
                    
                    # 组合分层提示词
                    if prompt_parts:
                        if prompt:
                            prompt = f"{prompt}, {', '.join(prompt_parts)}"
                        else:
                            prompt = ", ".join(prompt_parts)
                        logger.info(f"📂 已加载本地风格 [ {style} ] 的分层提示词组合")
                else:
                    # 如果本地没有，回退到内置预设
                    prompt = self._apply_style_preset(style, prompt)

            # 3. 基础参数
            width = int(kwargs.get('width', self.config.get('default_width', 768)))
            height = int(kwargs.get('height', self.config.get('default_height', 1024)))
            steps = int(kwargs.get('steps', self.config.get('default_steps', 30)))
            cfg_scale = float(kwargs.get('cfg_scale', self.config.get('default_cfg', 7.5)))
            seed = int(kwargs.get('seed', -1))
            model_name = kwargs.get('model_name')
            output_path = kwargs.get('output_path', str(self.output_dir / f"mecha_{int(time.time())}.png"))

            # 4. 校验
            if mode == 'txt2img' and not prompt:
                return {"status": "error", "error": "txt2img 模式下必须提供 prompt"}
            
            input_image = kwargs.get('input_image')
            if mode == 'img2img' and not input_image:
                # 如果没传 input_image，自动寻找本目录下的参考图
                ref_imgs = sorted(list(self.skill_dir.glob("Gemini_Generated_Image*.png")))
                if ref_imgs:
                    input_image = str(ref_imgs[0])
                    logger.info(f"🖼️ 自动使用目录下第一张参考图: {input_image}")
                else:
                    return {"status": "error", "error": "img2img 模式下必须提供 input_image"}

            # 5. 执行生成
            if mode == 'txt2img':
                result = self._generate_text_to_image(prompt, negative_prompt, width, height, steps, cfg_scale, seed, model_name)
            elif mode == 'img2img':
                controlnet_type = kwargs.get('controlnet_type', 'canny')
                strength = float(kwargs.get('strength', self.config.get('default_strength', 0.75)))
                result = self._generate_image_to_image(input_image, prompt, negative_prompt, controlnet_type, strength, output_path)
            else:
                return {"status": "error", "error": f"未知模式: {mode}"}

            # 6. 处理结果
            if result.get('status') == 'success':
                elapsed = time.time() - start_time
                return {
                    "status": "success",
                    "result": {
                        "mode": mode,
                        "image_paths": result.get('image_paths', [output_path]),
                        "elapsed_time": f"{elapsed:.2f}s",
                        "prompt_used": prompt,
                        "used_model": model_name
                    },
                    "metadata": {
                        "skill": self.name,
                        "version": self.version,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            else:
                return result

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
            
    def __repr__(self):
        return f"<Mechagenerator(name={self.name}, version={self.version})>"