"""
Expand to Full Body - 将人物半身/头像图扩展为全身图
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

# ==================== 导入依赖 ====================
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw
    from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers 未安装")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装")

try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("ControlNet 技能不可用")


class ExpandToFullBody:
    """
    半身图转全身图技能
    """

    # ==================== 可用模型列表 ====================
    AVAILABLE_MODELS = {
        # 推荐模型
        "anytimeRealistic_v10.safetensors": {
            "name": "Anytime Realistic",
            "size": "2.13 GB",
            "type": "写实",
            "description": "通用写实风格，推荐"
        },
        "asianrealisticSdlife_v40.safetensors": {
            "name": "Asian Realistic SDLife",
            "size": "3.29 GB",
            "type": "亚洲写实",
            "description": "亚洲人像写实"
        },
        "DreamShaper_8_pruned.safetensors": {
            "name": "DreamShaper 8",
            "size": "2.13 GB",
            "type": "艺术",
            "description": "梦幻/艺术风格"
        },
        "nextphoto_v30.safetensors": {
            "name": "Next Photo v3.0",
            "size": "2.13 GB",
            "type": "摄影",
            "description": "真实摄影风格"
        },
        "detailAsianRealistic_v60X21b.safetensors": {
            "name": "Detail Asian Realistic",
            "size": "2.13 GB",
            "type": "亚洲写实",
            "description": "细节丰富的亚洲写实"
        },
        "aiiiii01_v10.safetensors": {
            "name": "AIiiii v1.0",
            "size": "2.13 GB",
            "type": "写实",
            "description": "通用写实"
        },
        "henmixrealV10_henmixrealV10.safetensors": {
            "name": "Henmix Real",
            "size": "2.38 GB",
            "type": "写实",
            "description": "人像写实"
        },
        "girlMix_V2.safetensors": {
            "name": "Girl Mix V2",
            "size": "3.12 GB",
            "type": "写实",
            "description": "女性人像"
        },
        "real_asia.safetensors": {
            "name": "Real Asia",
            "size": "1.82 GB",
            "type": "亚洲写实",
            "description": "轻量级亚洲人像"
        },
        # 大型模型
        "anycharactermixBaked_v20BakedVae.safetensors": {
            "name": "Any Character Mix",
            "size": "4.27 GB",
            "type": "角色混合",
            "description": "角色混合风格"
        },
        "evalisenniaRealisticEastAsian_v40.safetensors": {
            "name": "Evalisennia East Asian",
            "size": "6.94 GB",
            "type": "亚洲写实",
            "description": "最高质量亚洲写实（大）"
        },
        "realisticmix_iiV12Version12.safetensors": {
            "name": "Realistic Mix II",
            "size": "4.27 GB",
            "type": "写实",
            "description": "写实混合"
        },
        "shmRealistic_v40.safetensors": {
            "name": "SHM Realistic",
            "size": "4.27 GB",
            "type": "写实",
            "description": "写实风格"
        },
        "t3_sdVer3.safetensors": {
            "name": "T3 SD Ver3",
            "size": "4.84 GB",
            "type": "通用",
            "description": "通用模型"
        },
        # Inpaint 模型（仅用于其他技能）
        "zenityXmix.inpainting.safetensors": {
            "name": "ZenityXmix Inpaint",
            "size": "3.18 GB",
            "type": "Inpaint",
            "description": "局部重绘专用"
        },
        "sd-v1-5-inpainting-tiny.safetensors": {
            "name": "SD 1.5 Inpaint Tiny",
            "size": "2.13 GB",
            "type": "Inpaint",
            "description": "轻量级局部重绘"
        },
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "expand_to_full_body"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cpu')

        # 默认参数
        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 30)
        self.default_strength = self.config.get('default_strength', 0.6)
        self.target_height = self.config.get('target_height', 1024)
        self.target_width = self.config.get('target_width', 768)

        # 缓存
        self.pipeline = None
        self.current_model = None
        self._yolo = None

        self._setup_logging()
        self._setup_config()

        # 初始化 ControlNet
        self.controlnet = None
        if CONTROLNET_AVAILABLE:
            try:
                self.controlnet = Controlnet(config={'device': self.device})
                logger.info("ControlNet 初始化成功")
            except Exception as e:
                logger.warning(f"ControlNet 初始化失败: {e}")

        logger.info(f"ExpandToFullBody 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  默认模型: {self.default_model}")
        logger.info(f"  目标尺寸: {self.target_width}x{self.target_height}")
        logger.info(f"  ControlNet: {'✅' if self.controlnet else '❌'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'target_width': 768,
            'target_height': 1024,
            'default_model': 'anytimeRealistic_v10.safetensors',
            'default_steps': 30,
            'default_strength': 0.6,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _find_model(self, model_name: str) -> Optional[Path]:
        """查找模型文件"""
        if not model_name:
            model_name = self.default_model

        # 直接查找
        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

        # 子目录查找
        filename = os.path.basename(model_name)
        for subdir in ['sd-v1-5', 'sdxl']:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path

        logger.error(f"未找到模型: {model_name}")
        return None

    def _load_pipeline(self, model_name: str, controlnet_type: str = None) -> bool:
        """加载 ControlNet Pipeline（普通 SD + ControlNet）"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型不存在: {model_name}")
            return False

        try:
            from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
            from skills.controlnet.skill import CONTROLNET_TYPES

            # 加载 ControlNet
            controlnet = None
            if controlnet_type:
                info = CONTROLNET_TYPES.get(controlnet_type)
                if info:
                    controlnet_id = info["model_id"]
                    logger.info(f"加载 ControlNet: {controlnet_id}")
                    controlnet = ControlNetModel.from_pretrained(
                        controlnet_id,
                        torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                    )

            # 加载普通 SD + ControlNet Pipeline（不是 Inpaint）
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                str(model_path),
                controlnet=controlnet,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            pipe.to(self.device)
            pipe.enable_attention_slicing()
            self.pipeline = pipe
            self.current_model = model_name
            logger.info(f"✅ ControlNet Pipeline 加载成功: {model_name}")
            return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False

    def _detect_face_and_body(self, image: Image.Image) -> Dict[str, Any]:
        """
        检测图片中的人物位置
        返回: 头部位置、身体区域、是否全身、裁剪位置
        """
        img_array = np.array(image)
        h, w = img_array.shape[:2]

        # 使用 YOLO 检测人体
        try:
            from ultralytics import YOLO
            if self._yolo is None:
                self._yolo = YOLO("yolov8n-pose.pt")

            results = self._yolo(image, verbose=False)
            if len(results) == 0 or results[0].keypoints is None:
                return {
                    "has_person": False,
                    "is_full_body": False,
                    "head_y": h * 0.15,
                    "body_top": 0,
                    "body_bottom": h,
                    "confidence": 0,
                }

            keypoints = results[0].keypoints
            if keypoints is None or len(keypoints.data) == 0:
                return {
                    "has_person": False,
                    "is_full_body": False,
                    "head_y": h * 0.15,
                    "body_top": 0,
                    "body_bottom": h,
                    "confidence": 0,
                }

            # 获取关键点
            kp = keypoints.data[0].cpu().numpy()
            visible = keypoints.conf[0].cpu().numpy()

            # 找到头部位置（鼻子/眼睛）
            head_y = h * 0.15  # 默认
            head_x = w // 2
            for idx, (x, y, conf) in enumerate(zip(kp[:, 0], kp[:, 1], visible)):
                if conf > 0.5 and idx in [0, 1, 2]:  # 鼻子、左眼、右眼
                    head_y = y
                    head_x = x
                    break

            # 检测脚踝位置判断是否全身
            has_ankles = False
            ankle_y = h
            for idx, (x, y, conf) in enumerate(zip(kp[:, 0], kp[:, 1], visible)):
                if conf > 0.5 and idx in [15, 16]:  # 左右脚踝
                    has_ankles = True
                    ankle_y = min(ankle_y, y)

            # 判断是否为全身图
            is_full_body = has_ankles
            body_bottom = ankle_y if has_ankles else h
            body_top = max(0, head_y - h * 0.25)

            # 检测到的身体高度
            body_height = body_bottom - body_top
            image_height_ratio = body_height / h

            # 如果身体高度占图片高度小于 60%，可能是半身或大头照
            if image_height_ratio < 0.6 and not is_full_body:
                is_full_body = False

            return {
                "has_person": True,
                "is_full_body": is_full_body,
                "head_y": head_y,
                "head_x": head_x,
                "body_top": body_top,
                "body_bottom": body_bottom,
                "body_height": body_height,
                "body_height_ratio": image_height_ratio,
                "has_ankles": has_ankles,
                "ankle_y": ankle_y if has_ankles else None,
                "confidence": float(kp[:, 2].max()) if len(kp) > 0 else 0,
            }

        except Exception as e:
            logger.warning(f"人体检测失败: {e}")
            return {
                "has_person": False,
                "is_full_body": False,
                "head_y": h * 0.15,
                "body_top": 0,
                "body_bottom": h,
                "confidence": 0,
            }

    def _expand_image_area(self, image: Image.Image, target_width: int, target_height: int,
                           head_y: float, head_x: float) -> tuple:
        """
        扩展画布，将人物放在合适位置
        返回: (扩展后的图片, 偏移量, 缩放比例)
        """
        src_w, src_h = image.size

        # 计算缩放比例：使头部在合适位置
        # 全身图中，头部大约在图片高度的 10-20% 位置
        head_ratio = 0.15
        scale = (target_height * head_ratio) / (head_y / src_h * src_h)

        # 限制缩放范围
        scale = max(0.5, min(1.8, scale))

        # 缩放图片
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 计算粘贴位置：头部在目标图片的 15% 高度位置
        head_y_new = head_y * scale
        offset_y = int(target_height * 0.15 - head_y_new)
        offset_x = int((target_width - new_w) // 2)

        # 创建扩展图片
        expanded = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        expanded.paste(resized, (offset_x, offset_y))

        return expanded, (offset_x, offset_y), scale

    def _generate_pose_image(self, image: Image.Image, controlnet_type: str = "openpose") -> Optional[Image.Image]:
        """生成姿态图"""
        if self.controlnet is None:
            return None

        try:
            result = self.controlnet.execute(
                action='detect_pose',
                image=image,
                controlnet_type=controlnet_type,
                output_path=None
            )
            if result['status'] == 'success' and os.path.exists(result['output_path']):
                return Image.open(result['output_path'])
            return None
        except Exception as e:
            logger.warning(f"姿态图生成失败: {e}")
            return None

    def _generate_full_body(self, image: Image.Image, prompt: str, negative_prompt: str,
                            steps: int, seed: int,
                            controlnet_type: str = None) -> Image.Image:
        """生成全身图（纯 ControlNet，不需要遮罩和 strength）"""
        target_w = self.config.get('target_width', 768)
        target_h = self.config.get('target_height', 1024)

        # 1. 检测人物
        detection = self._detect_face_and_body(image)

        if not detection['has_person']:
            # 没有检测到人物，使用默认扩展
            logger.info("未检测到人物，使用默认扩展")
            head_y = image.height * 0.15
            head_x = image.width // 2
        else:
            head_y = detection['head_y']
            head_x = detection['head_x']
            logger.info(f"检测到人物: 头部位置 ({head_x:.0f}, {head_y:.0f})")
            logger.info(f"  是否全身: {detection['is_full_body']}")

        # 2. 扩展画布
        expanded, offset, scale = self._expand_image_area(
            image, target_w, target_h, head_y, head_x
        )

        logger.info(f"  缩放: {scale:.2f}x, 偏移: ({offset[0]}, {offset[1]})")

        # 3. 生成姿态图
        control_image = None
        if controlnet_type:
            control_image = self._generate_pose_image(expanded, controlnet_type)

        # 4. 设置种子
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device=self.device).manual_seed(seed)

        # 5. 构建提示词
        full_prompt = f"{prompt}, full body, whole body, standing, detailed, masterpiece, best quality, photorealistic"

        # 6. 执行生成（使用 ControlNet Pipeline，不需要遮罩）
        pipeline_kwargs = {
            'prompt': full_prompt,
            'negative_prompt': negative_prompt if negative_prompt else None,
            'image': control_image if control_image else expanded,
            'num_inference_steps': steps,
            'guidance_scale': 7.5,
            'generator': generator,
            'width': target_w,
            'height': target_h,
        }

        result = self.pipeline(**pipeline_kwargs).images[0]
        return result

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行半身图转全身图

        Args:
            image_path: 输入图片路径 (必填)
            output_path: 输出路径 (可选)
            prompt: 人物描述提示词 (可选)
            negative_prompt: 负面提示词 (可选)
            model_name: 模型名称 (可选)
            steps: 推理步数 (可选)
            seed: 随机种子 (可选)
            controlnet_type: ControlNet 类型 (可选)
            target_width: 目标宽度 (可选)
            target_height: 目标高度 (可选)
            force_expand: 强制扩展 (即使已是全身图)

        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "image_path 是必填参数且文件必须存在"}

            image = Image.open(image_path).convert("RGB")

            output_path = kwargs.get('output_path')
            model_name = kwargs.get('model_name', self.default_model)
            prompt = kwargs.get('prompt', 'a person, beautiful, detailed')
            negative_prompt = kwargs.get('negative_prompt', 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality')
            steps = kwargs.get('steps', self.default_steps)
            seed = kwargs.get('seed', -1)
            controlnet_type = kwargs.get('controlnet_type', 'openpose')
            force_expand = kwargs.get('force_expand', False)

            # 更新目标尺寸
            target_w = kwargs.get('target_width', self.config.get('target_width', 768))
            target_h = kwargs.get('target_height', self.config.get('target_height', 1024))
            self.config['target_width'] = target_w
            self.config['target_height'] = target_h

            # 2. 检测是否全身
            detection = self._detect_face_and_body(image)
            if detection['is_full_body'] and not force_expand:
                logger.info("检测到已是全身图，跳过处理（使用 --force_expand 可强制扩展）")
                return {
                    "status": "success",
                    "message": "已检测到全身图，无需扩展",
                    "is_full_body": True,
                    "output_path": image_path,
                    "detection": detection,
                }

            # 3. 加载模型
            if not self._load_pipeline(model_name, controlnet_type if controlnet_type else None):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 4. 生成全身图
            result_image = self._generate_full_body(
                image, prompt, negative_prompt,
                steps, seed,
                controlnet_type
            )

            # 5. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"full_body_{timestamp}.png")

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result_image.save(output_path)

            elapsed = time.time() - start_time

            return {
                "status": "success",
                "output_path": output_path,
                "is_full_body": False,
                "expanded": True,
                "parameters": {
                    "model": model_name,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "steps": steps,
                    "seed": seed,
                    "controlnet_type": controlnet_type,
                    "target_size": f"{target_w}x{target_h}",
                },
                "detection": detection,
                "generation_time": f"{elapsed:.2f}s",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def list_models(self) -> Dict[str, Any]:
        """列出所有可用模型"""
        models = {}
        for key, info in self.AVAILABLE_MODELS.items():
            models[key] = {
                "name": info["name"],
                "size": info["size"],
                "type": info["type"],
                "description": info["description"],
            }
        return {
            "status": "success",
            "models": models,
            "count": len(models),
            "default": self.default_model,
            "timestamp": datetime.now().isoformat()
        }

    def __repr__(self):
        return f"<ExpandToFullBody(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    # 模型名称映射（用于显示）
    MODEL_CHOICES = list(ExpandToFullBody.AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="半身图转全身图")
    parser.add_argument("--input", "-i", required=False, help="输入图片路径 (--list-models 时无需提供)")
    parser.add_argument("--output", "-o", help="输出图片路径")
    parser.add_argument("--prompt", "-p", default="a person, beautiful, detailed", help="人物描述提示词")
    parser.add_argument("--negative", "-n", default="ugly, deformed, bad anatomy, extra limbs, blurry, low quality", help="负面提示词")
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors",
                        choices=MODEL_CHOICES,
                        help="模型名称")
    parser.add_argument("--steps", "-s", type=int, default=30, help="推理步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--width", type=int, default=768, help="目标宽度")
    parser.add_argument("--height", type=int, default=1024, help="目标高度")
    parser.add_argument("--controlnet-type", default="openpose",
                        choices=["openpose", "canny", "depth", "hed", "lineart", "normal", "mlsd"],
                        help="ControlNet 类型")
    parser.add_argument("--force-expand", action="store_true", help="强制扩展（即使已是全身图）")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="设备")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用模型")

    args = parser.parse_args()

    # 如果只是列出模型
    if args.list_models:
        skill = ExpandToFullBody()
        result = skill.list_models()
        print("\n" + "=" * 60)
        print("  可用模型列表")
        print("=" * 60)
        for key, info in result['models'].items():
            default_mark = " ⭐ (默认)" if key == result['default'] else ""
            print(f"  {key}")
            print(f"    名称: {info['name']}{default_mark}")
            print(f"    大小: {info['size']}")
            print(f"    类型: {info['type']}")
            print(f"    说明: {info['description']}")
            print()
        print(f"  共 {result['count']} 个模型")
        print("=" * 60)
        sys.exit(0)

    # 非列表模式，检查 input 参数
    if not args.input:
        parser.error("--input 是必填参数（除非使用 --list-models）")

    skill = ExpandToFullBody(config={
        'device': args.device,
        'default_model': args.model,
        'target_width': args.width,
        'target_height': args.height,
        'default_steps': args.steps,
    })

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        prompt=args.prompt,
        negative_prompt=args.negative,
        model_name=args.model,
        steps=args.steps,
        seed=args.seed,
        controlnet_type=args.controlnet_type,
        target_width=args.width,
        target_height=args.height,
        force_expand=args.force_expand,
    )

    if result['status'] == 'success':
        print(f"\n✅ 成功!")
        print(f"  📁 输出: {result['output_path']}")
        if result.get('is_full_body'):
            print(f"  ℹ️  已是全身图，未处理")
        else:
            print(f"  ⏱️  耗时: {result['generation_time']}")
            print(f"  📋 参数:")
            for key, value in result['parameters'].items():
                print(f"    {key}: {value}")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")