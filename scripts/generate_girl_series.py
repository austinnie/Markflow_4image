# scripts/generate_girl_series.py
"""
给 input/ 目录下所有图片批量生成系列图
自动组合不同的背景、姿势、表情、服装等技能
"""

import sys
import time
from pathlib import Path
import argparse

# 添加项目根目录
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill

# ========== 导入预处理 ==========
import preprocess_image
from preprocess_image import resize_image, SCALE_MODES


# ==================== 配置 ====================
INPUT_DIR = Path("input")               # 输入目录
OUTPUT_ROOT = Path("output")            # 统一输出目录
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# ========== 预处理配置（档位模式） ==========
PREPROCESS_ENABLED = True               # 是否启用预处理
PREPROCESS_MODE = 3                     # 档位: 0-10 (3=512px 标准)
PREPROCESS_MAX_SIZE = SCALE_MODES[PREPROCESS_MODE]["size"]
PREPROCESS_OVERWRITE = True             # 是否覆盖原图


def preprocess_image_file(input_path: Path):
    """预处理单张图片 - 检查短边是否已符合目标"""
    if not PREPROCESS_ENABLED:
        return input_path
    
    if not input_path.exists():
        print(f"⚠️ 图片不存在: {input_path}")
        return input_path
    
    # 检查图片尺寸是否已经符合目标
    try:
        from PIL import Image
        img = Image.open(input_path)
        w, h = img.size
        short_side = min(w, h)
        
        # 如果短边已经等于或小于 max_size，说明已经缩放过了
        if short_side <= PREPROCESS_MAX_SIZE:
            print(f"   ⏭️ 已缩放: {input_path.name} ({w}x{h}, 短边 {short_side} ≤ {PREPROCESS_MAX_SIZE})")
            return input_path
    except Exception as e:
        print(f"   ⚠️ 无法读取图片尺寸: {e}")
    
    mode_name = SCALE_MODES[PREPROCESS_MODE]["name"]
    print(f"   📐 缩放: {input_path.name} ({PREPROCESS_MODE}: {mode_name} {PREPROCESS_MAX_SIZE}px)")
    result = resize_image(
        input_path, 
        max_size=PREPROCESS_MAX_SIZE,
        overwrite=PREPROCESS_OVERWRITE
    )
    
    return Path(result) if result else input_path

# ==================== 批量任务列表 ====================
GENERATION_TASKS = [
    # ========== 1. 换背景系列 ==========
    {"skill": "change_background", "params": {"preset": "beach", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "forest", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "city", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "sakura", "strength": 0.55}},
    {"skill": "change_background", "params": {"preset": "sunset", "strength": 0.55}},

    # ========== 2. 换衣服系列 ==========
    {"skill": "change_clothes", "params": {"prompt": "wearing a beautiful elegant black evening gown", "strength": 0.65}},
    {"skill": "change_clothes", "params": {"prompt": "wearing a white summer dress", "strength": 0.65}},
    {"skill": "change_clothes", "params": {"prompt": "wearing a casual red jacket and jeans", "strength": 0.65}},

    # ========== 3. 换表情系列 ==========
    {"skill": "change_expression", "params": {"expression": "smile", "strength": 0.45}},
    {"skill": "change_expression", "params": {"expression": "laughing", "strength": 0.45}},
    {"skill": "change_expression", "params": {"expression": "surprised", "strength": 0.45}},

    # ========== 4. 换发色/发型系列 ==========
    {"skill": "change_hair", "params": {"hair_color": "pink", "strength": 0.45}},
    {"skill": "change_hair", "params": {"hair_color": "blonde", "strength": 0.45}},

    # ========== 5. 加配饰/特效 ==========
    {"skill": "add_glasses", "params": {"style": "round", "strength": 0.35}},
    {"skill": "add_animal_ears", "params": {"animal": "cat", "strength": 0.55}},

    # ========== 6. 多技能复杂组合 ==========
    {"skill": "expand_to_full_body", "params": {"prompt": "a beautiful elegant woman standing, full body", "controlnet_type": "openpose"}},
    {"skill": "style_transfer", "params": {"style": "oil_painting", "strength": 0.75}},
    {"skill": "style_transfer", "params": {"style": "watercolor", "strength": 0.75}},

    # ========== 7. 二次元/写实转换 ==========
    {"skill": "anime_to_real", "params": {"style": "photorealistic", "strength": 0.8}},
]


