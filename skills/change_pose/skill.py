
# skills/change_pose/skill.py
"""
改变人物姿态 Skill - 基于 ControlNet OpenPose
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

try:
    from skills.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 引擎不可用: {e}")

POSE_PROMPTS = {
    "standing": "standing upright, full body, straight posture, arms relaxed, looking forward, masterpiece, high quality",
    "sitting": "sitting on a chair, relaxed posture, legs together, hands on knees, looking at viewer, masterpiece, high quality",
    "lying": "lying down on bed, sideways, relaxed, peaceful expression, comfortable, masterpiece, high quality",
    "side_lying": "lying on side, one arm supporting head, elegant pose, relaxed, masterpiece, high quality",
    "kneeling": "kneeling on the ground, looking up, elegant posture, masterpiece, high quality",
    "walking": "walking forward, dynamic motion, one foot raised, confident stride, masterpiece, high quality",
    "running": "running, dynamic action, arms swinging, energetic, motion, masterpiece, high quality",
    "dancing": "dancing, elegant motion, arms raised, graceful, dynamic, masterpiece, high quality",
    "squatting": "squatting down, casual posture, relaxed, masterpiece, high quality",
    "jumping": "jumping in the air, dynamic, energetic, full extension, masterpiece, high quality",
}


class ChangePose:
    """改变人物姿态技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_pose"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  ✅ ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangePose v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  姿态类型: {list(POSE_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.65,
            'default_pose': 'standing',
            'default_controlnet_type': 'openpose',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}"}

            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))
            if pose not in POSE_PROMPTS:
                return {"status": "error", "error": f"未知姿态: {pose}，可用: {list(POSE_PROMPTS.keys())}"}

            pose_config = POSE_PROMPTS[pose]
            prompt = kwargs.get('prompt') or pose_config
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.65))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_pose_{pose}_{timestamp}.png")

            logger.info(f"目标姿态: {pose}")
            logger.info(f"提示词: {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                controlnet_type="openpose",
                controlnet_strength=1.0,
                strength=strength,
                steps=steps,
                seed=seed,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('output_path', output_path),
                "pose": pose,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "controlnet": "openpose"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ChangePose(name={self.name}, version={self.version})>"

# 在 skill.py 末尾添加（在 if __name__ == "__main__" 之前）

# 在 skill.py 末尾添加（在 if __name__ == "__main__" 之前）

def run_all_poses(image_path: str, **kwargs):
    """
    对所有姿态类型运行 ChangePose 技能
    
    Args:
        image_path: 输入图片路径
        **kwargs: 其他参数 (strength, steps, seed, output_dir 等)
    
    Returns:
        dict: 包含所有姿态运行结果的字典
    """
    skill = ChangePose()
    results = {}
    
    # 获取所有姿态类型
    all_poses = list(POSE_PROMPTS.keys())
    
    # 设置输出目录 - 修复 None 问题
    output_dir = kwargs.get('output_dir')
    if output_dir is None:
        output_dir = skill.output_dir / "all_poses"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取图片名称（不含扩展名）
    image_name = Path(image_path).stem
    
    print(f"🚀 开始批量生成 {len(all_poses)} 种姿态...")
    print(f"📁 输出目录: {output_dir}")
    print(f"🖼️  输入图片: {image_path}")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for idx, pose in enumerate(all_poses, 1):
        print(f"\n[{idx}/{len(all_poses)}] 生成姿态: {pose}")
        
        # 构建输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{image_name}_{pose}_{timestamp}.png"
        
        try:
            # 执行姿态改变
            result = skill.execute(
                image_path=image_path,
                pose=pose,
                prompt=kwargs.get('prompt'),  # None 表示使用默认预设提示词
                negative_prompt=kwargs.get('negative_prompt'),
                strength=kwargs.get('strength', 0.65),
                steps=kwargs.get('steps', 30),
                seed=kwargs.get('seed', -1) if kwargs.get('seed') else -1,
                output_path=str(output_path)
            )
            
            if result['status'] == 'success':
                print(f"  ✅ 成功! 输出: {result['output_path']}")
                print(f"  ⏱️  耗时: {result['generation_time']}")
                success_count += 1
            else:
                print(f"  ❌ 失败: {result.get('error', '未知错误')}")
                fail_count += 1
                
            results[pose] = result
            
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results[pose] = {"status": "error", "error": str(e)}
            fail_count += 1
    
    # 打印总结
    print("\n" + "=" * 60)
    print(f"📊 批量生成完成!")
    print(f"  ✅ 成功: {success_count}/{len(all_poses)}")
    print(f"  ❌ 失败: {fail_count}/{len(all_poses)}")
    print(f"  📁 输出目录: {output_dir}")
    
    # 保存结果摘要到 JSON
    summary_path = output_dir / "generation_summary.json"
    summary_data = {
        "input_image": image_path,
        "total_poses": len(all_poses),
        "success_count": success_count,
        "fail_count": fail_count,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"  📄 摘要已保存: {summary_path}")
    
    return results


# 修改命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Change Pose Skill')
    parser.add_argument('--image_path', required=True, help='输入图片路径')
    parser.add_argument('--pose', default='standing', help='目标姿态 (如需所有姿态，使用 --all)')
    parser.add_argument('--all', action='store_true', help='批量生成所有姿态')
    parser.add_argument('--strength', type=float, default=0.65, help='强度 (0-1)')
    parser.add_argument('--steps', type=int, default=30, help='步数')
    parser.add_argument('--seed', type=int, default=-1, help='随机种子')
    parser.add_argument('--output_dir', help='输出目录 (仅 --all 模式有效)')
    
    args = parser.parse_args()
    
    if args.all:
        # 批量运行所有姿态
        results = run_all_poses(
            image_path=args.image_path,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed,
            output_dir=args.output_dir
        )
    else:
        # 运行单个姿态
        skill = ChangePose()
        result = skill.execute(
            image_path=args.image_path,
            pose=args.pose,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed
        )
        print(json.dumps(result, indent=2))