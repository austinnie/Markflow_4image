"""
fix_human_anatomy - 修复人物畸形
修复 AI 生成图片中常见的人物畸形问题：
- 手部畸形（多指、少指、手指错乱）
- 肢体扭曲
- 面部不对称
- 身体比例失调

支持两种模式：
1. 自动修复：使用 ControlNet + 重绘
2. 手动修复：使用 Inpainting 局部重绘
"""

import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
from markflow.utils.model_config import get_model_config

logger = logging.getLogger(__name__)


class FixHumanAnatomy:
    """修复人物畸形技能"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "FixHumanAnatomy"
        self.version = "1.0.0"
        self.sd_config = get_model_config()
        
        # 修复强度映射
        self.REPAIR_LEVELS = {
            'light': {'strength': 0.35, 'steps': 20, 'description': '轻度修复（微调）'},
            'medium': {'strength': 0.55, 'steps': 30, 'description': '中度修复（推荐）'},
            'heavy': {'strength': 0.75, 'steps': 40, 'description': '重度修复（大幅重绘）'},
        }
        
        # 畸形类型提示词
        self.DEFORMITY_PROMPTS = {
            'hands': {
                'prompt': 'perfect hands, five fingers, natural hand pose, detailed fingers, realistic hands, beautiful hands, proper anatomy',
                'negative': 'bad hands, missing fingers, extra fingers, distorted hands, fused fingers, mangled hands, deformed hands, mutant hands',
                'description': '手部修复'
            },
            'face': {
                'prompt': 'beautiful face, symmetrical face, perfect facial features, clear eyes, natural expression, realistic face, flawless skin',
                'negative': 'ugly face, deformed face, asymmetrical face, distorted face, blurry face, bad facial features, mutant face',
                'description': '面部修复'
            },
            'body': {
                'prompt': 'perfect body proportions, natural pose, realistic anatomy, symmetrical body, beautiful body, proper proportions',
                'negative': 'bad anatomy, distorted body, asymmetrical body, deformed body, mutant body, extra limbs, missing limbs',
                'description': '身体修复'
            },
            'full': {
                'prompt': 'perfect human anatomy, beautiful face, perfect hands, natural pose, realistic proportions, symmetrical body, high quality, masterpiece',
                'negative': 'bad anatomy, distorted body, deformed, ugly, bad hands, extra fingers, missing fingers, asymmetrical, mutant, disfigured',
                'description': '全身修复'
            },
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行人物畸形修复
        
        Args:
            image_path: 输入图片路径（必填）
            deformity_type: 畸形类型 (hands/face/body/full) 默认 full
            repair_level: 修复强度 (light/medium/heavy) 默认 medium
            output_path: 输出路径（可选）
            prompt: 自定义提示词（可选）
            negative_prompt: 自定义负向提示词（可选）
            strength: 重绘强度（可选，覆盖 repair_level）
            steps: 迭代步数（可选）
            cfg_scale: CFG Scale（可选）
            seed: 随机种子（可选）
            batch: 生成多张候选（可选）
            device: 设备 (cpu/cuda)
        
        Returns:
            执行结果
        """
        # ========== 1. 获取参数 ==========
        image_path = kwargs.get("image_path")
        if not image_path:
            return {
                "status": "error",
                "error": "缺少必要参数: image_path",
                "skill": self.name
            }
        
        if not Path(image_path).exists():
            return {
                "status": "error",
                "error": f"图片不存在: {image_path}",
                "skill": self.name
            }
        
        deformity_type = kwargs.get("deformity_type", "full")
        repair_level = kwargs.get("repair_level", "medium")
        output_path = kwargs.get("output_path")
        custom_prompt = kwargs.get("prompt")
        custom_negative = kwargs.get("negative_prompt")
        strength = kwargs.get("strength")
        steps = kwargs.get("steps")
        cfg_scale = kwargs.get("cfg_scale", 7.5)
        seed = kwargs.get("seed", -1)
        batch = kwargs.get("batch", 1)
        device = kwargs.get("device", "cpu")
        verbose = kwargs.get("verbose", False)
        
        # ========== 2. 验证参数 ==========
        if deformity_type not in self.DEFORMITY_PROMPTS:
            deformity_type = "full"
        
        if repair_level not in self.REPAIR_LEVELS:
            repair_level = "medium"
        
        # ========== 3. 获取修复配置 ==========
        repair_config = self.REPAIR_LEVELS[repair_level]
        deformity_config = self.DEFORMITY_PROMPTS[deformity_type]
        
        # 确定最终参数
        final_strength = strength if strength is not None else repair_config['strength']
        final_steps = steps if steps is not None else repair_config['steps']
        final_prompt = custom_prompt if custom_prompt else deformity_config['prompt']
        final_negative = custom_negative if custom_negative else deformity_config['negative']
        
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        # ========== 4. 生成输出路径 ==========
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_name = Path(image_path).stem
            output_dir = Path("./output/fixed_anatomy")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{input_name}_fixed_{deformity_type}_{timestamp}.png")
        else:
            output_path = str(Path(output_path))
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # ========== 5. 打印信息 ==========
        print(f"\n{'='*60}")
        print(f"🔧 修复人物畸形")
        print(f"{'='*60}")
        print(f"📷 输入图片: {image_path}")
        print(f"📤 输出路径: {output_path}")
        print(f"📌 畸形类型: {deformity_type} - {deformity_config['description']}")
        print(f"📌 修复强度: {repair_level} - {repair_config['description']}")
        print(f"⚙️  参数: strength={final_strength}, steps={final_steps}, cfg={cfg_scale}")
        print(f"🌱 种子: {seed}")
        print(f"📦 模型: {self.sd_config.get('model_name', '未设置')}")
        print(f"💻 设备: {device}")
        print('='*60)
        
        if verbose:
            print(f"📝 提示词: {final_prompt[:100]}...")
            print(f"🚫 负向词: {final_negative[:100]}...")
        
        # ========== 6. 执行修复 ==========
        results = []
        success_count = 0
        
        for i in range(batch):
            if batch > 1:
                print(f"\n--- [{i+1}/{batch}] ---")
                current_seed = seed + i if seed != -1 else random.randint(0, 2**32 - 1)
            else:
                current_seed = seed
            
            # 生成输出文件名
            if batch > 1:
                batch_output = str(Path(output_path).parent / 
                    f"{Path(output_path).stem}_{i+1:02d}{Path(output_path).suffix}")
            else:
                batch_output = output_path
            
            try:
                result = execute_skill(
                    "sd_image_generator",
                    image_path=image_path,
                    prompt=final_prompt,
                    negative_prompt=final_negative,
                    strength=final_strength,
                    steps=final_steps,
                    cfg_scale=cfg_scale,
                    seed=current_seed,
                    width=kwargs.get("width", 768),
                    height=kwargs.get("height", 1024),
                    output_path=batch_output,
                    device=device,
                    controlnet_type="openpose",
                    use_controlnet=True
                )
                
                if result and isinstance(result, dict) and result.get('status') == 'success':
                    image_paths = result.get('image_paths', [batch_output])
                    print(f"✅ 修复成功: {image_paths[0]}")
                    success_count += 1
                    results.append({
                        'index': i + 1,
                        'seed': current_seed,
                        'output': image_paths[0],
                        'success': True
                    })
                else:
                    error = result.get('error', '未知错误') if isinstance(result, dict) else str(result)
                    print(f"❌ 修复失败: {error}")
                    results.append({
                        'index': i + 1,
                        'seed': current_seed,
                        'error': error,
                        'success': False
                    })
                    
            except Exception as e:
                print(f"❌ 修复异常: {e}")
                results.append({
                    'index': i + 1,
                    'seed': current_seed,
                    'error': str(e),
                    'success': False
                })
            
            time.sleep(0.5)
        
        # ========== 7. 返回结果 ==========
        print(f"\n{'='*60}")
        print(f"📊 修复完成! 成功: {success_count}/{batch}")
        print('='*60)
        
        return {
            "status": "success" if success_count > 0 else "error",
            "skill": self.name,
            "version": self.version,
            "deformity_type": deformity_type,
            "repair_level": repair_level,
            "strength": final_strength,
            "steps": final_steps,
            "seed": seed,
            "batch": batch,
            "success_count": success_count,
            "results": results,
            "output_paths": [r['output'] for r in results if r.get('success')],
            "metadata": {
                "input_image": image_path,
                "output_path": output_path,
                "executed_at": datetime.now().isoformat()
            }
        }
    
    def __repr__(self):
        return f"<FixHumanAnatomy(version={self.version})>"


