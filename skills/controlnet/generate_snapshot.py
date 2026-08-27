#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ControlNet 代码快照生成器
生成项目所有代码文件的文本快照，用于代码审查和文档记录
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Set

# ============ 配置 ============

# 要扫描的目录（当前脚本所在目录）
PROJECT_ROOT = Path(__file__).parent.absolute()

# 输出文件
OUTPUT_FILE = PROJECT_ROOT / "code_snapshot.txt"

# 要包含的文件扩展名
INCLUDE_EXTENSIONS = {
    '.py',           # Python
    '.yaml', '.yml', # 配置文件
    '.md',           # Markdown
    '.txt',          # 文本
    '.sh',           # Shell 脚本
    '.json',         # JSON
    '.cfg', '.conf', # 配置文件
    '.js', '.css',   # Web
    '.html',         # HTML
    '.xml',          # XML
}

# 要排除的目录
EXCLUDE_DIRS = {
    '__pycache__',
    '.git',
    '.github',
    '.vscode',
    '.idea',
    'tmp',
    'output',
    'logs',
    'ckpts',
    'models',
    'mmcv',
    'mmseg',
    'ldm',
    'annotator/midas/midas',      # 第三方库
    'annotator/uniformer/mmcv',
    'annotator/uniformer/mmseg',
    'annotator/uniformer/exp',
}

# 要排除的文件名（完整文件名）
EXCLUDE_FILES = {
    'LICENSE',
    'LICENSE.md',
    '.gitignore',
    '.gitattributes',
    '.gitmodules',
    '.dockerignore',
    'Dockerfile',
    'Makefile',
    'CMakeLists.txt',
    'cog.yaml',
    'environment.yaml',
    'download_weights.py',
    'tutorial_dataset.py',
    'tutorial_dataset_test.py',
    'tutorial_train.py',
    'utils.py',                   # 根目录的工具文件
}

# 排除包含这些关键词的文件
EXCLUDE_PATH_KEYWORDS = {
    'ckpts',            # 检查点文件
    'output',           # 输出目录
    'tmp',              # 临时目录
    '__pycache__',      # Python 缓存
    '.git',             # Git 目录
    'mmcv',             # 第三方库
    'mmseg',            # 第三方库
    'ldm',              # 第三方库
}

# 每个文件最大读取行数（防止大文件）
MAX_LINES_PER_FILE = 2000

# ============ 工具函数 ============

def should_exclude(path: Path, root: Path) -> bool:
    """判断文件/目录是否应该被排除"""
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        return True
    
    # 检查目录排除
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # 检查路径关键词排除
    for keyword in EXCLUDE_PATH_KEYWORDS:
        if keyword in str(path).lower():
            return True
    
    # 检查文件名排除
    if path.name in EXCLUDE_FILES:
        return True
    
    return False

def get_code_files(root: Path) -> List[Path]:
    """递归获取所有代码文件"""
    code_files = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        
        # 过滤排除的目录
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        # 检查当前目录是否应该排除
        if should_exclude(dirpath, root):
            continue
        
        for filename in filenames:
            filepath = dirpath / filename
            
            # 检查文件是否应该排除
            if should_exclude(filepath, root):
                continue
            
            # 检查文件扩展名
            ext = filepath.suffix.lower()
            if ext not in INCLUDE_EXTENSIONS:
                continue
            
            code_files.append(filepath)
    
    return sorted(code_files)

