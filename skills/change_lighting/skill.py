# skills/change_lighting/skill.py
"""
改变光照 Skill - 保持场景结构不变，改变光照氛围
使用 Depth ControlNet 保持空间结构，Inpaint 重绘光影
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

# 光照预设
LIGHTING_PRESETS = {
    "golden_hour": {
        "prompt": "golden hour lighting, warm sunset light, soft warm glow, beautiful lighting, masterpiece",
        "negative": "harsh lighting, dark, cold, blue"
    },
    "sunny": {
        "prompt": "bright sunny day, natural sunlight, clear lighting, vibrant, masterpiece",
        "negative": "dark, gloomy, night, harsh shadows"
    },
    "night": {
        "prompt": "night scene, moonlight, dark atmosphere, soft lighting, starry, masterpiece",
        "negative": "bright, sunny, daylight, harsh lighting"
    },
    "studio": {
        "prompt": "studio lighting, professional photography, soft light, elegant, masterpiece",
        "negative": "harsh, natural light, outdoor"
    },
    "dramatic": {
        "prompt": "dramatic lighting, chiaroscuro, strong contrast, moody, cinematic, masterpiece",
        "negative": "flat lighting, soft, bright, daylight"
    },
    "soft": {
        "prompt": "soft lighting, diffused light, gentle, warm, cozy, masterpiece",
        "negative": "harsh, dramatic, strong contrast"
    },
    "cyberpunk": {
        "prompt": "cyberpunk lighting, neon lights, colorful, futuristic, glowing, masterpiece",
        "negative": "natural, daylight, soft, warm"
    },
    "moody": {
        "prompt": "moody lighting, dark atmosphere, mysterious, soft shadows, cinematic, masterpiece",
        "negative": "bright, sunny, happy, flat"
    }
}


class ChangeLighting:
    """改变光照技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_lighting"
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

        logger.info(f"ChangeLighting 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  光照预设: {len(LIGHTING_PRESETS)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.7,
            'default_lighting': 'golden_hour',
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

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行改变光照"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            lighting = kwargs.get('lighting', self.config.get('default_lighting', 'golden_hour'))
            if lighting not in LIGHTING_PRESETS:
                return {"status": "error", "error": f"未知光照: {lighting}，可用: {list(LIGHTING_PRESETS.keys())}"}

            lighting_config = LIGHTING_PRESETS[lighting]
            prompt = kwargs.get('prompt') or lighting_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or lighting_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"光照: {lighting}")
            logger.info(f"提示词: {prompt[:80]}...")

            control_image = self._generate_depth_image(image)

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

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
                output_path = str(self.output_dir / f"{Path(image_path).stem}_light_{lighting}_{timestamp}.png")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "lighting": lighting,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed}
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def list_lightings(self) -> Dict[str, Any]:
        return {"status": "success", "lightings": list(LIGHTING_PRESETS.keys())}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="改变光照工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--lighting", "-l", default="golden_hour",
                        choices=list(LIGHTING_PRESETS.keys()), help="光照预设")
    parser.add_argument("--prompt", "-p", help="自定义提示词")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeLighting(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        lighting=args.lighting, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))