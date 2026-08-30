#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片预处理工具 - 在生成前缩放参考图
用法:
  python scripts/preprocess_image.py                    # 处理 input/girl.jpg
  python scripts/preprocess_image.py --input image.jpg  # 处理指定图片
  python scripts/preprocess_image.py --size 640         # 指定最大边长
  python scripts/preprocess_image.py --mode 3           # 使用预设档位
  python scripts/preprocess_image.py --all              # 批量处理 input/ 目录下所有图片
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

# 添加项目根目录
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ==================== 配置 ====================
DEFAULT_INPUT = "input/girl.jpg"
OUTPUT_SUFFIX = "_resized"  # 输出文件名后缀（仅在 --no-overwrite 时使用）

# ==================== 多档位预设 ====================
SCALE_MODES = {
    0: {"name": "极速测试", "size": 256},
    1: {"name": "迷你", "size": 320},
    2: {"name": "极速", "size": 384},
    3: {"name": "标准 ⭐", "size": 512},
    4: {"name": "中档", "size": 576},
    5: {"name": "高清", "size": 640},
    6: {"name": "细节", "size": 768},
    7: {"name": "超清", "size": 896},
    8: {"name": "准高清", "size": 1024},
    9: {"name": "高清大图", "size": 1280},
    10: {"name": "超高清", "size": 1536},
}

DEFAULT_MODE = 3  # 默认 512px


# ==================== 核心函数 ====================

def get_recommended_size():
    """根据当前模型类型获取推荐尺寸"""
    try:
        from markflow.utils.model_config import get_model_config
        cfg = get_model_config()
        model_type = cfg.get('model_type', 'sd15')
        if model_type == 'sdxl':
            return 1024
        return 768
    except:
        return 768


