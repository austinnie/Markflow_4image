# skills/change_perspective/skill.py
"""
改变视角 Skill - 改变图片的视角/景别（远景/中景/特写/俯视/仰视等）
复用通用 ControlNet 引擎（HED + Lineart 锁结构，高幅度重绘转视角）
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

PERSPECTIVE_PROMPTS = {
    "wide": {
        "prompt": "wide angle shot, expansive view, grand scale, wide perspective, masterpiece, high quality",
        "negative": "close-up, zoomed in, narrow, tight crop"
    },
    "close_up": {
        "prompt": "close-up shot, intimate, detailed, macro, masterpiece, high quality",
        "negative": "wide angle, far away, distant, zoomed out"
    },
    "aerial": {
        "prompt": "aerial view, birds eye view, top down, from above, majestic, masterpiece, high quality",
        "negative": "ground level, eye level, low angle"
    },
    "low_angle": {
        "prompt": "low angle shot, looking up, dramatic perspective, imposing, masterpiece, high quality",
        "negative": "high angle, top down, eye level"
    },
    "high_angle": {
        "prompt": "high angle shot, looking down, overview, dramatic, masterpiece, high quality",
        "negative": "low angle, ground level, eye level"
    },
    "eye_level": {
        "prompt": "eye level shot, natural perspective, neutral, balanced, masterpiece, high quality",
        "negative": "low angle, high angle, dramatic"
    }
}


class ChangePerspective:
    """改变视角技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_perspective"
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

        logger.info(f"ChangePerspective v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  视角类型: {list(PERSPECTIVE_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.75,
            'default_perspective': 'eye_level',
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_perspectives(self) -> Dict[str, Any]:
        return {"status": "success", "perspectives": list(PERSPECTIVE_PROMPTS.keys())}

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

            perspective = kwargs.get('perspective', self.config.get('default_perspective', 'eye_level'))
            if perspective not in PERSPECTIVE_PROMPTS:
                return {"status": "error", "error": f"未知视角: {perspective}，可用: {list(PERSPECTIVE_PROMPTS.keys())}"}

            p_config = PERSPECTIVE_PROMPTS[perspective]
            prompt = kwargs.get('prompt') or p_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or p_config.get('negative', self.config.get('default_negative'))

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
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_perspective_{perspective}_{timestamp}.png")

            logger.info(f"视角: {perspective}")
            logger.info(f"提示词: {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # 提取软边缘，保留原图构图
                controlnet_model="lineart",   # 使用本地 Lineart 模型
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "perspective": perspective,
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
        return f"<ChangePerspective(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="改变视角工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--perspective", "-p", default="eye_level",
                        choices=list(PERSPECTIVE_PROMPTS.keys()), help="视角类型")
    parser.add_argument("--strength", type=float, default=0.75, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangePerspective(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        perspective=args.perspective,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))