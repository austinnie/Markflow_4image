#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量重命名 input/ 目录下的图片
用法:
  python scripts/rename_images.py              # 预览重命名
  python scripts/rename_images.py --execute    # 执行重命名
  python scripts/rename_images.py --prefix girl --start 1
"""

import os
import sys
import argparse
from pathlib import Path

# 支持的文件扩展名
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}


def main():
    parser = argparse.ArgumentParser(description="批量重命名 input/ 目录下的图片")
    parser.add_argument("--dir", "-d", default="input", help="目标目录 (默认: input)")
    parser.add_argument("--prefix", "-p", default="girl", help="文件名前缀 (默认: girl)")
    parser.add_argument("--start", "-s", type=int, default=1, help="起始编号 (默认: 1)")
    parser.add_argument("--digits", "-n", type=int, default=2, help="编号位数 (默认: 2)")
    parser.add_argument("--execute", "-e", action="store_true", help="执行重命名 (不加此参数仅预览)")
    parser.add_argument("--dry-run", action="store_true", help="同 --execute 的预览模式")
    
    args = parser.parse_args()
    
    target_dir = Path(args.dir)
    if not target_dir.exists():
        print(f"❌ 目录不存在: {target_dir}")
        return
    
    # 收集所有图片
    images = []
    for ext in SUPPORTED_EXTS:
        images.extend(target_dir.glob(f"*{ext}"))
    
    if not images:
        print(f"❌ 在 {target_dir} 中未找到图片")
        return
    
    # 按修改时间排序（保证顺序一致）
    images.sort(key=lambda x: x.stat().st_mtime)
    
    print(f"\n📁 找到 {len(images)} 张图片")
    print("=" * 60)
    
    # 检查是否有 _resized 文件，优先保留原图
    # 实际上我们直接处理所有图片，但跳过已经符合命名规范的
    
    rename_plan = []
    for idx, img_path in enumerate(images, start=args.start):
        ext = img_path.suffix.lower()
        new_name = f"{args.prefix}_{idx:0{args.digits}d}{ext}"
        new_path = img_path.parent / new_name
        
        if img_path.name == new_name:
            print(f"  ⏭️  {img_path.name} -> 已是目标名称，跳过")
            continue
        
        rename_plan.append((img_path, new_path))
    
    if not rename_plan:
        print("\n✅ 所有图片已符合命名规范，无需重命名")
        return
    
    print("\n📋 重命名计划:")
    print("-" * 60)
    for old, new in rename_plan:
        print(f"  {old.name} -> {new.name}")
    
    print("-" * 60)
    print(f"共 {len(rename_plan)} 个文件需要重命名")
    
    if not args.execute and not args.dry_run:
        print("\n💡 以上为预览，加上 --execute 参数执行重命名")
        print("   python scripts/rename_images.py --execute")
        return
    
    # 执行重命名
    print("\n🔄 执行重命名...")
    success = 0
    for old, new in rename_plan:
        try:
            old.rename(new)
            print(f"  ✅ {old.name} -> {new.name}")
            success += 1
        except Exception as e:
            print(f"  ❌ {old.name} 失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ 完成: 成功重命名 {success}/{len(rename_plan)} 个文件")
    print(f"📂 目录: {target_dir.absolute()}")


if __name__ == "__main__":
    main()