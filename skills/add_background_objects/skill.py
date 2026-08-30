# skills/add_background_objects/skill.py
"""
添加背景物体 Skill - 在图片背景中添加指定物体，绝不破坏前景人物
复用通用 ControlNet 引擎（MLSD + Depth 锁空间结构，低强度精准加物体）
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

OBJECT_PROMPTS = {
    "flowers": "adding flowers, beautiful bouquet, colorful flowers, garden, masterpiece, high quality",
    "trees": "adding trees, beautiful trees, nature, greenery, masterpiece, high quality",
    "vase": "adding a vase, beautiful ceramic vase, decorative, masterpiece, high quality",
    "lamp": "adding a lamp, warm light, beautiful lamp, interior, masterpiece, high quality",
    "painting": "adding a painting, beautiful painting on wall, art, masterpiece, high quality",
    "books": "adding books, stack of books, library, cozy, masterpiece, high quality",
    "candle": "adding candles, warm glow, candlelight, cozy, masterpiece, high quality",
    "clock": "adding a clock, beautiful clock, decorative, masterpiece, high quality",
    "sculpture": "adding a sculpture, beautiful art piece, statue, masterpiece, high quality",
    "mirror": "adding a mirror, elegant mirror, decorative, masterpiece, high quality"
}


class AddBackgroundObjects:
    """添加背景物体技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "add_background_objects"
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

        logger.info(f"AddBackgroundObjects v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  物体类型: {list(OBJECT_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.50,  # 添加背景物体强度不能太高，避免破坏前景
            'default_object': 'flowers',
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_objects(self) -> Dict[str, Any]:
        return {"status": "success", "objects": list(OBJECT_PROMPTS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
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

            obj = kwargs.get('object', self.config.get('default_object', 'flowers'))
            if obj not in OBJECT_PROMPTS:
                return {"status": "error", "error": f"未知物体: {obj}，可用: {list(OBJECT_PROMPTS.keys())}"}

            obj_prompt = OBJECT_PROMPTS[obj]
            prompt = kwargs.get('prompt') or obj_prompt
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.50))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_add_{obj}_{timestamp}.png")

            logger.info(f"添加物体: {obj}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 MLSD（背景直线）+ Depth（深度空间），在不破坏前景的情况下添加物体
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="MLSD",
                controlnet_model="depth",
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "object": obj,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "depth"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<AddBackgroundObjects(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="添加背景物体工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--object", "-obj", default="flowers",
                        choices=list(OBJECT_PROMPTS.keys()), help="物体类型")
    parser.add_argument("--strength", type=float, default=0.50, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = AddBackgroundObjects(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        object=args.object,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))