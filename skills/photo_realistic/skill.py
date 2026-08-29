# skills/photo_realistic/skill.py
"""
照片真实化 Skill - 结合 ControlNet 图生图与 OpenCV 后期处理
默认只做纯后期处理，开启 ai_realistic 后可进行真实化重绘
"""

import os
import sys
import random
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV 未安装，图像处理功能不可用")

# ==================== 引入通用 ControlNet 引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

# ==================== 相机预设 ====================
CAMERA_PRESETS = {
    "sony_a7iv": {
        "Make": "Sony", "Model": "ILCE-7M4",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM"
    },
    "canon_r5": {
        "Make": "Canon", "Model": "Canon EOS R5",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 100],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-70mm F2.8 L IS USM"
    },
    "nikon_z8": {
        "Make": "Nikon", "Model": "NIKON Z 8",
        "ISO": [64, 100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 24-70mm f/2.8 S"
    },
    "iphone_15": {
        "Make": "Apple", "Model": "iPhone 15 Pro Max",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.78, 2.2, 2.8],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 48, 77],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "iPhone 15 Pro Max back triple camera"
    }
}

PHOTO_STYLES = {
    "portrait": {"ISO": [100, 200], "FNumber": [1.8, 2.8], "FocalLength": [50, 85, 105]},
    "landscape": {"ISO": [64, 100], "FNumber": [5.6, 8.0, 11.0], "FocalLength": [24, 35, 50]},
    "street": {"ISO": [200, 400, 800], "FNumber": [2.8, 4.0, 5.6], "FocalLength": [24, 35, 50]},
    "night": {"ISO": [1600, 3200, 6400], "FNumber": [1.8, 2.8], "FocalLength": [24, 35, 50]}
}


