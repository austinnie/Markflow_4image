"""
photo_restorer - 老照片修复工具

使用AI技术修复、上色、增强老照片
功能:
  - 照片修复（去噪、去划痕）
  - 超分辨率（放大）
  - 智能上色
  - 人脸修复
  - 多模型支持
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# 在文件最开头添加
import sys
import torchvision.transforms.functional as F

# 兼容性修复：如果 basicsr 尝试导入 functional_tensor
try:
    from torchvision.transforms import functional_tensor
except ImportError:
    # 创建别名
    import torchvision.transforms.functional as functional_tensor
    sys.modules['torchvision.transforms.functional_tensor'] = functional_tensor

class PhotoRestorer:
    """
    老照片修复器
    支持多种AI模型进行照片修复和增强
    """
    
    # 支持的修复模型
    SUPPORTED_MODELS = {
        "real_esrgan": {
            "name": "Real-ESRGAN",
            "description": "通用图像增强与超分辨率，适合去噪、去模糊、提升清晰度",
            "type": "gan",
            "default": True,
            "pipeline": "https://github.com/xinntao/Real-ESRGAN"
        },
        "gfpgan": {
            "name": "GFPGAN",
            "description": "专注于人脸修复，能有效重建面部细节",
            "type": "gan",
            "pipeline": "https://github.com/TencentARC/GFPGAN"
        },
        "ssdiff": {
            "name": "SSDiff",
            "description": "基于扩散模型，擅长处理严重破损和上色",
            "type": "diffusion",
            "pipeline": "https://github.com/saic-mdal/SSDiff"
        },
        "dcal_gan": {
            "name": "DCAF-GAN",
            "description": "注重细节与全局结构的平衡，适合风景或复杂场景照片",
            "type": "gan",
            "pipeline": "https://github.com/rosinaker/DCAF-GAN"
        },
        "deoldify": {
            "name": "DeOldify",
            "description": "专为黑白照片上色设计",
            "type": "diffusion",
            "pipeline": "https://github.com/jantic/DeOldify"
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_restorer"
        self.version = "1.0.0"
        
        # 获取技能所在目录
        self.skill_dir = Path(__file__).parent.absolute()
        
        # 项目根目录: skills/photo_restorer/ -> skills/ -> MarkFlow/ -> SD_OpenVINO/
        self.project_root = self.skill_dir.parent.parent.parent
        
        self._setup_logging()
        self._setup_config()
        
        # 处理统计
        self.total_processed = 0
        self.total_success = 0
        
        logger.info(f"照片修复器 初始化完成 (v{self.version})")
        logger.info(f"技能目录: {self.skill_dir}")
        logger.info(f"项目根目录: {self.project_root}")
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        """设置配置"""
        defaults = {
            # 模型配置
            "default_model": "real_esrgan",
            "model_weights_dir": str(self.project_root / "models"),  # 相对路径
            
            # 修复参数
            "scale": 2,  # 放大倍数: 2 或 4
            "denoise": True,
            "face_enhance": False,  # 是否启用面部增强
            
            # 输出配置
            "output_dir": str(self.skill_dir / "output"),
            "save_log": True,
            
            # 性能配置
            "gpu": True,
            "tile_size": 0,  # 分块大小，0为不分块
            
            # 日志配置
            "log_level": "INFO",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        # 创建输出目录
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def get_models(self) -> Dict[str, Dict]:
        """获取所有支持的模型"""
        return self.SUPPORTED_MODELS
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """获取模型信息"""
        return self.SUPPORTED_MODELS.get(model_name)
    
    def _check_dependencies(self) -> bool:
        """检查依赖是否安装"""
        try:
            import torch
            import cv2
            return True
        except ImportError as e:
            logger.error(f"依赖缺失: {e}")
            return False
    
    def _get_model_weights_path(self, model_name: str) -> Path:
        """
        获取模型权重路径
        优先从 models.json 读取，否则使用默认路径
        """
        models_dir = Path(self.config.get("model_weights_dir", "./models"))
        models_config_path = models_dir / "models.json"
        
        # 模型文件名映射
        weight_files = {
            "real_esrgan": "RealESRGAN_x4plus.pth",
            "gfpgan": "GFPGANv1.4.pth",  # 默认使用 v1.4
            "ssdiff": "ssdiff_v1.pth",
            "dcal_gan": "dcal_gan_v1.pth",
            "deoldify": "deoldify_v1.pth"
        }
        
        # 优先从 models.json 读取
        if models_config_path.exists():
            try:
                with open(models_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 查找匹配的模型
                for key, model_info in config.get("models", {}).items():
                    # 匹配模型名称
                    if model_name in key.lower() or key.lower() in model_name:
                        return Path(model_info["path"])
            except Exception as e:
                logger.warning(f"读取 models.json 失败: {e}")
        
        # 回退到默认路径
        filename = weight_files.get(model_name, f"{model_name}.pth")
        return models_dir / filename

    def _restore_with_real_esrgan(self, image_path: str, output_path: str, **kwargs) -> bool:
        """
        使用 Real-ESRGAN 修复
        """
        try:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            import cv2
            import torch
            
            model_path = self._get_model_weights_path("real_esrgan")
            if not model_path.exists():
                logger.error(f"模型权重文件不存在: {model_path}")
                logger.info("请运行 download_models.py 下载模型")
                return False
            
            scale = kwargs.get("scale", self.config["scale"])
            denoise = kwargs.get("denoise", self.config["denoise"])
            
            # 设置设备
            device = torch.device('cuda' if self.config.get("gpu", True) and torch.cuda.is_available() else 'cpu')
            
            # 创建模型 - 使用 4x 放大（RealESRGAN_x4plus 固定 4x）
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, 
                           num_block=23, num_grow_ch=32, scale=4)
            
            # 创建 upsampler
            upsampler = RealESRGANer(
                scale=4,  # 模型是 4x 的
                model_path=str(model_path),
                model=model,
                tile=kwargs.get("tile_size", self.config.get("tile_size", 0)),
                tile_pad=10,
                pre_pad=0,
                half=False,  # CPU 模式
                device=device
            )
            
            # 读取图像
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                logger.error(f"无法读取图像: {image_path}")
                return False
            
            # 去噪
            if denoise:
                img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
            
            # 超分辨率
            output, _ = upsampler.enhance(img, outscale=scale)
            
            # 保存结果
            cv2.imwrite(output_path, output)
            
            logger.info(f"Real-ESRGAN 修复完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Real-ESRGAN 修复失败: {e}")
            return False
        
    def _restore_with_gfpgan(self, image_path: str, output_path: str, **kwargs) -> bool:
        """
        使用 GFPGAN 修复人脸
        """
        try:
            import torch
            from gfpgan import GFPGANer
            
            model_path = self._get_model_weights_path("gfpgan")
            if not model_path.exists():
                logger.error(f"模型权重文件不存在: {model_path}")
                logger.info("请运行 download_models.py 下载模型")
                return False
            
            restorer = GFPGANer(
                model_path=str(model_path),
                upscale=kwargs.get("scale", self.config["scale"]),
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=None,
                device='cuda' if self.config.get("gpu", True) and torch.cuda.is_available() else 'cpu'
            )
            
            import cv2
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                logger.error(f"无法读取图像: {image_path}")
                return False
            
            _, _, output = restorer.enhance(
                img,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
                weight=0.5
            )
            
            cv2.imwrite(output_path, output)
            logger.info(f"GFPGAN 修复完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"GFPGAN 修复失败: {e}")
            return False
    
    def _restore_with_ssdiff(self, image_path: str, output_path: str, **kwargs) -> bool:
        """
        使用 SSDiff 扩散模型修复
        """
        try:
            from diffusers import StableDiffusionInpaintPipeline
            import torch
            import PIL.Image as Image
            
            pipe = StableDiffusionInpaintPipeline.from_pretrained(
                "stabilityai/stable-diffusion-2-inpainting",
                torch_dtype=torch.float16 if self.config.get("gpu", True) else torch.float32
            )
            
            if self.config.get("gpu", True):
                pipe = pipe.to("cuda")
            
            image = Image.open(image_path).convert("RGB")
            prompt = "high quality, detailed, restored old photo"
            
            result = pipe(
                prompt=prompt,
                image=image,
                mask_image=None,
                height=image.height,
                width=image.width,
                num_inference_steps=20,
            ).images[0]
            
            result.save(output_path)
            logger.info(f"SSDiff 修复完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"SSDiff 修复失败: {e}")
            return False
    
    def restore_image(self, image_path: str, model: str = None, 
                     output_path: str = None, **kwargs) -> Dict[str, Any]:
        """修复单张图片"""
        start_time = time.time()
        
        if not os.path.exists(image_path):
            return {"status": "error", "error": f"图片不存在: {image_path}"}
        
        model = model or self.config.get("default_model", "real_esrgan")
        if model not in self.SUPPORTED_MODELS:
            return {"status": "error", "error": f"不支持的模型: {model}"}
        
        if not output_path:
            input_name = Path(image_path).stem
            ext = Path(image_path).suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(self.config["output_dir"]) / f"{input_name}_restored_{timestamp}{ext}"
        
        output_path = str(output_path)
        
        logger.info(f"开始修复: {image_path}")
        logger.info(f"使用模型: {model}")
        logger.info(f"输出路径: {output_path}")
        
        if not self._check_dependencies():
            return {
                "status": "error",
                "error": "依赖缺失，请安装 opencv-python, torch, basicsr, gfpgan",
                "timestamp": datetime.now().isoformat()
            }
        
        success = False
        error_msg = None
        
        try:
            if model == "real_esrgan":
                success = self._restore_with_real_esrgan(image_path, output_path, **kwargs)
            elif model == "gfpgan":
                success = self._restore_with_gfpgan(image_path, output_path, **kwargs)
            elif model == "ssdiff":
                success = self._restore_with_ssdiff(image_path, output_path, **kwargs)
            else:
                error_msg = f"模型 {model} 的具体实现待添加"
                success = False
        except Exception as e:
            error_msg = str(e)
            success = False
        
        self.total_processed += 1
        if success:
            self.total_success += 1
        
        processing_time = time.time() - start_time
        
        result = {
            "status": "success" if success else "error",
            "action": "restore",
            "model_used": model,
            "input_path": image_path,
            "output_path": output_path if success else None,
            "processing_time": round(processing_time, 2),
            "total_processed": self.total_processed,
            "total_success": self.total_success,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_msg:
            result["error"] = error_msg
        
        logger.info(f"修复完成: {'成功' if success else '失败'}, 耗时 {processing_time:.2f}s")
        return result
    
    def batch_restore(self, image_paths: List[str], model: str = None, **kwargs) -> Dict[str, Any]:
        """批量修复"""
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths, 1):
            logger.info(f"处理第 {i}/{total} 张: {path}")
            result = self.restore_image(path, model, **kwargs)
            results.append(result)
        
        return {
            "status": "success",
            "action": "batch_restore",
            "total": total,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行修复任务"""
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            action = kwargs.get("action", "restore")
            
            # 列出模型
            if action == "list_models":
                models = {}
                for key, info in self.SUPPORTED_MODELS.items():
                    models[key] = {
                        "name": info["name"],
                        "description": info["description"],
                        "type": info["type"],
                        "default": info.get("default", False)
                    }
                
                print("\n" + "="*60)
                print("🤖 支持的修复模型")
                print("="*60)
                for key, info in models.items():
                    default_mark = "⭐" if info.get("default") else "  "
                    print(f"  {default_mark} {key}")
                    print(f"     📝 {info['description']}")
                    print(f"     🏷️ 类型: {info['type']}\n")
                print("="*60 + "\n")
                
                return {
                    "status": "success",
                    "action": "list_models",
                    "models": models,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 状态查询
            if action == "status":
                return {
                    "status": "success",
                    "action": "status",
                    "statistics": {
                        "total_processed": self.total_processed,
                        "total_success": self.total_success,
                        "success_rate": round(self.total_success / self.total_processed * 100, 1) 
                                       if self.total_processed > 0 else 0
                    },
                    "config": self.config,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 批量修复
            if action == "batch_restore":
                image_paths = kwargs.get("image_paths", [])
                if not image_paths:
                    return {"status": "error", "error": "请提供 image_paths 列表"}
                model = kwargs.get("model")
                return self.batch_restore(image_paths, model, **kwargs)
            
            # 单张修复 (默认)
            if action == "restore":
                image_path = kwargs.get("image_path")
                if not image_path:
                    return {"status": "error", "error": "请提供 image_path 参数"}
                
                model = kwargs.get("model")
                output_path = kwargs.get("output_path")
                
                restore_kwargs = {
                    "scale": kwargs.get("scale", self.config["scale"]),
                    "denoise": kwargs.get("denoise", self.config["denoise"]),
                    "face_enhance": kwargs.get("face_enhance", self.config.get("face_enhance", False)),
                    "tile_size": kwargs.get("tile_size", self.config.get("tile_size", 0))
                }
                
                return self.restore_image(image_path, model, output_path, **restore_kwargs)

            # 上色
            if action == "colorize":
                image_path = kwargs.get("image_path")
                if not image_path:
                    return {"status": "error", "error": "请提供 image_path 参数"}
                return self.restore_image(image_path, "deoldify", **kwargs)
    
            return {
                "status": "error",
                "error": f"未知操作: {action}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<PhotoRestorer(name={self.name}, version={self.version})>"


# 便捷函数
def restore_photo(image_path: str, model: str = None, **kwargs):
    """快速修复照片"""
    restorer = PhotoRestorer()
    return restorer.restore_image(image_path, model, **kwargs)


if __name__ == "__main__":
    restorer = PhotoRestorer()
    print("支持的模型:")
    for name, info in restorer.get_models().items():
        print(f"  {name}: {info['description']}")