# skills/pool_nude/skill.py
"""
泳池裸露 - 一键生成
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

POSE_MAP = {
    "standing": "standing in pool, water up to waist, full body, confident pose, masterpiece",
    "sitting": "sitting on pool edge, feet in water, relaxed posture, looking at viewer, masterpiece",
    "floating": "floating on water, relaxed, elegant pose, water reflections, masterpiece",
    "walking": "walking in shallow water, dynamic motion, water splashing, masterpiece",
}

LIGHTING_MAP = {
    "sunny": "bright sunlight, sparkling water, golden reflections, warm atmosphere, high quality",
    "golden": "golden hour lighting, warm orange tones, beautiful reflections, romantic, high quality",
    "blue": "blue hour lighting, cool tones, serene atmosphere, tranquil, high quality",
    "night": "night pool lighting, underwater lights, magical atmosphere, dreamy, high quality",
}


class PoolNude:
    """泳池裸露技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "pool_nude"
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

        logger.info(f"PoolNude v{self.version} 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_pose': 'standing',
            'default_lighting': 'sunny',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric',
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

            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))
            lighting = kwargs.get('lighting', self.config.get('default_lighting', 'sunny'))

            if pose not in POSE_MAP:
                return {"status": "error", "error": f"未知姿态: {pose}，可用: {list(POSE_MAP.keys())}"}
            if lighting not in LIGHTING_MAP:
                return {"status": "error", "error": f"未知灯光: {lighting}，可用: {list(LIGHTING_MAP.keys())}"}

            prompt = f"1girl, full body, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, wet skin, water droplets on skin, {POSE_MAP[pose]}, {LIGHTING_MAP[lighting]}, swimming pool background, blue water, high quality, masterpiece, 8k, photorealistic"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_pool_{pose}_{lighting}_{timestamp}.png")

            logger.info(f"姿态: {pose}, 灯光: {lighting}")
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
                "pose": pose,
                "lighting": lighting,
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
        return f"<PoolNude(name={self.name}, version={self.version})>"