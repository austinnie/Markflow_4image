# markflow/skills/remove_clothes/skill.py
"""
衣服移除 Skill - 使用本地 SD Inpaint 模型
支持多种分割方案: YOLO, Manual, CLIPSeg, SAM, Grounding DINO
ControlNet 和 Inpaint 分离执行
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)

# ==================== 依赖导入 ====================
try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"依赖未安装: {e}")

# ControlNet 技能
try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_SKILL_AVAILABLE = True
    logger.info("ControlNet 技能加载成功")
except ImportError as e:
    CONTROLNET_SKILL_AVAILABLE = False
    logger.warning(f"ControlNet 技能不可用: {e}")

# ==================== 分割模块 ====================
from .segmentation import (
    segment_with_yolo,
    segment_manual,
    segment_with_clipseg,
    segment_with_sam,
    segment_with_grounding_dino,
)

# YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装，将使用手动遮罩")


# ==================== 技能类 ====================
class ClothesRemover:
    """
    衣服移除技能 - 使用本地 SD Inpaint 模型
    ControlNet 和 Inpaint 分离执行
    """

    # 支持的图片格式
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    # 支持的分割方法
    SEGMENTATION_METHODS = ['yolo', 'manual', 'clipseg', 'sam', 'grounding_dino']

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化技能

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.name = "remove_clothes"
        self.version = "1.0.0"

        # 目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent

        # 模型配置
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))

        # 设备
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # 尺寸配置
        self.auto_resize = self.config.get('auto_resize', True)
        self.min_size = self.config.get('min_size', 512)
        self.max_size = self.config.get('max_size', 1024)

        # 分割方法配置
        self.default_seg_method = self.config.get('default_seg_method', 'yolo')

        # 运行时状态
        self.pipeline = None
        self.current_model = None
        self._yolo_model = None

        # ============ ControlNet 技能（独立于 Inpaint Pipeline） ============
        self.controlnet_skill = None
        if self.config.get('use_controlnet', True) and CONTROLNET_SKILL_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={'device': self.device, 'max_size': 512})
                logger.info("  ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"  ControlNet 技能初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ClothesRemover 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  ControlNet 技能: {'✅ 可用' if self.controlnet_skill else '❌ 不可用'}")
        logger.info(f"  YOLO: {'✅ 可用' if YOLO_AVAILABLE else '❌ 不可用'}")
        logger.info(f"  默认分割: {self.default_seg_method}")

    # ==================== 初始化方法 ====================

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.skill_dir / 'output'),
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.5,
            'use_controlnet': True,
            'default_controlnet_type': 'canny',
            'default_seg_method': 'yolo',
            'default_prompt': 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic',
            'default_negative': 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config['output_dir']).mkdir(parents=True, exist_ok=True)

    # ==================== 模型管理 ====================

    def _find_model(self, model_name: str) -> Optional[Path]:
        """查找模型文件"""
        if not model_name:
            model_name = self.config.get('default_model', 'zenityXmix.inpainting.safetensors')

        logger.info(f"查找模型: '{model_name}'")
        logger.info(f"模型目录: {self.models_dir}")

        direct_path = self.models_dir / model_name
        if direct_path.exists():
            logger.info(f"  找到: {direct_path}")
            return direct_path

        filename = os.path.basename(model_name)

        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                logger.info(f"  找到: {sub_path}")
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    logger.info(f"  找到: {file_path}")
                    return file_path

        logger.error(f"未找到模型: '{model_name}'")
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        """
        加载纯 Inpaint Pipeline（不加载 ControlNet）
        ControlNet 通过 control_image 参数传入
        """
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
            logger.info(f"  模型加载成功: {self.current_model}")
            return True

        except Exception as e:
            logger.error(f"  模型加载失败: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        """加载模型（通过名称）"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False

        logger.info(f"加载模型: {model_path}")
        return self._load_pipeline(model_path)

    def _load_model_from_path(self, model_path: str) -> bool:
        """加载模型（通过路径）"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        if not os.path.exists(model_path):
            logger.error(f"模型不存在: {model_path}")
            return False

        logger.info(f"从路径加载模型: {model_path}")
        return self._load_pipeline(Path(model_path))

    # ==================== 遮罩生成（使用分割模块） ====================

    def _generate_mask(self, image: Image.Image, method: str = None, **kwargs) -> Image.Image:
        """
        生成衣服遮罩，支持多种分割方案
        """
        method = method or self.default_seg_method
        logger.info(f"  使用分割方法: {method}")

        if method == 'yolo':
            mask = segment_with_yolo(image)
            if mask is not None:
                return mask
            logger.info("  YOLO 失败，降级到手动绘制")
            return segment_manual(image)

        elif method == 'manual':
            return segment_manual(image)

        elif method == 'clipseg':
            text = kwargs.get('text', 'clothes, dress, shirt')
            mask = segment_with_clipseg(image, text=text)
            if mask is not None:
                return mask
            logger.info("  CLIPSeg 失败，降级到 YOLO")
            return self._generate_mask(image, method='yolo')

        elif method == 'sam':
            points = kwargs.get('points')
            if points is None:
                from .segmentation.sam import get_points_from_click
                result = get_points_from_click(image)
                if result is None:
                    logger.info("  SAM 未获取到点，降级到 YOLO")
                    return self._generate_mask(image, method='yolo')
                points, labels = result
            else:
                labels = [1] * len(points)
            mask = segment_with_sam(image, points, labels)
            if mask is not None:
                return mask
            logger.info("  SAM 失败，降级到 YOLO")
            return self._generate_mask(image, method='yolo')

        elif method == 'grounding_dino':
            text = kwargs.get('text', 'clothes')
            mask = segment_with_grounding_dino(image, text=text)
            if mask is not None:
                return mask
            logger.info("  Grounding DINO 失败，降级到 YOLO")
            return self._generate_mask(image, method='yolo')

        else:
            logger.warning(f"  未知分割方法: {method}，使用 YOLO")
            return self._generate_mask(image, method='yolo')

    # ==================== ControlNet 集成（分离执行） ====================

    def _generate_pose_image(self, image: Image.Image, controlnet_type: str = "canny") -> Optional[Image.Image]:
        """
        使用 ControlNet 技能生成姿态图（独立于 Inpaint Pipeline）
        """
        if self.controlnet_skill is None:
            return None

        try:
            logger.info(f"  调用 ControlNet 技能 ({controlnet_type})...")
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type=controlnet_type,
                output_path=None
            )

            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    pose_image = Image.open(output_path)
                    logger.info(f"  姿态图生成完成: {output_path}")
                    return pose_image
                else:
                    logger.warning(f"  姿态图文件不存在: {output_path}")
                    return None
            else:
                logger.warning(f"  ControlNet 检测失败: {result.get('error', '未知错误')}")
                return None

        except Exception as e:
            logger.warning(f"  姿态图生成失败: {e}")
            return None

    # ==================== 图片预处理 ====================

    def _resize_image(self, image: Image.Image) -> tuple:
        """等比例缩放图片到合适尺寸"""
        if not self.auto_resize:
            return image, image.size

        original_size = image.size

        need_resize = False
        new_size = original_size

        if min(original_size) < self.min_size:
            ratio = self.min_size / min(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True
        elif max(original_size) > self.max_size:
            ratio = self.max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True

        if need_resize:
            logger.info(f"  等比例缩放: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            original_size = new_size

        # 确保是 8 的倍数（SD 要求）
        width = (original_size[0] // 8) * 8
        height = (original_size[1] // 8) * 8

        if width != original_size[0] or height != original_size[1]:
            new_image = Image.new("RGB", (width, height), (0, 0, 0))
            x_offset = (width - original_size[0]) // 2
            y_offset = (height - original_size[1]) // 2
            new_image.paste(image, (x_offset, y_offset))
            image = new_image
            logger.info(f"  填充对齐: {original_size[0]}x{original_size[1]} -> {width}x{height}")
            original_size = (width, height)

        return image, original_size

    # ==================== 批量处理 ====================

    def batch_process(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """批量处理目录下的所有图片"""
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"目录不存在: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "nude_output"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        images = []
        for ext in self.SUPPORTED_EXTENSIONS:
            images.extend(input_path.glob(f"*{ext}"))
            images.extend(input_path.glob(f"*{ext.upper()}"))

        if not images:
            return {"status": "error", "error": f"未找到图片: {input_dir}"}

        logger.info(f"📁 找到 {len(images)} 个图片")
        logger.info(f"📂 输出目录: {output_dir}")

        results = []
        success_count = 0
        failed_count = 0

        for i, img_path in enumerate(images, 1):
            logger.info(f"\n[{i}/{len(images)}] {img_path.name}")
            output_file = output_path / img_path.name

            try:
                result = self.execute(
                    image_path=str(img_path),
                    output_path=str(output_file),
                    **kwargs
                )
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                results.append(result)
            except Exception as e:
                failed_count += 1
                results.append({"status": "error", "error": str(e), "image": str(img_path)})

        return {
            "status": "success" if success_count > 0 else "error",
            "total": len(images),
            "success": success_count,
            "failed": failed_count,
            "results": results,
            "output_dir": str(output_path)
        }

    # ==================== 主执行方法 ====================

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行衣服移除

        ControlNet 和 Inpaint 分离执行：
        1. ControlNet 技能生成姿态图
        2. Inpaint Pipeline 使用姿态图作为 control_image 参考
        """
        logger.info(f"execute 收到参数: {kwargs}")
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path')
            if not image_path:
                error_msg = "❌ image_path 是必填参数"
                print(error_msg)
                return {"status": "error", "error": error_msg}

            if not os.path.exists(image_path):
                error_msg = f"❌ 图片不存在: {image_path}"
                print(error_msg)
                logger.error(error_msg)
                return {"status": "error", "error": error_msg}

            output_path = kwargs.get('output_path')
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            seg_method = kwargs.get('seg_method', self.default_seg_method)
            seg_text = kwargs.get('seg_text', 'clothes')
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'canny'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            # 2. 加载模型（纯 Inpaint Pipeline，不加载 ControlNet）
            if model_path:
                if not self._load_model_from_path(model_path):
                    error_msg = f"❌ 无法加载模型: {model_path}"
                    print(error_msg)
                    return {"status": "error", "error": error_msg}
            else:
                model_name = model_name or self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 3. 获取生成参数
            prompt = kwargs.get('prompt')
            if prompt is None:
                prompt = self.config.get('default_prompt')

            negative_prompt = kwargs.get('negative_prompt')
            if negative_prompt is None:
                negative_prompt = self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir'))
            save_mask = kwargs.get('save_mask', False)

            # 4. 加载并缩放图片
            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"处理: {os.path.basename(image_path)} ({image.size[0]}x{image.size[1]})")

            # 5. 生成遮罩
            logger.info("生成遮罩...")
            mask = self._generate_mask(image, method=seg_method, text=seg_text)

            if save_mask:
                mask_path = image_path.replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)
                logger.info(f"  遮罩: {os.path.basename(mask_path)}")

            # ============ 6. ControlNet 生成姿态图（独立执行） ============
            control_image = None
            if use_controlnet and self.controlnet_skill is not None:
                logger.info(f"生成姿态图 (controlnet_type={controlnet_type})...")
                control_image = self._generate_pose_image(image, controlnet_type)
                if control_image is not None:
                    logger.info("  ✅ 姿态图生成完成")
                else:
                    logger.info("  ⚠️ 姿态图生成失败，继续使用普通 Inpaint")

            # 7. 设置随机种子
            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            logger.info("SD Inpaint 生成中...")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  步数: {steps}")
            logger.info(f"  强度: {strength}")
            logger.info(f"  种子: {seed}")
            if control_image is not None:
                logger.info("  ControlNet: 姿态图已传入 (分离模式)")

            # ============ 8. 执行 Inpaint（使用 control_image 参数） ============
            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': mask,
                'strength': strength,
                'num_inference_steps': steps,
                'guidance_scale': 7.5,
                'generator': generator,
                'width': current_size[0],
                'height': current_size[1],
            }

            # 将 ControlNet 姿态图作为 control_image 传入
            if control_image is not None:
                pipeline_kwargs['control_image'] = control_image

            result = self.pipeline(**pipeline_kwargs).images[0]

            # 9. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                filename = f"{Path(image_path).stem}_{timestamp}_nude.png"
                output_path = str(output_dir_path / filename)

            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            result.save(output_path)

            generation_time = time.time() - start_time
            logger.info(f"  保存: {os.path.basename(output_path)}")

            return {
                "status": "success",
                "output_path": output_path,
                "parameters": {
                    "image_path": image_path,
                    "model": self.current_model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
                    "seg_method": seg_method,
                    "controlnet": control_image is not None,
                    "controlnet_type": controlnet_type if control_image is not None else None,
                },
                "model_used": self.current_model,
                "generation_time": f"{generation_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<ClothesRemover(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="衣服移除工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径或目录")
    parser.add_argument("--output", "-o", help="输出路径或目录")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--model", "-m", default="zenityXmix.inpainting.safetensors", help="模型名称")
    parser.add_argument("--prompt", "-p", default="nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic", help="生成提示词")
    parser.add_argument("--negative", "-n", default="clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime", help="负面提示词")
    parser.add_argument("--strength", "-s", type=float, default=0.5, help="重绘强度")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    parser.add_argument("--no-controlnet", action="store_true", help="禁用 ControlNet")
    parser.add_argument("--controlnet-type", default="canny",
                        choices=["canny", "openpose", "depth", "hed", "lineart", "normal", "mlsd", "openpose_full"],
                        help="ControlNet 类型")
    # 分割方法参数
    parser.add_argument("--seg-method", default="yolo",
                        choices=["yolo", "manual", "clipseg", "sam", "grounding_dino"],
                        help="分割方法")
    parser.add_argument("--seg-text", default="clothes",
                        help="CLIPSeg/Grounding DINO 的文字提示")

    args = parser.parse_args()

    skill = ClothesRemover(config={
        'device': args.device,
        'use_controlnet': not args.no_controlnet,
        'default_controlnet_type': args.controlnet_type,
        'default_seg_method': args.seg_method,
    })

    if args.batch:
        result = skill.batch_process(
            input_dir=args.input,
            output_dir=args.output,
            model_name=args.model,
            prompt=args.prompt,
            negative_prompt=args.negative,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed,
            save_mask=args.save_mask,
            seg_method=args.seg_method,
            seg_text=args.seg_text,
            controlnet_type=args.controlnet_type,
            use_controlnet=not args.no_controlnet
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = skill.execute(
            image_path=args.input,
            output_path=args.output,
            model_name=args.model,
            prompt=args.prompt,
            negative_prompt=args.negative,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed,
            save_mask=args.save_mask,
            seg_method=args.seg_method,
            seg_text=args.seg_text,
            controlnet_type=args.controlnet_type,
            use_controlnet=not args.no_controlnet
        )

        if result['status'] == 'success':
            print(f"\n✅ 成功!")
            print(f"  📁 输出: {result['output_path']}")
            print(f"  ⏱️  耗时: {result['generation_time']}")
            print(f"  📋 参数:")
            for key, value in result['parameters'].items():
                print(f"    {key}: {value}")
        else:
            print(f"\n❌ 失败: {result.get('error', '未知错误')}")