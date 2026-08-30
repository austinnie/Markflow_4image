# skills/change_background/skill.py
"""
换背景 Skill - 保持人物不变，替换背景
复用通用 ControlNet 引擎（MLSD + Depth 锁空间结构，低强度精准换背景）
"""

import os
import sys
import json
import time
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

try:
    import torch
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")


class ChangeBackground:
    """换背景技能 v2.0"""

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

        logger.info(f"ChangeBackground v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  预设背景: {len(self.PRESET_BACKGROUNDS)} 种")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.55,  # 换背景不能让前景人物变形
            'default_prompt': 'beautiful natural background, masterpiece, high quality',
            'default_negative': 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config.get('output_dir', str(self.skill_dir / 'output'))).mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> Dict[str, Any]:
        return {"status": "success", "presets": self.PRESET_BACKGROUNDS, "count": len(self.PRESET_BACKGROUNDS)}

    # ==================== 主执行方法 ====================
    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            output_path = kwargs.get('output_path')
            background_prompt = kwargs.get('background_prompt')
            preset = kwargs.get('preset')

            if preset and preset in self.PRESET_BACKGROUNDS:
                background_prompt = self.PRESET_BACKGROUNDS[preset]
                logger.info(f"  使用预设背景: {preset}")

            if not background_prompt:
                background_prompt = self.config.get('default_prompt', 'beautiful natural background, masterpiece, high quality')

            prompt = background_prompt
            negative_prompt = kwargs.get('negative_prompt', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.55))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                preset_suffix = f"_{preset}" if preset else ""
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{timestamp}_bg{preset_suffix}.png")

            logger.info(f"处理: {os.path.basename(abs_image_path)} ({Image.open(abs_image_path).size})")
            logger.info(f"背景描述: {background_prompt[:80]}...")

            # 使用 MLSD (提取场景直线) + Depth (锁空间深度)，配合低强度换背景
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",  # ✅ 从 "MLSD" 改为 "HED"
                controlnet_model="depth",  # 或 "canny"
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "parameters": {
                    "image_path": str(abs_image_path),
                    "background_prompt": background_prompt,
                    "preset": preset,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
                    "controlnet": True,
                    "controlnet_type": "depth"
                },
                "generation_time": f"{time.time() - start_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e), "skill": self.name}

    def __repr__(self):
        return f"<ChangeBackground(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="换背景工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--preset", "-p", choices=list(ChangeBackground.PRESET_BACKGROUNDS.keys()),
                        help="预设背景名称")
    parser.add_argument("--prompt", help="自定义背景描述提示词")
    parser.add_argument("--strength", "-s", type=float, default=0.55, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")

    args = parser.parse_args()

    skill = ChangeBackground(config={'device': args.device})

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        preset=args.preset,
        background_prompt=args.prompt,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed
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