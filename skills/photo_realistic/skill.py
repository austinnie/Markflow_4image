# skills/photo_realistic/skill.py
"""
照片真实化 Skill - 让 AI 图片看起来像真实相机照片
所有功能默认关闭，通过参数单独开启
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
    "fuji_x100v": {
        "Make": "FUJIFILM", "Model": "X100V",
        "ISO": [160, 200, 400, 800, 1600, 3200],
        "FNumber": [2.0, 2.8, 4.0, 5.6, 8.0],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [23],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FUJINON 23mm F2.0"
    },
    "iphone_15": {
        "Make": "Apple", "Model": "iPhone 15 Pro Max",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.78, 2.2, 2.8],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 48, 77],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "iPhone 15 Pro Max back triple camera"
    },
    "pixel_8": {
        "Make": "Google", "Model": "Pixel 8 Pro",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.68, 2.8, 3.5],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [25, 48, 113],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "Pixel 8 Pro back camera"
    }
}

PHOTO_STYLES = {
    "portrait": {"ISO": [100, 200], "FNumber": [1.8, 2.8], "FocalLength": [50, 85, 105]},
    "landscape": {"ISO": [64, 100], "FNumber": [5.6, 8.0, 11.0], "FocalLength": [24, 35, 50]},
    "street": {"ISO": [200, 400, 800], "FNumber": [2.8, 4.0, 5.6], "FocalLength": [24, 35, 50]},
    "sports": {"ISO": [800, 1600, 3200], "FNumber": [2.8, 4.0], "FocalLength": [70, 85, 135]},
    "night": {"ISO": [1600, 3200, 6400], "FNumber": [1.8, 2.8], "FocalLength": [24, 35, 50]},
    "macro": {"ISO": [100, 200], "FNumber": [2.8, 4.0], "FocalLength": [85, 105, 135]},
    "wedding": {"ISO": [200, 400, 800], "FNumber": [1.8, 2.8, 4.0], "FocalLength": [24, 35, 50, 85]}
}


class PhotoRealistic:
    """
    照片真实化技能 - 让 AI 图片看起来像真实相机照片
    所有功能默认关闭，通过参数单独开启
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_realistic"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self._setup_config()

        logger.info(f"照片真实化技能初始化完成")
        logger.info(f"  输出目录: {self.output_dir}")
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

    def _find_exiftool(self) -> Optional[str]:
        """查找 exiftool 路径"""
        exiftool = shutil.which("exiftool")
        if exiftool is None:
            logger.warning("exiftool 未找到，EXIF 注入将跳过")
        return exiftool

    def _inject_exif(
        self,
        image_path: str,
        camera: str = "sony_a7iv",
        style: str = "portrait",
        randomize: bool = True
    ) -> Dict[str, Any]:
        """注入 EXIF 元数据"""
        camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
        style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])

        exif_params = {
            "Make": camera_preset.get("Make", "Sony"),
            "Model": camera_preset.get("Model", "ILCE-7M4"),
            "Software": camera_preset.get("Software", "Adobe Photoshop Lightroom 6.0"),
            "Artist": "Photographer",
            "Copyright": "",
        }

        # ISO
        if randomize:
            exif_params["ISO"] = random.choice(camera_preset.get("ISO", [100, 200, 400]))
        else:
            exif_params["ISO"] = style_preset.get("ISO", [200])[0]

        # FNumber
        if randomize:
            exif_params["FNumber"] = random.choice(camera_preset.get("FNumber", [1.8, 2.8, 4.0]))
        else:
            exif_params["FNumber"] = style_preset.get("FNumber", [2.8])[0]

        # ExposureTime
        if randomize:
            exif_params["ExposureTime"] = random.choice(camera_preset.get("ExposureTime", ["1/125", "1/250", "1/500"]))
        else:
            exif_params["ExposureTime"] = "1/250"

        # FocalLength
        if randomize:
            exif_params["FocalLength"] = random.choice(camera_preset.get("FocalLength", [35, 50, 85]))
        else:
            exif_params["FocalLength"] = style_preset.get("FocalLength", [50])[0]

        exif_params["LensModel"] = camera_preset.get("LensModel", "")

        # DateTimeOriginal
        days_ago = random.randint(0, 30) if randomize else 0
        dt = datetime.now().replace(
            hour=random.randint(8, 20) if randomize else 12,
            minute=random.randint(0, 59) if randomize else 0,
            second=random.randint(0, 59) if randomize else 0
        )
        exif_params["DateTimeOriginal"] = dt.strftime("%Y:%m:%d %H:%M:%S")

        exiftool = self._find_exiftool()
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

        except subprocess.TimeoutExpired:
            return {"status": "warning", "message": "exiftool 超时"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def add_realistic_features(
        self,
        image: Image.Image,
        iso: int = 400,
        add_noise: bool = True,
        add_vignette: bool = True,
        add_sharpening: bool = True
    ) -> Image.Image:
        """添加真实相机特征"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV 不可用，跳过图像处理")
            return image

        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        # 1. 添加噪点
        if add_noise:
            noise_strength = max(1, min(20, iso / 50))
            noise = np.random.normal(0, noise_strength, img_cv.shape).astype(np.uint8)
            img_cv = cv2.add(img_cv, noise)
            logger.info(f"  ✅ 添加噪点 (ISO {iso}, 强度 {noise_strength:.1f})")

        # 2. 添加暗角
        if add_vignette:
            kernel_x = cv2.getGaussianKernel(w, w * 0.3)
            kernel_y = cv2.getGaussianKernel(h, h * 0.3)
            kernel = kernel_y * kernel_x.T
            mask = 1 - kernel * 0.25
            for i in range(3):
                img_cv[:, :, i] = (img_cv[:, :, i] * mask).astype(np.uint8)
            logger.info("  ✅ 添加暗角")

        # 3. 锐化
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
        # 功能开关（默认全部关闭）
        enable_noise: bool = False,
        enable_vignette: bool = False,
        enable_sharpen: bool = False,
        enable_exif: bool = False,
        # 参数
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
            enable_noise: 是否添加噪点
            enable_vignette: 是否添加暗角
            enable_sharpen: 是否锐化
            enable_exif: 是否注入 EXIF
            camera: 相机预设
            style: 照片风格
            strength: 强度 (light/medium/strong)
            iso: ISO 值
            randomize: 是否随机化
        """
        if not os.path.exists(image_path):
            return {"status": "error", "error": f"图片不存在: {image_path}"}

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{Path(image_path).stem}_processed_{timestamp}.jpg")

        # 加载图片
        image = Image.open(image_path).convert("RGB")

        # 确定 ISO
        strength_map = {"light": {"iso": 200}, "medium": {"iso": 400}, "strong": {"iso": 800}}
        if iso is None:
            iso = strength_map.get(strength, strength_map["medium"])["iso"]
            if randomize:
                iso = random.choice([iso, iso * 2])

        # 应用图像处理（只有开启时才处理）
        applied = {"noise": False, "vignette": False, "sharpen": False, "exif": False}

        if enable_noise or enable_vignette or enable_sharpen:
            image = self.add_realistic_features(
                image,
                iso=iso,
                add_noise=enable_noise,
                add_vignette=enable_vignette,
                add_sharpening=enable_sharpen
            )
            applied["noise"] = enable_noise
            applied["vignette"] = enable_vignette
            applied["sharpen"] = enable_sharpen

        # 保存
        image.save(output_path, format='JPEG', quality=92, optimize=True)

        result = {
            "status": "success",
            "output_path": output_path,
            "applied": applied,
            "iso": iso,
            "strength": strength,
        }

        # EXIF 注入（独立执行）
        if enable_exif:
            exif_result = self._inject_exif(output_path, camera=camera, style=style, randomize=randomize)
            applied["exif"] = True
            result["exif"] = exif_result
            if exif_result.get('status') == 'success':
                logger.info(f"  ✅ EXIF 注入成功 (相机: {camera})")

        # 如果没有开启任何功能
        if not any([enable_noise, enable_vignette, enable_sharpen, enable_exif]):
            logger.info("  ℹ️ 未开启任何处理功能，仅复制图片")

        logger.info(f"✅ 处理完成: {output_path}")
        return result

    def batch_process(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """批量处理"""
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"目录不存在: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "realistic_output"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        images = [f for f in input_path.glob("*") if f.suffix.lower() in extensions]

        if not images:
            return {"status": "error", "error": f"未找到图片: {input_dir}"}

        logger.info(f"📁 找到 {len(images)} 个图片")
        logger.info(f"📂 输出目录: {output_dir}")

        results = []
        success_count = 0

        for i, img_path in enumerate(images, 1):
            logger.info(f"\n[{i}/{len(images)}] {img_path.name}")
            out_file = output_path / img_path.name

            result = self.process(str(img_path), str(out_file), **kwargs)
            results.append(result)
            if result['status'] == 'success':
                success_count += 1

        return {
            "status": "success" if success_count > 0 else "error",
            "total": len(images),
            "success": success_count,
            "results": results,
            "output_dir": str(output_path)
        }

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

        elif action == 'batch':
            input_dir = kwargs.get('input_dir')
            if not input_dir:
                return {"status": "error", "error": "input_dir 是必填参数"}
            return self.batch_process(input_dir, kwargs.get('output_dir'), **kwargs)

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

    parser = argparse.ArgumentParser(
        description="照片真实化工具 - 让 AI 图片更像真实照片",
        epilog="所有功能默认关闭，通过参数单独开启"
    )

    parser.add_argument("--input", "-i", help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--input-dir", help="输入目录 (批量模式)")

    # ===== 功能开关（默认全部关闭） =====
    parser.add_argument("--noise", action="store_true", help="添加噪点")
    parser.add_argument("--vignette", action="store_true", help="添加暗角")
    parser.add_argument("--sharpen", action="store_true", help="锐化")
    parser.add_argument("--exif", action="store_true", help="注入 EXIF 元数据")

    # ===== 参数 =====
    parser.add_argument("--camera", default="sony_a7iv",
                        choices=list(CAMERA_PRESETS.keys()), help="相机预设")
    parser.add_argument("--style", default="portrait",
                        choices=list(PHOTO_STYLES.keys()), help="照片风格")
    parser.add_argument("--strength", default="medium",
                        choices=["light", "medium", "strong"], help="强度")
    parser.add_argument("--iso", type=int, help="ISO 值")
    parser.add_argument("--no-random", action="store_true", help="不随机化参数")

    args = parser.parse_args()

    skill = PhotoRealistic()

    if args.batch:
        if not args.input_dir:
            print("❌ 批量模式需要 --input-dir")
            exit(1)
        result = skill.batch_process(
            args.input_dir,
            args.output,
            enable_noise=args.noise,
            enable_vignette=args.vignette,
            enable_sharpen=args.sharpen,
            enable_exif=args.exif,
            camera=args.camera,
            style=args.style,
            strength=args.strength,
            iso=args.iso,
            randomize=not args.no_random
        )
    else:
        if not args.input:
            print("❌ 需要 --input")
            exit(1)
        result = skill.process(
            args.input,
            args.output,
            enable_noise=args.noise,
            enable_vignette=args.vignette,
            enable_sharpen=args.sharpen,
            enable_exif=args.exif,
            camera=args.camera,
            style=args.style,
            strength=args.strength,
            iso=args.iso,
            randomize=not args.no_random
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))