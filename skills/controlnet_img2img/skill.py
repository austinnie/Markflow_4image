# skills/controlnet_img2img/skill.py
import sys
import torch
import os
import warnings      # ✅ 需要添加
import logging       # ✅ 需要添加
from pathlib import Path
from PIL import Image
from typing import Dict, Any, Optional

# ============================================================
# 🔧 修改点 1: 添加环境变量和警告过滤（文件开头）
# ============================================================
# 在导入 diffusers 之前设置环境变量
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["DIFFUSERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# 过滤 controlnet_aux 的注册警告
warnings.filterwarnings("ignore", message="Overwriting tiny_vit_* in registry")
warnings.filterwarnings("ignore", category=FutureWarning, module="timm")
warnings.filterwarnings("ignore", category=UserWarning, module="controlnet_aux")

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 导入模型配置管理器
from markflow.utils.model_config import get_model_config
from markflow.utils.controlnet_config import (
    PREPROCESSOR_MAP, 
    resolve_controlnet_path,
    CONTROLNET_AUX_DIR
)

class ControlNetImg2Img:
    """利用 ControlNet Aux 提取线稿，并进行图生图重绘的专用技能"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "controlnet_img2img"
        self.version = "1.0.0"
        self.pipe = None
        self._setup_logging()
        
        # 设定本技能默认输出目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.default_output_dir = self.skill_dir / "output"
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        import logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

    def _load_base_pipeline(self, base_model_path, controlnet_key: str = "canny"):
        """懒加载底模和 ControlNet 模型"""
        from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel
        
        if self.pipe is not None:
            return self.pipe
            
        cn_path = resolve_controlnet_path(controlnet_key)
        if not cn_path:
            raise ValueError(f"找不到对应的 ControlNet 模型: {controlnet_key}")

        self.logger.info(f"加载 ControlNet: {cn_path}")
        
        # 🔧 修改点 2: ControlNet 加载时添加 low_cpu_mem_usage=True
        controlnet = ControlNetModel.from_pretrained(
            cn_path, 
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,  # ✅ 新增
        )

        self.logger.info(f"准备加载底模: {base_model_path}")
        
        # 🔧 修改点 3: 添加 requires_safety_checker=False 消除警告
        if base_model_path.endswith('.safetensors') or base_model_path.endswith('.ckpt'):
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,  # ✅ 新增：消除 safety checker 警告
                local_files_only=True,          # ✅ 新增：使用本地文件
                low_cpu_mem_usage=True,         # ✅ 新增：减少内存使用
            )
        else:
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,  # ✅ 新增：消除 safety checker 警告
                local_files_only=True,          # ✅ 新增：使用本地文件
                low_cpu_mem_usage=True,         # ✅ 新增：减少内存使用
            )
            
        # 保持 CPU
        self.pipe = self.pipe.to("cpu")
        
        ## 开启切片优化
        #try:
        #    self.pipe.enable_attention_slicing()
        #    self.logger.info("✅ 已启用 CPU 注意力切片优化")
        #except Exception as e:
        #    self.logger.warning(f"⚠️ 启用切片优化失败（不影响使用）: {e}")
            
        return self.pipe

    def _preprocess(self, image: Image.Image, preprocessor_type: str = "HED") -> Image.Image:
        """调用 controlnet_aux 获取线稿/边缘图"""
        # 🔧 修改点 4: 在预处理时临时禁用警告
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            
            try:
                if preprocessor_type == "HED":
                    from controlnet_aux import HEDdetector
                    processor = HEDdetector.from_pretrained("lllyasviel/Annotators")
                    return processor(image)
                elif preprocessor_type == "OPENPOSE":
                    from controlnet_aux import OpenposeDetector
                    processor = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
                    return processor(image)
                else:
                    # 默认 Canny
                    from controlnet_aux import CannyDetector
                    return CannyDetector()(image)
            except ImportError as e:
                raise ImportError(f"请先安装 controlnet_aux: pip install controlnet-aux. 错误: {e}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        input_path = kwargs.get("input_image_path")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        preprocessor_type = kwargs.get("preprocessor_type", "HED")
        controlnet_model = kwargs.get("controlnet_model", "canny")
        strength = kwargs.get("strength", 0.7)
        output_path = kwargs.get("output_path", None)
        
        if not input_path:
            return {"status": "error", "error": "缺少 input_image_path 参数"}
        abs_input_path = Path(input_path).absolute()
        if not abs_input_path.exists():
            return {"status": "error", "error": f"输入图片路径不存在: {abs_input_path}。请检查图片是否放对了位置！"}

        if output_path is None:
            timestamp = int(__import__('time').time())
            filename = f"{abs_input_path.stem}_controlnet_{timestamp}.png"
            output_path = str(self.default_output_dir / filename)

        try:
            sd_config = get_model_config()
            base_model_path = sd_config.get("model_path")
            if not base_model_path:
                return {"status": "error", "error": "未找到基础底模路径，请检查 model_config.py"}

            original_image = Image.open(abs_input_path).convert("RGB")
            
            # ✅ 终极修复：强制将尺寸对齐到 64 的倍数，并计算出目标宽高
            w, h = original_image.size
            target_w = (w // 64) * 64
            target_h = (h // 64) * 64
            if target_w < 64: target_w = 64
            if target_h < 64: target_h = 64
            
            self.logger.info(f"📐 最终生成尺寸: {target_w}x{target_h}")
            original_image = original_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            self.logger.info(f"正在使用 {preprocessor_type} 提取线稿...")
            control_image = self._preprocess(original_image, preprocessor_type)

            # ✅ 确保控制图也强制对齐到相同尺寸！
            if control_image.size != original_image.size:
                control_image = control_image.resize(original_image.size, Image.Resampling.LANCZOS)

            pipe = self._load_base_pipeline(base_model_path, controlnet_model)

            self.logger.info(f"正在图生图重绘，强度: {strength}...")
            result_image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=original_image,
                control_image=control_image,
                width=target_w,   # ✅ 强制传入宽度
                height=target_h,  # ✅ 强制传入高度
                strength=strength,
                num_inference_steps=30,
                guidance_scale=7.5,
                controlnet_conditioning_scale=1.0,
            ).images[0]

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result_image.save(output_path)

            self.logger.info(f"生成完成: {output_path}")
            return {"status": "success", "image_path": str(output_path), "control_image_path": None}

        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    skill = ControlNetImg2Img()
    result = skill.execute(
        input_image_path="test.png",
        prompt="a beautiful realistic portrait, full color",
        preprocessor_type="HED",
        controlnet_model="hed"
    )
    print(result)