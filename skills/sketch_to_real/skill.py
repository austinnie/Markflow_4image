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
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch 或 PIL 未安装")

# ==================== 引入真正的底层引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

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
    }
}


class SketchToReal:
    """素描转真人技能（纯 ControlNet，无需 Inpaint）"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "sketch_to_real"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        
        # ==================== 强制本技能输出目录 ====================
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
        self.controlnet_engine = None

        # ==================== 初始化底层引擎 ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  ✅ 底层引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

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

        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

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
            # ==================== 1. 严格路径校验 ====================
            image_path = kwargs.get('image_path') or kwargs.get('input')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            output_path = kwargs.get('output_path') or kwargs.get('output')

            # 提示词与风格配置
            style = kwargs.get('style', self.default_style)
            if style not in REALISM_STYLES:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(REALISM_STYLES.keys())}"}

            s_config = REALISM_STYLES[style]
            prompt = kwargs.get('prompt') or s_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or s_config.get('negative', self.default_negative)

            # ==================== 2. 直接调用底层 ControlNet 引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            logger.info(f"风格: {style}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 如果没传 output_path，默认存到本技能的 output 目录
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_sketch2real_{style}_{timestamp}.png")

            # 核心逻辑：传入 HED (提取线稿) + Lineart 底层模型
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),  # 绝对路径
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",               # 提取线稿
                controlnet_model="lineart",            # 强制使用本地 lineart 模型（你本地的 models--lllyasviel--control_v11p_sd15_lineart）
                strength=0.85,                         # 高强度重绘，让线稿变真人
                output_path=output_path                # 强制指定输出
            )

            # 检查引擎返回结果
            if result['status'] == 'success':
                return {
                    "status": "success",
                    "output_path": result.get('image_path', output_path),
                    "style": style,
                    "generation_time": f"{time.time() - start_time:.2f}s",
                    "parameters": {
                        "steps": kwargs.get('steps', self.default_steps),
                        "seed": kwargs.get('seed', -1),
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "controlnet": "lineart"
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 引擎报错，直接把引擎的错误原样抛出
                return {"status": "error", "error": result.get('error', '底层引擎调用失败')}

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
        print(f"  ⏱️  耗时: {result['generation_time']}")
        print(f"  📋 参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")