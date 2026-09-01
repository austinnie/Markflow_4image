# skills/intimate_closeup/skill.py
"""
私处特写 - 一键生成唯美私处特写
"""

import time
import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
except ImportError:
    torch = None

try:
    from skills.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 引擎不可用: {e}")

STYLE_MAP = {
    "artistic": "artistic nude photography, fine art, soft focus, elegant composition, tasteful, masterpiece",
    "natural": "natural lighting, soft shadows, intimate atmosphere, warm tones, beautiful skin texture, masterpiece",
    "romantic": "romantic mood, soft glow, gentle lighting, intimate, sensual, beautiful, masterpiece",
    "vintage": "vintage style, soft grain, warm sepia tones, classic nude photography, timeless, masterpiece",
    "ethereal": "ethereal glow, dreamy atmosphere, soft light, delicate, beautiful, masterpiece",
}

BACKGROUND_MAP = {
    "soft": "soft blurred background, gentle bokeh, intimate setting, cozy atmosphere",
    "dark": "dark background, dramatic contrast, moody, sensual, artistic",
    "warm": "warm ambient light, cozy bedroom, golden tones, romantic atmosphere",
    "nature": "nature setting, soft greenery, dappled light, organic, peaceful",
    "studio": "clean studio background, professional lighting, elegant, refined",
}


class IntimateCloseup:
    """私处特写技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "intimate_closeup"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch and torch.cuda.is_available() else 'cpu')

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  ✅ ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"IntimateCloseup v{self.version} 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.6,
            'default_style': 'artistic',
            'default_background': 'soft',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, explicit, pornographic, vulgar, extreme closeup, gore, blood, injury, medical, surgery, disease, infection, shaved, completely bald',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}"}

            style = kwargs.get('style', self.config.get('default_style', 'artistic'))
            background = kwargs.get('background', self.config.get('default_background', 'soft'))

            if style not in STYLE_MAP:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(STYLE_MAP.keys())}"}
            if background not in BACKGROUND_MAP:
                return {"status": "error", "error": f"未知背景: {background}，可用: {list(BACKGROUND_MAP.keys())}"}

            prompt = f"close-up of a woman's intimate area, lower body, delicate skin, feminine beauty, {STYLE_MAP[style]}, {BACKGROUND_MAP[background]}, high quality, 8k, fine art photography"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_intimate_{style}_{background}_{timestamp}.png")

            logger.info(f"风格: {style}, 背景: {background}")
            logger.info(f"提示词: {prompt[:100]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                controlnet_type="openpose",
                controlnet_strength=0.8,
                strength=strength,
                steps=steps,
                seed=seed,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('output_path', output_path),
                "style": style,
                "background": background,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<IntimateCloseup(name={self.name}, version={self.version})>"