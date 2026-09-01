#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片格式转换工具 - 支持 WebP 转 JPEG/PNG 等格式
支持单张图片和目录批量处理

用法：
  # 单张图片转换
  python scripts/convert_image.py --input image.webp --output image.jpg
  python scripts/convert_image.py --input image.webp --format png

  # 目录批量转换（默认转换所有 webp 为 jpg）
  python scripts/convert_image.py --input_dir input/ --format jpg

  # 目录批量转换 + 递归子目录
  python scripts/convert_image.py --input_dir input/ --format png --recursive

  # 目录批量转换 + 保留原目录结构
  python scripts/convert_image.py --input_dir input/ --output_dir output/ --format jpg --recursive --keep-structure

  # 支持多种格式
  python scripts/convert_image.py --input_dir input/ --format png --extensions .webp,.png,.bmp
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# 尝试导入 PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("❌ 请先安装 Pillow: pip install Pillow")
    sys.exit(1)


class ImageConverter:
    """图片格式转换器"""
    
    # 支持的输入格式
    SUPPORTED_INPUT = {'.webp', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.ico'}
    
    # 支持的输出格式（PIL 格式名 → 扩展名）
    SUPPORTED_OUTPUT = {
        'jpeg': '.jpg',
        'jpg': '.jpg',
        'png': '.png',
        'webp': '.webp',
        'bmp': '.bmp',
        'tiff': '.tiff',
        'gif': '.gif',
        'ico': '.ico',
    }
    
    # PIL 格式名映射（统一使用 JPEG）
    FORMAT_MAP = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'bmp': 'BMP',
        'tiff': 'TIFF',
        'gif': 'GIF',
        'ico': 'ICO',
    }
    
    # JPEG 质量映射
    QUALITY_MAP = {
        'low': 50,
        'medium': 70,
        'high': 85,
        'best': 95,
    }
    
    def __init__(self, quality: str = 'high', optimize: bool = True, 
                 max_workers: int = 4, verbose: bool = False):
        """
        初始化转换器
        
        Args:
            quality: 图片质量 (low/medium/high/best)
            optimize: 是否优化图片
            max_workers: 并发线程数
            verbose: 是否显示详细日志
        """
        self.quality = self.QUALITY_MAP.get(quality, 85)
        self.optimize = optimize
        self.max_workers = max_workers
        self.verbose = verbose
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'files': []
        }
    
    def _get_pil_format(self, fmt: str) -> str:
        """获取 PIL 格式名"""
        fmt = fmt.lower()
        return self.FORMAT_MAP.get(fmt, fmt.upper())
    
    def convert_image(self, input_path: Path, output_path: Path, 
                      output_format: str = None, quality: int = None) -> bool:
        """
        转换单张图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            output_format: 输出格式 (jpg/png/webp等)，默认从扩展名推断
            quality: 图片质量 (1-100)
        
        Returns:
            是否转换成功
        """
        try:
            # 检查输入文件是否存在
            if not input_path.exists():
                print(f"❌ 文件不存在: {input_path}")
                return False
            
            # 打开图片
            with Image.open(input_path) as img:
                # 确定输出格式
                if output_format:
                    fmt = output_format.lower()
                else:
                    fmt = output_path.suffix[1:].lower()
                
                # ========== 修复：使用正确的格式名 ==========
                pil_format = self._get_pil_format(fmt)
                
                # 如果是 JPEG，需要转换颜色模式
                if pil_format == 'JPEG':
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # 创建白色背景
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # 保存图片
                save_kwargs = {
                    'optimize': self.optimize
                }
                
                # 设置质量
                q = quality if quality is not None else self.quality
                save_kwargs['quality'] = q
                
                # 特定格式参数
                if pil_format == 'JPEG':
                    save_kwargs['subsampling'] = 0  # 4:4:4 色度采样，更好的质量
                    # 确保 quality 在有效范围内
                    save_kwargs['quality'] = max(1, min(95, save_kwargs['quality']))
                elif pil_format == 'PNG':
                    save_kwargs['compress_level'] = 6  # 平衡压缩和速度
                elif pil_format == 'WEBP':
                    save_kwargs['quality'] = max(1, min(100, save_kwargs['quality']))
                
                # 创建输出目录
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存
                img.save(output_path, format=pil_format, **save_kwargs)
                
                # 统计信息
                input_size = input_path.stat().st_size
                output_size = output_path.stat().st_size
                ratio = (output_size / input_size * 100) if input_size > 0 else 0
                
                if self.verbose:
                    print(f"   ✅ {input_path.name} -> {output_path.name} "
                          f"({input_size/1024:.1f}KB -> {output_size/1024:.1f}KB, {ratio:.1f}%)")
                
                return True
                
        except Exception as e:
            print(f"❌ 转换失败 {input_path.name}: {e}")
            return False
    
    def convert_directory(self, input_dir: Path, output_dir: Path = None,
                          output_format: str = 'jpg',
                          extensions: Set[str] = None,
                          recursive: bool = False,
                          keep_structure: bool = True,
                          overwrite: bool = False,
                          quality: int = None) -> dict:
        """
        批量转换目录中的图片
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录（默认与输入目录相同）
            output_format: 输出格式
            extensions: 要处理的扩展名集合
            recursive: 是否递归子目录
            keep_structure: 是否保持目录结构
            overwrite: 是否覆盖已存在的文件
            quality: 图片质量
        
        Returns:
            统计信息字典
        """
        input_dir = Path(input_dir)
        if not input_dir.exists():
            print(f"❌ 目录不存在: {input_dir}")
            return self.stats
        
        if not input_dir.is_dir():
            print(f"❌ 不是目录: {input_dir}")
            return self.stats
        
        # 设置输出目录
        if output_dir is None:
            output_dir = input_dir
        output_dir = Path(output_dir)
        
        # 设置扩展名
        if extensions is None:
            extensions = {'.webp'}
        extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                      for ext in extensions}
        
        # 收集所有图片
        images = []
        if recursive:
            # 递归遍历
            for ext in extensions:
                images.extend(input_dir.rglob(f'*{ext}'))
                images.extend(input_dir.rglob(f'*{ext.upper()}'))
        else:
            # 只遍历当前目录
            for ext in extensions:
                images.extend(input_dir.glob(f'*{ext}'))
                images.extend(input_dir.glob(f'*{ext.upper()}'))
        
        # 去重并排序
        images = sorted(set(images))
        
        if not images:
            print(f"⚠️ 在 {input_dir} 中没有找到 {', '.join(extensions)} 文件")
            return self.stats
        
        print(f"\n📁 找到 {len(images)} 个文件")
        print(f"📤 输出格式: {output_format}")
        print(f"📂 输出目录: {output_dir}")
        if recursive:
            print(f"📂 递归子目录: 是")
        print("=" * 60)
        
        self.stats['total'] = len(images)
        
        # 准备转换任务
        tasks = []
        for img_path in images:
            # 确定输出路径
            if keep_structure and img_path.parent != input_dir:
                # 保持子目录结构
                rel_path = img_path.parent.relative_to(input_dir)
                out_path = output_dir / rel_path / f"{img_path.stem}.{output_format}"
            else:
                out_path = output_dir / f"{img_path.stem}.{output_format}"
            
            # 检查是否跳过已存在的文件
            if out_path.exists() and not overwrite:
                self.stats['skipped'] += 1
                if self.verbose:
                    print(f"⏭️  跳过已存在: {out_path.name}")
                continue
            
            tasks.append((img_path, out_path))
        
        if not tasks:
            print(f"⚠️ 没有需要转换的文件（{self.stats['skipped']} 个已存在）")
            return self.stats
        
        print(f"🔄 正在转换 {len(tasks)} 个文件...")
        print("-" * 60)
        
        # 并发执行
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for img_path, out_path in tasks:
                future = executor.submit(
                    self.convert_image, 
                    img_path, 
                    out_path, 
                    output_format,
                    quality
                )
                futures[future] = (img_path, out_path)
            
            for future in as_completed(futures):
                img_path, out_path = futures[future]
                if future.result():
                    self.stats['success'] += 1
                    self.stats['files'].append({
                        'input': str(img_path),
                        'output': str(out_path),
                        'success': True
                    })
                else:
                    self.stats['failed'] += 1
                    self.stats['files'].append({
                        'input': str(img_path),
                        'output': str(out_path),
                        'success': False
                    })
        
        elapsed = time.time() - start_time
        
        # 打印统计
        print("=" * 60)
        print(f"📊 转换完成! 耗时: {elapsed:.1f}s")
        print(f"   ✅ 成功: {self.stats['success']}")
        print(f"   ⏭️  跳过: {self.stats['skipped']}")
        print(f"   ❌ 失败: {self.stats['failed']}")
        print(f"   📂 输出目录: {output_dir}")
        print("=" * 60)
        
        return self.stats


