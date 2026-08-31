# skills/controlnet_img2img/skill.py
"""
ControlNet 图生图技能 - 完整版
支持所有参数透传，集成统一模型配置
"""

# ===== 环境变量设置（消除警告） =====
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["DIFFUSERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import sys
import time
import json
import logging
import random
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from PIL import Image

# 过滤警告
warnings.filterwarnings("ignore", message="Overwriting tiny_vit_* in registry")
warnings.filterwarnings("ignore", category=FutureWarning, module="timm")
warnings.filterwarnings("ignore", category=UserWarning, module="controlnet_aux")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class ControlnetImg2Img:
    """ControlNet 图生图 - 支持所有参数透传"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "controlnet_img2img"
        self.version = "2.0.0"
        self.skill_dir = Path(__file__).parent
        self._pipeline = None  # 缓存 pipeline
        self._setup_logging()
        self._setup_config()
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        """设置默认配置"""
        defaults = {
            "device": "cpu",
            "output_dir": "./output/controlnet_img2img",
            "default_steps": 25,
            "default_cfg": 7.0,
            "default_strength": 0.6,
            "default_controlnet_type": "canny",
            "default_scheduler": "DDIM",
            "max_size": 768,
            "align": 64,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    # ==================== 主执行方法 ====================
    
    # ==================== 主执行方法 ====================
    
    def execute(
        self,
        # ===== 必填参数 =====
        input_image_path: str = None, 
        
        # ===== 提示词参数 =====
        prompt: str = None,
        negative_prompt: str = "",
        preset: str = None,
        
        # ===== 输出参数 =====
        output_path: str = None,
        output_dir: str = None,
        filename_prefix: str = None,
        
        # ===== ControlNet 参数 =====
        controlnet_type: str = None,
        controlnet_strength: float = None,
        controlnet_guidance_start: float = 0.0,
        controlnet_guidance_end: float = 1.0,
        
        # ===== 生成参数 =====
        strength: float = None,
        steps: int = None,
        cfg_scale: float = None,
        seed: int = None,
        scheduler: str = None,
        
        # ===== 模型参数 =====
        model_name: str = None,
        model_type: str = None,
        lora_weights: Dict[str, float] = None,
        
        # ===== 尺寸参数 =====
        width: int = None,
        height: int = None,
        resize_mode: str = "crop",  # crop, fit, stretch
        
        # ===== 高级参数 =====
        batch_size: int = 1,
        save_mask: bool = False,
        mask_blur: int = 4,
        eta: float = 0.0,
        guidance_rescale: float = 0.0,
        
        # ===== 透传参数 =====
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行 ControlNet 图生图
        
        Args:
            input_image_path: 输入图片路径
            prompt: 正向提示词
            negative_prompt: 负向提示词
            preset: 预设模板 (beach, forest, city, sakura, sunset, snow, rain, night, garden, mountain)
            
            output_path: 输出路径
            output_dir: 输出目录
            filename_prefix: 文件名前缀
            
            controlnet_type: ControlNet 类型 (canny, openpose, depth, hed, mlsd, lineart)
            controlnet_strength: ControlNet 权重 (0-1)
            controlnet_guidance_start: ControlNet 起始步数比例
            controlnet_guidance_end: ControlNet 结束步数比例
            
            strength: 重绘强度 (0-1)
            steps: 迭代步数
            cfg_scale: 提示词引导强度
            seed: 随机种子 (-1 表示随机)
            scheduler: 采样器 (DDIM, DPM, UniPC, Euler, EulerAncestral)
            
            model_name: 底模名称
            model_type: 模型类型 (sd15, sdxl)
            lora_weights: LoRA 权重配置 {"name": weight}
            
            width: 输出宽度
            height: 输出高度
            resize_mode: 调整模式 (crop, fit, stretch)
            
            batch_size: 批次大小
            save_mask: 是否保存遮罩
            mask_blur: 遮罩模糊半径
            eta: DDIM eta 参数
            guidance_rescale: 引导重缩放
            
            **kwargs: 透传参数
        
        Returns:
            {
                "status": "success" or "error",
                "output_path": "输出路径",
                "image_paths": ["路径列表"],
                "params": {...},
                "metadata": {...}
            }
        """
        start_time = time.time()
        
        # ===== 1. 应用默认配置 =====
        controlnet_type = controlnet_type or self.config.get("default_controlnet_type", "canny")
        strength = strength if strength is not None else self.config.get("default_strength", 0.6)
        steps = steps or self.config.get("default_steps", 25)
        cfg_scale = cfg_scale or self.config.get("default_cfg", 7.0)
        output_dir = output_dir or self.config.get("output_dir", "./output/controlnet_img2img")
        scheduler = scheduler or self.config.get("default_scheduler", "DDIM")
        device = self.config.get("device", "cpu")
        max_size = self.config.get("max_size", 768)
        align = self.config.get("align", 64)
        
        logger.info("=" * 60)
        logger.info(f"🚀 ControlNet 图生图 v{self.version}")
        logger.info("=" * 60)
        logger.info(f"📁 输入: {input_image_path}")
        logger.info(f"📝 提示词: {prompt[:80] if prompt else 'None'}...")
        logger.info(f"🎯 ControlNet: {controlnet_type}")
        logger.info(f"⚙️  强度: {strength}, 步数: {steps}, CFG: {cfg_scale}")
        logger.info(f"💻 设备: {device}")
        
        # ===== 2. 验证输入 =====
        if not input_image_path:
            raise ValueError("必须指定 input_image_path")
        
        input_path = Path(input_image_path)
        if not input_path.exists():
            raise FileNotFoundError(f"输入图片不存在: {input_image_path}")
        
        # 处理预设
        if preset and not prompt:
            prompt = self._build_prompt_from_preset(preset, **kwargs)
            logger.info(f"📌 使用预设: {preset}")
        
        if not prompt:
            raise ValueError("必须指定 prompt 或 preset")
        
        # 处理输出路径
        if not output_path:
            output_path = self._generate_output_path(
                output_dir, filename_prefix, input_image_path  
            )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 处理随机种子
        if seed is None or seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        # ===== 3. 构建参数 =====
        params = {
            "image_path": str(Path(input_image_path)),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "output_path": str(output_path),
            "controlnet_type": controlnet_type,
            "controlnet_strength": controlnet_strength or 1.0,
            "controlnet_guidance_start": controlnet_guidance_start,
            "controlnet_guidance_end": controlnet_guidance_end,
            "strength": strength,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "scheduler": scheduler,
            "model_name": model_name,
            "model_type": model_type,
            "lora_weights": lora_weights or {},
            "width": width,
            "height": height,
            "resize_mode": resize_mode,
            "batch_size": batch_size,
            "save_mask": save_mask,
            "mask_blur": mask_blur,
            "eta": eta,
            "guidance_rescale": guidance_rescale,
            "device": device,
            "max_size": max_size,
            "align": align,
        }
        
        # 合并透传参数
        params.update(kwargs)
        
        try:
            # ===== 4. 执行生成 =====
            result = self._generate_with_controlnet(params)
            
            # ===== 5. 返回结果 =====
            elapsed = time.time() - start_time
            logger.info(f"✅ 生成完成! 耗时: {elapsed:.1f}s")
            logger.info(f"📁 输出: {output_path}")
            logger.info("=" * 60)
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "image_paths": result.get("image_paths", [str(output_path)]),
                "params": {k: str(v)[:100] for k, v in params.items() if v},
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat(),
                    "elapsed_seconds": elapsed,
                    "seed": seed,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "controlnet_type": controlnet_type,
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== 预设模板系统 ====================
    
    def _build_prompt_from_preset(self, preset: str, **kwargs) -> str:
        """从预设模板构建 prompt"""
        PRESETS = {
            # ===== 背景预设 =====
            "beach": "a beautiful woman standing on a sunny sandy beach, ocean waves in background, palm trees, summer vacation, warm sunlight, high quality, masterpiece",
            "forest": "a beautiful woman in a lush green forest, dappled sunlight filtering through leaves, peaceful nature atmosphere, high quality, masterpiece",
            "city": "a beautiful woman in a modern city street, urban atmosphere, skyscrapers, stylish, cosmopolitan, high quality, masterpiece",
            "sakura": "a beautiful woman under a cherry blossom tree, pink petals falling, spring atmosphere, romantic, high quality, masterpiece",
            "sunset": "a beautiful woman at sunset, golden hour lighting, warm orange and pink sky, dramatic and beautiful, high quality, masterpiece",
            "snow": "a beautiful woman in a snowy landscape, gentle snow falling, winter wonderland, cozy and serene, high quality, masterpiece",
            "rain": "a beautiful woman in the rain, holding an umbrella, wet streets, moody and atmospheric, high quality, masterpiece",
            "night": "a beautiful woman at night, city lights, starry sky, mysterious and elegant, high quality, masterpiece",
            "garden": "a beautiful woman in a blooming garden, colorful flowers, butterflies, peaceful and serene, high quality, masterpiece",
            "mountain": "a beautiful woman in a mountain landscape, majestic peaks, fresh air, adventurous, high quality, masterpiece",
            "studio": "a beautiful woman in a professional photo studio, clean white background, soft studio lighting, high quality, masterpiece",
            "cyberpunk": "a beautiful woman in a cyberpunk city, neon lights, rain, futuristic, high quality, masterpiece",
            
            # ===== 服装预设 =====
            "elegant_dress": "a beautiful woman wearing an elegant evening gown, flowing fabric, sophisticated and refined, high quality, masterpiece",
            "casual": "a beautiful woman wearing casual everyday clothes, relaxed and comfortable, modern style, high quality, masterpiece",
            "sporty": "a beautiful woman wearing sportswear, athletic and energetic, fitness style, high quality, masterpiece",
            "traditional": "a beautiful woman wearing traditional clothing, cultural and elegant, timeless beauty, high quality, masterpiece",
            "futuristic": "a beautiful woman wearing futuristic sci-fi clothing, high-tech and stylish, cyberpunk aesthetic, high quality, masterpiece",
            "vintage": "a beautiful woman wearing vintage retro clothing, classic and timeless, old Hollywood glamour, high quality, masterpiece",
            "bohemian": "a beautiful woman wearing bohemian style clothing, free-spirited and artistic, flowy fabrics, high quality, masterpiece",
            "formal": "a beautiful woman wearing formal business attire, professional and confident, sharp and elegant, high quality, masterpiece",
            
            # ===== 风格预设 =====
            "anime": "anime style illustration, vibrant colors, expressive eyes, beautiful animation art, high quality, masterpiece",
            "realistic": "photorealistic, highly detailed, lifelike, professional photography, high quality, masterpiece",
            "oil_painting": "oil painting style, rich textures, artistic brushstrokes, masterpiece art, high quality, masterpiece",
            "watercolor": "watercolor painting style, soft colors, artistic and dreamy, high quality, masterpiece",
            "sketch": "pencil sketch style, hand-drawn, artistic linework, raw and expressive, high quality, masterpiece",
            "cinematic": "cinematic photography, dramatic lighting, movie scene, epic composition, high quality, masterpiece",
            "studio": "professional studio photography, softbox lighting, clean background, high quality, masterpiece",
        }
        
        base = PRESETS.get(preset, "")
        if not base:
            logger.warning(f"⚠️ 未知预设: {preset}，使用默认")
            base = "a beautiful woman, high quality, masterpiece"
        
        # 允许用户追加额外描述
        extra = kwargs.get("extra_prompt", "")
        if extra:
            return f"{base}, {extra}"
        return base
    
    def _generate_output_path(self, output_dir: str, prefix: str = None, image_path: str = None) -> str:
        """生成输出路径"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            filename = f"{prefix}_{timestamp}.png"
        elif image_path:
            stem = Path(image_path).stem
            filename = f"{stem}_controlnet_{timestamp}.png"
        else:
            filename = f"controlnet_{timestamp}.png"
        
        return str(output_dir / filename)
    
    # ==================== 核心生成逻辑 ====================
    
    def _generate_with_controlnet(self, params: Dict) -> Dict:
        """
        实际的 ControlNet 生成逻辑
        """
        from PIL import Image
        
        # ===== 1. 提取参数 =====
        image_path = params["image_path"]
        prompt = params["prompt"]
        negative_prompt = params.get("negative_prompt", "")
        output_path = params["output_path"]
        controlnet_type = params["controlnet_type"]
        controlnet_strength = params.get("controlnet_strength", 1.0)
        
        controlnet_guidance_start = params.get("controlnet_guidance_start", 0.0)
        controlnet_guidance_end = params.get("controlnet_guidance_end", 1.0)
        strength = params.get("strength", 0.6)
        steps = params.get("steps", 25)
        cfg_scale = params.get("cfg_scale", 7.0)
        seed = params.get("seed", -1)
        model_name = params.get("model_name")
        model_type = params.get("model_type")
        width = params.get("width")
        height = params.get("height")
        resize_mode = params.get("resize_mode", "crop")
        device = params.get("device", "cpu")
        scheduler = params.get("scheduler", "DDIM")
        lora_weights = params.get("lora_weights", {})
        max_size = params.get("max_size", 768)
        align = params.get("align", 64)
        batch_size = params.get("batch_size", 1)
        save_mask = params.get("save_mask", False)
        mask_blur = params.get("mask_blur", 4)
        eta = params.get("eta", 0.0)
        guidance_rescale = params.get("guidance_rescale", 0.0)
        
        # ===== 2. 解析模型路径 =====
        try:
            from markflow.utils.model_config import get_model_config, resolve_model_path, resolve_lora_paths
            from markflow.utils.controlnet_config import resolve_controlnet_path
        except ImportError as e:
            logger.error(f"导入配置模块失败: {e}")
            # 使用硬编码路径
            sd_root = Path("E:/SD_OpenVINO")
            model_path = sd_root / "models/sd-v1-5/sd-v1-5-tiny.safetensors"
            controlnet_model_path = sd_root / "models/controlnet/models--lllyasviel--sd-controlnet-canny"
        else:
            # 解析底模路径
            if model_name:
                model_path = resolve_model_path(model_name)
            else:
                config = get_model_config()
                model_path = config.get("model_path")
                model_type = model_type or config.get("model_type", "sd15")
            
            # 解析 ControlNet 路径
            controlnet_model_path = resolve_controlnet_path(controlnet_type)
        
        # 验证模型路径
        if not model_path or not Path(model_path).exists():
            # 尝试默认路径
            default_paths = [
                "E:/SD_OpenVINO/models/sd-v1-5/sd-v1-5-tiny.safetensors",
                "E:/SD_OpenVINO/models/sd-v1-5/sd-v1-5-inpainting-tiny.safetensors",
            ]
            for p in default_paths:
                if Path(p).exists():
                    model_path = p
                    break
        
        if not model_path or not Path(model_path).exists():
            raise FileNotFoundError(f"未找到底模: {model_path}")
        
        if not controlnet_model_path or not Path(controlnet_model_path).exists():
            # 尝试默认 ControlNet 路径
            default_cn_paths = [
                f"E:/SD_OpenVINO/models/controlnet/models--lllyasviel--sd-controlnet-{controlnet_type}",
                f"E:/SD_OpenVINO/models/controlnet/control_v11p_sd15_{controlnet_type}",
            ]
            for p in default_cn_paths:
                if Path(p).exists():
                    controlnet_model_path = p
                    break
        
        if not controlnet_model_path or not Path(controlnet_model_path).exists():
            raise FileNotFoundError(f"未找到 ControlNet 模型: {controlnet_type}")
        
        logger.info(f"📦 底模: {Path(model_path).name}")
        logger.info(f"🎯 ControlNet: {Path(controlnet_model_path).name}")
        
        # ===== 3. 加载图片 =====
        image = Image.open(image_path).convert("RGB")
        orig_w, orig_h = image.size
        
        # 调整尺寸
        if width and height:
            target_w, target_h = width, height
        else:
            # 自动适配
            if orig_w > max_size or orig_h > max_size:
                scale = max_size / max(orig_w, orig_h)
                target_w = int(orig_w * scale)
                target_h = int(orig_h * scale)
            else:
                target_w, target_h = orig_w, orig_h
        
        # 对齐到 64 的倍数
        target_w = ((target_w + align - 1) // align) * align
        target_h = ((target_h + align - 1) // align) * align
        
        # 处理 resize_mode
        if resize_mode == "crop":
            # 裁剪到目标尺寸
            if image.size != (target_w, target_h):
                image = self._crop_image(image, target_w, target_h)
        elif resize_mode == "fit":
            # 适应目标尺寸（保持比例）
            image = self._fit_image(image, target_w, target_h)
        else:
            # stretch: 拉伸到目标尺寸
            if image.size != (target_w, target_h):
                image = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        logger.info(f"📐 尺寸: {target_w}x{target_h} (原图: {orig_w}x{orig_h})")
        
        # ===== 4. 初始化 Pipeline =====
        try:
            from diffusers import (
                StableDiffusionControlNetPipeline,
                ControlNetModel,
                UniPCMultistepScheduler,
                DPMSolverMultistepScheduler,
                EulerAncestralDiscreteScheduler,
                EulerDiscreteScheduler,
            )
            import torch
        except ImportError as e:
            logger.error(f"导入 diffusers 失败: {e}")
            raise ImportError("请安装: pip install diffusers transformers accelerate")
        
        # 加载 ControlNet
        logger.info("⏳ 加载 ControlNet...")
        try:
            controlnet = ControlNetModel.from_pretrained(
                controlnet_model_path,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                local_files_only=True,
            )
        except Exception as e:
            logger.warning(f"加载 ControlNet 失败: {e}")
            # 尝试从子目录加载
            cn_path = Path(controlnet_model_path)
            for subdir in cn_path.iterdir():
                if subdir.is_dir() and (subdir / "config.json").exists():
                    controlnet = ControlNetModel.from_pretrained(
                        str(subdir),
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        local_files_only=True,
                    )
                    break
            else:
                raise
        
        # 加载底模 Pipeline
        logger.info("⏳ 加载底模...")
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            model_path,
            controlnet=controlnet,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            local_files_only=True,
            use_safetensors=True,
        )
        
        # 设置设备
        pipe = pipe.to(device)
        
        # 设置调度器
        if scheduler == "DPM":
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        elif scheduler == "UniPC":
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
        elif scheduler == "Euler":
            pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        elif scheduler == "EulerAncestral" or scheduler == "EulerA":
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
        
        # 启用优化
        if device == "cuda":
            pipe.enable_model_cpu_offload()
            pipe.enable_attention_slicing()
            # pipe.enable_xformers_memory_efficient_attention()  # 可选
        else:
            pipe.enable_attention_slicing()
        
        # ===== 5. 处理 LoRA =====
        if lora_weights:
            logger.info("🔧 加载 LoRA...")
            try:
                lora_list = resolve_lora_paths(lora_weights)
                for lora in lora_list:
                    lora_path = lora.get("path")
                    lora_name = lora.get("name", Path(lora_path).stem)
                    lora_weight = lora.get("weight", 0.8)
                    
                    if Path(lora_path).exists():
                        pipe.load_lora_weights(lora_path, adapter_name=lora_name)
                        pipe.set_adapters([lora_name], adapter_weights=[lora_weight])
                        logger.info(f"   ✅ {lora_name} ({lora_weight})")
                    else:
                        logger.warning(f"   ⚠️ LoRA 不存在: {lora_path}")
            except Exception as e:
                logger.warning(f"加载 LoRA 失败: {e}")
        
        # ===== 6. 生成 =====
        logger.info("🎨 生成中...")
        
        generator = torch.Generator(device=device).manual_seed(seed)
        
        # 构建额外参数
        extra_kwargs = {}
        if controlnet_guidance_start > 0 or controlnet_guidance_end < 1:
            extra_kwargs["controlnet_guidance_start"] = controlnet_guidance_start
            extra_kwargs["controlnet_guidance_end"] = controlnet_guidance_end
        if eta > 0:
            extra_kwargs["eta"] = eta
        if guidance_rescale > 0:
            extra_kwargs["guidance_rescale"] = guidance_rescale
        
        # 执行生成
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=cfg_scale,
            generator=generator,
            controlnet_conditioning_scale=controlnet_strength,
            num_images_per_prompt=batch_size,
            **extra_kwargs
        )
        
        # ===== 7. 保存图片 =====
        logger.info(f"💾 保存: {output_path}")
        
        image_paths = []
        if batch_size == 1:
            result.images[0].save(output_path)
            image_paths.append(str(output_path))
        else:
            output_path = Path(output_path)
            for i, img in enumerate(result.images):
                if i == 0:
                    save_path = output_path
                else:
                    save_path = output_path.parent / f"{output_path.stem}_{i:02d}{output_path.suffix}"
                img.save(save_path)
                image_paths.append(str(save_path))
        
        # 保存遮罩
        if save_mask and hasattr(result, "mask") and result.mask:
            mask_path = Path(output_path).with_suffix("_mask.png")
            result.mask.save(mask_path)
            logger.info(f"💾 遮罩: {mask_path}")
        
        # ===== 8. 清理资源 =====
        if device == "cuda":
            torch.cuda.empty_cache()
        
        return {
            "image_paths": image_paths,
            "seed": seed,
        }
    
    # ==================== 图片处理工具 ====================
    
    def _crop_image(self, image, target_w: int, target_h: int) -> Image.Image:
        """裁剪图片到目标尺寸（居中裁剪）"""
        w, h = image.size
        if w == target_w and h == target_h:
            return image
        
        # 计算裁剪区域
        if w / h > target_w / target_h:
            # 宽度过大，裁剪宽度
            new_w = int(h * target_w / target_h)
            left = (w - new_w) // 2
            right = left + new_w
            image = image.crop((left, 0, right, h))
        else:
            # 高度过大，裁剪高度
            new_h = int(w * target_h / target_w)
            top = (h - new_h) // 2
            bottom = top + new_h
            image = image.crop((0, top, w, bottom))
        
        return image.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def _fit_image(self, image, target_w: int, target_h: int) -> Image.Image:
        """适应图片到目标尺寸（保持比例，填充空白）"""
        w, h = image.size
        
        # 计算缩放比例
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 缩放
        if new_w != w or new_h != h:
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 创建画布并居中
        canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        left = (target_w - new_w) // 2
        top = (target_h - new_h) // 2
        canvas.paste(image, (left, top))
        
        return canvas
    
    
    def _preprocess(self, image: Image.Image, preprocessor_type: str = "HED") -> Optional[Image.Image]:
        """调用 controlnet_aux 获取线稿/边缘图（兼容旧版本）"""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            
            try:
                if preprocessor_type.upper() == "HED":
                    from controlnet_aux import HEDdetector
                    processor = HEDdetector.from_pretrained("lllyasviel/Annotators")
                    result = processor(image)
                    return result if isinstance(result, Image.Image) else Image.fromarray(result)
                    
                elif preprocessor_type.upper() == "OPENPOSE":
                    from controlnet_aux import OpenposeDetector
                    processor = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
                    result = processor(image)
                    return result if isinstance(result, Image.Image) else Image.fromarray(result)
                    
                elif preprocessor_type.upper() == "CANNY":
                    from controlnet_aux import CannyDetector
                    result = CannyDetector()(image)
                    return result if isinstance(result, Image.Image) else Image.fromarray(result)
                    
                else:
                    from controlnet_aux import HEDdetector
                    processor = HEDdetector.from_pretrained("lllyasviel/Annotators")
                    result = processor(image)
                    return result if isinstance(result, Image.Image) else Image.fromarray(result)
                    
            except ImportError as e:
                logger.warning(f"controlnet_aux 未安装: {e}")
                logger.warning("请安装: pip install controlnet-aux")
                return None
            except Exception as e:
                logger.warning(f"预处理失败: {e}")
                return None

    def _load_base_pipeline(self, base_model_path: str, controlnet_key: str = "canny"):
        """懒加载底模和 ControlNet 模型（兼容旧版本）"""
        from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel
        import torch

        if self._pipeline is not None:
            return self._pipeline

        from markflow.utils.controlnet_config import resolve_controlnet_path

        cn_path = resolve_controlnet_path(controlnet_key)
        if not cn_path:
            raise ValueError(f"找不到对应的 ControlNet 模型: {controlnet_key}")

        logger.info(f"加载 ControlNet: {cn_path}")

        controlnet = ControlNetModel.from_pretrained(
            cn_path,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )

        logger.info(f"准备加载底模: {base_model_path}")

        if base_model_path.endswith('.safetensors') or base_model_path.endswith('.ckpt'):
            self._pipeline = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )
        else:
            self._pipeline = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )

        self._pipeline = self._pipeline.to("cpu")
        return self._pipeline
    
    # ==================== 辅助方法 ====================
    
    def __repr__(self):
        return f"<ControlnetImg2Img(name={self.name}, version={self.version})>"


# ==================== 快捷函数 ====================

def create_skill(config: Dict = None) -> ControlnetImg2Img:
    return ControlnetImg2Img(config)


# ==================== 兼容旧代码 ====================

ControlNetImg2Img = ControlnetImg2Img


if __name__ == "__main__":
    skill = ControlnetImg2Img({"device": "cpu"})
    result = skill.execute(
        image_path="input/girl.jpg",
        prompt="a beautiful woman",
        preset="beach",
        steps=10,
        output_dir="./output/test",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))