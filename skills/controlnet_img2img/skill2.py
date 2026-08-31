# skills/controlnet_img2img/skill.py
import sys
import torch
import os
import warnings
import logging
from pathlib import Path
from PIL import Image
from typing import Dict, Any, Optional

# 在导入 diffusers 之前设置环境变量
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["DIFFUSERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# 过滤警告
warnings.filterwarnings("ignore", message="Overwriting tiny_vit_* in registry")
warnings.filterwarnings("ignore", category=FutureWarning, module="timm")
warnings.filterwarnings("ignore", category=UserWarning, module="controlnet_aux")

logging.basicConfig(level=logging.INFO)

# 导入模型配置管理器
from markflow.utils.model_config import get_model_config, update_user_config_item
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

        controlnet = ControlNetModel.from_pretrained(
            cn_path,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )

        self.logger.info(f"准备加载底模: {base_model_path}")

        if base_model_path.endswith('.safetensors') or base_model_path.endswith('.ckpt'):
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )
        else:
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                local_files_only=True,
                low_cpu_mem_usage=True,
            )

        self.pipe = self.pipe.to("cpu")
        return self.pipe

    def _preprocess(self, image: Image.Image, preprocessor_type: str = "HED") -> Image.Image:
        """调用 controlnet_aux 获取线稿/边缘图"""
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
                    from controlnet_aux import CannyDetector
                    return CannyDetector()(image)
            except ImportError as e:
                raise ImportError(f"请先安装 controlnet_aux: pip install controlnet-aux. 错误: {e}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行图生图重绘（支持参数透传）

        支持参数:
            - input_image_path: 输入图片路径 (必填)
            - prompt: 生成提示词
            - negative_prompt: 负面提示词
            - preprocessor_type: 预处理类型 (HED / OPENPOSE / Canny等)
            - controlnet_model: ControlNet 模型名称
            - strength: 重绘强度 (0-1)
            - output_path: 输出路径
            - width: 自定义输出宽度 (新增参数透传)
            - height: 自定义输出高度 (新增参数透传)
            - model_name: 自定义底模名称 (新增参数透传)
        """
        input_path = kwargs.get("input_image_path")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        preprocessor_type = kwargs.get("preprocessor_type", "HED")
        controlnet_model = kwargs.get("controlnet_model", "canny")
        strength = kwargs.get("strength", 0.7)
        output_path = kwargs.get("output_path", None)

        # ===== 新增：参数透传 =====
        width = kwargs.get("width", None)
        height = kwargs.get("height", None)
        model_name = kwargs.get("model_name", None)

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
            # ===== 动态获取配置或指定模型 =====
            sd_config = get_model_config()
            base_model_path = sd_config.get("model_path")

            # 如果传入了 model_name，强制覆盖全局配置
            if model_name:
                try:
                    update_user_config_item("manual_model_name", model_name)
                    update_user_config_item("model_selection_mode", "manual")
                    # 重新读取配置（模型路径会更新）
                    sd_config = get_model_config()
                    base_model_path = sd_config.get("model_path")
                    self.logger.info(f"已强制切换到指定模型: {model_name}")
                except Exception as e:
                    self.logger.warning(f"尝试手动切换模型失败，使用原配置: {e}")

            if not base_model_path:
                return {"status": "error", "error": "未找到基础底模路径，请检查 model_config.py"}

            original_image = Image.open(abs_input_path).convert("RGB")

            # ===== 动态尺寸控制 =====
            w, h = original_image.size
            if width and height:
                w, h = int(width), int(height)
            else:
                w = (w // 64) * 64
                h = (h // 64) * 64

            if w < 64: w = 64
            if h < 64: h = 64

            self.logger.info(f"📐 最终生成尺寸: {w}x{h}")
            original_image = original_image.resize((w, h), Image.Resampling.LANCZOS)

            self.logger.info(f"正在使用 {preprocessor_type} 提取线稿...")
            control_image = self._preprocess(original_image, preprocessor_type)

            if control_image.size != original_image.size:
                control_image = control_image.resize(original_image.size, Image.Resampling.LANCZOS)

            pipe = self._load_base_pipeline(base_model_path, controlnet_model)

            self.logger.info(f"正在图生图重绘，强度: {strength}...")
            result_image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=original_image,
                control_image=control_image,
                width=w,
                height=h,
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