def main():
    parser = argparse.ArgumentParser(
        description="图片格式转换工具 - 支持 WebP 转 JPEG/PNG 等",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图片转换
  python scripts/convert_image.py --input image.webp --output image.jpg
  python scripts/convert_image.py --input image.webp --format png

  # 目录批量转换（默认转换所有 webp 为 jpg）
  python scripts/convert_image.py --input_dir input/

  # 目录批量转换 + 指定格式
  python scripts/convert_image.py --input_dir input/ --format png

  # 目录批量转换 + 递归子目录
  python scripts/convert_image.py --input_dir input/ --recursive

  # 目录批量转换 + 保留原目录结构
  python scripts/convert_image.py --input_dir input/ --output_dir output/ --keep-structure --recursive

  # 支持多种输入格式
  python scripts/convert_image.py --input_dir input/ --extensions .webp,.png,.bmp --format jpg

  # 高质量转换
  python scripts/convert_image.py --input_dir input/ --quality best

  # 覆盖已存在的文件
  python scripts/convert_image.py --input_dir input/ --overwrite
        """
    )
    
    # ========== 输入输出参数 ==========
    parser.add_argument("--input", "-i", type=str, help="输入图片路径（单张）")
    parser.add_argument("--input_dir", "-d", type=str, help="输入目录路径（批量）")
    parser.add_argument("--output", "-o", type=str, help="输出路径（单张）或输出目录（批量）")
    parser.add_argument("--format", "-f", type=str, default="jpg", 
                       choices=['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif', 'ico'],
                       help="输出格式 (默认: jpg)")
    
    # ========== 批量处理参数 ==========
    parser.add_argument("--extensions", "-e", type=str, default=".webp",
                       help="要处理的扩展名，用逗号分隔 (默认: .webp)")
    parser.add_argument("--recursive", "-r", action="store_true",
                       help="递归处理子目录")
    parser.add_argument("--keep-structure", "-k", action="store_true",
                       help="保持原目录结构")
    parser.add_argument("--overwrite", action="store_true",
                       help="覆盖已存在的文件")
    
    # ========== 质量参数 ==========
    parser.add_argument("--quality", "-q", type=str, default="high",
                       choices=['low', 'medium', 'high', 'best'],
                       help="图片质量 (low/medium/high/best) (默认: high)")
    
    # ========== 性能参数 ==========
    parser.add_argument("--workers", "-w", type=int, default=4,
                       help="并发线程数 (默认: 4)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="显示详细日志")
    
    args = parser.parse_args()
    
    # ========== 检查依赖 ==========
    if not PIL_AVAILABLE:
        print("❌ 请先安装 Pillow: pip install Pillow")
        sys.exit(1)
    
    # ========== 解析扩展名 ==========
    extensions = set()
    for ext in args.extensions.split(','):
        ext = ext.strip()
        if not ext.startswith('.'):
            ext = f'.{ext}'
        extensions.add(ext.lower())
    
    # ========== 单张图片转换 ==========
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 文件不存在: {input_path}")
            sys.exit(1)
        
        # 确定输出路径
        if args.output:
            output_path = Path(args.output)
        else:
            # 自动生成输出路径
            output_path = input_path.parent / f"{input_path.stem}.{args.format}"
        
        # 创建转换器并执行
        converter = ImageConverter(
            quality=args.quality,
            verbose=args.verbose,
            max_workers=1
        )
        
        print(f"📷 转换: {input_path.name} -> {output_path.name}")
        print("=" * 40)
        
        success = converter.convert_image(input_path, output_path, args.format)
        
        if success:
            print(f"✅ 转换成功: {output_path}")
        else:
            print(f"❌ 转换失败")
            sys.exit(1)
        
        return
    
    # ========== 目录批量转换 ==========
    if args.input_dir:
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output) if args.output else None
        
        # 如果没有指定输出目录，默认与输入目录相同
        if output_dir is None:
            output_dir = input_dir
        
        # 创建转换器
        converter = ImageConverter(
            quality=args.quality,
            verbose=args.verbose,
            max_workers=args.workers
        )
        
        # 执行转换
        result = converter.convert_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=args.format,
            extensions=extensions,
            recursive=args.recursive,
            keep_structure=args.keep_structure,
            overwrite=args.overwrite
        )
        
        if result['failed'] > 0:
            sys.exit(1)
        return
    
    # ========== 没有参数 ==========
    parser.print_help()


if __name__ == "__main__":
    main()