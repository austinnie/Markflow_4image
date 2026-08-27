# skills/sketch_to_real/skill.py
"""
素描转真人 Skill - 将素描/线稿转换为真人照片
使用 Lineart ControlNet 保持线条结构
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image
    from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers 未安装")

try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("ControlNet 技能不可用")

# ==================== 风格配置 ====================
REALISM_STYLES = {
    "realistic": {
        "prompt": "photorealistic, real person, realistic skin texture, natural lighting, detailed, masterpiece, high quality, 8k",
        "negative": "anime, cartoon, 2d, illustration, drawing, painting, sketch"
    },
    "cinematic": {
        "prompt": "cinematic photography, real person, movie still, dramatic lighting, detailed, masterpiece, high quality, 8k",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    },
    "portrait": {
        "prompt": "professional portrait photography, real person, studio lighting, beautiful, detailed, masterpiece, high quality",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    },
    "artistic": {
        "prompt": "artistic photography, real person, creative lighting, beautiful, masterpiece, high quality",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    }
}

# ==================== 可用模型列表 ====================
AVAILABLE_MODELS = {
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
    "real_asia.safetensors": {
        "name": "Real Asia",
        "size": "1.82 GB",
        "type": "亚洲写实",
        "description": "轻量级亚洲人像"
    },
}


class SketchToReal:
    """素描转真人技能（纯 ControlNet，无需 Inpaint）"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "sketch_to_real"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cpu')

        # 默认参数
        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 35)
        self.default_strength = self.config.get('default_strength', 0.85)
        self.default_style = self.config.get('default_style', 'realistic')
        self.default_negative = self.config.get('default_negative', 'ugly, deformed, blurry, low quality, sketch, drawing, lineart, 2d')

        # 缓存
        self.pipeline = None
        self.current_model = None
        self.controlnet_skill = None

        # 初始化 ControlNet 技能（用于提取线稿）
        if CONTROLNET_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={'device': self.device, 'max_size': 512})
                logger.info("  ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"  ControlNet 技能初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"SketchToReal v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  默认模型: {self.default_model}")
        logger.info(f"  风格: {list(REALISM_STYLES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_model': 'anytimeRealistic_v10.safetensors',
            'default_steps': 35,
            'default_strength': 0.85,
            'default_style': 'realistic',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        Path(self.config.get('output_dir', str(self.output_dir))).mkdir(parents=True, exist_ok=True)

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

    def _load_pipeline(self, model_name: str) -> bool:
        """加载 ControlNet Pipeline（普通 SD + Lineart ControlNet）"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False

        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型不存在: {model_name}")
            return False

        try:
            from diffusers import StableDiffusionControlNetPipeline, ControlNetModel

            # 加载 Lineart ControlNet
            logger.info("加载 ControlNet: lllyasviel/control_v11p_sd15_lineart")
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/control_v11p_sd15_lineart",
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

    def _generate_lineart_image(self, image: Image.Image) -> Optional[Image.Image]:
        """使用 ControlNet 技能提取线稿（作为控制图）"""
        if self.controlnet_skill is None:
            return None
        try:
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=image,
                controlnet_type='lineart',
                output_path=None
            )
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    return Image.open(output_path)
            return None
        except Exception as e:
            logger.warning(f"  线稿图生成失败: {e}")
            return None

    def _resize_image(self, image: Image.Image) -> tuple:
        w, h = image.size
        max_size = 768
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image, image.size

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(REALISM_STYLES.keys())}

    def list_models(self) -> Dict[str, Any]:
        """列出所有可用模型"""
        models = {}
        for key, info in AVAILABLE_MODELS.items():
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

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} v{self.version}")

        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path') or kwargs.get('input')
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            output_path = kwargs.get('output_path') or kwargs.get('output')
            model_name = kwargs.get('model_name') or kwargs.get('model') or self.default_model
            style = kwargs.get('style', self.default_style)
            if style not in REALISM_STYLES:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(REALISM_STYLES.keys())}"}

            s_config = REALISM_STYLES[style]
            prompt = kwargs.get('prompt') or s_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or s_config.get('negative', self.default_negative)

            steps = kwargs.get('steps', self.default_steps)
            seed = kwargs.get('seed', -1)

            # 2. 加载模型
            if not self._load_pipeline(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 3. 加载图片
            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"风格: {style}")
            logger.info(f"模型: {model_name}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 4. 提取线稿作为控制图
            control_image = self._generate_lineart_image(image)
            if control_image is None:
                logger.warning("  线稿提取失败，使用原图作为控制图")
                control_image = image

            # 5. 设置种子
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            # 6. 构建提示词
            full_prompt = f"{prompt}, realistic, detailed, masterpiece, best quality"

            # 7. 执行生成（使用 ControlNet Pipeline，不需要遮罩）
            pipeline_kwargs = {
                'prompt': full_prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': control_image,
                'num_inference_steps': steps,
                'guidance_scale': 7.5,
                'generator': generator,
                'width': image.size[0],
                'height': image.size[1],
            }

            result = self.pipeline(**pipeline_kwargs).images[0]

            # 8. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(image_path).stem}_sketch2real_{style}_{timestamp}.png")

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "style": style,
                "model": model_name,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "steps": steps,
                    "seed": seed,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "controlnet": "lineart"
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<SketchToReal(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="素描转真人工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入素描/线稿图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors",
                        choices=MODEL_CHOICES, help="SD 模型名称")
    parser.add_argument("--style", "-s", default="realistic",
                        choices=list(REALISM_STYLES.keys()), help="真人风格")
    parser.add_argument("--prompt", "-p", help="自定义提示词（覆盖风格默认）")
    parser.add_argument("--negative", "-n", help="自定义负面提示词（覆盖风格默认）")
    parser.add_argument("--steps", type=int, default=35, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用模型")
    parser.add_argument("--list-styles", action="store_true", help="列出所有可用风格")

    args = parser.parse_args()

    # 如果只是列出模型
    if args.list_models:
        skill = SketchToReal()
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

    # 如果只是列出风格
    if args.list_styles:
        print("\n" + "=" * 60)
        print("  可用风格列表")
        print("=" * 60)
        for key, info in REALISM_STYLES.items():
            print(f"  {key}")
            print(f"    提示词: {info['prompt'][:60]}...")
            print(f"    负面: {info['negative'][:60]}...")
            print()
        print(f"  共 {len(REALISM_STYLES)} 种风格")
        print("=" * 60)
        sys.exit(0)

    skill = SketchToReal(config={
        'device': args.device,
        'default_model': args.model,
        'default_steps': args.steps,
        'default_style': args.style,
    })

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        model_name=args.model,
        style=args.style,
        prompt=args.prompt,
        negative_prompt=args.negative,
        steps=args.steps,
        seed=args.seed,
    )

    if result['status'] == 'success':
        print(f"\n✅ 成功!")
        print(f"  📁 输出: {result['output_path']}")
        print(f"  🎨 风格: {result['style']}")
        print(f"  🤖 模型: {result['model']}")
        print(f"  ⏱️  耗时: {result['generation_time']}")
        print(f"  📋 参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")