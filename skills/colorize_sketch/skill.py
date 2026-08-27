# skills/colorize_sketch/skill.py
"""
线稿上色 Skill - 给黑白线稿/素描上色
使用 Lineart ControlNet 保持线条，Inpaint 重绘颜色
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
    from PIL import Image, ImageFilter
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

# 上色风格预设
COLOR_STYLES = {
    "anime": {
        "prompt": "anime style, vibrant colors, cel shading, beautiful, detailed coloring, masterpiece, best quality, 2d illustration",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed, black and white"
    },
    "realistic": {
        "prompt": "photorealistic, vibrant colors, natural lighting, detailed, high quality, masterpiece, beautiful coloring",
        "negative": "anime, cartoon, ugly, deformed, blurry, black and white"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft colors, artistic, flowing, delicate, masterpiece, high quality, beautiful coloring",
        "negative": "photorealistic, 3d render, hard edges, anime, black and white"
    },
    "vintage": {
        "prompt": "vintage style, warm tones, nostalgic, retro coloring, soft, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, black and white"
    },
    "pastel": {
        "prompt": "pastel colors, soft, gentle, delicate, beautiful coloring, masterpiece, high quality, cute",
        "negative": "photorealistic, 3d render, dark, ugly, black and white"
    },
    "vibrant": {
        "prompt": "vibrant colors, colorful, rich colors, stunning, eye-catching, masterpiece, high quality, beautiful",
        "negative": "photorealistic, 3d render, ugly, deformed, black and white, dull"
    }
}


class ColorizeSketch:
    """线稿上色技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "colorize_sketch"
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

        logger.info(f"ColorizeSketch 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  上色风格: {len(COLOR_STYLES)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.8,
            'default_style': 'anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        Path(self.config.get('output_dir', str(self.output_dir))).mkdir(parents=True, exist_ok=True)

    def _find_model(self, model_name: str) -> Optional[Path]:
        # 简化，实际使用与 remove_clothes 相同逻辑
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

    def _generate_lineart_image(self, image: Image.Image) -> Optional[Image.Image]:
        """使用 ControlNet 生成线稿图"""
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type='lineart',
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  线稿图生成失败: {e}")
            return None

    def _resize_image(self, image: Image.Image) -> tuple:
        w, h = image.size
        max_size = 768
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image, image.size

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行线稿上色"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            style = kwargs.get('style', self.config.get('default_style', 'anime'))
            if style not in COLOR_STYLES:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(COLOR_STYLES.keys())}"}

            style_config = COLOR_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            # 加载模型
            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"上色风格: {style}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 生成线稿图（用于 ControlNet）
            control_image = self._generate_lineart_image(image)

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            # 全白遮罩 = 全部重绘
            current_size = image.size
            mask = Image.new("L", current_size, 0)

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
                output_path = str(self.output_dir / f"{Path(image_path).stem}_{style}_{timestamp}.png")

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
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(COLOR_STYLES.keys())}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="线稿上色工具")
    parser.add_argument("--input", "-i", required=True, help="输入线稿图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--style", "-s", default="anime",
                        choices=list(COLOR_STYLES.keys()), help="上色风格")
    parser.add_argument("--strength", type=float, default=0.8, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ColorizeSketch(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))