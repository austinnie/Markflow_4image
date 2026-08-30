# skills/weather_transfer/skill.py
"""
天气转换 Skill - 将图片转换为不同天气 (晴/雨/雪/雾)
复用通用 ControlNet 引擎（MLSD + Depth 锁空间结构，转换天气氛围）
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

WEATHERS = {
    "sunny": {
        "prompt": "bright sunny day, clear sky, warm sunlight, beautiful weather, masterpiece, high quality",
        "negative": "rain, snow, fog, dark, cloudy"
    },
    "rainy": {
        "prompt": "rainy day, rain drops, wet ground, cloudy sky, peaceful, atmosphere, masterpiece, high quality",
        "negative": "sunny, snow, clear sky, dry"
    },
    "snowy": {
        "prompt": "snowy day, snow falling, white landscape, cold, beautiful winter, masterpiece, high quality",
        "negative": "rain, sunny, green, warm"
    },
    "foggy": {
        "prompt": "foggy day, mist, soft atmosphere, mysterious, ethereal, masterpiece, high quality",
        "negative": "sunny, clear sky, bright"
    },
    "stormy": {
        "prompt": "stormy weather, dark clouds, lightning, dramatic, atmospheric, masterpiece, high quality",
        "negative": "sunny, clear sky, calm"
    },
    "cloudy": {
        "prompt": "cloudy day, overcast sky, soft light, peaceful, atmosphere, masterpiece, high quality",
        "negative": "sunny, clear sky, rain"
    }
}


class WeatherTransfer:
    """天气转换技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "weather_transfer"
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

        logger.info(f"WeatherTransfer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  天气: {list(WEATHERS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_weather': 'sunny',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_weathers(self) -> Dict[str, Any]:
        return {"status": "success", "weathers": list(WEATHERS.keys())}

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

            weather = kwargs.get('weather', self.config.get('default_weather', 'sunny'))
            if weather not in WEATHERS:
                return {"status": "error", "error": f"未知天气: {weather}，可用: {list(WEATHERS.keys())}"}

            weather_config = WEATHERS[weather]
            prompt = kwargs.get('prompt') or weather_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or weather_config['negative']

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
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{weather}_{timestamp}.png")

            logger.info(f"天气: {weather}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 MLSD（提取场景直线）+ Depth（锁空间深度），转换天气
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
                "weather": weather,
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
        return f"<WeatherTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="天气转换工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--weather", "-w", default="sunny",
                        choices=list(WEATHERS.keys()), help="天气")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = WeatherTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        weather=args.weather,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))