#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特殊内容生成器 - 支持文生图/图生图模式切换
功能：
  1. 文生图 (txt2img)：从零生成图片，使用完整提示词
  2. 图生图 (img2img)：基于输入图片生成，保留原图人物，只改变场景/风格
  3. 批量处理：支持单张、目录、所有模板

用法：
  # 查看所有模板
  python scripts/generate_special.py --list

  # 文生图 - 从零生成
  python scripts/generate_special.py --template bedroom_nude --mode txt2img

  # 图生图 - 单张图片换背景
  python scripts/generate_special.py --template change_background_beach --image_path input/girl.jpg --mode img2img

  # 图生图 - 批量处理整个目录
  python scripts/generate_special.py --template change_background_beach --input_dir input/ --mode img2img

  # 图生图 - 自定义参数
  python scripts/generate_special.py --template oil_painting --input_dir input/ --strength 0.7 --steps 35

  # 每张图生成多张（不同种子）
  python scripts/generate_special.py --template cyberpunk --input_dir input/ --batch 3
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
# 每个模板包含：
#   - prompt: 文生图完整提示词（包含人物描述）
#   - img2img_prompt: 图生图场景提示词（不包含人物，保留原图人物）
#   - negative: 负向提示词
#   - params: 默认参数 (width, height, steps, cfg_scale, strength)

