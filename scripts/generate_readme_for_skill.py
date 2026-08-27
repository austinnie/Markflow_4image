#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为指定技能生成 README.md
用法：
  python scripts/generate_skill_readme.py sd_image_generator
  python scripts/generate_skill_readme.py novel_writer
  python scripts/generate_skill_readme.py --all
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def generate_readme(skill_name: str):
    """为单个技能生成 README"""
    print(f"生成 {skill_name}/README.md...")

    skill_dir = project_root / "skills" / skill_name
    if not skill_dir.exists():
        print(f"  错误: 技能 {skill_name} 不存在")
        return False

    # 读取 meta.json
    meta_file = skill_dir / "meta.json"
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            description = meta.get('description', f'{skill_name} 技能')
    else:
        description = f'{skill_name} 技能'

    try:
        # 导入 execute_skill
        from markflow.cli.commands import execute_skill

        # 注意：这里的 skill_name 是传给 doc_generator 技能的参数
        # 需要放在一个字典里，避免和 execute_skill 的参数冲突
        result = execute_skill(
            "doc_generator",
            code_path=str(skill_dir / "skill.py"),
            doc_type="readme",
            skill_name_param=skill_name,  # 改名避免冲突
            project_name=skill_name,
            project_description=description
        )

        if result is not None and result.get('status') == 'success':
            print(f"  ✅ {skill_name}/README.md 生成成功")
            return True
        else:
            print(f"  ❌ {skill_name} 生成失败")
            return False

    except Exception as e:
        print(f"  ❌ {skill_name} 生成失败: {e}")
        return False


def generate_all():
    """为所有技能生成 README"""
    skills_dir = project_root / "skills"
    skills = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "skill.py").exists()]

    print(f"📚 找到 {len(skills)} 个技能")
    print("=" * 40)

    success = 0
    for skill_name in skills:
        if generate_readme(skill_name):
            success += 1

    print("=" * 40)
    print(f"✅ 完成: 成功 {success}/{len(skills)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/generate_skill_readme.py <skill_name>")
        print("  python scripts/generate_skill_readme.py --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        generate_all()
    else:
        generate_readme(sys.argv[1])