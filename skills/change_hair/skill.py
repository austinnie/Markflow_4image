# skills/change_hair/skill.py
"""
换发型/发色 Skill - 保持姿态和脸部不变，改变发型
复用通用 ControlNet 引擎（HED + Lineart 锁脸锁发际线，精准换发色/发型）
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

# 发型预设
HAIR_STYLES = {
    "long_flowing": "long flowing hair, beautiful hair, silky smooth, masterpiece",
    "curly": "curly hair, beautiful curls, voluminous hair, masterpiece",
    "short_bob": "short bob haircut, stylish hair, chic, masterpiece",
    "ponytail": "high ponytail hairstyle, sleek hair, masterpiece",
    "braid": "braided hair, beautiful braid, masterpiece",
    "bun": "hair bun, elegant hairstyle, updo, masterpiece",
    "wave": "wavy hair, beautiful waves, soft hair, masterpiece",
    "straight": "straight hair, sleek, smooth, masterpiece"
}

HAIR_COLORS = {
    "black": "black hair",
    "blonde": "blonde hair, golden hair",
    "brown": "brown hair, chestnut hair",
    "red": "red hair, auburn hair",
    "pink": "pink hair, pastel pink",
    "blue": "blue hair, vibrant blue",
    "silver": "silver hair, white hair",
    "purple": "purple hair, violet"
}


class ChangeHair:
    """换发型技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_hair"
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

        logger.info(f"ChangeHair v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.45,  # 换发色强度不能太高，否则脸部会崩
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(HAIR_STYLES.keys()), "colors": list(HAIR_COLORS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行换发型"""
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

            hair_style = kwargs.get('hair_style')
            hair_color = kwargs.get('hair_color')

            # 构建提示词
            prompt_parts = []
            if hair_style and hair_style in HAIR_STYLES:
                prompt_parts.append(HAIR_STYLES[hair_style])
            if hair_color and hair_color in HAIR_COLORS:
                prompt_parts.append(HAIR_COLORS[hair_color])
            if not prompt_parts:
                prompt_parts = ["beautiful hair", "masterpiece"]

            prompt = kwargs.get('prompt') or (", ".join(prompt_parts) + ", masterpiece, high quality")
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.45))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                style_suffix = hair_style or "custom"
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_hair_{style_suffix}_{timestamp}.png")

            logger.info(f"发型: {hair_style or '自定义'}, 发色: {hair_color or '自定义'}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 HED 提取软边缘，锁定脸部轮廓和发际线
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
                "hair_style": hair_style,
                "hair_color": hair_color,
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
        return f"<ChangeHair(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="换发型工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--style", "-s", choices=list(HAIR_STYLES.keys()), help="发型")
    parser.add_argument("--color", "-c", choices=list(HAIR_COLORS.keys()), help="发色")
    parser.add_argument("--prompt", "-p", help="自定义提示词")
    parser.add_argument("--strength", type=float, default=0.45, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeHair(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        hair_style=args.style, hair_color=args.color, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))