#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包项目（包含 .git）用于迁移到其他环境

用法:
  python scripts/pack_project.py                    # 打包当前项目
  python scripts/pack_project.py --output ../my_project_backup.zip  # 指定输出路径
  python scripts/pack_project.py --exclude .venv .idea  # 排除额外目录
  python scripts/pack_project.py --no-git           # 不包含 .git（只打包代码）
  python scripts/pack_project.py --help             # 显示帮助
"""

import os
import sys
import zipfile
import argparse
from pathlib import Path
from datetime import datetime
import subprocess


class ProjectPacker:
    """项目打包器 - 用于迁移项目到其他环境"""
    
    # 默认排除的目录和文件
    DEFAULT_EXCLUDE_DIRS = [
        '__pycache__',
        '.venv',
        'venv',
        'env',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        '.coverage',
        'htmlcov',
        '.eggs',
        '*.egg-info',
        '.git',
        '.idea',
        '.vscode',
        '.DS_Store',
        'Thumbs.db',
        'logs',
        'tmp',
        'temp',
    ]
    
    DEFAULT_EXCLUDE_FILES = [
        '*.pyc',
        '*.pyo',
        '*.so',
        '*.dll',
        '*.dylib',
        '*.exe',
        '*.log',
        '*.tmp',
        '*.swp',
        '*.swo',
    ]
    
    def __init__(self, root_dir: str = ".", output_dir: str = None):
        self.root = Path(root_dir).resolve()
        self.output_dir = Path(output_dir or ".").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.exclude_dirs = set(self.DEFAULT_EXCLUDE_DIRS)
        self.exclude_files = set(self.DEFAULT_EXCLUDE_FILES)
        self.extra_excludes = set()
        self.include_git = True
    
    def set_exclude_dirs(self, dirs: list):
        """添加排除目录"""
        self.extra_excludes.update(dirs)
    
    def set_include_git(self, include: bool):
        """设置是否包含 .git"""
        self.include_git = include
    
    def _should_exclude(self, path: Path) -> bool:
        """检查路径是否应该被排除"""
        name = path.name
        rel_path = str(path.relative_to(self.root))
        
        # 检查目录
        if path.is_dir():
            # 检查是否在排除列表中
            for pattern in self.exclude_dirs | self.extra_excludes:
                if path.match(pattern):
                    return True
                if name == pattern or name in pattern:
                    return True
            return False
        
        # 检查文件
        for pattern in self.exclude_files:
            if path.match(pattern):
                return True
        
        return False
    
    def pack(self, output_filename: str = None) -> Path:
        """打包项目"""
        if not self.root.exists():
            raise FileNotFoundError(f"项目目录不存在: {self.root}")
        
        # 检查是否是 Git 仓库
        git_dir = self.root / ".git"
        is_git_repo = git_dir.exists() and git_dir.is_dir()
        
        if is_git_repo and self.include_git:
            print(f"📦 打包 Git 仓库 (包含提交记录): {self.root}")
            # 获取当前分支
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                branch = result.stdout.strip() if result.returncode == 0 else "unknown"
                print(f"📌 当前分支: {branch}")
            except:
                branch = "unknown"
        elif is_git_repo and not self.include_git:
            print(f"📦 打包代码 (不包含 .git): {self.root}")
        else:
            print(f"📦 打包项目目录: {self.root}")
        
        # 生成文件名
        if not output_filename:
            project_name = self.root.name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{project_name}_{timestamp}.zip"
        
        output_path = self.output_dir / output_filename
        
        print(f"\n📁 输出文件: {output_path}")
        print(f"📂 排除目录: {', '.join(sorted(self.exclude_dirs | self.extra_excludes)[:10])}")
        if len(self.exclude_dirs | self.extra_excludes) > 10:
            print(f"   ... 等 {len(self.exclude_dirs | self.extra_excludes)} 项")
        print(f"📄 排除文件: {', '.join(sorted(self.exclude_files)[:5])}")
        print("-" * 60)
        
        # 收集文件
        files_to_pack = []
        total_size = 0
        
        for item in self.root.rglob("*"):
            # 跳过根目录本身
            if item == self.root:
                continue
            
            # 检查是否应该排除
            if self._should_exclude(item):
                continue
            
            # 排除 .git（如果不包含）
            if not self.include_git and ".git" in item.parts:
                continue
            
            # 跳过空目录
            if item.is_dir() and not any(item.iterdir()):
                continue
            
            if item.is_file():
                rel_path = item.relative_to(self.root)
                files_to_pack.append((item, rel_path))
                total_size += item.stat().st_size
        
        if not files_to_pack:
            print("❌ 没有找到任何文件")
            return None
        
        print(f"📊 共 {len(files_to_pack)} 个文件, 总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 打包
        print(f"⏳ 正在打包...")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, rel_path in files_to_pack:
                try:
                    zf.write(file_path, rel_path)
                except Exception as e:
                    print(f"⚠️ 跳过文件 {rel_path}: {e}")
        
        # 显示结果
        result_size = output_path.stat().st_size / 1024 / 1024
        print(f"\n✅ 打包完成!")
        print(f"   文件: {output_path}")
        print(f"   大小: {result_size:.2f} MB")
        
        # 显示 Git 信息
        if is_git_repo and self.include_git:
            print(f"\n📋 Git 信息:")
            print(f"   提交记录已包含，在另一个环境解压后可直接 push")
            print(f"   git remote add origin <仓库地址>")
            print(f"   git push origin {branch}")
        
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="打包项目（包含 .git）用于迁移到其他环境",
        epilog="""
示例:
  python scripts/pack_project.py                         # 打包当前项目
  python scripts/pack_project.py -o ../backup.zip        # 指定输出路径
  python scripts/pack_project.py --exclude .venv .idea   # 排除额外目录
  python scripts/pack_project.py --no-git                # 不包含 .git
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径 (默认: ./<项目名>_<时间戳>.zip)"
    )
    parser.add_argument(
        "--exclude", "-e",
        nargs="+",
        default=[],
        help="额外排除的目录或文件"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="不包含 .git 目录 (只打包代码)"
    )
    parser.add_argument(
        "--root", "-r",
        default=".",
        help="项目根目录 (默认: 当前目录)"
    )
    
    args = parser.parse_args()
    
    packer = ProjectPacker(args.root)
    
    # 设置排除项
    if args.exclude:
        packer.set_exclude_dirs(args.exclude)
    
    if args.no_git:
        packer.set_include_git(False)
    
    # 执行打包
    packer.pack(args.output)


if __name__ == "__main__":
    main()