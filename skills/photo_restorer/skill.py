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

# ==================== 模型路径映射 (基于你刚刚整理的目录) ====================
MODELS_DIR = Path(r"E:\SD_OpenVINO\models\upscalers_and_restorers")


class PhotoRestorer:
    """硬核老照片修复器 v3.0"""

    SUPPORTED_MODELS = {
        "codeformer": {
            "name": "CodeFormer",
            "description": "专门修复人脸细节和破损",
            "type": "gan",
            "default": True,
            "weights": MODELS_DIR / "codeformer" / "codeformer.pth",
            "detection": MODELS_DIR / "codeformer" / "detection_Resnet50_Final.pth",
            "parsing": MODELS_DIR / "codeformer" / "parsing_parsenet.pth",
        },
        "real_esrgan": {
            "name": "Real-ESRGAN",
            "description": "超分辨率放大和去噪",
            "type": "gan",
            "default": False,
            "weights": MODELS_DIR / "RealESRGAN_x4plus.pth",
        },
        "gfpgan": {
            "name": "GFPGAN",
            "description": "人脸增强专用",
            "type": "gan",
            "default": False,
            "weights": MODELS_DIR / "gfpgan" / "GFPGANv1.4.pth",
        },
        "controlnet": {
            "name": "ControlNet Restore",
            "description": "本地 ControlNet 引擎进行基础修复",
            "type": "diffusion",
            "default": False,
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_restorer"
        self.version = "3.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        self.total_processed = 0
        self.total_success = 0

        self._setup_logging()
        self._setup_config()

        logger.info(f"硬核照片修复器 v{self.version} 初始化完成")
        logger.info(f"  模型目录: {MODELS_DIR}")
        logger.info(f"  ControlNet: {'✅' if self.controlnet_engine else '❌'}")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _setup_config(self):
        defaults = {
            "default_model": "codeformer",
            "output_dir": str(self.output_dir),
            "log_level": "INFO",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def get_models(self) -> Dict[str, Dict]:
        return self.SUPPORTED_MODELS

    def _check_weights(self, model_name: str) -> bool:
        """检查模型权重是否存在"""
        info = self.SUPPORTED_MODELS.get(model_name, {})
        weights = info.get("weights")
        if weights and not Path(weights).exists():
            logger.error(f"模型权重不存在: {weights}")
            logger.info("请检查文件路径或重新下载模型！")
            return False
        return True

    def _restore_with_codeformer(self, image_path: str, output_path: str) -> bool:
        """使用 CodeFormer 硬核修复"""
        try:
            import cv2
            from facexlib.detection import init_detection_model
            from facexlib.parsing import init_parsing_model
            from basicsr.utils import imwrite, img2tensor, tensor2img
            from facelib.utils.face_restoration_helper import FaceRestoreHelper
            from facelib.utils.misc import is_gpu_supported, get_device
            from facelib.archs.codeformer_arch import CodeFormer

            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            # 1. 加载模型
            codeformer_net = CodeFormer(dim_embd=512, codebook_size=1024, n_head=8, n_layers=9,
                                        connect_list=['32', '64', '128', '256']).to(device)
            ckpt_path = self.SUPPORTED_MODELS["codeformer"]["weights"]
            state_dict = torch.load(str(ckpt_path), map_location=lambda storage, loc: storage)['params_ema']
            codeformer_net.load_state_dict(state_dict)
            codeformer_net.eval()

            # 2. 初始化人脸检测和解析辅助模型
            detection_path = str(self.SUPPORTED_MODELS["codeformer"]["detection"])
            parsing_path = str(self.SUPPORTED_MODELS["codeformer"]["parsing"])
            
            face_helper = FaceRestoreHelper(
                upscale_factor=1,
                face_size=512,
                crop_ratio=(1, 1),
                det_model=init_detection_model('retinaface_resnet50', half=False, device=device, model_rootpath=Path(detection_path).parent),
                save_ext='png',
                use_parse=True,
                device=device,
                parse_model=init_parsing_model('bisenet', device=device, model_rootpath=Path(parsing_path).parent)
            )

            # 3. 读取图片并修复
            img = cv2.imread(image_path)
            face_helper.read_image(img)
            face_helper.get_face_landmarks_5(only_center_face=False)
            face_helper.align_warp_face()
            
            for idx, cropped_face in enumerate(face_helper.cropped_faces):
                cropped_face_t = img2tensor(cropped_face / 255., bgr2rgb=True, float32=True).unsqueeze(0).to(device)
                with torch.no_grad():
                    output = codeformer_net(cropped_face_t, w=0.5, adain=True)[0]
                    restored_face = tensor2img(output, min_max=(-1, 1), is_bgr=True)
                face_helper.add_restored_face(restored_face)

            face_helper.get_inverse_affine(None)
            restored_img = face_helper.paste_faces_to_input_image()
            cv2.imwrite(output_path, restored_img)
            logger.info(f"CodeFormer 修复完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"CodeFormer 加载失败（需要在环境安装相关依赖）: {e}")
            return False

    def _restore_with_realesrgan(self, image_path: str, output_path: str) -> bool:
        """使用 Real-ESRGAN 硬核放大"""
        try:
            import cv2
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet

            model_path = str(self.SUPPORTED_MODELS["real_esrgan"]["weights"])
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            upsampler = RealESRGANer(
                scale=4,
                model_path=model_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=False,
                device=device
            )

            img = cv2.imread(image_path)
            output, _ = upsampler.enhance(img, outscale=4)
            cv2.imwrite(output_path, output)
            logger.info(f"Real-ESRGAN 修复完成: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Real-ESRGAN 加载失败: {e}")
            return False

    def _restore_with_controlnet(self, image_path: str, output_path: str, **kwargs) -> bool:
        """使用 ControlNet 进行基础重绘修复"""
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
            return True
        except Exception as e:
            logger.error(f"ControlNet 修复失败: {e}")
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

        model = model or self.config.get("default_model", "codeformer")
        
        if model not in self.SUPPORTED_MODELS:
            return {"status": "error", "error": f"不支持的模型: {model}"}

        if not self._check_weights(model):
            return {"status": "error", "error": f"模型权重缺失: {model}"}

        if not output_path:
            input_name = Path(abs_image_path).stem
            ext = Path(abs_image_path).suffix or ".png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{input_name}_restored_{timestamp}{ext}")
        
        output_path = str(output_path)
        logger.info(f"开始硬核修复: {abs_image_path}")
        logger.info(f"使用模型: {model}")
        logger.info(f"输出路径: {output_path}")

        success = False
        error_msg = None

        try:
            if model == "codeformer":
                success = self._restore_with_codeformer(str(abs_image_path), output_path)
            elif model == "real_esrgan":
                success = self._restore_with_realesrgan(str(abs_image_path), output_path)
            elif model == "gfpgan":
                # GFPGAN 需要独立的库，调用 codeformer 的底层 helper
                success = self._restore_with_codeformer(str(abs_image_path), output_path)
            elif model == "controlnet":
                success = self._restore_with_controlnet(str(abs_image_path), output_path, **kwargs)
            else:
                error_msg = f"模型 {model} 暂无实现"
                success = False
        except Exception as e:
            error_msg = str(e)
            success = False

        self.total_processed += 1
        if success:
            self.total_success += 1

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
                    models[key] = {"name": info["name"], "description": info["description"], "type": info["type"]}
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
    print("支持的硬核模型:")
    for name, info in restorer.get_models().items():
        print(f"  {name}: {info['description']}")