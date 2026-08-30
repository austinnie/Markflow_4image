# skills/expand_to_full_body/skill.py
"""
Expand to Full Body - 将人物半身/头像图扩展为全身图
复用通用 ControlNet 引擎，使用 MediaPipe 极速轻量检测定位头部
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    import numpy as np
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch 或 PIL 未安装")

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")


class ExpandToFullBody:
    """半身图转全身图技能 v2.0 (MediaPipe + OpenPose 锁姿态)"""

    # 可用模型列表（用于展示）
    AVAILABLE_MODELS = {
        "anytimeRealistic_v10.safetensors": {"name": "Anytime Realistic", "size": "2.13 GB", "type": "写实"},
        "aiiiii01_v10.safetensors": {"name": "AIiiii v1.0", "size": "2.13 GB", "type": "写实"},
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "expand_to_full_body"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 30)
        self.target_height = self.config.get('target_height', 1024)
        self.target_width = self.config.get('target_width', 768)

        # 缓存
        self.controlnet_engine = None

        # ==================== 初始化底层引擎 ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        # ==================== 初始化 MediaPipe（新版 API） ====================
        self._mediapipe_pose = None
        self._init_mediapipe()

        self._setup_logging()
        self._setup_config()

        logger.info(f"ExpandToFullBody v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  目标尺寸: {self.target_width}x{self.target_height}")
        logger.info(f"  ControlNet: {'✅' if self.controlnet_engine else '❌'}")

    def _init_mediapipe(self):
        """初始化 MediaPipe（新版 API）"""
        self._mediapipe_pose = None
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # 模型文件路径
            model_path = self.skill_dir / "pose_landmarker_heavy.task"

            # 如果模型不存在，尝试下载
            if not model_path.exists():
                logger.info("  📥 下载 MediaPipe 姿态模型...")
                try:
                    import urllib.request
                    url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
                    urllib.request.urlretrieve(url, str(model_path))
                    logger.info(f"  ✅ 模型已下载: {model_path}")
                except Exception as e:
                    logger.warning(f"  ⚠️ 模型下载失败: {e}")
                    return

            # 初始化姿态检测器
            pose_options = vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self._mediapipe_pose = vision.PoseLandmarker.create_from_options(pose_options)
            logger.info("  ✅ MediaPipe (新版 API) 初始化成功")

        except ImportError as e:
            logger.warning(f"  ⚠️ MediaPipe 未安装: {e}")
            logger.warning("  将使用默认扩展逻辑")
        except Exception as e:
            logger.warning(f"  ⚠️ MediaPipe 初始化失败: {e}")
            logger.warning("  将使用默认扩展逻辑")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'target_width': 768,
            'target_height': 1024,
            'default_model': 'anytimeRealistic_v10.safetensors',
            'default_steps': 30,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _detect_head_position(self, image: Image.Image) -> tuple:
        """使用 MediaPipe 检测头部在图像中的 Y 坐标比例（新版 API）"""
        try:
            if self._mediapipe_pose is None:
                return image.size[1] * 0.15, image.size[0] // 2

            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # 将 PIL Image 转换为 MediaPipe Image
            img_rgb = image.convert('RGB')
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(img_rgb))

            # 检测姿态
            detection_result = self._mediapipe_pose.detect(mp_image)

            if detection_result and detection_result.pose_landmarks:
                landmarks = detection_result.pose_landmarks[0]
                h, w = img_rgb.size[1], img_rgb.size[0]
                # 0 是鼻子
                nose = landmarks[0]
                head_y = int(nose.y * h)
                head_x = int(nose.x * w)
                return head_y, head_x
        except Exception as e:
            logger.warning(f"头部检测失败: {e}")

        return image.size[1] * 0.15, image.size[0] // 2

    def _expand_image_area(self, image: Image.Image, target_width: int, target_height: int,
                           head_y: float, head_x: float) -> Image.Image:
        """扩展画布，将原图放置在头部位于 15% 高度的位置"""
        src_w, src_h = image.size

        # 计算缩放比例：让头部大约在 15% 位置
        head_ratio = 0.15
        scale = (target_height * head_ratio) / max(src_h * 0.15, head_y)

        # 限制缩放范围
        scale = max(0.5, min(2.0, scale))

        # 缩放图片
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 计算粘贴位置
        offset_y = int(target_height * 0.15 - head_y * scale)
        offset_x = int((target_width - new_w) // 2)

        # 创建扩展图片
        expanded = Image.new("RGB", (target_width, target_height), (128, 128, 128))
        expanded.paste(resized, (offset_x, offset_y))

        return expanded

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            image = Image.open(abs_image_path).convert("RGB")

            output_path = kwargs.get('output_path')
            model_name = kwargs.get('model_name', self.default_model)
            prompt = kwargs.get('prompt', 'a person, beautiful, detailed, full body, standing')
            negative_prompt = kwargs.get('negative_prompt', 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality')
            steps = kwargs.get('steps', self.default_steps)
            seed = kwargs.get('seed', -1)

            # 更新目标尺寸
            target_w = kwargs.get('target_width', self.config.get('target_width', 768))
            target_h = kwargs.get('target_height', self.config.get('target_height', 1024))

            # ==================== 1. 扩展画布 ====================
            head_y, head_x = self._detect_head_position(image)
            expanded = self._expand_image_area(image, target_w, target_h, head_y, head_x)
            logger.info(f"画布扩展完成: {target_w}x{target_h}")

            # ==================== 2. 保存扩展图作为临时输入 ====================
            temp_input = self.output_dir / "_temp_expanded.png"
            expanded.save(temp_input)

            # ==================== 3. 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"full_body_{timestamp}.png")

            prompt = f"{prompt}, full body, whole body, standing, detailed, masterpiece, best quality, photorealistic"

            # 使用 OpenPose 锁死人物原始结构
            result = self.controlnet_engine.execute(
                input_image_path=str(temp_input),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",
                controlnet_model="openpose",
                strength=0.75,
                steps=steps,
                output_path=output_path
            )

            # 清理临时文件
            if temp_input.exists():
                temp_input.unlink()

            if result['status'] != 'success':
                return result

            elapsed = time.time() - start_time

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "parameters": {
                    "model": model_name,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "steps": steps,
                    "seed": seed,
                    "controlnet_type": "openpose",
                    "target_size": f"{target_w}x{target_h}",
                },
                "generation_time": f"{elapsed:.2f}s",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def list_models(self) -> Dict[str, Any]:
        models = {}
        for key, info in self.AVAILABLE_MODELS.items():
            models[key] = {"name": info["name"], "size": info["size"], "type": info["type"]}
        return {"status": "success", "models": models, "count": len(models), "default": self.default_model}

    def __repr__(self):
        return f"<ExpandToFullBody(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(ExpandToFullBody.AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="半身图转全身图 v2.0")
    parser.add_argument("--input", "-i", required=False, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出图片路径")
    parser.add_argument("--prompt", "-p", default="a person, beautiful, detailed, full body", help="人物描述提示词")
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors", choices=MODEL_CHOICES, help="模型名称")
    parser.add_argument("--steps", "-s", type=int, default=30, help="推理步数")
    parser.add_argument("--width", type=int, default=768, help="目标宽度")
    parser.add_argument("--height", type=int, default=1024, help="目标高度")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="设备")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用模型")

    args = parser.parse_args()

    if args.list_models:
        skill = ExpandToFullBody()
        result = skill.list_models()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.input:
        parser.error("--input 是必填参数")

    skill = ExpandToFullBody(config={'device': args.device, 'target_width': args.width, 'target_height': args.height})

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        prompt=args.prompt,
        model_name=args.model,
        steps=args.steps,
        target_width=args.width,
        target_height=args.height,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))