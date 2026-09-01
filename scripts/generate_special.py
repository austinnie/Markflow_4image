#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特殊内容文生图/图生图批量生成器（增强版）
支持自定义提示词、参数、输入图片

用法：
  python scripts/generate_special.py --list                           # 列出所有模板
  python scripts/generate_special.py --template bedroom_nude         # 生成指定模板
  python scripts/generate_special.py --template bedroom_nude --image_path input/girl.jpg  # 图生图
  python scripts/generate_special.py --template bedroom_nude --prompt "自定义提示词" --steps 40
  python scripts/generate_special.py --all                           # 生成所有模板
  python scripts/generate_special.py --batch 5 --template studio_nude # 批量生成5张
"""

import sys
import os
import json
import argparse
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目根目录
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
from markflow.utils.model_config import get_model_config


# ==================== 模板定义 ====================

TEMPLATES = {
    # ===== 卧室系列 =====
    "bedroom_nude": {
        "name": "卧室裸露",
        "category": "卧室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, realistic skin texture, lying on a large bed, soft mattress, white sheets, sideways, relaxed pose, one hand on chest, bedroom background, soft lighting, warm atmosphere, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    "bedroom_lingerie": {
        "name": "卧室唯美内衣",
        "category": "卧室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, white lace lingerie, delicate lace, elegant, lying on a large bed, soft mattress, white sheets, sideways, relaxed pose, bedroom background, soft lighting, warm atmosphere, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    
    # ===== 海滩系列 =====
    "beach_nude": {
        "name": "海滩裸露",
        "category": "海滩",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, standing on a beautiful sandy beach, ocean waves in background, confident posture, hands on hips, beach background, sunny day, golden sunlight, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 1024, "height": 768, "steps": 30, "cfg_scale": 7.0}
    },
    "beach_lingerie": {
        "name": "海滩唯美内衣",
        "category": "海滩",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, white lace lingerie, delicate lace, elegant, standing on a beautiful sandy beach, ocean waves in background, confident posture, beach background, sunny day, golden sunlight, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 1024, "height": 768, "steps": 30, "cfg_scale": 7.0}
    },
    
    # ===== 工作室系列 =====
    "studio_nude": {
        "name": "工作室裸露",
        "category": "工作室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, realistic skin texture, standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    "studio_lingerie": {
        "name": "工作室唯美内衣",
        "category": "工作室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, black silk lingerie, glossy silk, sophisticated, standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    
    # ===== 泳池系列 =====
    "pool_nude": {
        "name": "泳池裸露",
        "category": "泳池",
        "prompt": "1girl, full body, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, wet skin, water droplets on skin, standing in pool, water up to waist, swimming pool background, blue water, bright sunlight, sparkling water, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    "pool_lingerie": {
        "name": "泳池唯美内衣",
        "category": "泳池",
        "prompt": "1girl, full body, beautiful face, perfect body, large bust, hourglass figure, pink satin lingerie, soft satin, romantic, standing in pool, water up to waist, swimming pool background, blue water, bright sunlight, sparkling water, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    
    # ===== 浴室系列 =====
    "bathroom_nude": {
        "name": "浴室裸露",
        "category": "浴室",
        "prompt": "1girl, full body, beautiful face, perfect body, large bust, hourglass figure, nude, naked, beautiful skin, wet skin, water droplets, standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    "bathroom_lingerie": {
        "name": "浴室唯美内衣",
        "category": "浴室",
        "prompt": "1girl, full body, beautiful face, perfect body, large bust, hourglass figure, blue lace lingerie, delicate lace, elegant, standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, high quality, masterpiece, 8k, photorealistic",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    
    # ===== 油画系列 =====
    "oil_painting_classical": {
        "name": "古典油画裸体",
        "category": "油画",
        "prompt": "1girl, full body, nude, oil painting, canvas texture, classical oil painting, Renaissance style, soft chiaroscuro, warm earth tones, standing upright, classical contrapposto, studio lighting, soft shadows, artistic, fine art, high quality, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, 3d render, plastic",
        "params": {"width": 768, "height": 1024, "steps": 35, "cfg_scale": 7.5}
    },
    "oil_painting_realistic": {
        "name": "写实油画裸体",
        "category": "油画",
        "prompt": "1girl, full body, nude, oil painting, canvas texture, photorealistic oil painting, ultra detailed, smooth blending, lifelike skin texture, reclining on couch, elegant pose, warm golden lighting, intimate atmosphere, artistic, fine art, high quality, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, 3d render, plastic",
        "params": {"width": 1024, "height": 768, "steps": 35, "cfg_scale": 7.5}
    },
    
    # ===== 雕塑系列 =====
    "sculpture_marble": {
        "name": "大理石雕塑裸体",
        "category": "雕塑",
        "prompt": "1girl, full body, nude, sculpture, 3D statue, white marble sculpture, smooth polished surface, translucent effect, classical Greek sculpture, idealized proportions, standing upright, elegant posture, pedestal, museum lighting, high quality, masterpiece, 8k, photorealistic 3D render",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, painting, drawing",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
    "sculpture_bronze": {
        "name": "青铜雕塑裸体",
        "category": "雕塑",
        "prompt": "1girl, full body, nude, sculpture, 3D statue, bronze sculpture, patina texture, greenish-brown tones, aged metal, Hellenistic sculpture, dramatic emotion, dynamic pose, pedestal, museum lighting, high quality, masterpiece, 8k, photorealistic 3D render",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, painting, drawing",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0}
    },
}


def get_sd_config():
    """获取 SD 配置"""
    cfg = get_model_config()
    return {
        "model_path": cfg.get("model_path"),
        "model_name": cfg.get("model_name"),
        "device": cfg.get("device", "cpu"),
        "steps": cfg.get("default_steps", 25),
        "cfg_scale": cfg.get("default_cfg", 7.5),
    }


class SpecialGenerator:
    """特殊内容生成器（增强版）"""
    
    def __init__(self, output_dir: str = "./output/special"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sd_config = get_sd_config()
        
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📦 当前模型: {self.sd_config.get('model_name', '未设置')}")
        print(f"💻 设备: {self.sd_config.get('device', 'cpu')}")
        print()
    
    def list_templates(self):
        """列出所有模板"""
        print("\n" + "=" * 70)
        print("📋 可用模板列表")
        print("=" * 70)
        
        categories = {}
        for key, template in TEMPLATES.items():
            cat = template.get("category", "其他")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((key, template))
        
        for cat, items in categories.items():
            print(f"\n【{cat}】")
            for key, template in items:
                params = template.get('params', {})
                steps = params.get('steps', 30)
                cfg = params.get('cfg_scale', 7.0)
                print(f"  {key:<30} {template['name']:<20} (steps={steps}, cfg={cfg})")
        
        print("\n" + "=" * 70)
        print(f"共 {len(TEMPLATES)} 个模板")
        print("\n💡 使用: --template <模板名>")
        print("   python scripts/generate_special.py --template bedroom_nude")
        print("   python scripts/generate_special.py --template bedroom_nude --image_path input/girl.jpg")
    
    def generate_one(self, template_key: str, 
                     image_path: str = None,
                     custom_prompt: str = None,
                     custom_negative: str = None,
                     steps: int = None,
                     cfg_scale: float = None,
                     strength: float = None,
                     width: int = None,
                     height: int = None,
                     seed: int = None,
                     batch_size: int = 1) -> Dict:
        """
        生成单个模板（支持自定义参数覆盖）
        """
        if template_key not in TEMPLATES:
            return {"status": "error", "error": f"未知模板: {template_key}"}
        
        template = TEMPLATES[template_key]
        params = template.get("params", {})
        
        # 使用自定义参数或模板默认值
        prompt = custom_prompt if custom_prompt else template["prompt"]
        negative = custom_negative if custom_negative else template.get("negative", "")
        steps = steps if steps is not None else params.get("steps", self.sd_config.get("default_steps", 25))
        cfg_scale = cfg_scale if cfg_scale is not None else params.get("cfg_scale", self.sd_config.get("default_cfg", 7.5))
        width = width if width is not None else params.get("width", 512)
        height = height if height is not None else params.get("height", 768)
        strength = strength if strength is not None else 0.55
        
        # 处理种子
        if seed is None or seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        # 获取模型配置
        model_name = self.sd_config.get("model_name")
        
        print(f"\n{'='*60}")
        print(f"🎨 生成: {template['name']}")
        print(f"📝 模板: {template_key}")
        if image_path:
            print(f"📷 输入图片: {image_path}")
        print(f"📐 尺寸: {width}x{height}")
        print(f"⚙️  步数: {steps}, CFG: {cfg_scale}")
        if strength is not None:
            print(f"💪 强度: {strength}")
        print(f"🌱 种子: {seed}")
        print(f"📦 模型: {model_name}")
        print('='*60)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{template_key}_{seed}.png"
        output_path = str(self.output_dir / filename)
        
        # 构建参数
        skill_params = {
            "prompt": prompt,
            "negative_prompt": negative,
            "model_name": model_name,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "batch_size": batch_size,
            "output_path": output_path
        }
        
        # 如果有输入图片，添加图生图参数
        if image_path:
            skill_params["image_path"] = image_path
            skill_params["strength"] = strength
        
        try:
            result = execute_skill("sd_image_generator", **skill_params)
            
            if isinstance(result, dict) and result.get('status') == 'success':
                image_paths = result.get('image_paths', [output_path])
                print(f"\n✅ 生成成功!")
                for path in image_paths:
                    print(f"   📁 {path}")
                return {
                    "status": "success",
                    "template": template_key,
                    "name": template['name'],
                    "image_paths": image_paths,
                    "seed": seed
                }
            else:
                error = result.get('error', '未知错误') if isinstance(result, dict) else str(result)
                print(f"\n❌ 生成失败: {error}")
                return {"status": "error", "error": error, "template": template_key}
                
        except Exception as e:
            print(f"\n❌ 生成异常: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e), "template": template_key}
    
    def generate_all(self, **kwargs):
        """生成所有模板"""
        print(f"\n{'='*60}")
        print(f"🚀 生成所有模板 (共 {len(TEMPLATES)} 个)")
        print('='*60)
        
        results = []
        success_count = 0
        
        for key in TEMPLATES:
            result = self.generate_one(key, **kwargs)
            results.append(result)
            if result.get('status') == 'success':
                success_count += 1
            time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"📊 完成! 成功: {success_count}/{len(TEMPLATES)}")
        print('='*60)
        
        return results
    
    def generate_batch(self, template_key: str, count: int = 5, **kwargs):
        """批量生成同一模板多张"""
        print(f"\n{'='*60}")
        print(f"🚀 批量生成: {TEMPLATES[template_key]['name']}")
        print(f"📊 数量: {count}")
        print('='*60)
        
        results = []
        success_count = 0
        
        # 如果指定了种子，递增使用
        base_seed = kwargs.get('seed')
        
        for i in range(count):
            print(f"\n--- [{i+1}/{count}] ---")
            current_kwargs = kwargs.copy()
            if base_seed is not None:
                current_kwargs['seed'] = base_seed + i
            result = self.generate_one(template_key, **current_kwargs)
            results.append(result)
            if result.get('status') == 'success':
                success_count += 1
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"📊 完成! 成功: {success_count}/{count}")
        print('='*60)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="特殊内容生成器（支持自定义参数和输入图片）",
        epilog="""