class PhotoRealistic:
    """照片真实化技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_realistic"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ==================== ControlNet 引擎实例化 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"照片真实化技能 v{self.version} 初始化完成")
        logger.info(f"  ControlNet: {'✅ 可用' if self.controlnet_engine else '❌ 不可用'}")
        logger.info(f"  OpenCV: {'✅ 可用' if CV2_AVAILABLE else '❌ 不可用'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_camera': 'sony_a7iv',
            'default_style': 'portrait',
            'default_strength': 'medium',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _inject_exif(self, image_path: str, camera: str = "sony_a7iv", style: str = "portrait", randomize: bool = True) -> Dict[str, Any]:
        """注入 EXIF 元数据（使用 ExifTool）"""
        camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
        style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])

        exif_params = {
            "Make": camera_preset.get("Make", "Sony"),
            "Model": camera_preset.get("Model", "ILCE-7M4"),
            "Software": camera_preset.get("Software", "Adobe Photoshop Lightroom 6.0"),
        }

        if randomize:
            exif_params["ISO"] = random.choice(camera_preset.get("ISO", [100]))
            exif_params["FNumber"] = random.choice(camera_preset.get("FNumber", [1.8]))
            exif_params["ExposureTime"] = random.choice(camera_preset.get("ExposureTime", ["1/125"]))
            exif_params["FocalLength"] = random.choice(camera_preset.get("FocalLength", [50]))
        else:
            exif_params["ISO"] = style_preset.get("ISO", [100])[0]
            exif_params["FNumber"] = style_preset.get("FNumber", [2.8])[0]
            exif_params["FocalLength"] = style_preset.get("FocalLength", [50])[0]
            exif_params["ExposureTime"] = "1/250"

        exif_params["LensModel"] = camera_preset.get("LensModel", "")

        exiftool = shutil.which("exiftool")
        if exiftool is None:
            return {"status": "warning", "message": "exiftool 未找到"}

        try:
            cmd = [exiftool, "-overwrite_original"]
            for key, value in exif_params.items():
                if value:
                    cmd.extend([f"-{key}", str(value)])
            cmd.append(image_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {"status": "warning", "message": f"EXIF 注入失败: {result.stderr}"}
            return {"status": "success", "exif_params": exif_params}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def add_realistic_features(self, image: Image.Image, iso: int = 400, add_noise: bool = True, add_vignette: bool = True, add_sharpening: bool = True) -> Image.Image:
        """添加真实相机特征（OpenCV）"""
        if not CV2_AVAILABLE:
            return image

        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        if add_noise:
            noise_strength = max(1, min(20, iso / 50))
            noise = np.random.normal(0, noise_strength, img_cv.shape).astype(np.uint8)
            img_cv = cv2.add(img_cv, noise)
            logger.info(f"  ✅ 添加噪点 (ISO {iso})")

        if add_vignette:
            kernel_x = cv2.getGaussianKernel(w, w * 0.3)
            kernel_y = cv2.getGaussianKernel(h, h * 0.3)
            kernel = kernel_y * kernel_x.T
            mask = 1 - kernel * 0.25
            for i in range(3):
                img_cv[:, :, i] = (img_cv[:, :, i] * mask).astype(np.uint8)
            logger.info("  ✅ 添加暗角")

        if add_sharpening:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) * 0.8 + 0.2 * np.eye(3)
            kernel = kernel / np.sum(kernel)
            img_cv = cv2.filter2D(img_cv, -1, kernel)
            logger.info("  ✅ 锐化")

        return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    def process(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        # ===== 核心开关 =====
        ai_realistic: bool = False,       # 是否开启 ControlNet 重绘
        enable_noise: bool = False,
        enable_vignette: bool = False,
        enable_sharpen: bool = False,
        enable_exif: bool = False,
        # ===== 参数 =====
        camera: str = "sony_a7iv",
        style: str = "portrait",
        strength: str = "medium",
        iso: Optional[int] = None,
        randomize: bool = True
    ) -> Dict[str, Any]:
        """
        处理图片
        Args:
            image_path: 输入图片路径
            output_path: 输出路径
            ai_realistic: 是否开启 ControlNet AI 真实化重绘 (设为 True 将优先调用 controlnet_img2img)
            enable_noise: 是否添加噪点
            enable_vignette: 是否添加暗角
            enable_sharpen: 是否锐化
            enable_exif: 是否注入 EXIF
        """
        # ==================== 严格路径校验 ====================
        if not image_path:
            return {"status": "error", "error": "image_path 是必填参数"}
        abs_image_path = Path(image_path).absolute()
        if not os.path.exists(abs_image_path):
            return {"status": "error", "error": f"输入图片不存在: {abs_image_path}"}

        # 默认输出到本技能目录
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_realistic_{timestamp}.jpg")

        # 1. 先判断是否调用 ControlNet 进行重绘
        if ai_realistic:
            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}
            logger.info("  🔥 开启 ControlNet AI 真实化重绘...")
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt="photorealistic, real person, realistic skin texture, natural lighting, detailed, masterpiece, high quality, 8k",
                negative_prompt="anime, cartoon, 2d, illustration, drawing, painting, sketch, blurry, low quality",
                preprocessor_type="HED",
                controlnet_model="canny",
                strength=0.45,  # 低重绘幅度，保持原图结构
                output_path=output_path
            )
            if result['status'] != 'success':
                return result
            # 重绘后的图片
            image = Image.open(output_path).convert("RGB")
        else:
            # 不重绘，直接读取原图
            image = Image.open(abs_image_path).convert("RGB")

        # 2. OpenCV 后期效果（基于重绘后的图片）
        applied = {"noise": False, "vignette": False, "sharpen": False, "exif": False}

        # 确定 ISO
        strength_map = {"light": {"iso": 200}, "medium": {"iso": 400}, "strong": {"iso": 800}}
        if iso is None:
            iso = strength_map.get(strength, strength_map["medium"])["iso"]
            if randomize:
                iso = random.choice([iso, iso * 2])

        if enable_noise or enable_vignette or enable_sharpen:
            image = self.add_realistic_features(
                image, iso=iso,
                add_noise=enable_noise,
                add_vignette=enable_vignette,
                add_sharpening=enable_sharpen
            )
            applied["noise"] = enable_noise
            applied["vignette"] = enable_vignette
            applied["sharpen"] = enable_sharpen

        # 3. 保存最终结果
        image.save(output_path, format='JPEG', quality=92, optimize=True)

        result = {
            "status": "success",
            "output_path": output_path,
            "applied": applied,
            "ai_realistic": ai_realistic,
            "iso": iso,
        }

        # 4. EXIF 注入
        if enable_exif:
            exif_result = self._inject_exif(output_path, camera=camera, style=style, randomize=randomize)
            applied["exif"] = True
            result["exif"] = exif_result
            logger.info(f"  ✅ EXIF 注入成功 (相机: {camera})")

        logger.info(f"✅ 处理完成: {output_path}")
        return result

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行技能"""
        action = kwargs.get('action', 'process')

        if action == 'process':
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            return self.process(
                image_path=image_path,
                output_path=kwargs.get('output_path'),
                ai_realistic=kwargs.get('ai_realistic', False),
                enable_noise=kwargs.get('enable_noise', False),
                enable_vignette=kwargs.get('enable_vignette', False),
                enable_sharpen=kwargs.get('enable_sharpen', False),
                enable_exif=kwargs.get('enable_exif', False),
                camera=kwargs.get('camera', self.config.get('default_camera', 'sony_a7iv')),
                style=kwargs.get('style', self.config.get('default_style', 'portrait')),
                strength=kwargs.get('strength', self.config.get('default_strength', 'medium')),
                iso=kwargs.get('iso'),
                randomize=kwargs.get('randomize', True)
            )

        elif action == 'list_cameras':
            return {"status": "success", "cameras": list(CAMERA_PRESETS.keys())}

        elif action == 'list_styles':
            return {"status": "success", "styles": list(PHOTO_STYLES.keys())}

        else:
            return {"status": "error", "error": f"未知操作: {action}"}

    def __repr__(self):
        return f"<PhotoRealistic(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="照片真实化工具 v2.0")

    parser.add_argument("--input", "-i", help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")

    parser.add_argument("--ai-realistic", action="store_true", help="开启 ControlNet AI 真实化")
    parser.add_argument("--noise", action="store_true", help="添加噪点")
    parser.add_argument("--vignette", action="store_true", help="添加暗角")
    parser.add_argument("--sharpen", action="store_true", help="锐化")
    parser.add_argument("--exif", action="store_true", help="注入 EXIF")

    parser.add_argument("--camera", default="sony_a7iv", choices=list(CAMERA_PRESETS.keys()), help="相机预设")
    parser.add_argument("--style", default="portrait", choices=list(PHOTO_STYLES.keys()), help="照片风格")
    parser.add_argument("--strength", default="medium", choices=["light", "medium", "strong"], help="强度")
    parser.add_argument("--iso", type=int, help="ISO 值")

    args = parser.parse_args()

    skill = PhotoRealistic()

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        ai_realistic=args.ai_realistic,
        enable_noise=args.noise,
        enable_vignette=args.vignette,
        enable_sharpen=args.sharpen,
        enable_exif=args.exif,
        camera=args.camera,
        style=args.style,
        strength=args.strength,
        iso=args.iso
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))