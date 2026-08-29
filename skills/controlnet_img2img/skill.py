# skills/controlnet_img2img/skill.py
import sys
import torch
import os
from pathlib import Path
from PIL import Image
from typing import Dict, Any, Optional

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
        """懒加载底模和 ControlNet 模型（纯 CPU 稳定模式）"""
        from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel
        
        if self.pipe is not None:
            return self.pipe
            
        # 解析 ControlNet 模型路径
        cn_path = resolve_controlnet_path(controlnet_key)
        if not cn_path:
            raise ValueError(f"找不到对应的 ControlNet 模型: {controlnet_key}")

        self.logger.info(f"加载 ControlNet: {cn_path}")
        controlnet = ControlNetModel.from_pretrained(
            cn_path, torch_dtype=torch.float32
        )

        self.logger.info(f"准备加载底模: {base_model_path}")
        if base_model_path.endswith('.safetensors') or base_model_path.endswith('.ckpt'):
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
            ).to("cpu")  # CPU设备
        else:
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
            ).to("cpu") 

        # 开启 CPU 优化切片，提速
        try:
            self.pipe.enable_attention_slicing()
            self.pipe.enable_vae_slicing()
            self.logger.info("✅ 已启用 CPU 注意力切片优化")
        except Exception as e:
            self.logger.warning(f"⚠️ 启用切片优化失败（不影响使用）: {e}")
            
        return self.pipe

    def _preprocess(self, image: Image.Image, preprocessor_type: str = "HED") -> Image.Image:
        """调用 controlnet_aux 获取线稿/边缘图"""
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
            self.logger.info(f"正在使用 {preprocessor_type} 提取线稿...")
            control_image = self._preprocess(original_image, preprocessor_type)

            pipe = self._load_base_pipeline(base_model_path, controlnet_model)

            self.logger.info(f"正在图生图重绘，强度: {strength}...")
            result_image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=original_image,
                control_image=control_image,
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