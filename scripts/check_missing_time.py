#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查所有 skills 是否缺少 import time
"""

from pathlib import Path

skills_dir = Path("skills")
missing_time = []

for skill_file in skills_dir.glob("*/skill.py"):
    content = skill_file.read_text(encoding='utf-8')
    # 检查是否使用了 time 相关函数但没有 import time
    if ("time.time()" in content or "time.sleep(" in content):
        if "import time" not in content:
            missing_time.append(skill_file.parent.name)

print("=" * 60)
print("检查结果：缺少 import time 的技能")
print("=" * 60)

if missing_time:
    for name in missing_time:
        print(f"  ❌ {name}")
    print(f"\n共 {len(missing_time)} 个技能需要修复")
    print("\n修复命令：")
    print(f"  python scripts/fix_missing_time.py")
else:
    print("  ✅ 所有技能都已正确导入 time")

print("=" * 60)