示例:
  # 列出所有模板
  python scripts/generate_special.py --list

  # 生成卧室裸露（文生图）
  python scripts/generate_special.py --template bedroom_nude

  # 图生图 - 指定输入图片
  python scripts/generate_special.py --template bedroom_nude --image_path input/girl.jpg

  # 自定义提示词和参数
  python scripts/generate_special.py --template bedroom_nude --prompt "自定义提示词" --steps 40 --cfg 8.0

  # 批量生成5张
  python scripts/generate_special.py --template bedroom_nude --batch 5

  # 批量生成 + 图生图
  python scripts/generate_special.py --template bedroom_nude --image_path input/girl.jpg --batch 5 --strength 0.6

  # 生成所有模板
  python scripts/generate_special.py --all

  # 生成所有模板 + 图生图
  python scripts/generate_special.py --all --image_path input/girl.jpg
        """
    )
    
    # 基本参数
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板")
    parser.add_argument("--template", "-t", type=str, help="指定模板名称")
    parser.add_argument("--all", "-a", action="store_true", help="生成所有模板")
    parser.add_argument("--batch", "-b", type=int, default=1, help="批量生成数量")
    parser.add_argument("--output", "-o", type=str, default="./output/special", help="输出目录")
    
    # ========== 新增：自定义参数 ==========
    parser.add_argument("--image_path", "-i", type=str, help="输入图片路径（图生图模式）")
    parser.add_argument("--prompt", "-p", type=str, help="自定义提示词（覆盖模板）")
    parser.add_argument("--negative", "-n", type=str, help="自定义负向提示词")
    parser.add_argument("--steps", "-s", type=int, help="迭代步数")
    parser.add_argument("--cfg_scale", "-c", type=float, help="CFG Scale")
    parser.add_argument("--strength", "-r", type=float, help="重绘强度 (0-1)")
    parser.add_argument("--width", type=int, help="输出宽度")
    parser.add_argument("--height", type=int, help="输出高度")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    
    args = parser.parse_args()
    
    generator = SpecialGenerator(args.output)
    
    if args.list:
        generator.list_templates()
        return
    
    # 构建 kwargs
    kwargs = {}
    if args.image_path:
        kwargs['image_path'] = args.image_path
    if args.prompt:
        kwargs['custom_prompt'] = args.prompt
    if args.negative:
        kwargs['custom_negative'] = args.negative
    if args.steps is not None:
        kwargs['steps'] = args.steps
    if args.cfg_scale is not None:
        kwargs['cfg_scale'] = args.cfg_scale
    if args.strength is not None:
        kwargs['strength'] = args.strength
    if args.width is not None:
        kwargs['width'] = args.width
    if args.height is not None:
        kwargs['height'] = args.height
    if args.seed is not None:
        kwargs['seed'] = args.seed
    
    if args.template:
        if args.template not in TEMPLATES:
            print(f"❌ 未知模板: {args.template}")
            print(f"💡 可用: {', '.join(TEMPLATES.keys())}")
            print("   使用 --list 查看所有模板")
            return
        
        if args.batch > 1:
            generator.generate_batch(args.template, args.batch, **kwargs)
        else:
            generator.generate_one(args.template, **kwargs)
        return
    
    if args.all:
        generator.generate_all(**kwargs)
        return
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()