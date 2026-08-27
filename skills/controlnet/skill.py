"""
ControlNet - 提供姿态检测和 ControlNet 控制能力
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# ==================== 依赖检查 ====================
try:
    import torch
    import numpy as np
    from PIL import Image
    import cv2
    TORCH_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    logger.warning(f"基础依赖未安装: {e}")

try:
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")

try:
    from controlnet_aux import (
        OpenposeDetector,
        CannyDetector,
        HEDdetector,
        MidasDetector,
        LineartDetector,
        NormalBaeDetector,
        MLSDdetector,
        DWposeDetector,
    )
    CONTROLNET_AUX_AVAILABLE = True
except ImportError as e:
    CONTROLNET_AUX_AVAILABLE = False
    logger.warning(f"controlnet_aux 未安装: {e}")


# ==================== ControlNet 类型配置（无需 mediapipe） ====================
CONTROLNET_TYPES = {
    "canny": {
        "name": "Canny (边缘)",
        "model_id": "lllyasviel/sd-controlnet-canny",
        "preprocessor": "canny",
        "description": "边缘轮廓控制，适合保持构图"
    },
    "hed": {
        "name": "HED (软边缘)",
        "model_id": "lllyasviel/sd-controlnet-hed",
        "preprocessor": "hed",
        "description": "软边缘检测，更灵活"
    },
    "lineart": {
        "name": "Lineart (线稿)",
        "model_id": "lllyasviel/control_v11p_sd15_lineart",
        "preprocessor": "lineart",
        "description": "线稿提取，适合二次元"
    },
    "depth": {
        "name": "Depth (深度)",
        "model_id": "lllyasviel/sd-controlnet-depth",
        "preprocessor": "depth",
        "description": "深度图控制，适合保持空间结构"
    },
    "normal": {
        "name": "Normal (法线)",
        "model_id": "lllyasviel/sd-controlnet-normal",
        "preprocessor": "normal",
        "description": "法线图控制，适合保持光影"
    },
    "mlsd": {
        "name": "MLSD (直线)",
        "model_id": "lllyasviel/sd-controlnet-mlsd",
        "preprocessor": "mlsd",
        "description": "直线检测，适合建筑"
    },
    "openpose": {
        "name": "OpenPose (姿态)",
        "model_id": "lllyasviel/sd-controlnet-openpose",
        "preprocessor": "openpose",
        "description": "检测人体姿态骨架，适合换装、换姿势"
    },
    "openpose_full": {
        "name": "OpenPose Full (完整姿态)",
        "model_id": "lllyasviel/control_v11p_sd15_openpose",
        "preprocessor": "openpose_full",
        "description": "全身姿态 + 手指 + 面部表情"
    },
}


class Controlnet:
    """
    ControlNet 技能

    提供:
        1. 姿态检测 (detect_pose)
        2. ControlNet Pipeline 加载 (load_pipeline)
        3. 状态查看 (status)
        4. 类型列表 (list_types)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 ControlNet 技能

        Args:
            config: 配置字典
                - device: 设备 (cpu/cuda)
                - max_size: 最大尺寸
                - cache_dir: 缓存目录
        """
        self.config = config or {}
        self.name = "ControlNet"
        self.version = "1.0.0"

        # 获取技能目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 配置
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.max_size = self.config.get('max_size', 512)
        self.cache_dir = self.config.get('cache_dir', str(self.skill_dir / 'cache'))

        # 缓存
        self._pipelines = {}
        self._detectors = {}

        self._setup_logging()
        self._setup_config()

        logger.info(f"ControlNet 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  最大尺寸: {self.max_size}")
        logger.info(f"  diffusers: {'✅' if DIFFUSERS_AVAILABLE else '❌'}")
        logger.info(f"  controlnet_aux: {'✅' if CONTROLNET_AUX_AVAILABLE else '❌'}")

    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        """设置配置默认值"""
        defaults = {
            'max_size': 512,
            'controlnet_strength': 0.8,
            'device': self.device,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _get_detector(self, controlnet_type: str):
        """获取或创建检测器"""
        if not CONTROLNET_AUX_AVAILABLE:
            return None

        if controlnet_type in self._detectors:
            return self._detectors[controlnet_type]

        try:
            #detectors = {
            #    "openpose": lambda: OpenposeDetector.from_pretrained("lllyasviel/ControlNet"),  # 修改这里
            #    "openpose_full": lambda: OpenposeDetector.from_pretrained("lllyasviel/ControlNet"),
            #    "dwpose": lambda: DWposeDetector.from_pretrained("lllyasviel/ControlNet"),
            #    "canny": lambda: CannyDetector(),
            #    "hed": lambda: HEDdetector.from_pretrained("lllyasviel/ControlNet"),
            #    "lineart": lambda: LineartDetector.from_pretrained("lllyasviel/ControlNet"),
            #    "depth": lambda: MidasDetector.from_pretrained("lllyasviel/ControlNet"),
            #    "normal": lambda: NormalBaeDetector.from_pretrained("lllyasviel/ControlNet"),
            #    "mlsd": lambda: MLSDdetector.from_pretrained("lllyasviel/ControlNet"),
            #}

            detectors = {
                "openpose": lambda: OpenposeDetector.from_pretrained("lllyasviel/Annotators"),
                "openpose_full": lambda: OpenposeDetector.from_pretrained("lllyasviel/Annotators"),
                #"dwpose": lambda: DWposeDetector(),  # 🔥 修复：不需要 from_pretrained
                "canny": lambda: CannyDetector(),
                "hed": lambda: HEDdetector.from_pretrained("lllyasviel/Annotators"),
                "lineart": lambda: LineartDetector.from_pretrained("lllyasviel/Annotators"),
                "depth": lambda: MidasDetector.from_pretrained("lllyasviel/Annotators"),
                "normal": lambda: NormalBaeDetector.from_pretrained("lllyasviel/Annotators"),
                "mlsd": lambda: MLSDdetector.from_pretrained("lllyasviel/Annotators"),
            }

            if controlnet_type in detectors:
                logger.info(f"加载检测器: {controlnet_type}")
                self._detectors[controlnet_type] = detectors[controlnet_type]()
                return self._detectors[controlnet_type]
            else:
                logger.warning(f"不支持的检测器类型: {controlnet_type}")
                return None

        except Exception as e:
            logger.error(f"加载检测器失败 ({controlnet_type}): {e}")
            return None

    def detect_pose(
        self,
        image: Union[str, Image.Image],
        controlnet_type: str = "openpose",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检测图片姿态，生成 ControlNet 控制图

        Args:
            image: 图片路径或 PIL Image
            controlnet_type: ControlNet 类型
            output_path: 输出路径 (可选)

        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"检测姿态: controlnet_type={controlnet_type}")

        # 1. 检查依赖
        if not CONTROLNET_AUX_AVAILABLE:
            return {
                "status": "error",
                "error": "controlnet_aux 未安装，请运行: pip install controlnet-aux"
            }

        # 2. 加载图片
        try:
            if isinstance(image, str):
                if not os.path.exists(image):
                    return {"status": "error", "error": f"图片不存在: {image}"}
                pil_image = Image.open(image).convert("RGB")
                image_path = image
            else:
                pil_image = image.convert("RGB")
                image_path = None
        except Exception as e:
            return {"status": "error", "error": f"加载图片失败: {e}"}

        # 3. 获取检测器
        detector = self._get_detector(controlnet_type)
        if detector is None:
            return {
                "status": "error",
                "error": f"无法加载检测器: {controlnet_type}"
            }

        # 4. 生成控制图
        try:
            # 调整尺寸
            w, h = pil_image.size
            if max(w, h) > self.max_size:
                scale = self.max_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # 执行检测
            if controlnet_type == "openpose":
                result = detector(pil_image, output_type="pil", include_hands=False, include_face=False)
            elif controlnet_type == "openpose_full":
                result = detector(pil_image, output_type="pil", include_hands=True, include_face=True)
            else:
                result = detector(pil_image, output_type="pil")

            if result is None:
                return {"status": "error", "error": "姿态检测返回空结果"}

            # 5. 保存结果
            if output_path is None:
                if image_path:
                    base, ext = os.path.splitext(image_path)
                    filename = f"{os.path.basename(base)}_{controlnet_type}_control.png"
                    output_path = str(self.output_dir / filename)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = str(self.output_dir / f"pose_{controlnet_type}_{timestamp}.png")

            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "controlnet_type": controlnet_type,
                "processing_time": f"{time.time() - start_time:.2f}s",
                "size": result.size,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"姿态检测失败: {e}")
            return {"status": "error", "error": str(e)}

    def get_pipeline(
        self,
        model_path: str,
        controlnet_type: str = "openpose"
    ) -> Dict[str, Any]:
        """
        加载 ControlNet Pipeline

        Args:
            model_path: SD 模型路径
            controlnet_type: ControlNet 类型

        Returns:
            执行结果
        """
        logger.info(f"加载 ControlNet Pipeline: model={model_path}, type={controlnet_type}")

        # 1. 检查依赖
        if not DIFFUSERS_AVAILABLE:
            return {
                "status": "error",
                "error": "diffusers 未安装，请运行: pip install diffusers"
            }

        # 2. 检查模型
        if not os.path.exists(model_path):
            return {
                "status": "error",
                "error": f"模型不存在: {model_path}"
            }

        # 3. 检查缓存
        cache_key = f"{model_path}_{controlnet_type}"
        if cache_key in self._pipelines:
            logger.info("使用缓存的 Pipeline")
            return {
                "status": "success",
                "pipeline": self._pipelines[cache_key],
                "controlnet_type": controlnet_type,
                "cached": True
            }

        # 4. 加载 ControlNet
        try:
            info = CONTROLNET_TYPES.get(controlnet_type)
            if info is None:
                return {
                    "status": "error",
                    "error": f"不支持的 ControlNet 类型: {controlnet_type}"
                }

            model_id = info["model_id"]
            logger.info(f"加载 ControlNet 模型: {model_id}")

            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                cache_dir=self.cache_dir,
            )

            # 5. 加载 Pipeline
            logger.info(f"加载 SD 模型: {model_path}")
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                model_path,
                controlnet=controlnet,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            pipe.to(self.device)
            pipe.enable_attention_slicing()

            # 6. 缓存
            self._pipelines[cache_key] = pipe

            return {
                "status": "success",
                "pipeline": pipe,
                "controlnet_type": controlnet_type,
                "cached": False,
                "device": self.device,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"加载 ControlNet Pipeline 失败: {e}")
            return {"status": "error", "error": str(e)}

    def list_types(self) -> Dict[str, Any]:
        """列出所有支持的 ControlNet 类型"""
        types = {}
        for key, info in CONTROLNET_TYPES.items():
            types[key] = {
                "name": info["name"],
                "description": info["description"],
                "available": CONTROLNET_AUX_AVAILABLE,
            }

        return {
            "status": "success",
            "types": types,
            "count": len(types),
            "controlnet_aux_available": CONTROLNET_AUX_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

    def status(self) -> Dict[str, Any]:
        """查看 ControlNet 技能状态"""
        return {
            "status": "success",
            "skill": {
                "name": self.name,
                "version": self.version,
                "device": self.device,
                "max_size": self.max_size,
                "cache_dir": self.cache_dir,
            },
            "dependencies": {
                "diffusers": DIFFUSERS_AVAILABLE,
                "controlnet_aux": CONTROLNET_AUX_AVAILABLE,
                "torch": TORCH_AVAILABLE,
            },
            "cached_pipelines": list(self._pipelines.keys()),
            "timestamp": datetime.now().isoformat()
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 ControlNet 技能

        支持的操作:
            - status: 查看状态 (默认)
            - list_types: 列出支持的 ControlNet 类型
            - detect_pose: 检测姿态，生成控制图
            - load_pipeline: 加载 ControlNet Pipeline
        """
        action = kwargs.get('action', 'status')
        logger.info(f"执行 ControlNet 技能: action={action}")

        if action == 'status':
            return self.status()

        elif action == 'list_types':
            return self.list_types()

        elif action == 'detect_pose':
            image = kwargs.get('image') or kwargs.get('image_path')
            if image is None:
                return {"status": "error", "error": "image 或 image_path 是必填参数"}

            controlnet_type = kwargs.get('controlnet_type', 'openpose')
            output_path = kwargs.get('output_path')

            return self.detect_pose(image, controlnet_type, output_path)

        elif action == 'load_pipeline':
            model_path = kwargs.get('model_path')
            if model_path is None:
                return {"status": "error", "error": "model_path 是必填参数"}

            controlnet_type = kwargs.get('controlnet_type', 'openpose')

            return self.get_pipeline(model_path, controlnet_type)

        else:
            return {
                "status": "error",
                "error": f"未知操作: {action}，支持: status, list_types, detect_pose, load_pipeline",
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<Controlnet(name={self.name}, version={self.version})>"


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ControlNet 技能")
    parser.add_argument("--action", default="status",
                        choices=["status", "list_types", "detect_pose", "load_pipeline"],
                        help="操作类型")
    parser.add_argument("--image", help="图片路径 (detect_pose)")
    parser.add_argument("--image-path", help="图片路径 (detect_pose, 同 image)")
    parser.add_argument("--output-path", help="输出路径 (detect_pose)")
    parser.add_argument("--model-path", help="SD 模型路径 (load_pipeline)")
    parser.add_argument("--controlnet-type", default="canny",
                        choices=list(CONTROLNET_TYPES.keys()),
                        help="ControlNet 类型")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")

    args = parser.parse_args()

    skill = Controlnet(config={'device': args.device})
    result = skill.execute(
        action=args.action,
        image=args.image or args.image_path,
        output_path=args.output_path,
        model_path=args.model_path,
        controlnet_type=args.controlnet_type,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))