# skills/photo_restorer/skill.py
"""
photo_restorer - 老照片修复工具

使用AI技术修复、上色、增强老照片
功能:
  - 照片修复（去噪、去划痕）
  - 超分辨率（放大）
  - 智能上色
  - 人脸修复
  - 多模型支持

注意：主打的硬核修复模型（CodeFormer/GFPGAN/RealESRGAN）路径已归档于:
E:/SD_OpenVINO/models/upscalers_and_restorers/
纯CPU环境下，ControlNet 引擎作为稳定备用方案。
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# 添加项目路径
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

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

# ==================== 模型路径映射 (基于你刚刚整理的目录) ====================
MODELS_DIR = Path(r"E:\SD_OpenVINO\models\upscalers_and_restorers")


class PhotoRestorer:
    """老照片修复器 v4.0 (基础版)"""
    SUPPORTED_MODELS = {
        "controlnet": {
            "name": "ControlNet Restore",
            "description": "使用本地 ControlNet 引擎进行稳定修复",
            "type": "diffusion",
            "default": True,
        },
        "codeformer": {
            "name": "CodeFormer",
            "description": "人脸修复 (需 Python 3.10+ 且安装完满依赖)",
            "type": "gan",
            "default": False,
            "weights": MODELS_DIR / "codeformer" / "codeformer.pth",
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_restorer"
        self.version = "4.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"照片修复器 v{self.version} 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _setup_config(self):
        defaults = {
            "default_model": "controlnet",
            "output_dir": str(self.output_dir),
            "log_level": "INFO",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def get_models(self) -> Dict[str, Dict]:
        return self.SUPPORTED_MODELS

    def _restore_with_controlnet(self, image_path: str, output_path: str, **kwargs) -> bool:
        """使用 ControlNet 进行基础重绘修复 (稳定方案)"""
        if self.controlnet_engine is None:
            logger.error("底层 ControlNet 引擎不可用")
            return False

        try:
            result = self.controlnet_engine.execute(
                input_image_path=image_path,
                prompt="high quality, detailed, restored old photo, masterpiece, best quality",
                negative_prompt="low quality, blurry, damaged, torn, noise, ugly, deformed",
                preprocessor_type="HED",
                controlnet_model="lineart",
                strength=0.45,
                output_path=output_path
            )
            if result['status'] != 'success':
                logger.error(f"ControlNet 引擎调用失败: {result.get('error')}")
                return False
            logger.info(f"ControlNet 修复完成: {output_path}")
            return True
        except Exception as e:
            logger.error(f"ControlNet 修复失败: {e}")
            return False

    def _restore_with_codeformer(self, image_path: str, output_path: str) -> bool:
        """使用 CodeFormer 硬核修复 (需要完整依赖)"""
        try:
            # 防呆检查：如果没有完整的库，直接失败返回
            try:
                import facexlib
                import gfpgan
            except ImportError:
                logger.error("缺少硬核依赖库，当前环境无法运行 CodeFormer。")
                return False

            import cv2
            from basicsr.utils import imwrite, img2tensor, tensor2img
            # ... (此处实际代码较复杂，由于当前 Python 环境无法运行 basicsr，这里作为预留接口)
            # 实际运行会走上面的 ControlNet
            return False

        except Exception as e:
            logger.error(f"CodeFormer 加载失败: {e}")
            return False

    def restore_image(self, image_path: str, model: str = None,
                      output_path: str = None, **kwargs) -> Dict[str, Any]:
        """修复单张图片"""
        start_time = time.time()
        if not image_path:
            return {"status": "error", "error": "image_path 是必填参数"}
        abs_image_path = Path(image_path).absolute()
        if not os.path.exists(abs_image_path):
            return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

        model = model or self.config.get("default_model", "controlnet")

        if not output_path:
            input_name = Path(abs_image_path).stem
            ext = Path(abs_image_path).suffix or ".png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{input_name}_restored_{timestamp}{ext}")

        logger.info(f"开始修复: {abs_image_path}")
        logger.info(f"使用模型: {model}")

        success = False
        error_msg = None

        try:
            if model == "controlnet":
                success = self._restore_with_controlnet(str(abs_image_path), output_path, **kwargs)
            elif model == "codeformer":
                success = self._restore_with_codeformer(str(abs_image_path), output_path)
            else:
                error_msg = f"模型 {model} 暂无实现"
                success = False
        except Exception as e:
            error_msg = str(e)
            success = False

        result = {
            "status": "success" if success else "error",
            "action": "restore",
            "model_used": model,
            "input_path": str(abs_image_path),
            "output_path": output_path if success else None,
            "processing_time": round(time.time() - start_time, 2),
            "timestamp": datetime.now().isoformat()
        }

        if error_msg:
            result["error"] = error_msg
        return result

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"执行技能: {self.name} (v{self.version})")
        try:
            action = kwargs.get("action", "restore")
            if action == "list_models":
                models = {}
                for key, info in self.SUPPORTED_MODELS.items():
                    models[key] = {"name": info["name"], "description": info["description"]}
                return {"status": "success", "action": "list_models", "models": models}

            if action == "restore":
                image_path = kwargs.get("image_path")
                if not image_path:
                    return {"status": "error", "error": "请提供 image_path 参数"}
                return self.restore_image(image_path, kwargs.get("model"), kwargs.get("output_path"), **kwargs)

            return {"status": "error", "error": f"未知操作: {action}"}
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<PhotoRestorer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    restorer = PhotoRestorer()
    print("当前可用的修复模型:")
    for name, info in restorer.get_models().items():
        print(f"  {name}: {info['description']}")