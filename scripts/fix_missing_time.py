#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修复技能文件缺少 import time 的问题
"""

import re
from pathlib import Path

skills_dir = Path("skills")

# 需要修复的技能列表（从检查脚本获取）
SKILLS_TO_FIX = [
    "add_animal_ears",
    "add_background_objects",
    "add_glasses",
    "add_tattoo",
    "anime_to_real",
    "change_age",
    "change_body_type",
    "change_clothing_style",
    "change_expression",
    "change_eye_color",
    "change_face",
    "change_furniture",
    "change_gender",
    "change_hair",
    "change_lighting",
    "change_makeup",
    "change_nationality",
    "change_perspective",
    "change_skin_tone",
    "colorize_sketch",
    "day_night_transfer",
    "old_photo_restore",
    "real_to_anime",
    "remove_object",
    "replace_object",
    "season_transfer",
    "style_transfer",
    "weather_transfer",
]


def fix_time_import(skill_path: Path) -> bool:
    """在文件开头添加 import time"""
    if not skill_path.exists():
        print(f"  ❌ 文件不存在: {skill_path}")
        return False

    content = skill_path.read_text(encoding='utf-8')

    # 检查是否已有 import time
    if "import time" in content:
        print(f"  ⏭️  {skill_path.parent.name} 已有 import time")
        return False

    # 在文件顶部添加 import time（在 docstring 之后，其他 import 之前）
    lines = content.split("\n")

    # 找到插入位置：跳过 shebang、docstring、空行
    insert_pos = 0
    in_docstring = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过 shebang
        if stripped.startswith("#!") and i == 0:
            insert_pos = i + 1
            continue

        # 处理 docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_docstring:
                in_docstring = False
                insert_pos = i + 1
                continue
            else:
                in_docstring = True
                insert_pos = i + 1
                continue

        if in_docstring:
            insert_pos = i + 1
            continue

        # 跳过空行
        if not stripped:
            insert_pos = i + 1
            continue

        # 跳过注释
        if stripped.startswith("#"):
            insert_pos = i + 1
            continue

        # 找到第一个非注释、非空行（通常是 import）
        insert_pos = i
        break

    # 插入 import time
    lines.insert(insert_pos, "import time")
    new_content = "\n".join(lines)

    skill_path.write_text(new_content, encoding='utf-8')
    print(f"  ✅ {skill_path.parent.name} 已添加 import time")
    return True


def main():
    print("=" * 60)
    print("🔧 批量修复缺少 import time 的技能")
    print("=" * 60)

    if not skills_dir.exists():
        print(f"❌ skills 目录不存在: {skills_dir}")
        return

    fixed_count = 0

    for skill_name in SKILLS_TO_FIX:
        skill_file = skills_dir / skill_name / "skill.py"
        if fix_time_import(skill_file):
            fixed_count += 1

    print("=" * 60)
    print(f"✅ 完成! 修复了 {fixed_count} 个技能")
    print("=" * 60)

    # 再次检查是否还有遗漏
    print("\n🔍 再次检查...")
    missing = []
    for skill_file in skills_dir.glob("*/skill.py"):
        content = skill_file.read_text(encoding='utf-8')
        if ("time.time()" in content or "time.sleep(" in content):
            if "import time" not in content:
                missing.append(skill_file.parent.name)

    if missing:
        print("⚠️ 仍有技能缺少 import time:")
        for name in missing:
            print(f"  - {name}")
    else:
        print("✅ 所有技能都已正确导入 time")


if __name__ == "__main__":
    main()