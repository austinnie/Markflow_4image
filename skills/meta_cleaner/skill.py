# skills/meta_cleaner/skill.py
"""
元数据清理 Skill - 清除图片中的 AI 生成痕迹
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL 未安装")


class MetaCleaner:
    """
    元数据清理技能 - 清除图片中的 AI 生成痕迹
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "meta_cleaner"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self._setup_config()

        logger.info(f"元数据清理器初始化完成")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_method': 'auto',
            'jpg_quality': 92,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def clean_metadata(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        method: str = "auto",
        jpg_quality: int = 92
    ) -> Dict[str, Any]:
        """
        清理图片元数据

        Args:
            image_path: 输入图片路径
            output_path: 输出路径
            method: 清理方法 (png, jpg, auto)
            jpg_quality: JPG 质量

        Returns:
            执行结果
        """
        if not os.path.exists(image_path):
            return {"status": "error", "error": f"图片不存在: {image_path}"}

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{Path(image_path).stem}_clean_{timestamp}.jpg")

        try:
            img = Image.open(image_path).convert("RGB")
            ext = Path(image_path).suffix.lower()

            if method == "png" or (method == "auto" and ext == '.png'):
                # PNG: 重新保存，清除元数据
                out_path = output_path
                if not out_path.endswith('.png'):
                    out_path = out_path.replace('.jpg', '.png')
                img.save(out_path, format='PNG', optimize=True)
                logger.info(f"  PNG 元数据已清除: {out_path}")
                return {"status": "success", "output_path": out_path, "method": "png"}

            else:
                # JPG: 转 JPG，元数据自动丢失
                out_path = output_path
                if not out_path.endswith('.jpg'):
                    out_path = out_path.replace('.png', '.jpg')
                img.save(out_path, format='JPEG', quality=jpg_quality, optimize=True)
                logger.info(f"  已转换为 JPG，元数据已清除: {out_path}")
                return {"status": "success", "output_path": out_path, "method": "jpg"}

        except Exception as e:
            logger.error(f"清理失败: {e}")
            return {"status": "error", "error": str(e)}

    def batch_process(self, input_dir: str, output_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """批量处理"""
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"目录不存在: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "cleaned_output"
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

            result = self.clean_metadata(str(img_path), str(out_file), **kwargs)
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
        action = kwargs.get('action', 'clean')

        if action == 'clean':
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            return self.clean_metadata(
                image_path=image_path,
                output_path=kwargs.get('output_path'),
                method=kwargs.get('method', self.config.get('default_method', 'auto')),
                jpg_quality=kwargs.get('jpg_quality', self.config.get('jpg_quality', 92))
            )

        elif action == 'batch':
            input_dir = kwargs.get('input_dir')
            if not input_dir:
                return {"status": "error", "error": "input_dir 是必填参数"}
            return self.batch_process(input_dir, kwargs.get('output_dir'), **kwargs)

        else:
            return {"status": "error", "error": f"未知操作: {action}"}

    def __repr__(self):
        return f"<MetaCleaner(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse
    import json
    from datetime import datetime

    parser = argparse.ArgumentParser(description="元数据清理工具")
    parser.add_argument("--input", "-i", help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--method", default="auto", choices=["png", "jpg", "auto"], help="清理方法")
    parser.add_argument("--quality", type=int, default=92, help="JPG 质量")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--input-dir", help="输入目录 (批量模式)")

    args = parser.parse_args()

    skill = MetaCleaner()

    if args.batch:
        if not args.input_dir:
            print("❌ 批量模式需要 --input-dir")
            exit(1)
        result = skill.batch_process(args.input_dir, args.output, method=args.method, jpg_quality=args.quality)
    else:
        if not args.input:
            print("❌ 需要 --input")
            exit(1)
        result = skill.clean_metadata(args.input, args.output, method=args.method, jpg_quality=args.quality)

    print(json.dumps(result, ensure_ascii=False, indent=2))