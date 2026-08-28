import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

"""
SDImageGenerator - 使用本地 Stable Diffusion 模型生成图片的技能
"""

import time
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 导入 SD 相关库
try:
    import torch
    from diffusers import StableDiffusionPipeline
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")

# 导入统一配置
from markflow.utils.model_config import get_model_config


class Sdimagegenerator:
    """使用本地 Stable Diffusion 模型生成图片的技能"""
        
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "SDImageGenerator"
        self.version = "1.0.0"
        
        # ✅ 读取配置
        try:
            model_cfg = get_model_config()
            if model_cfg is None:
                model_cfg = {}
        except Exception:
            model_cfg = {}
        
        # ✅ 直接使用完整路径，带扩展名
        model_path = model_cfg.get("model_path")
        if model_path and Path(model_path).exists():
            self.models_dir = Path(model_path).parent
            self.default_model = Path(model_path).name  # 完整文件名，带扩展名
        else:
            # 回退
            self.models_dir = Path("D:/SD_OpenVINO/models/sd-v1-5")
            self.default_model = "aiiiiii01_v10.safetensors"
        
        self.device = "cpu"
        self.loras = []
        self.default_steps = 25
        self.default_cfg = 7.5
        self.max_resolution = 768
        
        self.pipeline = None
        self.current_model = None
        
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"SDImageGenerator 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  默认模型: {self.default_model}")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'output_dir': './skills/sd_image_generator/output/images',
            'default_model': self.default_model,
            'default_width': 512,
            'default_height': 768,
            'default_steps': self.default_steps,
            'default_cfg_scale': self.default_cfg,
            'default_seed': -1,
            'default_batch_size': 1,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
    def _find_model(self, model_name: str) -> Optional[Path]:
        if not model_name:
            model_name = self.config.get('default_model', 'aiiiiii01_v10.safetensors')
        
        logger.info(f"🔍 查找模型: '{model_name}'")
        logger.info(f"📁 模型目录: {self.models_dir}")
        
        # 直接拼接查找
        model_path = self.models_dir / model_name
        if model_path.exists():
            logger.info(f"✅ 找到: {model_path}")
            return model_path
        
        # 如果带扩展名找不到，尝试子目录
        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / model_name
            if sub_path.exists():
                logger.info(f"✅ 找到: {sub_path}")
                return sub_path
        
        logger.error(f"❌ 未找到模型: '{model_name}'")
        return None
    
    def _load_model(self, model_name: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False
        
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False
        
        try:
            logger.info(f"加载模型: {model_path}")
            
            self.pipeline = StableDiffusionPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            self.pipeline.to(self.device)
            
            # 加载 LoRA
            for lora in self.loras:
                lora_path = lora.get("path")
                lora_weight = lora.get("weight", 0.8)
                lora_name = lora.get("name", "unknown")
                
                if lora_path and Path(lora_path).exists():
                    try:
                        self.pipeline.load_lora_weights(str(lora_path))
                        logger.info(f"  ✅ LoRA 加载成功: {lora_name} (权重: {lora_weight})")
                    except Exception as e:
                        logger.warning(f"  ⚠️ LoRA 加载失败 ({lora_name}): {e}")
                else:
                    logger.warning(f"  ⚠️ LoRA 文件不存在: {lora_path}")
            
            if self.device == 'cuda':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = model_name
            logger.info(f"✅ 模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def _validate_inputs(self, **kwargs) -> bool:
        if 'prompt' not in kwargs or not kwargs['prompt']:
            raise ValueError("prompt 是必填参数")
        
        width = kwargs.get('width', self.config.get('default_width', 512))
        height = kwargs.get('height', self.config.get('default_height', 768))
        steps = kwargs.get('steps', self.config.get('default_steps', 25))
        cfg_scale = kwargs.get('cfg_scale', self.config.get('default_cfg_scale', 7.5))
        batch_size = kwargs.get('batch_size', 1)
        
        if width < 256 or width > 1024:
            raise ValueError(f"width 必须在 256-1024 之间，当前值: {width}")
        if height < 256 or height > 1024:
            raise ValueError(f"height 必须在 256-1024 之间，当前值: {height}")
        if steps < 10 or steps > 50:
            raise ValueError(f"steps 必须在 10-50 之间，当前值: {steps}")
        if cfg_scale < 1.0 or cfg_scale > 20.0:
            raise ValueError(f"cfg_scale 必须在 1.0-20.0 之间，当前值: {cfg_scale}")
        if batch_size < 1 or batch_size > 4:
            raise ValueError(f"batch_size 必须在 1-4 之间，当前值: {batch_size}")
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            prompt = kwargs.get('prompt')
            negative_prompt = kwargs.get('negative_prompt', '')
            
            # ✅ 获取模型名称
            if kwargs.get('model_name'):
                model_name = kwargs.get('model_name')
            else:
                model_name = self.config.get('default_model')
            
            width = kwargs.get('width', self.config.get('default_width', 512))
            height = kwargs.get('height', self.config.get('default_height', 768))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            cfg_scale = kwargs.get('cfg_scale', self.config.get('default_cfg_scale', 7.5))
            
            output_dir = kwargs.get('output_dir', self.config.get('output_dir', './skills/sd_image_generator/output/images'))
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            batch_size = kwargs.get('batch_size', 1)
            
            width = (width // 8) * 8
            height = (height // 8) * 8
            
            if self.pipeline is None or self.current_model != model_name:
                if not self._load_model(model_name):
                    return {"status": "error", "error": f"无法加载模型: {model_name}"}
            
            seed = kwargs.get('seed', -1)
            if isinstance(seed, str):
                try:
                    seed = int(seed)
                except:
                    seed = -1
            
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)
            
            logger.info(f"生成参数:")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  模型: {model_name}")
            logger.info(f"  尺寸: {width}x{height}")
            logger.info(f"  步数: {steps}")
            logger.info(f"  种子: {seed}")
            
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=cfg_scale,
                generator=generator,
                num_images_per_prompt=batch_size
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_paths = []
            
            for i, image in enumerate(result.images):
                filename = f"image_{timestamp}_{seed}_{i}.png"
                filepath = output_dir / filename
                image.save(filepath)
                image_paths.append(str(filepath))
                logger.info(f"  ✅ 图片 {i+1}: {filepath}")
            
            generation_time = time.time() - start_time
            
            return {
                "status": "success",
                "image_paths": image_paths,
                "parameters": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model": model_name,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "seed": seed,
                    "batch_size": batch_size,
                    "output_dir": str(output_dir)
                },
                "model_used": model_name,
                "generation_time": f"{generation_time:.2f}s",
                "generated_at": datetime.now().isoformat()
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
        return f"<Sdimagegenerator(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SD 图片生成器")
    parser.add_argument("--prompt", "-p", required=True, help="提示词")
    parser.add_argument("--negative", "-n", default="", help="负面提示词")
    parser.add_argument("--model", "-m", default=None, help="模型名称（可选）")
    parser.add_argument("--width", "-W", type=int, default=512, help="宽度")
    parser.add_argument("--height", "-H", type=int, default=768, help="高度")
    parser.add_argument("--steps", "-s", type=int, default=None, help="步数")
    parser.add_argument("--cfg", "-c", type=float, default=None, help="CFG尺度")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--output", "-o", default="./generated_images", help="输出目录")
    parser.add_argument("--batch", "-b", type=int, default=1, help="批量数量")
    
    args = parser.parse_args()
    
    skill = Sdimagegenerator()
    
    execute_kwargs = {
        "prompt": args.prompt,
        "negative_prompt": args.negative,
        "width": args.width,
        "height": args.height,
        "seed": args.seed,
        "output_dir": args.output,
        "batch_size": args.batch,
    }
    
    if args.model:
        execute_kwargs["model_name"] = args.model
    if args.steps is not None:
        execute_kwargs["steps"] = args.steps
    if args.cfg is not None:
        execute_kwargs["cfg_scale"] = args.cfg
    
    result = skill.execute(**execute_kwargs)
    
    if result['status'] == 'success':
        print(f"\n✅ 生成成功!")
        print(f"  📁 图片: {result['image_paths']}")
        print(f"  ⏱️  耗时: {result['generation_time']}")
        print(f"  📋 参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n❌ 生成失败: {result.get('error', '未知错误')}")