def resize_image(input_path: Path, max_size: int = None, output_path: Path = None, 
                 overwrite: bool = True, align: int = 64):  # 默认 overwrite=True
    """缩放图片到指定最大边长"""
    if max_size is None:
        max_size = get_recommended_size()
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return None
    
    img = Image.open(input_path)
    w, h = img.size
    
    # 如果已经小于目标，跳过
    if w <= max_size and h <= max_size:
        print(f"✅ 图片尺寸 {w}x{h} 已小于 {max_size}，无需缩放")
        return input_path
    
    # 等比例缩放
    if w > h:
        scale = max_size / w
    else:
        scale = max_size / h
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 对齐到 64 的倍数
    new_w = ((new_w + align - 1) // align) * align
    new_h = ((new_h + align - 1) // align) * align
    
    print(f"📐 缩放: {w}x{h} -> {new_w}x{new_h} (最大边长: {max_size})")
    
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 确定输出路径
    if output_path is None:
        if overwrite:
            # 默认覆盖原图
            output_path = input_path
        else:
            # 不覆盖时添加 _resized 后缀
            stem = input_path.stem
            suffix = input_path.suffix
            if stem.endswith(OUTPUT_SUFFIX):
                output_path = input_path.parent / f"{stem}{suffix}"
            else:
                output_path = input_path.parent / f"{stem}{OUTPUT_SUFFIX}{suffix}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resized.save(output_path, quality=95)
    print(f"✅ 已保存: {output_path}")
    
    return output_path


def batch_process(input_dir: Path, max_size: int = None, overwrite: bool = True):  # 默认 overwrite=True
    """批量处理目录下所有图片"""
    if not input_dir.exists():
        print(f"❌ 目录不存在: {input_dir}")
        return
    
    # 排除已缩放的图片（避免重复处理）
    extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    images = [f for f in input_dir.iterdir() if f.suffix.lower() in extensions]
    
    # 如果 overwrite=False，排除 _resized 文件
    if not overwrite:
        images = [f for f in images if OUTPUT_SUFFIX not in f.stem]
    
    if not images:
        print(f"❌ 未找到图片: {input_dir}")
        return
    
    print(f"\n📁 找到 {len(images)} 张图片")
    print("=" * 50)
    
    processed = 0
    for img_path in images:
        print(f"\n🔄 处理: {img_path.name}")
        result = resize_image(img_path, max_size, overwrite=overwrite)
        if result:
            processed += 1
    
    print(f"\n✅ 完成: 处理了 {processed}/{len(images)} 张图片")


def main():
    # ========== 如果没有参数，显示帮助 ==========
    if len(sys.argv) == 1:
        print(__doc__)
        print("\n📊 预设档位列表")
        print("=" * 50)
        print(f"{'档位':<6} {'尺寸':<10} {'名称':<15}")
        print("-" * 50)
        for key, val in SCALE_MODES.items():
            star = " ⭐" if key == DEFAULT_MODE else ""
            print(f"  {key:<4} {val['size']:<6}px {val['name']:<15}{star}")
        print("=" * 50)
        print("\n💡 示例:")
        print("  python scripts/preprocess_image.py --mode 3          # 使用 512px (默认覆盖原图)")
        print("  python scripts/preprocess_image.py --mode 5          # 使用 640px")
        print("  python scripts/preprocess_image.py --no-overwrite    # 不覆盖，输出 _resized 文件")
        print("  python scripts/preprocess_image.py --size 600        # 自定义 600px")
        print("  python scripts/preprocess_image.py --all             # 批量处理")
        print("  python scripts/preprocess_image.py --list            # 列出所有档位")
        return
    
    parser = argparse.ArgumentParser(
        description="图片预处理 - 缩放参考图以加速生成",
        epilog="""
示例:
  python scripts/preprocess_image.py                    # 处理 input/girl.jpg (默认 512px，覆盖原图)
  python scripts/preprocess_image.py --mode 5          # 使用预设档位 5 (640px)
  python scripts/preprocess_image.py --no-overwrite   # 不覆盖原图，输出 _resized 文件
  python scripts/preprocess_image.py --size 640        # 指定最大边长 640px
  python scripts/preprocess_image.py --list            # 列出所有档位
  python scripts/preprocess_image.py --all             # 批量处理 input/
        """
    )
    
    parser.add_argument("--input", "-i", type=str, help="输入图片路径")
    parser.add_argument("--output", "-o", type=str, help="输出路径")
    parser.add_argument("--size", "-s", type=int, default=None, 
                       help="最大边长 (默认: 自动适配，SD1.5: 768, SDXL: 1024)")
    parser.add_argument("--mode", "-m", type=int, default=None,
                       help=f"使用预设档位 (0-10, 默认: {DEFAULT_MODE}=512px)")
    parser.add_argument("--list", action="store_true", help="列出所有档位")
    parser.add_argument("--all", "-a", action="store_true", 
                       help="批量处理 input/ 目录下所有图片")
    parser.add_argument("--no-overwrite", action="store_true", 
                       help="不覆盖原图，输出 _resized 文件 (默认覆盖)")
    parser.add_argument("--align", type=int, default=64, 
                       help="对齐到多少的倍数 (默认: 64)")
    
    args = parser.parse_args()
    
    # ========== 列出档位 ==========
    if args.list:
        print("\n📊 预设档位列表")
        print("=" * 50)
        print(f"{'档位':<6} {'尺寸':<10} {'名称':<15}")
        print("-" * 50)
        for key, val in SCALE_MODES.items():
            star = " ⭐" if key == DEFAULT_MODE else ""
            print(f"  {key:<4} {val['size']:<6}px {val['name']:<15}{star}")
        print("=" * 50)
        print(f"💡 使用: --mode <档位>  如 --mode 3")
        return
    
    # ========== 确定尺寸 ==========
    max_size = args.size
    
    # 如果指定了 mode，覆盖 size
    if args.mode is not None:
        if args.mode in SCALE_MODES:
            max_size = SCALE_MODES[args.mode]["size"]
            print(f"📌 使用档位 {args.mode}: {SCALE_MODES[args.mode]['name']} ({max_size}px)")
        else:
            print(f"❌ 无效档位: {args.mode}，有效范围 0-10")
            print("💡 使用 --list 查看所有档位")
            sys.exit(1)
    
    # 确定是否覆盖（默认 True，--no-overwrite 时 False）
    overwrite = not args.no_overwrite
    
    # 如果指定了 --all，批量处理
    if args.all:
        input_dir = Path("input")
        batch_process(input_dir, max_size, overwrite)
        return
    
    # 确定输入路径
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = Path(DEFAULT_INPUT)
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        print(f"💡 请指定正确的路径: --input <文件路径>")
        print(f"   或确保 {DEFAULT_INPUT} 存在")
        sys.exit(1)
    
    # 执行缩放
    output_path = Path(args.output) if args.output else None
    resize_image(input_path, max_size, output_path, overwrite, args.align)


if __name__ == "__main__":
    main()