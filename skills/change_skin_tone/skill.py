# skills/change_skin_tone/skill.py
"""
改变肤色 Skill - 改变人物肤色（白皙/古铜/深色等）
优先使用 YOLO 定位皮肤区域，复用通用 ControlNet 引擎进行局部/全局重绘
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
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch 或 OpenCV 未安装")

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装")

SKIN_TONES = {
    "fair": {
        "prompt": "fair skin, pale skin, light complexion, beautiful, masterpiece, high quality",
        "negative": "dark skin, tan, brown, ugly, deformed"
    },
    "tan": {
        "prompt": "tan skin, sun-kissed, golden complexion, beautiful, masterpiece, high quality",
        "negative": "pale, fair, dark, ugly, deformed"
    },
    "dark": {
        "prompt": "dark skin, beautiful brown skin, rich complexion, beautiful, masterpiece, high quality",
        "negative": "fair, pale, tan, ugly, deformed"
    },
    "olive": {
        "prompt": "olive skin, warm complexion, Mediterranean, beautiful, masterpiece, high quality",
        "negative": "fair, pale, dark, ugly, deformed"
    },
    "warm": {
        "prompt": "warm skin tone, golden undertone, glowing skin, beautiful, masterpiece, high quality",
        "negative": "pale, cold, dark, ugly, deformed"
    }
}


class ChangeSkinTone:
    """改变肤色技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_skin_tone"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.pipeline = None
        self.current_model = None
        self._yolo_model = None

        # ==================== 初始化底层引擎 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeSkinTone v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  肤色类型: {list(SKIN_TONES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.45,  # 改变肤色不能太大强度，以免改变五官
            'default_tone': 'fair',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
            except Exception as e:
                logger.warning(f"  YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_skin_mask(self, image: Image.Image) -> Optional[Image.Image]:
        """生成皮肤遮罩（YOLO 全身）"""
        h, w = image.size[1], image.size[0]
        yolo = self._get_yolo_model()
        if not yolo:
            return None

        try:
            results = yolo(image, verbose=False)
            if len(results) == 0 or results[0].masks is None:
                return None

            masks = results[0].masks.data.cpu().numpy()
            combined = np.zeros((h, w), dtype=np.uint8)
            for m in masks:
                m_resized = cv2.resize(m, (w, h))
                combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)

            coords = np.where(combined > 0)
            if len(coords[0]) == 0:
                return None

            skin_mask = combined
            kernel = np.ones((10, 10), np.uint8)
            skin_mask = cv2.dilate(skin_mask, kernel, iterations=1)
            skin_mask = cv2.GaussianBlur(skin_mask, (15, 15), 0)

            if np.sum(skin_mask > 0) < 100:
                return None

            return Image.fromarray(skin_mask, mode="L")

        except Exception as e:
            logger.warning(f"  皮肤遮罩生成失败: {e}")
            return None

    def list_tones(self) -> Dict[str, Any]:
        return {"status": "success", "tones": list(SKIN_TONES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            tone = kwargs.get('tone', self.config.get('default_tone', 'fair'))
            if tone not in SKIN_TONES:
                return {"status": "error", "error": f"未知肤色: {tone}，可用: {list(SKIN_TONES.keys())}"}

            tone_config = SKIN_TONES[tone]
            prompt = kwargs.get('prompt') or tone_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or tone_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.45))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # 默认输出到本技能目录
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_skintone_{tone}_{timestamp}.png")

            # ==================== 直接调用底层引擎（全局） ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            logger.info(f"肤色: {tone}")
            logger.info(f"提示词: {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # 保留五官和身体轮廓
                controlnet_model="canny",     # 对应本地模型
                strength=strength,            # 低强度，避免五官变形
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "tone": tone,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "canny"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ChangeSkinTone(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="改变肤色工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--tone", "-t", default="fair",
                        choices=list(SKIN_TONES.keys()), help="肤色类型")
    parser.add_argument("--strength", type=float, default=0.45, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeSkinTone(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        tone=args.tone,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))