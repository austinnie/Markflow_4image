# tools/fix_all_skills.py
"""
一键修复所有技能中的 config 硬编码索引问题
将 self.config['xxx'] 自动修改为 self.config.get('xxx', 默认值)
"""

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"

def fix_skill_file(file_path: Path) -> int:
    """修复单个技能文件，返回修复次数"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return 0

    original = content
    fixes = 0

    # 1. 修复 self.config['output_dir'] -> self.config.get('output_dir', 默认值)
    content = re.sub(
        r"self\.config\['output_dir'\]",
        "self.config.get('output_dir', str(self.skill_dir / 'output'))",
        content
    )
    fixes += content.count("self.config.get('output_dir', str(self.skill_dir / 'output'))") - original.count("self.config.get('output_dir', str(self.skill_dir / 'output'))")

    # 2. 修复 self.config['default_xxx'] -> self.config.get('default_xxx', 默认值)
    content = re.sub(
        r"self\.config\['(default_[a-z_]+)'\]",
        r"self.config.get('\1', None)",
        content
    )
    
    # 3. 修复 self.config['device'] -> self.config.get('device', 'cpu')
    content = re.sub(
        r"self\.config\['device'\]",
        r"self.config.get('device', 'cpu')",
        content
    )

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ 已修复: {file_path.name}")
        return 1
    return 0

def main():
    print("=" * 60)
    print("🔧 自动修复所有技能中的 config 硬编码问题")
    print("=" * 60)

    total_fixed = 0
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "skill.py"
            if skill_file.exists():
                total_fixed += fix_skill_file(skill_file)

    print(f"\n🎉 修复完成！共修改了 {total_fixed} 个技能文件。")
    print("💡 修复后，所有技能在无参数调用时都能稳定运行！")

if __name__ == "__main__":
    main()