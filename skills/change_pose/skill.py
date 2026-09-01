
# skills/change_pose/skill.py
"""
改变人物姿态 Skill - 基于 ControlNet OpenPose
"""

import time
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
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch 或 PIL 未安装")

try:
    from skills.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 引擎不可用: {e}")

POSE_PROMPTS = {
    "standing": "standing upright, full body, straight posture, arms relaxed, looking forward, masterpiece, high quality",
    "sitting": "sitting on a chair, relaxed posture, legs together, hands on knees, looking at viewer, masterpiece, high quality",
    "lying": "lying down on bed, sideways, relaxed, peaceful expression, comfortable, masterpiece, high quality",
    "side_lying": "lying on side, one arm supporting head, elegant pose, relaxed, masterpiece, high quality",
    "kneeling": "kneeling on the ground, looking up, elegant posture, masterpiece, high quality",
    "walking": "walking forward, dynamic motion, one foot raised, confident stride, masterpiece, high quality",
    "running": "running, dynamic action, arms swinging, energetic, motion, masterpiece, high quality",
    "dancing": "dancing, elegant motion, arms raised, graceful, dynamic, masterpiece, high quality",
    "squatting": "squatting down, casual posture, relaxed, masterpiece, high quality",
    "jumping": "jumping in the air, dynamic, energetic, full extension, masterpiece, high quality",
}


class ChangePose:
    """改变人物姿态技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_pose"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  ✅ ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangePose v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  姿态类型: {list(POSE_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.65,
            'default_pose': 'standing',
            'default_controlnet_type': 'openpose',
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

            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))
            if pose not in POSE_PROMPTS:
                return {"status": "error", "error": f"未知姿态: {pose}，可用: {list(POSE_PROMPTS.keys())}"}

            pose_config = POSE_PROMPTS[pose]
            prompt = kwargs.get('prompt') or pose_config
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.65))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_pose_{pose}_{timestamp}.png")

            logger.info(f"目标姿态: {pose}")
            logger.info(f"提示词: {prompt[:80]}...")

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
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "controlnet": "openpose"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ChangePose(name={self.name}, version={self.version})>"