def read_file_content(filepath: Path) -> str:
    """读取文件内容，处理编码问题"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= MAX_LINES_PER_FILE:
                        lines.append(f"\n... (文件超出 {MAX_LINES_PER_FILE} 行，已截断) ...\n")
                        break
                    lines.append(line.rstrip('\n'))
                return '\n'.join(lines)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue
    
    return f"[无法读取文件内容 (编码尝试: {', '.join(encodings)})]"

def get_file_info(filepath: Path, root: Path) -> str:
    """获取文件信息"""
    try:
        rel_path = filepath.relative_to(root)
    except ValueError:
        rel_path = filepath
    
    size = filepath.stat().st_size
    return f"  📄 {rel_path} ({size:,} bytes)"

def generate_snapshot() -> str:
    """生成代码快照"""
    lines = []
    
    # ========== 头部 ==========
    lines.append("=" * 100)
    lines.append("📸 ControlNet 代码快照")
    lines.append("=" * 100)
    lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  项目路径: {PROJECT_ROOT}")
    lines.append(f"  文件限制: {MAX_LINES_PER_FILE} 行/文件")
    lines.append("=" * 100)
    lines.append("")
    
    # ========== 项目概览 ==========
    # 统计信息
    all_files = get_code_files(PROJECT_ROOT)
    
    # 按扩展名统计
    ext_counts = {}
    for f in all_files:
        ext = f.suffix.lower() or '无扩展名'
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    # 按目录统计
    dir_counts = {}
    for f in all_files:
        try:
            rel = f.relative_to(PROJECT_ROOT)
            parent = rel.parent
            dir_key = str(parent) if str(parent) != '.' else '(根目录)'
            dir_counts[dir_key] = dir_counts.get(dir_key, 0) + 1
        except:
            pass
    
    lines.append("📊 项目统计")
    lines.append("-" * 100)
    lines.append(f"  代码文件总数: {len(all_files)}")
    lines.append("")
    
    lines.append("📁 按目录分布:")
    for dir_name, count in sorted(dir_counts.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"    {dir_name}: {count} 个文件")
    if len(dir_counts) > 20:
        lines.append(f"    ... 还有 {len(dir_counts) - 20} 个目录")
    lines.append("")
    
    lines.append("📄 按文件类型分布:")
    for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1]):
        lines.append(f"    {ext}: {count} 个文件")
    lines.append("")
    
    lines.append("=" * 100)
    lines.append("")
    
    # ========== 文件内容 ==========
    lines.append("📄 文件内容")
    lines.append("=" * 100)
    lines.append("")
    
    for idx, filepath in enumerate(all_files, 1):
        try:
            rel_path = filepath.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = filepath
        
        # 文件头
        lines.append("-" * 100)
        lines.append(f"[{idx:>4}/{len(all_files)}] 📄 {rel_path}")
        lines.append(f"  大小: {filepath.stat().st_size:,} bytes")
        lines.append(f"  路径: {filepath}")
        lines.append("-" * 100)
        
        # 文件内容
        content = read_file_content(filepath)
        lines.append(content)
        lines.append("")  # 空行分隔
    
    # ========== 尾部 ==========
    lines.append("=" * 100)
    lines.append("📸 快照生成完成")
    lines.append("=" * 100)
    lines.append(f"  总文件数: {len(all_files)}")
    lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 100)
    
    return '\n'.join(lines)

# ============ 主程序 ============

def main():
    print("=" * 70)
    print("📸 ControlNet 代码快照生成器")
    print("=" * 70)
    print(f"📂 项目路径: {PROJECT_ROOT}")
    print(f"📄 输出文件: {OUTPUT_FILE}")
    print("")
    
    # 检查项目路径是否存在
    if not PROJECT_ROOT.exists():
        print("❌ 项目路径不存在！")
        sys.exit(1)
    
    print("📂 扫描代码文件...")
    files = get_code_files(PROJECT_ROOT)
    print(f"   找到 {len(files)} 个代码文件")
    
    # 显示文件列表（前10个）
    print("\n📄 文件列表（前 10 个）:")
    for i, f in enumerate(files[:10], 1):
        try:
            rel = f.relative_to(PROJECT_ROOT)
        except:
            rel = f
        print(f"   {i:2}. {rel}")
    if len(files) > 10:
        print(f"   ... 还有 {len(files) - 10} 个文件")
    
    print("\n" + "=" * 70)
    print("📝 生成快照...")
    
    # 生成快照
    snapshot = generate_snapshot()
    
    # 保存到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(snapshot)
    
    print(f"✅ 快照已保存: {OUTPUT_FILE}")
    
    # 文件大小
    size = OUTPUT_FILE.stat().st_size
    if size > 1024 * 1024:
        print(f"📦 文件大小: {size / (1024 * 1024):.2f} MB")
    elif size > 1024:
        print(f"📦 文件大小: {size / 1024:.2f} KB")
    else:
        print(f"📦 文件大小: {size} bytes")
    
    print("=" * 70)
    print("✅ 完成！")

if __name__ == "__main__":
    main()