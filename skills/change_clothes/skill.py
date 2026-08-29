# markflow/skills/change_clothes/skill.py
"""
换衣服 Skill - 将人物衣服替换为指定款式
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
import os
import time
import json
import random
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

# 引入 controlnet_img2img 底层技能作为保形引擎
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
    logger.info("通用 ControlNet 引擎加载成功")
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

# YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装，将使用手动遮罩")


# ==================== 技能类 ====================
class ChangeClothes:
    """换衣服技能 - 将人物衣服替换为指定款式"""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_clothes"
        self.version = "2.0.0"

        # 强制设置本技能输出目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        
        self.default_output_dir = self.skill_dir / "output"
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.auto_resize = self.config.get('auto_resize', True)
        self.min_size = self.config.get('min_size', 512)
        self.max_size = self.config.get('max_size', 1024)

        self.pipeline = None
        self.current_model = None
        self._yolo_model = None
        
        # ControlNet 底层引擎（方案1）
        self.controlnet_engine = None
        if self.config.get('use_controlnet', True) and CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  ✅ 通用保形引擎 (controlnet_img2img) 初始化成功")
            except Exception as e:
                logger.warning(f"  ❌ 通用保形引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeClothes 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  ControlNet: {'✅ 可用' if self.controlnet_engine else '❌ 不可用'}")
        logger.info(f"  YOLO: {'✅ 可用' if YOLO_AVAILABLE else '❌ 不可用'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.default_output_dir),
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.6,
            'use_controlnet': True,
            'default_controlnet_type': 'openpose',
            'default_prompt': 'wearing a beautiful dress, elegant, fashionable, high quality, detailed, masterpiece',
            'default_negative': 'nude, naked, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config.get('output_dir', str(self.skill_dir / 'output'))).mkdir(parents=True, exist_ok=True)

    # ==================== 模型管理 ====================
    def _find_model(self, model_name: str) -> Optional[Path]:
        if not model_name:
            model_name = self.config.get('default_model', 'zenityXmix.inpainting.safetensors')

        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

        filename = os.path.basename(model_name)
        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path

        logger.error(f"未找到模型: '{model_name}'")
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        """加载 SD Inpaint Pipeline（备用路线）"""
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
            logger.info(f"  ✅ Inpaint 模型加载成功: {self.current_model}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Inpaint 模型加载失败: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False

        return self._load_pipeline(model_path)

    def _load_model_from_path(self, model_path: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        if not os.path.exists(model_path):
            logger.error(f"模型不存在: {model_path}")
            return False

        return self._load_pipeline(Path(model_path))

    # ==================== 遮罩生成 ====================
    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
            except Exception as e:
                logger.warning(f"  YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_mask_auto(self, image: Image.Image) -> Optional[Image.Image]:
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

            coords = np.where(combined > 0)
            if len(coords[0]) == 0:
                return None

            y_min, y_max = coords[0].min(), coords[0].max()
            body_h = y_max - y_min
            neck = y_min + int(body_h * 0.18)
            hip = y_min + int(body_h * 0.70)

            x_min, x_max = coords[1].min(), coords[1].max()
            body_w = x_max - x_min
            left = x_min + int(body_w * 0.08)
            right = x_max - int(body_w * 0.08)

            clothes = np.zeros_like(combined)
            clothes[neck:hip, left:right] = combined[neck:hip, left:right]

            kernel = np.ones((5, 5), np.uint8)
            clothes = cv2.dilate(clothes, kernel, iterations=1)
            clothes = cv2.GaussianBlur(clothes, (9, 9), 0)

            if np.sum(clothes > 0) < 100:
                return None

            return Image.fromarray(clothes, mode="L")

        except Exception as e:
            logger.warning(f"  YOLO 分割失败: {e}")
            return None

    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30

        print("\n" + "=" * 50)
        print("手动绘制遮罩模式")
        print("=" * 50)
        print("  按住鼠标左键绘制遮罩（白色区域）")
        print("  滚轮调节画笔大小")
        print("  按 R 键重置遮罩")
        print("  按 Q 或 空格键 完成绘制")
        print("=" * 50 + "\n")

        def draw_callback(event, x, y, flags, param):
            nonlocal drawing, brush_size
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                cv2.circle(mask, (x, y), brush_size, 255, -1)
                cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    cv2.circle(mask, (x, y), brush_size, 255, -1)
                    cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
            elif event == cv2.EVENT_MOUSEWHEEL:
                delta = flags
                brush_size = min(100, max(5, brush_size + (5 if delta > 0 else -5)))
                print(f"   画笔大小: {brush_size}")

        cv2.namedWindow('Draw Mask - Change Clothes')
        cv2.setMouseCallback('Draw Mask - Change Clothes', draw_callback)

        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw clothes, press Q to finish", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow('Draw Mask - Change Clothes', mask_overlay)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)
                print("  遮罩已重置")

        cv2.destroyAllWindows()

        if np.sum(mask > 0) < 100:
            print("  遮罩区域太小，使用椭圆默认遮罩")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 3), 0, 0, 360, 255, -1)

        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        print(f"  遮罩完成，覆盖 {np.sum(mask > 0)} 像素")
        return Image.fromarray(mask, mode="L")

    def _generate_mask(self, image: Image.Image, use_manual: bool = False) -> Image.Image:
        if use_manual:
            return self._generate_mask_manual(image)

        mask = self._generate_mask_auto(image)
        if mask is not None:
            logger.info("  ✅ 使用 YOLO 自动遮罩")
            return mask

        logger.info("  ⚠️ 自动遮罩失败，切换到手动绘制")
        return self._generate_mask_manual(image)

    # ==================== ControlNet 引擎集成 ====================
    def _generate_pose_image(self, image: Image.Image, controlnet_type: str = "openpose") -> Optional[Image.Image]:
        """使用 controlnet_img2img 底层引擎预处理（提取骨骼/线稿），不涉及模型加载"""
        if self.controlnet_engine is None:
            return None

        try:
            logger.info(f"  ✅ 提取控制特征 ({controlnet_type})...")
            control_image = self.controlnet_engine._preprocess(image, preprocessor_type=controlnet_type.upper())
            
            if control_image is not None:
                logger.info("  ✅ 控制特征提取完成")
                return control_image
            else:
                logger.warning("  ⚠️ 控制特征提取失败，继续使用普通 Inpaint")
                return None

        except Exception as e:
            logger.warning(f"  ⚠️ 控制特征提取异常: {e}")
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
    def batch_process(self, input_dir: str, output_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"目录不存在: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "changed_output"
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
                result = self.execute(image_path=str(img_path), output_path=str(output_file), **kwargs)
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
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            output_path = kwargs.get('output_path')
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            manual_mask = kwargs.get('manual_mask', False)
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'openpose'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            # 2. 加载 Inpaint 模型（备用路线）
            if model_path:
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"无法加载模型: {model_path}"}
            else:
                model_name = model_name or self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 3. 获取生成参数
            prompt = kwargs.get('prompt') if kwargs.get('prompt') is not None else self.config.get('default_prompt')
            negative_prompt = kwargs.get('negative_prompt') if kwargs.get('negative_prompt') is not None else self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir'))
            save_mask = kwargs.get('save_mask', False)

            # 4. 加载并缩放图片
            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"处理: {os.path.basename(abs_image_path)} ({image.size[0]}x{image.size[1]})")
            logger.info(f"服装描述: {prompt[:80]}...")

            # 5. 生成遮罩
            logger.info("生成遮罩...")
            mask = self._generate_mask(image, use_manual=manual_mask)

            if save_mask:
                mask_path = str(abs_image_path).replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)
                logger.info(f"  遮罩: {os.path.basename(mask_path)}")

            # 6. 生成姿态图（ControlNet）
            control_image = None
            if use_controlnet and self.controlnet_engine is not None:
                logger.info(f"生成姿态图 (controlnet_type={controlnet_type})...")
                control_image = self._generate_pose_image(image, controlnet_type)
                if control_image is not None:
                    logger.info("  姿态图生成完成")
                else:
                    logger.info("  姿态图生成失败，继续使用普通 Inpaint")

            # 7. 设置随机种子
            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            logger.info("SD 生成中...")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  步数: {steps}")
            logger.info(f"  强度: {strength}")
            logger.info(f"  种子: {seed}")
            if control_image is not None:
                logger.info("  ControlNet: 已启用")

            # 8. 执行生成
            if control_image is not None:
                # 走方案1：调用通用的 ControlNet 图生图引擎（百分百保形）
                logger.info("  🔥 使用 ControlNet 图生图引擎进行保形重绘...")
                
                # 创建一个临时保存路径（写入本技能目录）
                tmp_output = str(self.default_output_dir / f"_tmp_{int(time.time())}.png")
                
                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),  # 必须传绝对路径
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type=controlnet_type.upper(),
                    controlnet_model="openpose",          # 直接锁定 openpose 底层模型
                    strength=0.65,                        # 保形重绘幅度
                    output_path=tmp_output
                )
                
                if result['status'] == 'success':
                    result = Image.open(result.get('image_path', tmp_output))
                else:
                    logger.warning(f"  引擎调用失败: {result.get('error')}，回退到原 Inpaint")
                    pipeline_kwargs = {
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'image': image,
                        'mask_image': mask,
                        'strength': strength,
                        'num_inference_steps': steps,
                        'guidance_scale': 7.5,
                        'generator': generator,
                    }
                    result = self.pipeline(**pipeline_kwargs).images[0]
            else:
                # 如果没有可用的控制特征，走原有的局部重绘逻辑
                logger.info("  使用局部重绘（Inpaint）进行重绘...")
                pipeline_kwargs = {
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'image': image,
                    'mask_image': mask,
                    'strength': strength,
                    'num_inference_steps': steps,
                    'guidance_scale': 7.5,
                    'generator': generator,
                }
                result = self.pipeline(**pipeline_kwargs).images[0]

            # 9. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{Path(abs_image_path).stem}_{timestamp}_changed.png"
                output_path = str(self.default_output_dir / filename)

            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            result.save(output_path)

            generation_time = time.time() - start_time
            logger.info(f"  保存: {os.path.basename(output_path)}")

            return {
                "status": "success",
                "output_path": output_path,
                "parameters": {
                    "image_path": str(abs_image_path),
                    "model": self.current_model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
                    "controlnet": control_image is not None,
                    "controlnet_type": controlnet_type if control_image is not None else None,
                    "manual_mask": manual_mask
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
        return f"<ChangeClothes(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="换衣服工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径或目录")
    parser.add_argument("--output", "-o", help="输出路径或目录")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--model", "-m", default="zenityXmix.inpainting.safetensors", help="模型名称")
    parser.add_argument("--prompt", "-p", default="wearing a beautiful dress, elegant, fashionable, high quality, detailed, masterpiece", help="服装描述提示词")
    parser.add_argument("--negative", "-n", default="nude, naked, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime", help="负面提示词")
    parser.add_argument("--strength", "-s", type=float, default=0.6, help="重绘强度")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    parser.add_argument("--manual-mask", action="store_true", help="手动绘制遮罩")
    parser.add_argument("--no-controlnet", action="store_true", help="禁用 ControlNet")
    parser.add_argument("--controlnet-type", default="openpose",
                        choices=["canny", "openpose", "depth", "hed", "lineart", "normal", "mlsd", "openpose_full"],
                        help="ControlNet 类型")

    args = parser.parse_args()

    skill = ChangeClothes(config={
        'device': args.device,
        'use_controlnet': not args.no_controlnet,
        'default_controlnet_type': args.controlnet_type
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
            manual_mask=args.manual_mask,
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
            manual_mask=args.manual_mask,
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