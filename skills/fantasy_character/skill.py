# skills/fantasy_character/skill.py
"""
奇幻角色 Skill - 将人物变成奇幻角色（精灵/天使/恶魔/魔法师等）
复用通用 ControlNet 引擎（OpenPose锁姿态，高幅度重绘转奇幻风）
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

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"torch 或 PIL 未安装: {e}")

# ==================== 引入通用引擎（方案1） ====================
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"通用 ControlNet 引擎不可用: {e}")

# 奇幻角色提示词配置
FANTASY_PROMPTS = {
    "elf": {
        "prompt": "beautiful elf, long pointed ears, fantasy elf, elegant, magical, nature, fantasy character, masterpiece, high quality, detailed",
        "negative": "ugly, deformed, human, modern, realistic, bad anatomy"
    },
    "angel": {
        "prompt": "beautiful angel, white feathered wings, golden halo, divine, ethereal, heavenly, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, demon, devil, dark, evil"
    },
    "demon": {
        "prompt": "beautiful demon, curved horns, dark bat wings, seductive, dark fantasy, hellfire, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, angel, holy, light, pure"
    },
    "mage": {
        "prompt": "powerful mage, wizard, magical robes, staff, spellcasting, arcane energy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, realistic, casual"
    },
    "knight": {
        "prompt": "majestic knight, full plate armor, fantasy knight, sword, shield, heroic, noble, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, casual, civilian"
    },
    "fairy": {
        "prompt": "beautiful fairy, translucent wings, glowing, magical, ethereal, nature spirit, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "vampire": {
        "prompt": "elegant vampire, pale skin, sharp fangs, gothic, aristocratic, dark fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cheerful"
    },
    "merfolk": {
        "prompt": "beautiful mermaid, fish tail, underwater, coral, seashells, aquatic fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, legs"
    },
    "dragonborn": {
        "prompt": "dragonborn character, dragon scales, reptilian features, fantasy, powerful, elemental, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "phoenix": {
        "prompt": "phoenix themed character, fiery, reborn, majestic, golden flames, fantasy, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cold"
    }
}


class FantasyCharacter:
    """奇幻角色技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = Path(self.config.get('output_dir', self.skill_dir / 'output'))
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

        logger.info(f"FantasyCharacter v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  奇幻类型: {list(FANTASY_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.8,
            'default_type': 'elf',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality, modern, realistic, human',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def get_available_types(self) -> Dict[str, str]:
        return {k: v['prompt'][:50] + '...' for k, v in FANTASY_PROMPTS.items()}

    def get_type_info(self, fantasy_type: str) -> Optional[Dict[str, str]]:
        return FANTASY_PROMPTS.get(fantasy_type)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行奇幻角色转换"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} v{self.version}")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "缺少 image_path 参数"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            # 2. 获取参数
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_PROMPTS:
                return {
                    "status": "error",
                    "error": f"未知奇幻类型: {fantasy_type}，可用: {list(FANTASY_PROMPTS.keys())}"
                }

            f_config = FANTASY_PROMPTS[fantasy_type]
            prompt = kwargs.get('prompt') or f_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or f_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== 直接调用底层引擎 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "底层 ControlNet 引擎不可用"}

            # 默认输出到本技能目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = kwargs.get('output_path') or str(self.output_dir / f"{fantasy_type}_{timestamp}.png")

            logger.info(f"奇幻类型: {fantasy_type}")
            logger.info(f"提示词: {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # 提取人体骨架
                controlnet_model="openpose",    # 锁死人体姿态，防止奇幻化导致崩坏
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            # 保存元数据
            metadata = {
                'skill': self.name,
                'version': self.version,
                'fantasy_type': fantasy_type,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'steps': steps,
                'strength': strength,
                'seed': seed,
                'output_path': output_path,
                'timestamp': timestamp,
                'use_controlnet': True,
            }

            metadata_path = Path(output_path).with_suffix('.meta.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "metadata_path": str(metadata_path),
                "fantasy_type": fantasy_type,
                "seed": seed,
                "elapsed_time": time.time() - start_time,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"执行失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    def batch_process(self, image_paths: List[str], fantasy_type: str = 'elf', **kwargs) -> List[Dict[str, Any]]:
        """批量处理多张图片"""
        results = []
        total = len(image_paths)
        for idx, img_path in enumerate(image_paths):
            logger.info(f"处理 {idx+1}/{total}: {img_path}")
            result = self.execute(
                image_path=img_path,
                fantasy_type=fantasy_type,
                **kwargs
            )
            results.append({'image': img_path, 'result': result})
            if idx < total - 1:
                time.sleep(0.5)
        return results

    def __repr__(self) -> str:
        return f"<FantasyCharacter skill v{self.version} on {self.device}>"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='奇幻角色生成器 v2.0 - 将人物照片转换为奇幻角色',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''可用的奇幻类型: {', '.join(FANTASY_PROMPTS.keys())}'''
    )
    
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-t', '--type', default='elf', choices=list(FANTASY_PROMPTS.keys()), help='奇幻类型 (默认: elf)')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-s', '--steps', type=int, default=35, help='推理步数')
    parser.add_argument('-r', '--strength', type=float, default=0.8, help='变换强度 0.0-1.0')
    parser.add_argument('--seed', type=int, default=-1, help='随机种子')
    parser.add_argument('--prompt', help='自定义提示词')
    parser.add_argument('--negative', help='自定义负面提示词')
    parser.add_argument('--list-types', action='store_true', help='列出所有奇幻类型')
    
    args = parser.parse_args()
    
    if args.list_types:
        print("可用的奇幻类型:")
        for t in FANTASY_PROMPTS.keys():
            print(f"  - {t}")
        sys.exit(0)
    
    skill = FantasyCharacter()
    result = skill.execute(
        image_path=args.image,
        fantasy_type=args.type,
        output_dir=args.output,
        steps=args.steps,
        strength=args.strength,
        seed=args.seed,
        prompt=args.prompt,
        negative_prompt=args.negative,
    )
    
    if result['status'] == 'success':
        print(f"\n✅ 生成成功!")
        print(f"  输出: {result['output_path']}")
        print(f"  类型: {result['fantasy_type']}")
        print(f"  种子: {result['seed']}")
        print(f"  耗时: {result['elapsed_time']:.2f}s")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")
        sys.exit(1)