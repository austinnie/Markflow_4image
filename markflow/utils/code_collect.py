"""
代码收集器 - 收集项目代码，生成汇总报告、打包或生成单一 TXT 文件
"""

import os
import json
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse


class CodeCollector:
    """代码收集器 - 收集并汇总/打包项目中的所有代码文件"""
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.xml': 'XML',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        '.go': 'Go',
        '.rs': 'Rust',
        '.java': 'Java',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.pl': 'Perl',
        '.lua': 'Lua',
        '.r': 'R',
        '.swift': 'Swift',
        '.m': 'Objective-C',
        '.mm': 'Objective-C++',
        '.dart': 'Dart',
        '.ex': 'Elixir',
        '.exs': 'Elixir Script',
        '.erl': 'Erlang',
        '.hrl': 'Erlang Header',
        '.clj': 'Clojure',
        '.fs': 'F#',
        '.fsx': 'F# Script',
        '.vb': 'Visual Basic',
        '.vbs': 'VBScript',
        '.lisp': 'Lisp',
        '.el': 'Emacs Lisp',
        '.rkt': 'Racket',
        '.scm': 'Scheme',
        '.ml': 'OCaml',
        '.mli': 'OCaml Interface',
        '.hs': 'Haskell',
        '.lhs': 'Literate Haskell',
    }
    
    IGNORE_DIRS = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules', 'vendor',
        'dist', 'build', 'target', 'out', 'bin', 'obj', '.idea', '.vscode',
        '.mypy_cache', '.pytest_cache', '.coverage', 'htmlcov', '.tox',
        'venv', 'env', '.env', 'virtualenv', '.eggs', '*.egg-info',
        '.mvn', '.gradle', '.settings', 'logs', 'tmp', 'temp',
        'collected_code', 'skills', 'generated_images', 'generated_novels',
        'audio_output',
    }
    
    IGNORE_PATTERNS = {
        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib', '*.exe',
        '*.class', '*.o', '*.a', '*.lib', '*.jar', '*.war', '*.ear',
        '*.zip', '*.tar.gz', '*.rar', '*.7z', '*.log', '*.tmp', '*.swp',
        '*.swo', '*~', '*.bak', '*.orig', '*.rej', '.DS_Store', 'Thumbs.db',
        'desktop.ini', '*.safetensors', '*.ckpt', '*.pth', '*.bin',
        '*.mp3', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico',
        '*.pdf', '*.doc', '*.docx',
    }
    
    def __init__(self, root_dir: str = ".", output_dir: str = "collected_code"):
        self.root_dir = Path(root_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files: List[Path] = []
        self.file_info: List[Dict] = []
        self.stats: Dict = {
            'total_files': 0,
            'total_lines': 0,
            'total_characters': 0,
            'by_extension': {},
            'by_language': {},
            'largest_files': [],
        }
    
    def collect(self, include_extensions: List[str] = None, 
                exclude_dirs: List[str] = None,
                exclude_files: List[str] = None) -> List[Path]:
        include_extensions = include_extensions or list(self.SUPPORTED_EXTENSIONS.keys())
        exclude_dirs = exclude_dirs or []
        exclude_files = exclude_files or []
        
        ignore_dirs = self.IGNORE_DIRS | set(exclude_dirs)
        ignore_patterns = self.IGNORE_PATTERNS | set(exclude_files)
        
        self.files = []
        self.file_info = []
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_characters': 0,
            'by_extension': {},
            'by_language': {},
            'largest_files': [],
        }
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                file_path = Path(root) / file
                if self._should_ignore(file_path, ignore_patterns):
                    continue
                ext = file_path.suffix.lower()
                if ext not in include_extensions:
                    continue
                self.files.append(file_path)
        
        return self.files
    
    def _should_ignore(self, file_path: Path, patterns: set) -> bool:
        for pattern in patterns:
            if file_path.match(pattern):
                return True
        if file_path.name.startswith('.'):
            return True
        return False
    
    def _collect_file_info(self, file_path: Path) -> Optional[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            lines = content.splitlines()
            stat = file_path.stat()
            ext = file_path.suffix.lower()
            language = self.SUPPORTED_EXTENSIONS.get(ext, 'Unknown')
            rel_path = file_path.relative_to(self.root_dir)
            return {
                'path': str(rel_path),
                'extension': ext,
                'language': language,
                'size': stat.st_size,
                'lines': len(lines),
                'characters': len(content),
                'content': content,
            }
        except Exception as e:
            print(f"⚠️  读取文件失败: {file_path} - {e}")
            return None
    
    def _update_stats(self, info: Dict):
        ext = info['extension']
        language = info['language']
        self.stats['total_lines'] += info['lines']
        self.stats['total_characters'] += info['characters']
        self.stats['by_extension'][ext] = self.stats['by_extension'].get(ext, 0) + 1
        self.stats['by_language'][language] = self.stats['by_language'].get(language, 0) + 1
    
    # ===================== 功能1: 生成单一 TXT（最重要的功能） =====================
    
    def export_txt(self, filename: str = "code_snapshot.txt", 
                   include_meta: bool = True,
                   include_content: bool = True) -> Path:
        """
        导出为单一 TXT 文件 - 适合分享给 AI 分析
        
        Args:
            filename: 输出文件名
            include_meta: 是否包含元信息
            include_content: 是否包含文件内容
        """
        output_file = self.output_dir / filename
        
        lines = []
        
        # 文件头
        lines.append("=" * 80)
        lines.append("代码快照 - Code Snapshot")
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append(f"项目根目录: {self.root_dir}")
        lines.append(f"总文件数: {self.stats['total_files']}")
        lines.append(f"总代码行数: {self.stats['total_lines']:,}")
        lines.append(f"总字符数: {self.stats['total_characters']:,}")
        lines.append("=" * 80)
        lines.append("")
        
        if include_meta:
            # 按语言统计
            lines.append("【按语言统计】")
            lines.append("-" * 40)
            for lang, count in sorted(self.stats['by_language'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {lang}: {count} 个文件")
            lines.append("")
            
            # 按扩展名统计
            lines.append("【按扩展名统计】")
            lines.append("-" * 40)
            for ext, count in sorted(self.stats['by_extension'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {ext}: {count} 个文件")
            lines.append("")
            
            # 文件列表
            lines.append("【文件列表】")
            lines.append("-" * 40)
            for f in self.file_info:
                lines.append(f"  {f['path']} ({f['lines']} 行, {f['size'] / 1024:.1f} KB)")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        if include_content:
            # 文件内容
            lines.append("【文件内容】")
            lines.append("=" * 80)
            lines.append("")
            
            for f in self.file_info:
                lines.append("")
                lines.append("=" * 80)
                lines.append(f"文件: {f['path']}")
                lines.append(f"语言: {f['language']}")
                lines.append(f"行数: {f['lines']}")
                lines.append(f"大小: {f['size'] / 1024:.1f} KB")
                lines.append("-" * 80)
                lines.append("")
                lines.append(f['content'])
                lines.append("")
        
        # 文件尾
        lines.append("")
        lines.append("=" * 80)
        lines.append("代码快照结束")
        lines.append("=" * 80)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_file
    
    # ===================== 功能2: 打包 ZIP =====================
    
    def pack_to_zip(self, filename: str = None, include_meta: bool = True) -> Path:
        if not self.file_info:
            print("⚠️  请先运行 collect() 收集文件")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = self.root_dir.name
            filename = f"{project_name}_snapshot_{timestamp}"
        
        zip_path = self.output_dir / f"{filename}.zip"
        
        print(f"📦 打包 {len(self.file_info)} 个文件到: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for info in self.file_info:
                file_path = self.root_dir / info['path']
                zf.write(file_path, info['path'])
            
            if include_meta:
                meta_data = {
                    'snapshot_created': datetime.now().isoformat(),
                    'project_root': str(self.root_dir),
                    'total_files': self.stats['total_files'],
                    'total_lines': self.stats['total_lines'],
                    'total_characters': self.stats['total_characters'],
                    'by_extension': self.stats['by_extension'],
                    'by_language': self.stats['by_language'],
                    'files': [
                        {
                            'path': f['path'],
                            'extension': f['extension'],
                            'language': f['language'],
                            'size': f['size'],
                            'lines': f['lines'],
                        }
                        for f in self.file_info
                    ]
                }
                zf.writestr('__meta__.json', json.dumps(meta_data, indent=2, ensure_ascii=False))
        
        print(f"✅ 打包完成: {zip_path}")
        return zip_path
    
    # ===================== 功能3: 生成报告 =====================
    
    def export_json(self, filename: str = "code_collection.json") -> Path:
        output_file = self.output_dir / filename
        export_data = {
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'root_dir': str(self.root_dir),
                'total_files': self.stats['total_files'],
                'total_lines': self.stats['total_lines'],
                'total_characters': self.stats['total_characters']
            },
            'stats': {
                'by_extension': self.stats['by_extension'],
                'by_language': self.stats['by_language'],
            },
            'files': [
                {
                    'path': f['path'],
                    'extension': f['extension'],
                    'language': f['language'],
                    'size': f['size'],
                    'lines': f['lines'],
                }
                for f in self.file_info
            ]
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        return output_file
    
    def export_markdown(self, filename: str = "code_collection.md") -> Path:
        output_file = self.output_dir / filename
        lines = []
        lines.append("# 代码收集报告")
        lines.append("")
        lines.append(f"**收集时间**: {datetime.now().isoformat()}")
        lines.append(f"**项目根目录**: `{self.root_dir}`")
        lines.append("")
        lines.append("## 概览")
        lines.append("")
        lines.append(f"- 总文件数: **{self.stats['total_files']}**")
        lines.append(f"- 总代码行数: **{self.stats['total_lines']:,}**")
        lines.append(f"- 总字符数: **{self.stats['total_characters']:,}**")
        lines.append("")
        lines.append("## 按语言统计")
        lines.append("")
        lines.append("| 语言 | 文件数 |")
        lines.append("|------|--------|")
        for lang, count in sorted(self.stats['by_language'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {lang} | {count} |")
        lines.append("")
        lines.append("## 按扩展名统计")
        lines.append("")
        lines.append("| 扩展名 | 文件数 |")
        lines.append("|--------|--------|")
        for ext, count in sorted(self.stats['by_extension'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {ext} | {count} |")
        lines.append("")
        lines.append("## 所有文件列表")
        lines.append("")
        lines.append("| 文件 | 行数 | 大小 |")
        lines.append("|------|------|------|")
        for f in self.file_info:
            lines.append(f"| `{f['path']}` | {f['lines']:,} | {f['size'] / 1024:.1f} KB |")
        lines.append("")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return output_file


# ===================== 命令行入口 =====================

def main():
    parser = argparse.ArgumentParser(
        description="代码收集器 - 生成代码快照 (TXT) 或打包",
        epilog="""
示例:
  # 生成 TXT 快照（推荐，直接复制分享）
  python code_collect.py --txt

  # 生成 TXT 快照 + 打包 ZIP
  python code_collect.py --txt --pack

  # 只打包 ZIP
  python code_collect.py --pack

  # 指定输出文件名
  python code_collect.py --txt --name my_code_snapshot
        """
    )
    
    parser.add_argument("--root", "-r", default=".", help="项目根目录 (默认: 当前目录)")
    parser.add_argument("--output", "-o", default="collected_code", help="输出目录")
    
    # 功能选择
    parser.add_argument("--txt", action="store_true", help="生成单一 TXT 文件（推荐）")
    parser.add_argument("--pack", action="store_true", help="打包成 ZIP")
    parser.add_argument("--json", action="store_true", help="生成 JSON 报告")
    parser.add_argument("--md", action="store_true", help="生成 Markdown 报告")
    
    # 选项
    parser.add_argument("--name", "-n", default=None, help="输出文件名（不含扩展名）")
    parser.add_argument("--no-content", action="store_true", help="TXT 中不包含文件内容")
    parser.add_argument("--extensions", "-e", nargs="+", help="只包含指定扩展名")
    parser.add_argument("--exclude-dir", nargs="+", help="排除指定目录")
    
    args = parser.parse_args()
    
    # 如果没有任何操作，默认生成 TXT
    if not args.txt and not args.pack and not args.json and not args.md:
        args.txt = True
        print("💡 未指定操作，默认生成 TXT 快照")
    
    # 初始化收集器
    collector = CodeCollector(args.root, args.output)
    
    # 收集文件
    print("🔍 正在收集代码文件...")
    include_ext = args.extensions if args.extensions else None
    exclude_dirs = args.exclude_dir if args.exclude_dir else None
    
    files = collector.collect(
        include_extensions=include_ext,
        exclude_dirs=exclude_dirs
    )
    
    print(f"📊 找到 {len(files)} 个代码文件")
    
    # 收集文件详情
    for file_path in files:
        info = collector._collect_file_info(file_path)
        if info:
            collector.file_info.append(info)
            collector._update_stats(info)
    
    collector.stats['total_files'] = len(collector.file_info)
    
    # 执行操作
    if args.json:
        print("\n📝 生成 JSON 报告...")
        path = collector.export_json()
        print(f"   ✅ {path}")
    
    if args.md:
        print("\n📝 生成 Markdown 报告...")
        path = collector.export_markdown()
        print(f"   ✅ {path}")
    
    if args.txt:
        print("\n📝 生成 TXT 快照...")
        filename = f"{args.name}.txt" if args.name else "code_snapshot.txt"
        path = collector.export_txt(filename, include_content=not args.no_content)
        size_kb = path.stat().st_size / 1024
        print(f"   ✅ {path} ({size_kb:.1f} KB)")
        print(f"\n💡 打开 {path}，复制全部内容即可分享")
    
    if args.pack:
        print("\n📦 打包 ZIP...")
        zip_name = args.name if args.name else None
        path = collector.pack_to_zip(zip_name)
        if path:
            size_kb = path.stat().st_size / 1024
            print(f"   ✅ {path} ({size_kb:.1f} KB)")
    
    print(f"\n✅ 完成! 输出目录: {args.output}")


if __name__ == "__main__":
    main()