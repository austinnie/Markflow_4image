# skills/style_transfer/skill.py
"""
风格转换 Skill - 将图片转换为指定风格（油画/水彩/动漫/素描等）
使用 Canny ControlNet 保持构图
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
    from PIL import Image
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

# 风格预设
STYLE_PRESETS = {
    "oil_painting": {
        "prompt": "oil painting, thick brushstrokes, canvas texture, masterpiece, van gogh style, rich colors, artistic, high quality",
        "negative": "photorealistic, 3d render, digital art, smooth, cartoon, anime"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft wash, paper texture, flowing colors, transparent, artistic, masterpiece, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges, oil painting"
    },
    "anime": {
        "prompt": "anime style, cel shading, vibrant colors, anime art, masterpiece, best quality, 2d illustration, manga style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "sketch": {
        "prompt": "pencil sketch, graphite drawing, fine lines, cross-hatching, monochrome, black and white, masterpiece, high quality",
        "negative": "photorealistic, color, 3d render, smooth, oil painting"
    },
    "impressionist": {
        "prompt": "impressionist painting, soft brushstrokes, vibrant colors, light effects, masterpiece, claude monet style, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges"
    },
    "pixel_art": {
        "prompt": "pixel art, retro game style, 8-bit, blocky, colorful, masterpiece, high quality",
        "negative": "photorealistic, 3d render, smooth, blurry, oil painting"
    },
    "cyberpunk": {
        "prompt": "cyberpunk style, neon colors, futuristic, glowing lights, dark atmosphere, sci-fi, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, blurry"
    },
    "vintage": {
        "prompt": "vintage photo style, retro, film grain, warm tones, nostalgic, old photo, masterpiece, high quality",
        "negative": "digital art, 3d render, photorealistic, ugly, deformed"
    }
}


class StyleTransfer:
    """风格转换技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "style_transfer"
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

        logger.info(f"StyleTransfer 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  预设风格: {len(STYLE_PRESETS)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.75,
            'default_style': 'oil_painting',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        Path(self.config.get('output_dir', str(self.output_dir))).mkdir(parents=True, exist_ok=True)

    def _find_model(self, model_name: str) -> Optional[Path]:
        if not model_name:
            model_name = self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
        # ... (同其他 skill 的查找逻辑)
        return None  # 简化，实际使用时补全

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
        # 简化实现
        return True

    def _generate_edge_image(self, image: Image.Image) -> Optional[Image.Image]:
        """使用 ControlNet 生成边缘图"""
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type='canny',
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  边缘图生成失败: {e}")
            return None

    def _generate_control_image(self, image: Image.Image, controlnet_type: str) -> Optional[Image.Image]:
        """生成 ControlNet 控制图"""
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type=controlnet_type,
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  控制图生成失败: {e}")
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
        """执行风格转换"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            style = kwargs.get('style', self.config.get('default_style', 'oil_painting'))
            if style not in STYLE_PRESETS:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(STYLE_PRESETS.keys())}"}

            style_config = STYLE_PRESETS[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.75))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"风格: {style}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 生成 ControlNet 控制图
            control_image = self._generate_control_image(image, 'canny')

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            # 执行 Inpaint
            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': Image.new("L", current_size, 0),  # 全白遮罩 = 全部重绘
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
            return {"status": "error", "error": str(e)}

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(STYLE_PRESETS.keys())}

    def __repr__(self):
        return f"<StyleTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="风格转换工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--style", "-s", default="oil_painting",
                        choices=list(STYLE_PRESETS.keys()), help="风格")
    parser.add_argument("--strength", type=float, default=0.75, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = StyleTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))