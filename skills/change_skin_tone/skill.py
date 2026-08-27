# skills/change_skin_tone/skill.py
"""
改变肤色 Skill - 改变人物肤色（白皙/古铜/深色等）
使用 OpenPose ControlNet 保持姿态，Inpaint 重绘皮肤区域
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
    """改变肤色技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_skin_tone"
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

        logger.info(f"ChangeSkinTone 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  肤色类型: {list(SKIN_TONES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.6,
            'default_tone': 'fair',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
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

    def _generate_skin_mask(self, image: Image.Image) -> Optional[Image.Image]:
        """生成皮肤遮罩（面部 + 身体暴露区域）"""
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

            # 全身皮肤区域（排除头发和衣服）
            # 这里简化处理，使用全身遮罩
            skin_mask = combined

            kernel = np.ones((10, 10), np.uint8)
            skin_mask = cv2.dilate(skin_mask, kernel, iterations=1)
            skin_mask = cv2.GaussianBlur(skin_mask, (15, 15), 0)

            if np.sum(skin_mask > 0) < 100:
                return None

            logger.info(f"  皮肤遮罩生成完成")
            return Image.fromarray(skin_mask, mode="L")

        except Exception as e:
            logger.warning(f"  皮肤遮罩生成失败: {e}")
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

            tone = kwargs.get('tone', self.config.get('default_tone', 'fair'))
            if tone not in SKIN_TONES:
                return {"status": "error", "error": f"未知肤色: {tone}，可用: {list(SKIN_TONES.keys())}"}

            tone_config = SKIN_TONES[tone]
            prompt = kwargs.get('prompt') or tone_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or tone_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"肤色: {tone}")
            logger.info(f"提示词: {prompt[:80]}...")

            skin_mask = self._generate_skin_mask(image)
            if skin_mask is None:
                h, w = image.size[1], image.size[0]
                skin_mask = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(skin_mask)
                cx, cy = w // 2, h // 2
                draw.ellipse((cx - w//3, cy - h//2, cx + w//3, cy + h//2), fill=255)
                skin_mask = skin_mask.filter(ImageFilter.GaussianBlur(radius=15))

            control_image = self._generate_pose_image(image)

            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': skin_mask,
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
                output_path = str(self.output_dir / f"{Path(image_path).stem}_skintone_{tone}_{timestamp}.png")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "tone": tone,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed}
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def list_tones(self) -> Dict[str, Any]:
        return {"status": "success", "tones": list(SKIN_TONES.keys())}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="改变肤色工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--tone", "-t", default="fair",
                        choices=list(SKIN_TONES.keys()), help="肤色类型")
    parser.add_argument("--strength", type=float, default=0.6, help="重绘强度")
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