def process_single_image(image_path: Path, image_index: int, total_images: int):
    """处理单张图片的所有任务"""
    print(f"\n{'='*60}")
    print(f"📸 处理图片 [{image_index}/{total_images}]: {image_path.name}")
    print('='*60)
    
    # 预处理图片
    processed_path = preprocess_image_file(image_path)
    
    success_count = 0
    total_tasks = len(GENERATION_TASKS)
    
    for idx, task in enumerate(GENERATION_TASKS, 1):
        skill_name = task['skill']
        params = task['params'].copy()
        
        # 生成输出文件名: 图片名_任务序号_技能名.png
        base_name = image_path.stem
        safe_name = f"{base_name}_{idx:02d}_{skill_name.replace('_', '-')}"
        output_path = str(OUTPUT_ROOT / f"{safe_name}.png")
        
        # 注入参数
        params['image_path'] = str(processed_path)
        params['output_path'] = output_path
        
        print(f"\n  [{idx}/{total_tasks}] 🚀 调用: {skill_name}")
        
        try:
            result = execute_skill(skill_name, **params)
            
            if isinstance(result, dict) and result.get('status') == 'success':
                print(f"      ✅ 成功: {output_path}")
                success_count += 1
            else:
                error = result.get('error', '未知错误') if isinstance(result, dict) else str(result)
                print(f"      ❌ 失败: {error}")
                
        except Exception as e:
            print(f"      ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(0.5)
    
    return success_count, total_tasks


def main():
    # ========== 解析命令行参数 ==========
    parser = argparse.ArgumentParser(description="批量生成女孩系列图")
    parser.add_argument("--image", "-i", type=str, help="指定要处理的图片文件名 (如: girl.jpg)")
    parser.add_argument("--first", "-f", action="store_true", help="只处理第一张图片")
    parser.add_argument("--all", "-a", action="store_true", help="处理所有图片 (默认行为)")
    args = parser.parse_args()
    
    # 收集所有图片
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    images = [f for f in INPUT_DIR.iterdir() if f.suffix.lower() in extensions]
    
    # 排除已缩放的图片
    images = [f for f in images if '_resized' not in f.stem]
    
    if not images:
        print(f"❌ 在 {INPUT_DIR} 中未找到图片")
        return
    
    # 排序
    images.sort()
    
    # ========== 根据参数筛选图片 ==========
    if args.image:
        # 查找指定的图片
        target = INPUT_DIR / args.image
        if not target.exists():
            # 如果没有扩展名，自动尝试添加
            for ext in extensions:
                test_path = INPUT_DIR / f"{args.image}{ext}"
                if test_path.exists():
                    target = test_path
                    break
        
        if target.exists():
            images = [target]
            print(f"📌 指定图片: {target.name}")
        else:
            print(f"❌ 未找到指定图片: {args.image}")
            print(f"💡 可用的图片:")
            for img in images:
                print(f"   - {img.name}")
            return
    elif args.first:
        images = images[:1]
        print(f"📌 只处理第一张: {images[0].name}")
    elif args.all:
        print(f"📌 处理所有 {len(images)} 张图片")
    else:
        # 默认行为：处理所有图片
        print(f"📌 处理所有 {len(images)} 张图片")
    
    print(f"📸 找到 {len(images)} 张图片")
    print(f"💾 输出目录: {OUTPUT_ROOT}")
    print(f"📐 档位 {PREPROCESS_MODE}: {SCALE_MODES[PREPROCESS_MODE]['name']} ({PREPROCESS_MAX_SIZE}px)")
    print(f"📋 每张图片执行 {len(GENERATION_TASKS)} 个任务")
    print(f"📊 总计: {len(images) * len(GENERATION_TASKS)} 次生成")
    print("=" * 60)
    
    total_success = 0
    total_all = 0
    
    for idx, img_path in enumerate(images, 1):
        success, total = process_single_image(img_path, idx, len(images))
        total_success += success
        total_all += total
    
    print(f"\n{'='*60}")
    print(f"🎉 全部完成！")
    print(f"   📸 图片: {len(images)} 张")
    print(f"   ✅ 成功: {total_success}/{total_all} 次")
    print(f"   📂 输出: {OUTPUT_ROOT}")
    print('='*60)


if __name__ == "__main__":
    main()