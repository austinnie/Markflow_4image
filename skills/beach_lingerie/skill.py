# skills/beach_lingerie/skill.py
"""
海滩唯美内衣 - 一键生成
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

OUTFIT_MAP = {
    "white_lace": "white lace lingerie, delicate lace, elegant, beautiful, masterpiece",
    "black_silk": "black silk lingerie, glossy silk, sophisticated, seductive, masterpiece",
    "pink_satin": "pink satin lingerie, soft satin, romantic, cute, masterpiece",
    "red_velvet": "red velvet lingerie, luxurious velvet, passionate, bold, masterpiece",
    "blue_lace": "blue lace lingerie, delicate lace, elegant, beautiful, masterpiece",
}

POSE_MAP = {
    "standing": "standing on sandy beach, full body, confident pose, hands on hips, masterpiece",
    "walking": "walking on beach, dynamic motion, one foot raised, elegant stride, masterpiece",
    "sitting": "sitting on beach towel, relaxed posture, looking at viewer, masterpiece",
}


class BeachLingerie:
    """海滩唯美内衣技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "beach_lingerie"
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

        logger.info(f"BeachLingerie v{self.version} 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_outfit': 'white_lace',
            'default_pose': 'standing',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality',
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

            outfit = kwargs.get('outfit', self.config.get('default_outfit', 'white_lace'))
            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))

            if outfit not in OUTFIT_MAP:
                return {"status": "error", "error": f"未知内衣风格: {outfit}，可用: {list(OUTFIT_MAP.keys())}"}
            if pose not in POSE_MAP:
                return {"status": "error", "error": f"未知姿态: {pose}，可用: {list(POSE_MAP.keys())}"}

            base_prompt = "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, "

            if pose == "standing":
                base_prompt += "standing on a beautiful sandy beach, ocean waves in background, confident posture, hands on hips, "
            elif pose == "walking":
                base_prompt += "walking along the beach, dynamic motion, ocean in background, elegant stride, "
            elif pose == "sitting":
                base_prompt += "sitting on a beach towel on the sand, relaxed posture, ocean view, "

            prompt = base_prompt + OUTFIT_MAP[outfit] + ", beach background, sunny day, golden sunlight, high quality, masterpiece, 8k, photorealistic"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_beach_{outfit}_{pose}_{timestamp}.png")

            logger.info(f"内衣风格: {outfit}, 姿态: {pose}")
            logger.info(f"提示词: {prompt[:100]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                controlnet_type="openpose",
                controlnet_strength=1.0,
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
                "outfit": outfit,
                "pose": pose,
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
        return f"<BeachLingerie(name={self.name}, version={self.version})>"