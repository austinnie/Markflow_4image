# skills/change_background/skill.py
"""
换背景 Skill - 保持人物不变，替换背景
使用 Depth ControlNet 保持空间结构，Inpaint 重绘背景区域
"""

import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
    logger.warning(f"diffusers 未安装: {e}")

# ControlNet 技能
try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_SKILL_AVAILABLE = True
    logger.info("ControlNet 技能加载成功")
except ImportError as e:
    CONTROLNET_SKILL_AVAILABLE = False
    logger.warning(f"ControlNet 技能不可用: {e}")

# YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装")


class ChangeBackground:
    """
    换背景技能 - 保持人物不变，替换背景
    """

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    # 预设背景提示词
    PRESET_BACKGROUNDS = {
        "beach": "beach, ocean waves, golden sand, sunset, palm trees, tropical paradise",
        "forest": "deep forest, sunlight through trees, green moss, peaceful nature, woodland",
        "mountain": "snowy mountain peaks, alpine meadow, clear blue sky, majestic landscape",
        "city": "modern city skyline, skyscrapers, night lights, urban atmosphere, bustling street",
        "space": "outer space, stars, nebula, galaxy, cosmic, sci-fi background",
        "underwater": "underwater world, coral reef, colorful fish, sun rays through water",
        "sakura": "cherry blossom trees, pink petals, spring, Japanese garden, soft pink",
        "autumn": "autumn forest, golden and red leaves, warm colors, fall season",
        "snow": "snowy landscape, winter wonderland, white snow, pine trees, cozy cabin",
        "desert": "desert dunes, golden sand, warm sunset, vast landscape, arid",
        "library": "old library, bookshelves, warm lighting, academic atmosphere, quiet",
        "cafe": "cozy cafe, warm lighting, coffee, comfortable chairs, urban life",
        "temple": "ancient temple, traditional architecture, serene, spiritual, cultural",
        "sunset": "sunset over the sea, vibrant orange and pink sky, romantic, beautiful",
        "aurora": "northern lights, aurora borealis, starry night, magical, arctic",
        "waterfall": "majestic waterfall, mist, lush green, tropical, powerful nature",
        "castle": "medieval castle, stone walls, historical, fantasy, majestic",
        "cyberpunk": "cyberpunk city, neon lights, rainy street, futuristic, dark",
        "studio": "white studio background, professional photography, clean, minimal",
        "gradient": "smooth gradient background, soft colors, modern, clean aesthetic",
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_background"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 模型配置
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # 尺寸配置
        self.auto_resize = self.config.get('auto_resize', True)
        self.min_size = self.config.get('min_size', 512)
        self.max_size = self.config.get('max_size', 1024)

        # 运行时状态
        self.pipeline = None
        self.current_model = None
        self._yolo_model = None

        # ControlNet 技能
        self.controlnet_skill = None
        if self.config.get('use_controlnet', True) and CONTROLNET_SKILL_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={'device': self.device, 'max_size': 512})
                logger.info("  ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"  ControlNet 技能初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeBackground 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  ControlNet: {'✅ 可用' if self.controlnet_skill else '❌ 不可用'}")
        logger.info(f"  预设背景: {len(self.PRESET_BACKGROUNDS)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.7,
            'use_controlnet': True,
            'default_controlnet_type': 'depth',
            'default_prompt': 'beautiful natural background, masterpiece, high quality',
            'default_negative': 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config['output_dir']).mkdir(parents=True, exist_ok=True)

    # ==================== 模型管理 ====================

    def _find_model(self, model_name: str) -> Optional[Path]:
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
        """加载纯 Inpaint Pipeline"""
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
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        if not os.path.exists(model_path):
            logger.error(f"模型不存在: {model_path}")
            return False

        logger.info(f"从路径加载模型: {model_path}")
        return self._load_pipeline(Path(model_path))

    # ==================== 遮罩生成（人物区域） ====================

    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None

        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
                logger.info("  YOLO 加载成功")
            except Exception as e:
                logger.warning(f"  YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_person_mask(self, image: Image.Image) -> Optional[Image.Image]:
        """生成人物遮罩（用于保护人物）"""
        h, w = image.size[1], image.size[0]

        yolo = self._get_yolo_model()
        if not yolo:
            return None

        try:
            results = yolo(image, verbose=False)
            if len(results) == 0 or results[0].masks is None:
                return None

            masks = results[0].masks.data.cpu().numpy()
            combined = np.zeros((h, w), dtype=np.uint8)
            for m in masks:
                m_resized = cv2.resize(m, (w, h))
                combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)

            # 膨胀让边缘更自然
            kernel = np.ones((10, 10), np.uint8)
            combined = cv2.dilate(combined, kernel, iterations=2)
            combined = cv2.GaussianBlur(combined, (15, 15), 0)

            if np.sum(combined > 0) < 100:
                return None

            logger.info(f"  人物遮罩生成完成，覆盖 {np.sum(combined > 0)} 像素")
            return Image.fromarray(combined, mode="L")

        except Exception as e:
            logger.warning(f"  YOLO 分割失败: {e}")
            return None

    def _generate_background_mask(self, person_mask: Image.Image) -> Image.Image:
        """生成背景遮罩（人物遮罩的反转）"""
        # 反转遮罩 -> 背景区域
        bg_mask = Image.eval(person_mask, lambda x: 255 - x)
        return bg_mask

    # ==================== ControlNet 集成 ====================

    def _generate_depth_image(self, image: Image.Image, controlnet_type: str = "depth") -> Optional[Image.Image]:
        """使用 ControlNet 技能生成深度图（保持空间结构）"""
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
                    depth_image = Image.open(output_path)
                    logger.info(f"  深度图生成完成: {output_path}")
                    return depth_image
            return None

        except Exception as e:
            logger.warning(f"  深度图生成失败: {e}")
            return None

    # ==================== 图片预处理 ====================

    def _resize_image(self, image: Image.Image) -> tuple:
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

        # 确保是 8 的倍数
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
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"目录不存在: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "bg_output"
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

        for i, img_path in enumerate(images, 1):
            logger.info(f"\n[{i}/{len(images)}] {img_path.name}")
            out_file = output_path / img_path.name

            try:
                result = self.execute(
                    image_path=str(img_path),
                    output_path=str(out_file),
                    **kwargs
                )
                if result['status'] == 'success':
                    success_count += 1
                results.append(result)
            except Exception as e:
                results.append({"status": "error", "error": str(e), "image": str(img_path)})

        return {
            "status": "success" if success_count > 0 else "error",
            "total": len(images),
            "success": success_count,
            "failed": len(images) - success_count,
            "results": results,
            "output_dir": str(output_path)
        }

    # ==================== 主执行方法 ====================

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行换背景

        Args:
            image_path: 输入图片路径 (必填)
            output_path: 输出路径 (可选)
            background_prompt: 背景描述提示词 (可选)
            preset: 预设背景名称 (可选)
            model_name: 模型名称 (可选)
            model_path: 模型路径 (可选)
            strength: 重绘强度 (可选)
            steps: 迭代步数 (可选)
            seed: 随机种子 (可选)
            output_dir: 输出目录 (可选)
            save_mask: 是否保存遮罩 (可选)
            controlnet_type: ControlNet 类型 (可选)
            use_controlnet: 是否使用 ControlNet (可选)

        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            if not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            output_path = kwargs.get('output_path')
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')

            # 2. 获取背景提示词
            background_prompt = kwargs.get('background_prompt')
            preset = kwargs.get('preset')

            if preset and preset in self.PRESET_BACKGROUNDS:
                background_prompt = self.PRESET_BACKGROUNDS[preset]
                logger.info(f"  使用预设背景: {preset}")

            if not background_prompt:
                background_prompt = self.config.get('default_prompt', 'beautiful natural background, masterpiece, high quality')

            # 完整提示词 = 人物 + 背景
            prompt = background_prompt
            negative_prompt = kwargs.get('negative_prompt', self.config.get('default_negative'))

            # 3. 参数
            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir', str(self.output_dir)))
            save_mask = kwargs.get('save_mask', False)
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'depth'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            # 4. 加载模型
            if model_path:
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"无法加载模型: {model_path}"}
            else:
                model_name = model_name or self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 5. 加载并缩放图片
            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"处理: {os.path.basename(image_path)} ({image.size[0]}x{image.size[1]})")
            logger.info(f"背景描述: {background_prompt[:80]}...")

            # 6. 生成人物遮罩
            logger.info("生成人物遮罩...")
            person_mask = self._generate_person_mask(image)

            if person_mask is None:
                logger.warning("  人物遮罩生成失败，使用默认中心椭圆遮罩")
                h, w = image.size[1], image.size[0]
                person_mask = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(person_mask)
                cx, cy = w // 2, h // 2
                draw.ellipse((cx - w//3, cy - h//2.5, cx + w//3, cy + h//2.5), fill=255)
                person_mask = person_mask.filter(ImageFilter.GaussianBlur(radius=15))

            # 生成背景遮罩（人物遮罩的反转）
            bg_mask = self._generate_background_mask(person_mask)

            if save_mask:
                mask_path = image_path.replace('.png', '_person_mask.png').replace('.jpg', '_person_mask.png')
                person_mask.save(mask_path)
                logger.info(f"  人物遮罩: {os.path.basename(mask_path)}")
                bg_mask_path = image_path.replace('.png', '_bg_mask.png').replace('.jpg', '_bg_mask.png')
                bg_mask.save(bg_mask_path)
                logger.info(f"  背景遮罩: {os.path.basename(bg_mask_path)}")

            # 7. 生成深度图（保持空间结构）
            control_image = None
            if use_controlnet and self.controlnet_skill is not None:
                logger.info(f"生成深度图 (controlnet_type={controlnet_type})...")
                control_image = self._generate_depth_image(image, controlnet_type)
                if control_image is not None:
                    logger.info("  深度图生成完成")
                else:
                    logger.info("  深度图生成失败，继续使用普通 Inpaint")

            # 8. 设置随机种子
            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            logger.info("SD Inpaint 生成中...")
            logger.info(f"  步数: {steps}")
            logger.info(f"  强度: {strength}")
            logger.info(f"  种子: {seed}")
            if control_image is not None:
                logger.info("  ControlNet: 已启用 (深度图)")

            # 9. 执行 Inpaint（重绘背景区域）
            current_size = image.size
            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': image,
                'mask_image': bg_mask,
                'strength': strength,
                'num_inference_steps': steps,
                'guidance_scale': 7.5,
                'generator': generator,
                'width': current_size[0],
                'height': current_size[1],
            }

            if control_image is not None:
                pipeline_kwargs['control_image'] = control_image

            result = self.pipeline(**pipeline_kwargs).images[0]

            # 10. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                preset_suffix = f"_{preset}" if preset else ""
                filename = f"{Path(image_path).stem}_{timestamp}_bg{preset_suffix}.png"
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
                    "background_prompt": background_prompt,
                    "preset": preset,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
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

    def list_presets(self) -> Dict[str, Any]:
        """列出所有预设背景"""
        return {
            "status": "success",
            "presets": self.PRESET_BACKGROUNDS,
            "count": len(self.PRESET_BACKGROUNDS),
            "timestamp": datetime.now().isoformat()
        }

    def __repr__(self):
        return f"<ChangeBackground(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="换背景工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--preset", "-p", choices=list(ChangeBackground.PRESET_BACKGROUNDS.keys()),
                        help="预设背景名称")
    parser.add_argument("--prompt", help="自定义背景描述提示词")
    parser.add_argument("--model", "-m", default="zenityXmix.inpainting.safetensors", help="模型名称")
    parser.add_argument("--strength", "-s", type=float, default=0.7, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    parser.add_argument("--no-controlnet", action="store_true", help="禁用 ControlNet")
    parser.add_argument("--controlnet-type", default="depth",
                        choices=["depth", "canny", "hed", "lineart"],
                        help="ControlNet 类型 (推荐 depth)")

    args = parser.parse_args()

    skill = ChangeBackground(config={
        'device': args.device,
        'use_controlnet': not args.no_controlnet,
        'default_controlnet_type': args.controlnet_type
    })

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        preset=args.preset,
        background_prompt=args.prompt,
        model_name=args.model,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed,
        save_mask=args.save_mask,
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