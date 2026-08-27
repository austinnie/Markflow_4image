# skills/change_furniture/skill.py
"""
换家具 Skill - 改变室内场景中的家具风格
使用 Depth ControlNet 保持空间结构，Inpaint 重绘室内区域
"""

import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image, ImageDraw, ImageFilter
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers 未安装")

try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("ControlNet 技能不可用")

FURNITURE_STYLES = {
    "modern": {
        "prompt": "modern furniture, contemporary, minimalist, sleek design, elegant interior, masterpiece, high quality",
        "negative": "vintage, retro, traditional, old-fashioned"
    },
    "vintage": {
        "prompt": "vintage furniture, retro style, antique, classic, warm interior, masterpiece, high quality",
        "negative": "modern, contemporary, minimalist, futuristic"
    },
    "minimalist": {
        "prompt": "minimalist furniture, simple design, clean lines, neutral colors, interior, masterpiece, high quality",
        "negative": "vintage, retro, traditional, cluttered"
    },
    "industrial": {
        "prompt": "industrial style furniture, metal, wood, loft style, urban interior, masterpiece, high quality",
        "negative": "vintage, retro, traditional, minimalist"
    },
    "scandinavian": {
        "prompt": "scandinavian furniture, light wood, cozy, hygge, warm interior, masterpiece, high quality",
        "negative": "industrial, vintage, minimalist, modern"
    },
    "traditional": {
        "prompt": "traditional furniture, classic, elegant, warm interior, masterpiece, high quality",
        "negative": "modern, minimalist, contemporary, futuristic"
    }
}


class ChangeFurniture:
    """换家具技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_furniture"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.pipeline = None
        self.current_model = None
        self.controlnet_skill = None

        if CONTROLNET_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={'device': self.device, 'max_size': 512})
                logger.info("  ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"  ControlNet 技能初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeFurniture 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  家具风格: {list(FURNITURE_STYLES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.7,
            'default_style': 'modern',
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        Path(self.config.get('output_dir', str(self.output_dir))).mkdir(parents=True, exist_ok=True)

    def _find_model(self, model_name: str) -> Optional[Path]:
        return Path(self.models_dir / "sd-v1-5" / model_name) if model_name else None

    def _load_pipeline(self, model_path: Path) -> bool:
        try:
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline.to(self.device)
            self.pipeline.enable_attention_slicing()
            self.current_model = model_path.name
            return True
        except Exception as e:
            logger.error(f"  模型加载失败: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        model_path = self._find_model(model_name)
        if not model_path or not model_path.exists():
            logger.error(f"模型不存在: {model_name}")
            return False
        return self._load_pipeline(model_path)

    def _generate_depth_image(self, image: Image.Image) -> Optional[Image.Image]:
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type='depth',
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  深度图生成失败: {e}")
            return None

    def _resize_image(self, image: Image.Image) -> tuple:
        w, h = image.size
        max_size = 768
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image, image.size

    def _generate_indoor_mask(self, image: Image.Image) -> Image.Image:
        """生成室内遮罩（保留整体结构，重绘家具区域）"""
        # 使用全白遮罩，让模型重绘整体室内
        h, w = image.size[1], image.size[0]
        mask = Image.new("L", (w, h), 0)
        return mask

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            style = kwargs.get('style', self.config.get('default_style', 'modern'))
            if style not in FURNITURE_STYLES:
                return {"status": "error", "error": f"未知家具风格: {style}，可用: {list(FURNITURE_STYLES.keys())}"}

            style_config = FURNITURE_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"家具风格: {style}")
            logger.info(f"提示词: {prompt[:80]}...")

            control_image = self._generate_depth_image(image)
            mask = self._generate_indoor_mask(image)

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': mask,
                'strength': strength,
                'num_inference_steps': steps,
                'guidance_scale': 7.5,
                'generator': generator,
                'width': current_size[0],
                'height': current_size[1],
            }
            if control_image is not None:
                pipeline_kwargs['control_image'] = control_image

            result = self.pipeline(**pipeline_kwargs).images[0]

            if kwargs.get('output_path'):
                output_path = kwargs['output_path']
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(image_path).stem}_furniture_{style}_{timestamp}.png")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "style": style,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed}
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(FURNITURE_STYLES.keys())}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="换家具工具")
    parser.add_argument("--input", "-i", required=True, help="输入室内图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--style", "-s", default="modern",
                        choices=list(FURNITURE_STYLES.keys()), help="家具风格")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeFurniture(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))