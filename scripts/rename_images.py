#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量重命名 input/ 目录下的图片
用法:
  python scripts/rename_images.py              # 预览重命名
  python scripts/rename_images.py --execute    # 执行重命名
  python scripts/rename_images.py --prefix girl --start 1
  python scripts/rename_images.py --reset      # 重置编号，从头开始
"""

import os
import sys
import re
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
    parser.add_argument("--reset", "-r", action="store_true", help="重置编号从1开始，忽略已有编号")
    
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
    
    # 过滤出已经是目标格式的文件
    existing_girls = []
    others = []
    pattern = re.compile(rf'^{args.prefix}_(\d+)\.', re.IGNORECASE)
    
    for img in images:
        if pattern.match(img.name):
            existing_girls.append(img)
        else:
            others.append(img)
    
    # 确定起始编号
    start_num = args.start
    
    if not args.reset and existing_girls:
        # 找出最大的编号
        max_num = 0
        for img in existing_girls:
            match = pattern.match(img.name)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        if max_num >= start_num:
            start_num = max_num + 1
            print(f"📌 检测到已有编号，从 {start_num} 开始")
    
    # 构建重命名计划
    rename_plan = []
    skipped = 0
    current_num = start_num
    
    # 先处理非标准命名的文件（others）
    # 再处理已存在的 girl_xx 文件（重新编号）
    process_files = others + existing_girls
    
    # 如果 reset，全部重新编号
    if args.reset:
        process_files = images
        current_num = args.start
        print(f"📌 重置模式: 全部从 {current_num} 开始编号")
    
    for img_path in process_files:
        # 检查是否是目标格式且不需要重命名
        match = pattern.match(img_path.name)
        if match and not args.reset:
            num = int(match.group(1))
            # 如果编号与当前编号一致，保留
            if num == current_num:
                print(f"  ⏭️  {img_path.name} -> 已是目标名称，跳过")
                skipped += 1
                current_num += 1
                continue
        
        ext = img_path.suffix.lower()
        new_name = f"{args.prefix}_{current_num:0{args.digits}d}{ext}"
        new_path = img_path.parent / new_name
        
        # 检查目标文件是否已存在
        if new_path.exists() and new_path != img_path:
            print(f"  ⚠️  {img_path.name} -> {new_name} 已存在，跳过")
            skipped += 1
            current_num += 1
            continue
        
        rename_plan.append((img_path, new_path))
        current_num += 1
    
    if not rename_plan:
        print("\n✅ 所有图片已符合命名规范，无需重命名")
        if skipped > 0:
            print(f"   (跳过了 {skipped} 个文件)")
        return
    
    print("\n📋 重命名计划:")
    print("-" * 60)
    for old, new in rename_plan[:30]:
        print(f"  {old.name} -> {new.name}")
    if len(rename_plan) > 30:
        print(f"  ... 还有 {len(rename_plan) - 30} 个文件")
    
    print("-" * 60)
    print(f"共 {len(rename_plan)} 个文件需要重命名")
    if skipped > 0:
        print(f"(跳过 {skipped} 个文件)")
    
    if not args.execute:
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