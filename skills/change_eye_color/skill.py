# skills/change_eye_color/skill.py
"""
改变瞳色 Skill - 改变人物眼睛颜色
使用 OpenPose ControlNet 保持姿态，Inpaint 重绘眼部区域
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
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
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

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装")

EYE_COLORS = {
    "blue": {
        "prompt": "blue eyes, bright blue irises, beautiful blue eyes, striking, masterpiece, high quality",
        "negative": "brown eyes, green eyes, dark eyes, ugly, deformed"
    },
    "green": {
        "prompt": "green eyes, emerald green irises, beautiful green eyes, striking, masterpiece, high quality",
        "negative": "brown eyes, blue eyes, dark eyes, ugly, deformed"
    },
    "hazel": {
        "prompt": "hazel eyes, golden brown irises, beautiful hazel eyes, warm, masterpiece, high quality",
        "negative": "blue eyes, green eyes, dark eyes, ugly, deformed"
    },
    "brown": {
        "prompt": "brown eyes, deep brown irises, beautiful brown eyes, warm, masterpiece, high quality",
        "negative": "blue eyes, green eyes, hazel eyes, ugly, deformed"
    },
    "gray": {
        "prompt": "gray eyes, silver gray irises, beautiful gray eyes, striking, masterpiece, high quality",
        "negative": "brown eyes, blue eyes, green eyes, ugly, deformed"
    },
    "purple": {
        "prompt": "purple eyes, violet irises, beautiful purple eyes, fantasy, striking, masterpiece, high quality",
        "negative": "brown eyes, blue eyes, green eyes, ugly, deformed"
    },
    "red": {
        "prompt": "red eyes, crimson irises, beautiful red eyes, striking, fantasy, masterpiece, high quality",
        "negative": "brown eyes, blue eyes, green eyes, ugly, deformed"
    },
    "gold": {
        "prompt": "golden eyes, gold irises, beautiful golden eyes, striking, masterpiece, high quality",
        "negative": "brown eyes, blue eyes, green eyes, ugly, deformed"
    }
}


class ChangeEyeColor:
    """改变瞳色技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_eye_color"
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
        self._yolo_model = None

        if CONTROLNET_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={'device': self.device, 'max_size': 512})
                logger.info("  ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"  ControlNet 技能初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeEyeColor 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  瞳色类型: {list(EYE_COLORS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.5,
            'default_color': 'blue',
            'default_negative': 'ugly, deformed, bad anatomy, blurry, low quality',
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

    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
                logger.info("  YOLO 加载成功")
            except Exception as e:
                logger.warning(f"  YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_eye_mask(self, image: Image.Image) -> Optional[Image.Image]:
        """生成眼部遮罩（精确到眼部区域）"""
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

            y_min, y_max = coords[0].min(), coords[0].max()
            body_h = y_max - y_min

            # 眼部区域（精确到眼睛位置）
            eye_top = y_min + int(body_h * 0.24)
            eye_bottom = y_min + int(body_h * 0.34)

            x_min, x_max = coords[1].min(), coords[1].max()
            body_w = x_max - x_min
            eye_left = x_min + int(body_w * 0.15)
            eye_right = x_max - int(body_w * 0.15)

            eye_mask = np.zeros_like(combined)
            eye_mask[eye_top:eye_bottom, eye_left:eye_right] = combined[eye_top:eye_bottom, eye_left:eye_right]

            kernel = np.ones((5, 5), np.uint8)
            eye_mask = cv2.dilate(eye_mask, kernel, iterations=1)
            eye_mask = cv2.GaussianBlur(eye_mask, (7, 7), 0)

            if np.sum(eye_mask > 0) < 50:
                return None

            logger.info(f"  眼部遮罩生成完成")
            return Image.fromarray(eye_mask, mode="L")

        except Exception as e:
            logger.warning(f"  眼部遮罩生成失败: {e}")
            return None

    def _generate_pose_image(self, image: Image.Image) -> Optional[Image.Image]:
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type='openpose',
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  姿态图生成失败: {e}")
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
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            color = kwargs.get('color', self.config.get('default_color', 'blue'))
            if color not in EYE_COLORS:
                return {"status": "error", "error": f"未知瞳色: {color}，可用: {list(EYE_COLORS.keys())}"}

            color_config = EYE_COLORS[color]
            prompt = kwargs.get('prompt') or color_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or color_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"瞳色: {color}")
            logger.info(f"提示词: {prompt[:80]}...")

            eye_mask = self._generate_eye_mask(image)
            if eye_mask is None:
                h, w = image.size[1], image.size[0]
                eye_mask = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(eye_mask)
                cx, cy = w // 2, h // 3
                draw.ellipse((cx - w//6, cy - h//12, cx + w//6, cy + h//12), fill=255)
                eye_mask = eye_mask.filter(ImageFilter.GaussianBlur(radius=5))

            control_image = self._generate_pose_image(image)

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': eye_mask,
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
                output_path = str(self.output_dir / f"{Path(image_path).stem}_eyes_{color}_{timestamp}.png")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "color": color,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed}
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def list_colors(self) -> Dict[str, Any]:
        return {"status": "success", "colors": list(EYE_COLORS.keys())}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="改变瞳色工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--color", "-c", default="blue",
                        choices=list(EYE_COLORS.keys()), help="瞳色")
    parser.add_argument("--strength", type=float, default=0.5, help="重绘强度")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeEyeColor(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        color=args.color,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))