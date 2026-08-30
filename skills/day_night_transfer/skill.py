# skills/day_night_transfer/skill.py
"""
昼夜转换 Skill - 将图片从白天转为夜晚或反之
复用通用 ControlNet 引擎（MLSD + Depth 锁空间几何，完成光景转换）
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

TIME_MODES = {
    "day": {
        "prompt": "bright sunny day, natural sunlight, clear sky, vibrant, masterpiece, high quality",
        "negative": "night, dark, moonlight, stars, dim"
    },
    "night": {
        "prompt": "night scene, moonlight, stars, dark sky, soft lighting, mysterious, masterpiece, high quality",
        "negative": "day, sunlight, bright, sunny, daylight"
    },
    "sunset": {
        "prompt": "sunset, golden hour, warm orange sky, beautiful sunset, masterpiece, high quality",
        "negative": "night, dark, harsh sunlight"
    },
    "dawn": {
        "prompt": "dawn, early morning, soft light, sunrise, misty, peaceful, masterpiece, high quality",
        "negative": "night, harsh light, sunset"
    }
}


class DayNightTransfer:
    """昼夜转换技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "day_night_transfer"
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

        logger.info(f"DayNightTransfer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  模式: {list(TIME_MODES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_mode': 'night',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_modes(self) -> Dict[str, Any]:
        return {"status": "success", "modes": list(TIME_MODES.keys())}

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

            mode = kwargs.get('mode', self.config.get('default_mode', 'night'))
            if mode not in TIME_MODES:
                return {"status": "error", "error": f"未知模式: {mode}，可用: {list(TIME_MODES.keys())}"}

            mode_config = TIME_MODES[mode]
            prompt = kwargs.get('prompt') or mode_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or mode_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{mode}_{timestamp}.png")

            logger.info(f"模式: {mode}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 MLSD 提取几何线条 + 底层 Depth 模型，完美保持场景空间结构
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="MLSD",      # 提取建筑/景物直线
                controlnet_model="depth",      # 使用深度模型锁死空间关系
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "mode": mode,
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
        return f"<DayNightTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="昼夜转换工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--mode", "-m", default="night",
                        choices=list(TIME_MODES.keys()), help="模式")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = DayNightTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        mode=args.mode,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))