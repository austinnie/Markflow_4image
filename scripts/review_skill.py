#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对已有技能进行 AI 代码审查（不重新生成）
用法: 
  python scripts/review_skill.py doc_generator
  python scripts/review_skill.py doc_generator --model qwen2.5:7b
  python scripts/review_skill.py --list              # 列出所有可审查的技能
  python scripts/review_skill.py --all               # 审查所有技能
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.core.quality import CodeQualityChecker


def list_skills():
    """列出所有可审查的技能"""
    skills_dir = project_root / "skills"
    if not skills_dir.exists():
        print("❌ skills 目录不存在")
        return []
    
    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "skill.py"
            meta_file = skill_dir / "meta.json"
            if skill_file.exists() and meta_file.exists():
                # 读取 meta.json 获取描述
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    description = meta.get('description', '')[:50]
                except:
                    description = ''
                skills.append({
                    'name': skill_dir.name,
                    'description': description,
                    'has_skill': True
                })
    
    return sorted(skills, key=lambda x: x['name'])


def review_skill(skill_name: str, model: str = "qwen2.5:7b", verbose: bool = False):
    """审查指定技能的代码"""
    
    skill_dir = project_root / "skills" / skill_name
    skill_file = skill_dir / "skill.py"
    
    if not skill_file.exists():
        print(f"❌ 技能不存在: {skill_name}")
        print(f"   路径: {skill_file}")
        return False
    
    if verbose:
        print(f"📂 技能: {skill_name}")
        print(f"📄 文件: {skill_file}")
        print(f"🤖 模型: {model}")
        print("-" * 50)
    
    # 读取代码
    code = skill_file.read_text(encoding='utf-8')
    
    if verbose:
        print(f"📊 代码行数: {len(code.splitlines())}")
        print("-" * 50)
    
    # 执行 AI 审查
    if verbose:
        print("⏳ 正在执行 AI 审查...")
    checker = CodeQualityChecker()
    result = checker.review_code_with_ollama(
        code,
        language="python",
        model=model
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    print(f"📋 AI 审查结果: {skill_name}")
    print("=" * 60)
    
    score = result.get("score", 0)
    if score >= 80:
        icon = "🟢"
    elif score >= 60:
        icon = "🟡"
    else:
        icon = "🔴"
    
    print(f"评分: {icon} {score}/100")
    print()
    
    # 维度
    dimensions = result.get("dimensions", {})
    if dimensions:
        print("📊 维度评分:")
        for name, value in dimensions.items():
            bar = "█" * int(value) + "░" * (10 - int(value))
            print(f"   {name}: {value}/10 {bar}")
        print()
    
    # 问题
    issues = result.get("issues", [])
    if issues:
        print(f"🐛 问题 ({len(issues)} 个):")
        for issue in issues[:10]:
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... 还有 {len(issues) - 10} 个问题")
        print()
    
    # 建议
    suggestions = result.get("suggestions", [])
    if suggestions:
        print(f"💡 建议 ({len(suggestions)} 个):")
        for suggestion in suggestions[:5]:
            print(f"   - {suggestion}")
        if len(suggestions) > 5:
            print(f"   ... 还有 {len(suggestions) - 5} 条建议")
        print()
    
    # 总结
    summary = result.get("summary", "")
    if summary:
        print(f"📝 总结: {summary}")
    
    print("=" * 60)
    
    return True


def review_all_skills(model: str = "qwen2.5:7b", verbose: bool = True):
    """审查所有技能"""
    skills = list_skills()
    
    if not skills:
        print("❌ 没有找到可审查的技能")
        return
    
    print(f"\n📚 找到 {len(skills)} 个技能")
    print("=" * 60)
    
    results = []
    for skill in skills:
        name = skill['name']
        print(f"\n▶️ 审查: {name}")
        print("-" * 40)
        
        try:
            success = review_skill(name, model, verbose=False)
            # 重新读取结果（review_skill 已经打印了）
            results.append({
                'name': name,
                'success': success,
                'score': 0  # 无法从 review_skill 获取分数
            })
        except Exception as e:
            print(f"❌ 审查失败: {e}")
            results.append({'name': name, 'success': False, 'score': 0})
    
    print("\n" + "=" * 60)
    print("📊 审查完成")
    print("=" * 60)
    success_count = sum(1 for r in results if r['success'])
    print(f"✅ 成功: {success_count}/{len(results)}")
    print(f"❌ 失败: {len(results) - success_count}/{len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description="AI 审查已有技能",
        epilog="""
示例:
  python scripts/review_skill.py doc_generator           # 审查指定技能
  python scripts/review_skill.py doc_generator -m qwen2.5:14b  # 指定模型
  python scripts/review_skill.py --list                 # 列出所有技能
  python scripts/review_skill.py --all                  # 审查所有技能
  python scripts/review_skill.py --all -m qwen2.5:14b   # 用大模型审查所有
        """
    )
    parser.add_argument("skill", nargs="?", help="技能名称 (如 doc_generator)")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可审查的技能")
    parser.add_argument("--all", "-a", action="store_true", help="审查所有技能")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", 
                       help="Ollama 模型 (默认: qwen2.5:7b)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    
    # --list 优先
    if args.list:
        skills = list_skills()
        if not skills:
            print("❌ 没有找到可审查的技能")
            return
        
        print("\n📚 可审查的技能:")
        print("-" * 60)
        for skill in skills:
            desc = skill.get('description', '')
            print(f"  {skill['name']:<25} {desc[:40]}")
        print("-" * 60)
        print(f"共 {len(skills)} 个技能")
        print("\n💡 使用: python scripts/review_skill.py <技能名称>")
        return
    
    # --all
    if args.all:
        review_all_skills(args.model, args.verbose)
        return
    
    # 单个技能
    if not args.skill:
        parser.print_help()
        return
    
    review_skill(args.skill, args.model, args.verbose)


if __name__ == "__main__":
    main()