TEMPLATES = {
    # ============================================================
    # 1. 卧室系列
    # ============================================================
    "bedroom_nude": {
        "name": "卧室裸露",
        "category": "卧室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, nude, lying on a large bed, soft mattress, white sheets, bedroom background, soft lighting, warm atmosphere, masterpiece, 8k, photorealistic",
        "img2img_prompt": "lying on a large bed, soft mattress, white sheets, bedroom background, soft lighting, warm atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.6}
    },
    "bedroom_lingerie": {
        "name": "卧室唯美内衣",
        "category": "卧室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, white lace lingerie, delicate lace, lying on a large bed, soft mattress, white sheets, bedroom background, soft lighting, warm atmosphere, masterpiece, 8k, photorealistic",
        "img2img_prompt": "wearing white lace lingerie, lying on a large bed, soft mattress, white sheets, bedroom background, soft lighting, warm atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    
    # ============================================================
    # 2. 海滩系列
    # ============================================================
    "beach_nude": {
        "name": "海滩裸露",
        "category": "海滩",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, nude, standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 1024, "height": 768, "steps": 30, "cfg_scale": 7.0, "strength": 0.6}
    },
    "beach_lingerie": {
        "name": "海滩唯美内衣",
        "category": "海滩",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, white lace lingerie, standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece, 8k, photorealistic",
        "img2img_prompt": "wearing white lace lingerie, standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 1024, "height": 768, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    
    # ============================================================
    # 3. 工作室系列
    # ============================================================
    "studio_nude": {
        "name": "工作室裸露",
        "category": "工作室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, nude, standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.6}
    },
    "studio_lingerie": {
        "name": "工作室唯美内衣",
        "category": "工作室",
        "prompt": "1girl, full body, facing viewer, beautiful face, perfect body, black silk lingerie, glossy silk, standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, masterpiece, 8k, photorealistic",
        "img2img_prompt": "wearing black silk lingerie, standing upright, soft studio lighting, gentle shadows, professional studio background, clean background, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    
    # ============================================================
    # 4. 泳池系列
    # ============================================================
    "pool_nude": {
        "name": "泳池裸露",
        "category": "泳池",
        "prompt": "1girl, full body, beautiful face, perfect body, nude, standing in pool, water up to waist, swimming pool background, blue water, bright sunlight, sparkling water, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing in a swimming pool, water up to waist, blue water, bright sunlight, sparkling water, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.6}
    },
    "pool_lingerie": {
        "name": "泳池唯美内衣",
        "category": "泳池",
        "prompt": "1girl, full body, beautiful face, perfect body, pink satin lingerie, standing in pool, water up to waist, swimming pool background, blue water, bright sunlight, sparkling water, masterpiece, 8k, photorealistic",
        "img2img_prompt": "wearing pink satin lingerie, standing in a swimming pool, water up to waist, blue water, bright sunlight, sparkling water, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    
    # ============================================================
    # 5. 浴室系列
    # ============================================================
    "bathroom_nude": {
        "name": "浴室裸露",
        "category": "浴室",
        "prompt": "1girl, full body, beautiful face, perfect body, nude, standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, clothes, fabric",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.6}
    },
    "bathroom_lingerie": {
        "name": "浴室唯美内衣",
        "category": "浴室",
        "prompt": "1girl, full body, beautiful face, perfect body, blue lace lingerie, standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, masterpiece, 8k, photorealistic",
        "img2img_prompt": "wearing blue lace lingerie, standing in shower, water flowing, steamy bathroom, foggy mirrors, warm mist, bathroom interior, tiles, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    
    # ============================================================
    # 6. 风格转换系列
    # ============================================================
    "oil_painting": {
        "name": "油画风格转换",
        "category": "风格转换",
        "prompt": "1girl, full body, oil painting, canvas texture, classical oil painting, Renaissance style, soft chiaroscuro, artistic, fine art, masterpiece",
        "img2img_prompt": "oil painting style, canvas texture, classical oil painting, Renaissance style, soft chiaroscuro, artistic, fine art",
        "negative": "ugly, deformed, bad anatomy, bad proportions, blurry, low quality, cartoon, anime, digital art, 3d render, plastic",
        "params": {"width": 768, "height": 1024, "steps": 35, "cfg_scale": 7.5, "strength": 0.7}
    },
    "watercolor": {
        "name": "水彩风格转换",
        "category": "风格转换",
        "prompt": "1girl, full body, watercolor painting, soft brush strokes, flowing colors, artistic, fine art, masterpiece",
        "img2img_prompt": "watercolor painting style, soft brush strokes, flowing colors, artistic, fine art",
        "negative": "ugly, deformed, bad anatomy, bad proportions, blurry, low quality, cartoon, anime, digital art, 3d render",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.7}
    },
    "sketch": {
        "name": "素描风格转换",
        "category": "风格转换",
        "prompt": "1girl, full body, pencil sketch, fine linework, graphite shading, white paper background, 2D illustration, masterpiece",
        "img2img_prompt": "pencil sketch style, graphite shading, fine linework, white paper background, 2D illustration",
        "negative": "ugly, deformed, bad anatomy, bad proportions, blurry, low quality, color, 3d render",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.7}
    },
    "cyberpunk": {
        "name": "赛博朋克风格",
        "category": "风格转换",
        "prompt": "1girl, full body, cyberpunk style, neon lights, futuristic city, glowing cybernetic elements, dark atmosphere, masterpiece, 8k",
        "img2img_prompt": "cyberpunk style, neon lights, futuristic city background, glowing cybernetic elements, dark atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, bad proportions, blurry, low quality, old, vintage",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.5, "strength": 0.6}
    },
    
    # ============================================================
    # 7. 换背景系列（通用）
    # ============================================================
    "change_background_beach": {
        "name": "换海滩背景",
        "category": "换背景",
        "prompt": "1girl, full body, beautiful face, perfect body, standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing on a beautiful sandy beach, ocean waves in background, sunny day, golden sunlight, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    "change_background_forest": {
        "name": "换森林背景",
        "category": "换背景",
        "prompt": "1girl, full body, beautiful face, perfect body, standing in a lush green forest, sunlight filtering through trees, magical atmosphere, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing in a lush green forest, sunlight filtering through trees, magical atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    "change_background_city": {
        "name": "换城市背景",
        "category": "换背景",
        "prompt": "1girl, full body, beautiful face, perfect body, standing on a city rooftop, skyscrapers in background, city lights, night atmosphere, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing on a city rooftop, skyscrapers in background, city lights, night atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    "change_background_snow": {
        "name": "换雪景背景",
        "category": "换背景",
        "prompt": "1girl, full body, beautiful face, perfect body, standing in a snowy landscape, snowflakes falling, winter forest, cold atmosphere, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing in a snowy landscape, snowflakes falling, winter forest, cold atmosphere, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
    },
    "change_background_sunset": {
        "name": "换日落背景",
        "category": "换背景",
        "prompt": "1girl, full body, beautiful face, perfect body, standing in a golden sunset, warm orange sky, dramatic clouds, silhouette, masterpiece, 8k, photorealistic",
        "img2img_prompt": "standing in a golden sunset, warm orange sky, dramatic clouds, silhouette, masterpiece",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality",
        "params": {"width": 768, "height": 1024, "steps": 30, "cfg_scale": 7.0, "strength": 0.55}
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
    """特殊内容生成器（支持文生图/图生图模式切换）"""
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    
    def __init__(self, output_dir: str = "./output/special"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sd_config = get_sd_config()
        
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📦 当前模型: {self.sd_config.get('model_name', '未设置')}")
        print(f"💻 设备: {self.sd_config.get('device', 'cpu')}")
        print()
    
    # ============================================================
    # 1. 列出模板
    # ============================================================
    def list_templates(self):
        """列出所有模板"""
        print("\n" + "=" * 90)
        print("📋 可用模板列表")
        print("=" * 90)
        
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
                strength = params.get('strength', 0.6)
                print(f"  {key:<30} {template['name']:<20} (steps={steps}, cfg={cfg}, strength={strength})")
        
        print("\n" + "=" * 90)
        print(f"共 {len(TEMPLATES)} 个模板")
        print("\n💡 使用示例:")
        print("  # 文生图（从零生成）")
        print("  python scripts/generate_special.py --template bedroom_nude --mode txt2img")
        print()
        print("  # 图生图（保留人物，换背景）")
        print("  python scripts/generate_special.py --template change_background_beach --image_path input/girl.jpg --mode img2img")
        print()
        print("  # 图生图 + 批量处理目录")
        print("  python scripts/generate_special.py --template change_background_beach --input_dir input/ --mode img2img")
    
    # ============================================================
    # 2. 获取目录中的图片
    # ============================================================
    def get_images_from_dir(self, dir_path: str) -> List[Path]:
        """从目录获取所有图片"""
        input_dir = Path(dir_path)
        if not input_dir.exists():
            print(f"❌ 目录不存在: {dir_path}")
            return []
        
        if not input_dir.is_dir():
            print(f"❌ 不是目录: {dir_path}")
            return []
        
        images = []
        for ext in self.IMAGE_EXTENSIONS:
            images.extend(input_dir.glob(f"*{ext}"))
            images.extend(input_dir.glob(f"*{ext.upper()}"))
        
        return sorted(set(images))
    
    # ============================================================
    # 3. 生成单张图片
    # ============================================================
    def generate_one(self, template_key: str, 
                     mode: str = "auto",
                     image_path: str = None,
                     custom_prompt: str = None,
                     custom_negative: str = None,
                     steps: int = None,
                     cfg_scale: float = None,
                     strength: float = None,
                     width: int = None,
                     height: int = None,
                     seed: int = None,
                     batch_size: int = 1,
                     output_filename: str = None) -> Dict:
        """
        生成单个模板
        
        Args:
            template_key: 模板名称
            mode: txt2img | img2img | auto
            image_path: 输入图片路径（图生图模式需要）
            custom_prompt: 自定义提示词（覆盖模板）
            custom_negative: 自定义负向提示词
            steps: 迭代步数
            cfg_scale: CFG Scale
            strength: 重绘强度 (0-1)
            width: 输出宽度
            height: 输出高度
            seed: 随机种子
            batch_size: 批量生成数量
            output_filename: 输出文件名
        
        Returns:
            执行结果字典
        """
        if template_key not in TEMPLATES:
            return {"status": "error", "error": f"未知模板: {template_key}"}
        
        template = TEMPLATES[template_key]
        params = template.get("params", {})
        
        # ========== 确定模式 ==========
        has_image = image_path is not None and Path(image_path).exists()
        
        if mode == "auto":
            mode = "img2img" if has_image else "txt2img"
        
        # ========== 选择提示词 ==========
        if custom_prompt:
            prompt = custom_prompt
            print(f"📌 使用自定义提示词")
        elif mode == "img2img" and has_image:
            prompt = template.get("img2img_prompt", template["prompt"])
            print(f"📌 图生图模式: 使用场景提示词（保留原图人物）")
        else:
            prompt = template["prompt"]
            print(f"📌 文生图模式: 使用完整提示词")
        
        # ========== 参数处理 ==========
        negative = custom_negative if custom_negative else template.get("negative", "")
        steps = steps if steps is not None else params.get("steps", self.sd_config.get("default_steps", 25))
        cfg_scale = cfg_scale if cfg_scale is not None else params.get("cfg_scale", self.sd_config.get("default_cfg", 7.5))
        width = width if width is not None else params.get("width", 512)
        height = height if height is not None else params.get("height", 768)
        strength = strength if strength is not None else params.get("strength", 0.55)
        
        # 处理种子
        if seed is None or seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        model_name = self.sd_config.get("model_name")
        
        # ========== 生成文件名 ==========
        if output_filename:
            output_path = str(self.output_dir / output_filename)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_name = Path(image_path).stem if image_path else "text"
            mode_tag = "img2img" if mode == "img2img" else "txt2img"
            filename = f"{timestamp}_{mode_tag}_{template_key}_{img_name}_{seed}.png"
            output_path = str(self.output_dir / filename)
        
        # ========== 打印信息 ==========
        print(f"\n{'='*60}")
        print(f"🎨 生成: {template['name']}")
        print(f"📝 模板: {template_key}")
        print(f"📌 模式: {mode.upper()}")
        if image_path:
            print(f"📷 输入图片: {image_path}")
        print(f"📐 尺寸: {width}x{height}")
        print(f"⚙️  步数: {steps}, CFG: {cfg_scale}")
        if has_image and mode == "img2img":
            print(f"💪 强度: {strength}")
        print(f"🌱 种子: {seed}")
        print(f"📦 模型: {model_name}")
        print('='*60)
        print(f"📝 提示词: {prompt[:150]}...")
        if negative:
            print(f"🚫 负向词: {negative[:100]}...")
        
        # ========== 构建参数 ==========
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
        
        # 图生图模式：添加图片和强度
        if has_image and mode == "img2img":
            skill_params["image_path"] = image_path
            skill_params["strength"] = strength
        
        # ========== 执行生成 ==========
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
                    "mode": mode,
                    "image_paths": image_paths,
                    "seed": seed,
                    "input_image": image_path
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
    
    # ============================================================
    # 4. 批量生成（同一模板，多张不同种子）
    # ============================================================
    def generate_batch(self, template_key: str, count: int = 5, 
                       image_path: str = None, **kwargs) -> List[Dict]:
        """
        批量生成同一模板多张图片（每张使用不同种子）
        
        Args:
            template_key: 模板名称
            count: 生成数量
            image_path: 输入图片路径
            **kwargs: 其他参数
        
        Returns:
            结果列表
        """
        print(f"\n{'='*60}")
        print(f"🚀 批量生成: {TEMPLATES[template_key]['name']}")
        print(f"📊 数量: {count}")
        if image_path:
            print(f"📷 输入图片: {image_path}")
        print('='*60)
        
        results = []
        success_count = 0
        
        # 如果指定了种子，递增使用
        base_seed = kwargs.get('seed')
        
        for i in range(count):
            print(f"\n--- [{i+1}/{count}] ---")
            current_kwargs = kwargs.copy()
            if base_seed is not None and base_seed != -1:
                current_kwargs['seed'] = base_seed + i
            else:
                current_kwargs['seed'] = random.randint(0, 2**32 - 1)
            
            result = self.generate_one(
                template_key, 
                image_path=image_path,
                **current_kwargs
            )
            results.append(result)
            if result.get('status') == 'success':
                success_count += 1
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"📊 完成! 成功: {success_count}/{count}")
        print('='*60)
        
        return results
    
    # ============================================================
    # 5. 生成所有模板
    # ============================================================
    def generate_all(self, image_path: str = None, **kwargs) -> List[Dict]:
        """
        生成所有模板
        
        Args:
            image_path: 输入图片路径（所有模板共用）
            **kwargs: 其他参数
        
        Returns:
            结果列表
        """
        print(f"\n{'='*60}")
        print(f"🚀 生成所有模板 (共 {len(TEMPLATES)} 个)")
        if image_path:
            print(f"📷 输入图片: {image_path}")
        print('='*60)
        
        results = []
        success_count = 0
        
        for key in TEMPLATES:
            result = self.generate_one(key, image_path=image_path, **kwargs)
            results.append(result)
            if result.get('status') == 'success':
                success_count += 1
            time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"📊 完成! 成功: {success_count}/{len(TEMPLATES)}")
        print('='*60)
        
        return results
    
    # ============================================================
    # 6. 目录批量处理
    # ============================================================
    def generate_directory(self, template_key: str, 
                           input_dir: str,
                           mode: str = "img2img",
                           **kwargs) -> Dict:
        """
        处理目录中的所有图片
        
        Args:
            template_key: 模板名称
            input_dir: 输入目录路径
            mode: 生成模式（默认 img2img）
            **kwargs: 其他参数
        
        Returns:
            执行结果字典
        """
        images = self.get_images_from_dir(input_dir)
        
        if not images:
            print(f"❌ 在 {input_dir} 中未找到图片")
            print(f"   支持的格式: {', '.join(self.IMAGE_EXTENSIONS)}")
            return {"status": "error", "error": "未找到图片"}
        
        print(f"\n{'='*60}")
        print(f"📁 目录批量处理: {input_dir}")
        print(f"📊 找到 {len(images)} 张图片")
        print(f"🎯 模板: {template_key} - {TEMPLATES[template_key]['name']}")
        print(f"📌 模式: {mode.upper()} (图生图，保留原图人物)")
        print('='*60)
        
        results = []
        success_count = 0
        
        for idx, img_path in enumerate(images, 1):
            print(f"\n📸 [{idx}/{len(images)}] 处理: {img_path.name}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{timestamp}_{mode}_{template_key}_{img_path.stem}.png"
            
            result = self.generate_one(
                template_key,
                mode=mode,
                image_path=str(img_path),
                output_filename=output_filename,
                **kwargs
            )
            results.append(result)
            if result.get('status') == 'success':
                success_count += 1
            
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"📊 完成! 成功: {success_count}/{len(images)}")
        print('='*60)
        
        return {
            "status": "success" if success_count == len(images) else "partial",
            "total": len(images),
            "success": success_count,
            "results": results
        }


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="特殊内容生成器（支持文生图/图生图模式切换）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 1. 列出所有模板
  python scripts/generate_special.py --list

  # 2. 文生图（从零生成）
  python scripts/generate_special.py --template bedroom_nude --mode txt2img
  python scripts/generate_special.py --template bedroom_nude --mode txt2img --seed 42

  # 3. 图生图 - 单张图片换背景
  python scripts/generate_special.py --template change_background_beach --image_path input/girl.jpg --mode img2img

  # 4. 图生图 - 批量处理整个目录
  python scripts/generate_special.py --template change_background_beach --input_dir input/ --mode img2img

  # 5. 图生图 - 自定义参数
  python scripts/generate_special.py --template oil_painting --input_dir input/ --strength 0.7 --steps 35

  # 6. 图生图 - 每张图生成3张（不同种子）
  python scripts/generate_special.py --template cyberpunk --input_dir input/ --batch 3 --seed 100

  # 7. 图生图 - 自定义提示词（覆盖模板）
  python scripts/generate_special.py --template change_background_beach --input_dir input/ --prompt "standing on beach, sunset, masterpiece"

  # 8. 生成所有模板
  python scripts/generate_special.py --all --mode txt2img
  python scripts/generate_special.py --all --image_path input/girl.jpg --mode img2img
        """
    )
    
    # ========== 基本参数 ==========
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板")
    parser.add_argument("--template", "-t", type=str, help="指定模板名称")
    parser.add_argument("--all", "-a", action="store_true", help="生成所有模板")
    parser.add_argument("--batch", "-b", type=int, default=1, help="每张图片生成数量（不同种子）")
    parser.add_argument("--output", "-o", type=str, default="./output/special", help="输出目录")
    
    # ========== 模式选择 ==========
    parser.add_argument("--mode", "-m", type=str, default="auto",
                       choices=["txt2img", "img2img", "auto"],
                       help="生成模式: txt2img(文生图), img2img(图生图), auto(自动检测)")
    
    # ========== 输入源 ==========
    parser.add_argument("--image_path", "-i", type=str, help="输入单张图片路径")
    parser.add_argument("--input_dir", "-d", type=str, help="输入目录路径（处理所有图片）")
    
    # ========== 自定义参数 ==========
    parser.add_argument("--prompt", "-p", type=str, help="自定义提示词（覆盖模板）")
    parser.add_argument("--negative", "-n", type=str, help="自定义负向提示词")
    parser.add_argument("--steps", "-s", type=int, help="迭代步数")
    parser.add_argument("--cfg_scale", "-c", type=float, help="CFG Scale")
    parser.add_argument("--strength", "-r", type=float, help="重绘强度 (0-1)，图生图模式专用")
    parser.add_argument("--width", type=int, help="输出宽度")
    parser.add_argument("--height", type=int, help="输出高度")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    
    args = parser.parse_args()
    
    # ========== 初始化 ==========
    generator = SpecialGenerator(args.output)
    
    # ========== 列出模板 ==========
    if args.list:
        generator.list_templates()
        return
    
    # ========== 构建 kwargs ==========
    kwargs = {}
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
    if args.batch > 1:
        kwargs['batch_size'] = args.batch
    if args.mode:
        kwargs['mode'] = args.mode
    
    # ========== 检查模板是否存在 ==========
    if args.template and args.template not in TEMPLATES:
        print(f"❌ 未知模板: {args.template}")
        print(f"💡 可用: {', '.join(TEMPLATES.keys())}")
        print("   使用 --list 查看所有模板")
        return
    
    # ========== 目录批量处理 ==========
    if args.input_dir:
        if not args.template:
            print("❌ 目录模式需要指定 --template")
            return
        
        # 目录模式默认使用 img2img
        if args.mode == "auto" or args.mode == "txt2img":
            print(f"💡 目录模式自动切换到 img2img（保留原图人物）")
            kwargs['mode'] = "img2img"
        
        generator.generate_directory(args.template, args.input_dir, **kwargs)
        return
    
    # ========== 单张图片 / 批量生成 ==========
    if args.template:
        if args.batch > 1:
            generator.generate_batch(args.template, args.batch, 
                                     image_path=args.image_path, **kwargs)
        else:
            generator.generate_one(args.template, 
                                   image_path=args.image_path, **kwargs)
        return
    
    # ========== 生成所有模板 ==========
    if args.all:
        generator.generate_all(image_path=args.image_path, **kwargs)
        return
    
    # ========== 默认显示帮助 ==========
    parser.print_help()


if __name__ == "__main__":
    main()