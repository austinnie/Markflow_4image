# skills/style_transfer/skill.py
"""
风格转换 Skill - 将图片转换为指定风格（油画/水彩/动漫/素描等）
复用通用 ControlNet 引擎（HED + Lineart 锁死构图，高幅度重构画面质感）
"""

import time
import os
import sys
import json
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

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

# 风格预设
STYLE_PRESETS = {
    "oil_painting": {
        "prompt": "oil painting, thick brushstrokes, canvas texture, masterpiece, van gogh style, rich colors, artistic, high quality",
        "negative": "photorealistic, 3d render, digital art, smooth, cartoon, anime"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft wash, paper texture, flowing colors, transparent, artistic, masterpiece, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges, oil painting"
    },
    "anime": {
        "prompt": "anime style, cel shading, vibrant colors, anime art, masterpiece, best quality, 2d illustration, manga style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "sketch": {
        "prompt": "pencil sketch, graphite drawing, fine lines, cross-hatching, monochrome, black and white, masterpiece, high quality",
        "negative": "photorealistic, color, 3d render, smooth, oil painting"
    },
    "impressionist": {
        "prompt": "impressionist painting, soft brushstrokes, vibrant colors, light effects, masterpiece, claude monet style, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges"
    },
    "pixel_art": {
        "prompt": "pixel art, retro game style, 8-bit, blocky, colorful, masterpiece, high quality",
        "negative": "photorealistic, 3d render, smooth, blurry, oil painting"
    },
    "cyberpunk": {
        "prompt": "cyberpunk style, neon colors, futuristic, glowing lights, dark atmosphere, sci-fi, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, blurry"
    },
    "vintage": {
        "prompt": "vintage photo style, retro, film grain, warm tones, nostalgic, old photo, masterpiece, high quality",
        "negative": "digital art, 3d render, photorealistic, ugly, deformed"
    }
}


class StyleTransfer:
    """风格转换技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "style_transfer"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== 初始化底层引擎 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  ✅ 底层 ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  底层引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"StyleTransfer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  预设风格: {len(STYLE_PRESETS)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.75,  # 风格转换需要高强度重绘来释放质感
            'default_style': 'oil_painting',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(STYLE_PRESETS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行风格转换"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            style = kwargs.get('style', self.config.get('default_style', 'oil_painting'))
            if style not in STYLE_PRESETS:
                return {"status": "error", "error": f"未知风格: {style}，可用: {list(STYLE_PRESETS.keys())}"}

            style_config = STYLE_PRESETS[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.75))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{style}_{timestamp}.png")

            logger.info(f"风格: {style}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 HED 提取软边缘，配合 Lineart 模型锁死构图
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",
                controlnet_model="lineart",
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "style": style,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "lineart"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<StyleTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="风格转换工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--style", "-s", default="oil_painting",
                        choices=list(STYLE_PRESETS.keys()), help="风格")
    parser.add_argument("--strength", type=float, default=0.75, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = StyleTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))