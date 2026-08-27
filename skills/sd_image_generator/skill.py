"""
SDImageGenerator - 使用本地 Stable Diffusion 模型生成图片的技能
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 导入 SD 相关库
try:
    import torch
    from diffusers import StableDiffusionPipeline
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")


class Sdimagegenerator:
    """
    使用本地 Stable Diffusion 模型生成图片的技能
    
    利用 E:/SD_OpenVINO/models 目录下的模型文件生成图片
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化技能
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.name = "SDImageGenerator"
        self.version = "1.0.0"
        self.models_dir = Path(self.config.get('models_dir', 'E:/SD_OpenVINO/models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.pipeline = None
        self.current_model = None
        
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"SDImageGenerator 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'output_dir': './skills/sd_image_generator/output/images',  # ✅ 改为新路径
            'default_model': 'sd-v1-5-tiny.safetensors',
            'default_width': 512,
            'default_height': 512,
            'default_steps': 20,
            'default_cfg_scale': 7.0,
            'default_seed': -1,
            'default_batch_size': 1,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        # 如果是默认的亚洲真实模型（用户没在GUI里手动修改宽高），自动切换到竖屏
        if (self.config.get('default_model') == 'asianrealisticSdlife_v40.safetensors'):
            self.config['width'] = 768
            self.config['height'] = 768
            
    
    def _find_model(self, model_name: str) -> Optional[Path]:
        """查找模型文件"""
        import os
        
        if not model_name:
            model_name = self.config.get('default_model', 'sd-v1-5-tiny.safetensors')
        
        # ✅ 调试：打印传入的模型名
        logger.info(f"🔍 查找模型: '{model_name}'")
        logger.info(f"📁 模型目录: {self.models_dir}")
        
        # 1. 直接查找
        direct_path = self.models_dir / model_name
        logger.info(f"  1️⃣ 直接查找: {direct_path}")
        if direct_path.exists():
            logger.info(f"  ✅ 找到: {direct_path}")
            return direct_path
        logger.info(f"  ❌ 不存在")
        
        # 2. 提取文件名
        filename = os.path.basename(model_name)
        logger.info(f"  2️⃣ 提取文件名: '{filename}'")
        
        # 3. 在子目录中查找文件名
        subdirs = ['sd-v1-5', 'sdxl', 'sd15-lora', 'sdxl-lora']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            logger.info(f"    检查: {sub_path}")
            if sub_path.exists():
                logger.info(f"  ✅ 找到: {sub_path}")
                return sub_path
        
        # 4. 遍历所有子目录
        logger.info("  4️⃣ 遍历所有子目录...")
        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                logger.info(f"    检查: {file_path}")
                if file_path.exists():
                    logger.info(f"  ✅ 找到: {file_path}")
                    return file_path
        
        # 5. 尝试各种扩展名
        for ext in ['.safetensors', '.ckpt', '.pth']:
            if not filename.endswith(ext):
                test_name = filename + ext
                logger.info(f"  5️⃣ 尝试扩展名: '{test_name}'")
                for subdir in subdirs:
                    test_path = self.models_dir / subdir / test_name
                    if test_path.exists():
                        logger.info(f"  ✅ 找到: {test_path}")
                        return test_path
        
        logger.error(f"❌ 未找到模型: '{model_name}'")
        return None
    
    def _load_model(self, model_name: str) -> bool:
        """加载模型"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装，请运行: pip install diffusers torch transformers accelerate safetensors Pillow")
            return False
        
        logger.info(f"🔍 _load_model 接收到的 model_name: '{model_name}'")
        
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False
        
        try:
            logger.info(f"加载模型: {model_path}")
            
            self.pipeline = StableDiffusionPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            self.pipeline.to(self.device)
            
            if self.device == 'cuda':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = model_name
            logger.info(f"✅ 模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        if 'prompt' not in kwargs or not kwargs['prompt']:
            raise ValueError("prompt 是必填参数")
        
        # 验证数值范围
        width = kwargs.get('width', self.config.get('width', 512))
        height = kwargs.get('height', self.config.get('height', 512))
        steps = kwargs.get('steps', self.config.get('steps', 20))
        cfg_scale = kwargs.get('cfg_scale', self.config.get('cfg_scale', 7.0))
        batch_size = kwargs.get('batch_size', 1)
        
        if width < 256 or width > 1024:
            raise ValueError(f"width 必须在 256-1024 之间，当前值: {width}")
        if height < 256 or height > 1024:
            raise ValueError(f"height 必须在 256-1024 之间，当前值: {height}")
        if steps < 10 or steps > 50:
            raise ValueError(f"steps 必须在 10-50 之间，当前值: {steps}")
        if cfg_scale < 1.0 or cfg_scale > 20.0:
            raise ValueError(f"cfg_scale 必须在 1.0-20.0 之间，当前值: {cfg_scale}")
        if batch_size < 1 or batch_size > 4:
            raise ValueError(f"batch_size 必须在 1-4 之间，当前值: {batch_size}")
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行图片生成
        
        Args:
            **kwargs: 输入参数
                - prompt: 提示词 (必填)
                - negative_prompt: 负面提示词
                - model_name: 模型名称
                - width: 宽度
                - height: 高度
                - steps: 步数
                - cfg_scale: CFG尺度
                - seed: 随机种子
                - output_dir: 输出目录
                - batch_size: 批量数量
            
        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            # 1. 验证输入参数
            self._validate_inputs(**kwargs)
            
            # 2. 获取参数
            prompt = kwargs.get('prompt')
            negative_prompt = kwargs.get('negative_prompt', '')
            model_name = kwargs.get('model_name', self.config.get('default_model', 'sd-v1-5-tiny.safetensors'))
            width = kwargs.get('width', self.config.get('width', 512))
            height = kwargs.get('height', self.config.get('height', 512))
            steps = kwargs.get('steps', self.config.get('steps', 20))
            cfg_scale = kwargs.get('cfg_scale', self.config.get('cfg_scale', 7.0))

            output_dir = kwargs.get('output_dir', self.config.get('output_dir', './skills/sd_image_generator/output/images'))
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            batch_size = kwargs.get('batch_size', 1)
            
            # 确保宽高是8的倍数
            width = (width // 8) * 8
            height = (height // 8) * 8
            
            # 3. 加载模型
            if self.pipeline is None or self.current_model != model_name:
                if not self._load_model(model_name):
                    return {
                        "status": "error",
                        "error": f"无法加载模型: {model_name}"
                    }
            
            # 4. 设置随机种子
            seed = kwargs.get('seed', -1)

            # ✅ 如果 seed 是字符串，转为整数
            if isinstance(seed, str):
                try:
                    seed = int(seed)
                except:
                    seed = -1
        
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)
            
            logger.info(f"生成参数:")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  模型: {model_name}")
            logger.info(f"  尺寸: {width}x{height}")
            logger.info(f"  步数: {steps}")
            logger.info(f"  种子: {seed}")
            
            # 5. 生成图片
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=cfg_scale,
                generator=generator,
                num_images_per_prompt=batch_size
            )
            
            # 6. 保存图片
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_paths = []
            
            for i, image in enumerate(result.images):
                filename = f"image_{timestamp}_{seed}_{i}.png"
                filepath = output_path / filename
                image.save(filepath)
                image_paths.append(str(filepath))
                logger.info(f"  ✅ 图片 {i+1}: {filepath}")
            
            generation_time = time.time() - start_time
            
            return {
                "status": "success",
                "image_paths": image_paths,
                "parameters": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model": model_name,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "seed": seed,
                    "batch_size": batch_size,
                    "output_dir": str(output_path)
                },
                "model_used": model_name,
                "generation_time": f"{generation_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<Sdimagegenerator(name={self.name}, version={self.version})>"


# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SD 图片生成器")
    parser.add_argument("--prompt", "-p", required=True, help="提示词")
    parser.add_argument("--negative", "-n", default="", help="负面提示词")
    parser.add_argument("--model", "-m", default="sd-v1-5-tiny.safetensors", help="模型名称")
    parser.add_argument("--width", "-W", type=int, default=512, help="宽度")
    parser.add_argument("--height", "-H", type=int, default=512, help="高度")
    parser.add_argument("--steps", "-s", type=int, default=20, help="步数")
    parser.add_argument("--cfg", "-c", type=float, default=7.0, help="CFG尺度")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--output", "-o", default="./generated_images", help="输出目录")
    parser.add_argument("--batch", "-b", type=int, default=1, help="批量数量")
    
    args = parser.parse_args()
    
    skill = Sdimagegenerator()
    result = skill.execute(
        prompt=args.prompt,
        negative_prompt=args.negative,
        model_name=args.model,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg_scale=args.cfg,
        seed=args.seed,
        output_dir=args.output,
        batch_size=args.batch
    )
    
    if result['status'] == 'success':
        print(f"\n✅ 生成成功!")
        print(f"  📁 图片: {result['image_paths']}")
        print(f"  ⏱️  耗时: {result['generation_time']}")
        print(f"  📋 参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n❌ 生成失败: {result.get('error', '未知错误')}")