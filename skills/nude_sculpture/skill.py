# skills/nude_sculpture/skill.py
"""
裸体雕塑 - 一键生成大理石/青铜雕塑风格裸体人像
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

MATERIAL_MAP = {
    "marble": "white marble sculpture, smooth polished surface, translucent effect, classical, masterpiece",
    "bronze": "bronze sculpture, patina texture, greenish-brown tones, aged metal, masterpiece",
    "terracotta": "terracotta sculpture, warm terracotta color, matte surface, earthy, masterpiece",
    "jade": "jade sculpture, smooth polished jade, green tones, translucent, precious, masterpiece",
    "alabaster": "alabaster sculpture, soft white, translucent, smooth, ethereal, masterpiece",
    "gold": "gold sculpture, polished gold surface, luxurious, brilliant, masterpiece",
}

STYLE_MAP = {
    "classical": "classical Greek sculpture, idealized proportions, contrapposto, timeless beauty, masterpiece",
    "hellenistic": "Hellenistic sculpture, dramatic emotion, dynamic pose, expressive, masterpiece",
    "renaissance": "Renaissance sculpture, anatomical precision, graceful, refined, masterpiece",
    "neoclassical": "Neoclassical sculpture, elegant lines, restrained emotion, noble, masterpiece",
    "modern": "modern sculpture, abstract forms, simplified shapes, contemporary, masterpiece",
    "archaic": "archaic sculpture, stiff pose, archaic smile, ancient, primitive, masterpiece",
}

POSE_MAP = {
    "standing": "standing upright, elegant posture, arms relaxed, masterpiece",
    "reclining": "reclining, one arm supporting head, relaxed, sensual, masterpiece",
    "sitting": "sitting on pedestal, graceful pose, hands on lap, masterpiece",
    "kneeling": "kneeling, looking up, devotional, masterpiece",
    "dancing": "dancing, dynamic motion, one foot raised, graceful, masterpiece",
}


class NudeSculpture:
    """裸体雕塑技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "nude_sculpture"
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

        logger.info(f"NudeSculpture v{self.version} 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.6,
            'default_material': 'marble',
            'default_style': 'classical',
            'default_pose': 'standing',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, painting, drawing',
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

            material = kwargs.get('material', self.config.get('default_material', 'marble'))
            style = kwargs.get('style', self.config.get('default_style', 'classical'))
            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))

            if material not in MATERIAL_MAP:
                return {"status": "error", "error": f"未知材质: {material}，可用: {list(MATERIAL_MAP.keys())}"}
            if style not in STYLE_MAP:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(STYLE_MAP.keys())}"}
            if pose not in POSE_MAP:
                return {"status": "error", "error": f"未知姿态: {pose}，可用: {list(POSE_MAP.keys())}"}

            prompt = f"1girl, full body, nude, sculpture, 3D statue, {MATERIAL_MAP[material]}, {STYLE_MAP[style]}, {POSE_MAP[pose]}, pedestal, museum lighting, high quality, masterpiece, 8k, photorealistic 3D render"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_sculpture_{material}_{style}_{timestamp}.png")

            logger.info(f"材质: {material}, 风格: {style}, 姿态: {pose}")
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
                "material": material,
                "style": style,
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
        return f"<NudeSculpture(name={self.name}, version={self.version})>"