# skills/exif_injector/skill.py
"""
EXIF 注入 Skill - 为图片添加相机元数据，让 AI 图片更像真实照片
"""

import os
import sys
import random
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
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL 未安装")


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


class ExifInjector:
    """
    EXIF 注入技能 - 为图片添加相机元数据
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "exif_injector"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self._setup_config()

        logger.info(f"EXIF 注入器初始化完成")
        logger.info(f"  输出目录: {self.output_dir}")

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
            'randomize': True,
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

    def inject_exif(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        camera: str = "sony_a7iv",
        style: str = "portrait",
        iso: Optional[int] = None,
        fnumber: Optional[float] = None,
        focal_length: Optional[int] = None,
        exposure_time: Optional[str] = None,
        date_time: Optional[str] = None,
        randomize: bool = True,
        artist: str = "Photographer"
    ) -> Dict[str, Any]:
        """
        为图片注入 EXIF 元数据

        Args:
            image_path: 输入图片路径
            output_path: 输出路径
            camera: 相机预设
            style: 照片风格
            iso: ISO 值
            fnumber: 光圈值
            focal_length: 焦距
            exposure_time: 快门速度
            date_time: 拍摄时间
            randomize: 是否随机化
            artist: 作者

        Returns:
            执行结果
        """
        if not os.path.exists(image_path):
            return {"status": "error", "error": f"图片不存在: {image_path}"}

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{Path(image_path).stem}_with_exif_{timestamp}.jpg")

        # 获取预设
        camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
        style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])

        # 构建 EXIF 参数
        exif_params = {
            "Make": camera_preset.get("Make", "Sony"),
            "Model": camera_preset.get("Model", "ILCE-7M4"),
            "Software": camera_preset.get("Software", "Adobe Photoshop Lightroom 6.0"),
            "Artist": artist,
        }

        # ISO
        if iso is not None:
            exif_params["ISO"] = iso
        elif randomize:
            exif_params["ISO"] = random.choice(camera_preset.get("ISO", [100, 200, 400]))
        else:
            exif_params["ISO"] = style_preset.get("ISO", [200])[0]

        # FNumber
        if fnumber is not None:
            exif_params["FNumber"] = fnumber
        elif randomize:
            exif_params["FNumber"] = random.choice(camera_preset.get("FNumber", [1.8, 2.8, 4.0]))
        else:
            exif_params["FNumber"] = style_preset.get("FNumber", [2.8])[0]

        # ExposureTime
        if exposure_time is not None:
            exif_params["ExposureTime"] = exposure_time
        elif randomize:
            exif_params["ExposureTime"] = random.choice(camera_preset.get("ExposureTime", ["1/125", "1/250", "1/500"]))
        else:
            exif_params["ExposureTime"] = "1/250"

        # FocalLength
        if focal_length is not None:
            exif_params["FocalLength"] = focal_length
        elif randomize:
            exif_params["FocalLength"] = random.choice(camera_preset.get("FocalLength", [35, 50, 85]))
        else:
            exif_params["FocalLength"] = style_preset.get("FocalLength", [50])[0]

        # LensModel
        exif_params["LensModel"] = camera_preset.get("LensModel", "")

        # DateTimeOriginal
        if date_time:
            exif_params["DateTimeOriginal"] = date_time
        else:
            days_ago = random.randint(0, 30) if randomize else 0
            dt = datetime.now().replace(
                hour=random.randint(8, 20) if randomize else 12,
                minute=random.randint(0, 59) if randomize else 0,
                second=random.randint(0, 59) if randomize else 0
            )
            exif_params["DateTimeOriginal"] = dt.strftime("%Y:%m:%d %H:%M:%S")

        # 执行注入
        exiftool = self._find_exiftool()
        if exiftool is None:
            # 直接复制文件
            shutil.copy2(image_path, output_path)
            return {
                "status": "warning",
                "output_path": output_path,
                "message": "exiftool 未找到，仅复制文件"
            }

        try:
            cmd = [exiftool, "-overwrite_original"]
            for key, value in exif_params.items():
                if value:
                    cmd.extend([f"-{key}", str(value)])
            cmd.append(image_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                shutil.copy2(image_path, output_path)
                return {
                    "status": "warning",
                    "output_path": output_path,
                    "message": f"EXIF 注入失败: {result.stderr}"
                }

            if output_path != image_path:
                shutil.move(image_path, output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "exif_params": exif_params,
                "camera": camera,
                "style": style
            }

        except subprocess.TimeoutExpired:
            shutil.copy2(image_path, output_path)
            return {"status": "warning", "output_path": output_path, "message": "exiftool 超时"}
        except Exception as e:
            shutil.copy2(image_path, output_path)
            return {"status": "error", "output_path": output_path, "error": str(e)}

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
            output_dir = input_path / "exif_output"
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

            result = self.inject_exif(
                str(img_path),
                str(out_file),
                **kwargs
            )
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
        action = kwargs.get('action', 'inject')

        if action == 'inject':
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            return self.inject_exif(
                image_path=image_path,
                output_path=kwargs.get('output_path'),
                camera=kwargs.get('camera', self.config.get('default_camera', 'sony_a7iv')),
                style=kwargs.get('style', self.config.get('default_style', 'portrait')),
                iso=kwargs.get('iso'),
                fnumber=kwargs.get('fnumber'),
                focal_length=kwargs.get('focal_length'),
                exposure_time=kwargs.get('exposure_time'),
                date_time=kwargs.get('date_time'),
                randomize=kwargs.get('randomize', self.config.get('randomize', True)),
                artist=kwargs.get('artist', 'Photographer')
            )

        elif action == 'batch':
            input_dir = kwargs.get('input_dir')
            if not input_dir:
                return {"status": "error", "error": "input_dir 是必填参数"}
            return self.batch_process(input_dir, kwargs.get('output_dir'), **kwargs)

        elif action == 'list_cameras':
            return {
                "status": "success",
                "cameras": list(CAMERA_PRESETS.keys())
            }

        elif action == 'list_styles':
            return {
                "status": "success",
                "styles": list(PHOTO_STYLES.keys())
            }

        else:
            return {"status": "error", "error": f"未知操作: {action}"}

    def __repr__(self):
        return f"<ExifInjector(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EXIF 注入工具")
    parser.add_argument("--input", "-i", help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--camera", default="sony_a7iv",
                        choices=list(CAMERA_PRESETS.keys()), help="相机预设")
    parser.add_argument("--style", default="portrait",
                        choices=list(PHOTO_STYLES.keys()), help="照片风格")
    parser.add_argument("--iso", type=int, help="ISO 值")
    parser.add_argument("--fnumber", type=float, help="光圈值")
    parser.add_argument("--focal-length", type=int, help="焦距")
    parser.add_argument("--no-random", action="store_true", help="不随机化")
    parser.add_argument("--date", help="拍摄时间 (YYYY:MM:DD HH:MM:SS)")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--input-dir", help="输入目录 (批量模式)")

    args = parser.parse_args()

    skill = ExifInjector()

    if args.batch:
        if not args.input_dir:
            print("❌ 批量模式需要 --input-dir")
            exit(1)
        result = skill.batch_process(
            args.input_dir,
            args.output,
            camera=args.camera,
            style=args.style,
            iso=args.iso,
            fnumber=args.fnumber,
            focal_length=args.focal_length,
            date_time=args.date,
            randomize=not args.no_random
        )
    else:
        if not args.input:
            print("❌ 需要 --input")
            exit(1)
        result = skill.inject_exif(
            args.input,
            args.output,
            camera=args.camera,
            style=args.style,
            iso=args.iso,
            fnumber=args.fnumber,
            focal_length=args.focal_length,
            date_time=args.date,
            randomize=not args.no_random
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))