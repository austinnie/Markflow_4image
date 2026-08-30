#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除所有技能目录下的图片文件
"""

import argparse
from pathlib import Path

# 支持的图片扩展名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def main():
    parser = argparse.ArgumentParser(description="删除所有技能目录下的图片文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际删除")
    parser.add_argument("--skills-dir", default="skills", help="技能目录 (默认: skills)")
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.exists():
        print(f"❌ 目录不存在: {skills_dir}")
        return

    print("=" * 60)
    print("🗑️  删除技能目录下的图片文件")
    print("=" * 60)

    total_files = 0
    total_size = 0

    for skill_file in skills_dir.glob("*/skill.py"):
        skill_dir = skill_file.parent
        images = []

        for ext in IMAGE_EXTS:
            images.extend(skill_dir.glob(f"*{ext}"))

        # 排除 output 目录下的图片
        images = [f for f in images if "output" not in f.parts]

        if images:
            print(f"\n📂 {skill_dir.name}/")
            for img in images:
                size = img.stat().st_size
                total_size += size
                total_files += 1
                print(f"   📄 {img.name} ({size / 1024:.1f} KB)")

    if total_files == 0:
        print("\n✅ 没有找到需要删除的图片文件")
        return

    print("\n" + "=" * 60)
    print(f"📊 共找到 {total_files} 个图片文件")
    print(f"📦 总大小: {total_size / 1024 / 1024:.2f} MB")

    if args.dry_run:
        print("\n💡 预览模式，加上 --execute 参数执行删除")
        print("   python scripts/clean_skill_images.py --execute")
        return

    print("\n⚠️  确认删除? (输入 y 确认)")
    confirm = input("> ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    print("\n🔄 执行删除...")
    deleted = 0
    for skill_file in skills_dir.glob("*/skill.py"):
        skill_dir = skill_file.parent
        for ext in IMAGE_EXTS:
            for img in skill_dir.glob(f"*{ext}"):
                if "output" in img.parts:
                    continue
                try:
                    img.unlink()
                    print(f"  ✅ 删除: {img.parent.name}/{img.name}")
                    deleted += 1
                except Exception as e:
                    print(f"  ❌ 删除失败: {img.name} - {e}")

    print("\n" + "=" * 60)
    print(f"✅ 完成! 删除了 {deleted} 个图片文件")


if __name__ == "__main__":
    main()