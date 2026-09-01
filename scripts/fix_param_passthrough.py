# scripts/fix_param_passthrough.py
"""
批量修复所有技能，添加 **kwargs 参数透传
用法: python scripts/fix_param_passthrough.py
      python scripts/fix_param_passthrough.py --dry-run  # 预览模式
      python scripts/fix_param_passthrough.py --skill change_clothes  # 只修复指定技能
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple, Set

# 配置
SKILLS_DIR = Path("skills")
SKIP_SKILLS = {
    "controlnet_img2img",  # 核心技能，已手动修改
    "sd_image_generator",  # 文生图，不调用 controlnet
}


def find_skills_to_fix() -> List[Path]:
    """找出所有需要修复的技能"""
    skills = []
    if not SKILLS_DIR.exists():
        print(f"❌ skills 目录不存在: {SKILLS_DIR}")
        return skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        if skill_dir.name in SKIP_SKILLS:
            continue
        
        skill_file = skill_dir / "skill.py"
        if skill_file.exists():
            skills.append(skill_file)
    
    return skills


def fix_skill_file(skill_file: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    修复单个技能文件
    返回: (是否修改, 修改次数)
    """
    content = skill_file.read_text(encoding='utf-8')
    original = content
    changes = 0
    
    # ============================================================
    # 修复 1: execute 方法签名添加 **kwargs
    # ============================================================
    # 匹配: def execute(self, ...):
    # 需要处理各种情况:
    #   - def execute(self, image_path: str, output_path: str = None):
    #   - def execute(self, image_path, output_path=None):
    #   - def execute(self, **kwargs):
    #   - def execute(self):
    
    def fix_execute_signature(match):
        nonlocal changes
        indent = match.group(1)  # 缩进
        params = match.group(2).strip()
        
        # 如果已经有 **kwargs，跳过
        if '**kwargs' in params:
            return match.group(0)
        
        # 构建新参数
        if params == '' or params == 'self':
            new_params = 'self, **kwargs'
        else:
            # 检查是否以逗号结尾
            if params.endswith(','):
                new_params = f'{params} **kwargs'
            else:
                new_params = f'{params}, **kwargs'
        
        new_line = f'{indent}def execute({new_params}):'
        changes += 1
        return new_line
    
    # 使用更精确的正则匹配 execute 方法定义
    pattern1 = r'(\s*)def\s+execute\s*\(([^)]*)\)\s*:'
    content = re.sub(pattern1, fix_execute_signature, content)
    
    # ============================================================
    # 修复 2: 调用 execute_skill("controlnet_img2img", ...) 添加 **kwargs
    # ============================================================
    # 匹配各种调用形式:
    #   execute_skill("controlnet_img2img", image_path=image_path)
    #   execute_skill("controlnet_img2img", image_path=image_path, prompt=prompt)
    #   execute_skill( "controlnet_img2img", ... )
    
    def fix_execute_call(match):
        nonlocal changes
        prefix = match.group(1)
        args = match.group(2)
        
        # 如果已经有 **kwargs，跳过
        if '**kwargs' in args:
            return match.group(0)
        
        # 检查是否以逗号结尾
        if args.endswith(','):
            new_args = f'{args} **kwargs'
        else:
            new_args = f'{args}, **kwargs'
        
        changes += 1
        return f'{prefix}execute_skill("controlnet_img2img", {new_args})'
    
    # 匹配 execute_skill 调用（支持跨行）
    pattern2 = r'(\s*)execute_skill\s*\(\s*["\']controlnet_img2img["\']\s*,\s*([^)]*(?:\([^)]*\)[^)]*)*?)\)'
    
    # 由于跨行匹配复杂，先用简单版本
    content = re.sub(pattern2, fix_execute_call, content, flags=re.DOTALL)
    
    # ============================================================
    # 修复 3: 如果内容有变化，保存
    # ============================================================
    if content != original:
        if not dry_run:
            skill_file.write_text(content, encoding='utf-8')
        return True, changes
    
    return False, 0


def main():
    parser = argparse.ArgumentParser(description="批量修复技能参数透传")
    parser.add_argument("--dry-run", "-d", action="store_true", help="预览模式，不实际修改")
    parser.add_argument("--skill", "-s", type=str, help="只修复指定技能")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 批量修复技能参数透传")
    if args.dry_run:
        print("📋 预览模式 (不会修改文件)")
    print("=" * 60)
    
    # 找到要修复的技能
    if args.skill:
        skill_file = SKILLS_DIR / args.skill / "skill.py"
        if not skill_file.exists():
            print(f"❌ 技能不存在: {args.skill}")
            return
        skill_files = [skill_file]
    else:
        skill_files = find_skills_to_fix()
    
    if not skill_files:
        print("❌ 没有找到需要修复的技能")
        return
    
    print(f"📁 找到 {len(skill_files)} 个技能需要检查")
    print("-" * 60)
    
    # 执行修复
    fixed = []
    total_changes = 0
    
    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        fixed_flag, changes = fix_skill_file(skill_file, args.dry_run)
        
        if fixed_flag:
            fixed.append((skill_name, changes))
            total_changes += changes
            print(f"  ✅ {skill_name} ({changes} 处修改)")
        elif args.verbose:
            print(f"  ⏭️  {skill_name} (无需修改)")
    
    # 总结
    print("-" * 60)
    print(f"📊 修改了 {len(fixed)} 个技能, 共 {total_changes} 处修改")
    
    if fixed:
        print(f"   修改列表: {', '.join([s for s, _ in fixed])}")
    
    if args.dry_run:
        print("\n💡 预览完成，去掉 --dry-run 参数执行实际修改")
        print("   python scripts/fix_param_passthrough.py")
    
    print("=" * 60)


if __name__ == "__main__":
    main()