# ==================== 独立运行入口 ====================

def main():
    """独立运行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="修复人物畸形 - 修复 AI 生成图片中的手部、面部、身体畸形",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法 - 自动修复全身畸形
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg

  # 只修复手部
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --type hands

  # 只修复面部
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --type face

  # 重度修复（更强效果）
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --level heavy

  # 生成多张候选（选择最好的）
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --batch 3

  # 自定义提示词
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --prompt "perfect hands, beautiful face" --negative "bad anatomy"

  # 指定输出路径
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --output output/fixed.png

  # 使用 GPU
  python skills/fix_human_anatomy/skill.py --image_path input/girl.jpg --device cuda
        """
    )
    
    parser.add_argument("--image_path", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--type", "-t", default="full", 
                       choices=["hands", "face", "body", "full"],
                       help="畸形类型: hands(手部), face(面部), body(身体), full(全身) (默认: full)")
    parser.add_argument("--level", "-l", default="medium",
                       choices=["light", "medium", "heavy"],
                       help="修复强度: light(轻度), medium(中度), heavy(重度) (默认: medium)")
    parser.add_argument("--prompt", "-p", help="自定义提示词")
    parser.add_argument("--negative", "-n", help="自定义负向提示词")
    parser.add_argument("--strength", "-s", type=float, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, help="迭代步数")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG Scale (默认: 7.5)")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--batch", "-b", type=int, default=1, help="生成多张候选 (默认: 1)")
    parser.add_argument("--device", "-d", default="cpu", choices=["cpu", "cuda"], help="设备 (默认: cpu)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    # 执行修复
    skill = FixHumanAnatomy()
    result = skill.execute(
        image_path=args.image_path,
        output_path=args.output,
        deformity_type=args.type,
        repair_level=args.level,
        prompt=args.prompt,
        negative_prompt=args.negative,
        strength=args.strength,
        steps=args.steps,
        cfg_scale=args.cfg,
        seed=args.seed,
        batch=args.batch,
        device=args.device,
        verbose=args.verbose
    )
    
    # 输出结果
    if result.get('status') == 'success':
        print(f"\n✅ 修复完成!")
        for path in result.get('output_paths', []):
            print(f"   📁 {path}")
    else:
        print(f"\n❌ 修复失败: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()