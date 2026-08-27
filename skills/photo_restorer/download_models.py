#!/usr/bin/env python3
"""
download_models.py - 自动下载老照片修复所需的AI模型权重
支持 Windows/Linux/macOS 跨平台
使用方法: python download_models.py
"""

import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import shutil
import time

# 颜色输出（跨平台）
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'
    
    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.CYAN = cls.NC = ''

# 如果是 Windows，禁用颜色
if os.name == 'nt':
    Colors.disable()

class ModelDownloader:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent.parent.parent
        self.models_dir = self.project_root / "models"
        
        # 模型定义
        self.models = [
            {
                "name": "Real-ESRGAN_x4plus",
                "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
                "filename": "RealESRGAN_x4plus.pth",
                "size_mb": 64,
                "md5": None  # 可选：添加 MD5 校验
            },
            {
                "name": "Real-ESRGAN_x4plus_anime",
                "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
                "filename": "RealESRGAN_x4plus_anime_6B.pth",
                "size_mb": 24,
                "md5": None
            },
            {
                "name": "GFPGANv1.3",
                "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
                "filename": "GFPGANv1.3.pth",
                "size_mb": 330,
                "md5": None
            },
            {
                "name": "GFPGANv1.4",
                "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
                "filename": "GFPGANv1.4.pth",
                "size_mb": 330,
                "md5": None
            },
            {
                "name": "CodeFormer",
                "url": "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth",
                "filename": "codeformer.pth",
                "size_mb": 400,
                "md5": None
            },
            {
                "name": "RealESRGANv2-anime",
                "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/realesrgan_anime_video_v3.pth",
                "filename": "realesrgan_anime_video_v3.pth",
                "size_mb": 12,
                "md5": None
            }
        ]
        
    def print_header(self):
        print(f"{Colors.CYAN}========================================{Colors.NC}")
        print(f"{Colors.CYAN}📥 老照片修复模型下载工具{Colors.NC}")
        print(f"{Colors.CYAN}========================================{Colors.NC}")
        print(f"项目根目录: {Colors.GREEN}{self.project_root}{Colors.NC}")
        print(f"模型目录: {Colors.GREEN}{self.models_dir}{Colors.NC}")
        print()
    
    def setup_directories(self):
        """创建必要的目录"""
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, filename: str, name: str) -> bool:
        """下载文件（带进度条）"""
        filepath = self.models_dir / filename
        
        # 检查文件是否已存在
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"{Colors.GREEN}✅ {name} 已存在 ({size_mb:.1f} MB)，跳过下载{Colors.NC}")
            return True
        
        print(f"{Colors.YELLOW}📦 下载 {name}...{Colors.NC}")
        print(f"   URL: {url}")
        print(f"   文件: {filename}")
        
        try:
            # 创建请求
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # 打开连接
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                downloaded = 0
                
                # 使用临时文件
                temp_file = filepath.with_suffix('.tmp')
                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = downloaded / total_size
                            bar_length = 40
                            filled = int(bar_length * progress)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            sys.stdout.write(f'\r   [{bar}] {progress*100:.1f}%')
                            sys.stdout.flush()
                
                sys.stdout.write('\n')
                
                # 重命名临时文件
                temp_file.rename(filepath)
                
                if filepath.exists():
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    print(f"{Colors.GREEN}✅ {name} 下载完成 ({size_mb:.1f} MB){Colors.NC}")
                    return True
                else:
                    print(f"{Colors.RED}❌ {name} 下载失败: 文件未保存{Colors.NC}")
                    return False
                    
        except urllib.error.URLError as e:
            print(f"{Colors.RED}❌ {name} 下载失败: 网络错误 - {e}{Colors.NC}")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ {name} 下载失败: {e}{Colors.NC}")
            return False
    
    def download_all(self):
        """下载所有模型"""
        self.print_header()
        self.setup_directories()
        
        print(f"{Colors.CYAN}📋 准备下载以下模型: {Colors.NC}")
        for model in self.models:
            print(f"  - {model['name']} ({model['filename']})")
        print()
        
        success_count = 0
        skip_count = 0
        
        for model in self.models:
            if self.download_file(model['url'], model['filename'], model['name']):
                success_count += 1
            else:
                # 检查是否因已存在而跳过
                if (self.models_dir / model['filename']).exists():
                    skip_count += 1
        
        # 创建配置文件
        self.create_config()
        
        # 显示结果
        print()
        print(f"{Colors.CYAN}========================================{Colors.NC}")
        print(f"{Colors.CYAN}📊 下载结果汇总{Colors.NC}")
        print(f"{Colors.CYAN}========================================{Colors.NC}")
        
        pth_files = list(self.models_dir.glob("*.pth"))
        for f in pth_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name} ({size_mb:.1f} MB)")
        
        print()
        print(f"{Colors.GREEN}✅ 下载完成！{Colors.NC}")
        print(f"模型存放位置: {Colors.GREEN}{self.models_dir}{Colors.NC}")
        
        # 创建软链接/快捷方式提示
        if os.name == 'nt':
            print(f"\n{Colors.YELLOW}💡 提示: 在 skill.py 中设置模型路径:{Colors.NC}")
            print(f"  config = {{'model_weights_dir': '{self.models_dir.as_posix()}'}}")
        else:
            print(f"\n{Colors.YELLOW}💡 提示: 在 skill.py 中设置模型路径:{Colors.NC}")
            print(f"  config = {{'model_weights_dir': '{self.models_dir}'}}")
    
    def create_config(self):
        """创建模型配置文件"""
        config_path = self.models_dir / "models.json"
        config = {
            "models": {},
            "downloaded_at": datetime.now().isoformat(),
            "base_dir": self.models_dir.as_posix()
        }
        
        for model in self.models:
            config["models"][model["filename"].replace('.pth', '')] = {
                "name": model["name"],
                "file": model["filename"],
                "path": (self.models_dir / model["filename"]).as_posix(),
                "type": "gan"
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"{Colors.GREEN}✅ 配置文件已创建: models.json{Colors.NC}")
    
    def verify_models(self):
        """验证模型文件完整性"""
        print(f"{Colors.CYAN}🔍 验证模型文件...{Colors.NC}")
        
        missing = []
        for model in self.models:
            filepath = self.models_dir / model["filename"]
            if not filepath.exists():
                missing.append(model["name"])
            elif model.get("md5"):
                # 验证 MD5
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    if file_hash != model["md5"]:
                        print(f"{Colors.RED}❌ {model['name']} MD5 校验失败{Colors.NC}")
        
        if missing:
            print(f"{Colors.YELLOW}⚠️ 缺少模型: {', '.join(missing)}{Colors.NC}")
            return False
        else:
            print(f"{Colors.GREEN}✅ 所有模型文件验证通过{Colors.NC}")
            return True

def main():
    downloader = ModelDownloader()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--verify":
            downloader.setup_directories()
            downloader.verify_models()
            return
        elif sys.argv[1] == "--list":
            print("可用的模型:")
            for model in downloader.models:
                print(f"  {model['name']} -> {model['filename']}")
            return
    
    # 开始下载
    downloader.download_all()

if __name__ == "__main__":
    main()