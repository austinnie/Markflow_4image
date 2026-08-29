# skills/controlnet_img2img/skill.py
import sys
import torch
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

    def _setup_logging(self):
        import logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

    def _find_base_model_dir(self, model_path):
        """解决单文件底模问题：尝试寻找完整的模型文件夹"""
        from pathlib import Path
        p = Path(model_path)
        
        # 1. 如果传进来的是一个完整文件夹，直接返回
        if p.is_dir():
            return str(p)
            
        # 2. 如果传进来的是文件，优先在父目录下找完整的 diffusers 模型文件夹
        parent_dir = p.parent
        for sub in parent_dir.iterdir():
            if sub.is_dir() and (sub / "model_index.json").exists():
                return str(sub)
        
        # 3. 尝试在父目录的同级里找相关文件夹（例如 models/sd-v1-5/xxx）
        # 这里你可以打印出当前父目录有哪些文件夹，方便调试
        print(f"⚠️ 警告：未找到包含 model_index.json 的完整模型文件夹。")
        print(f"   当前路径: {model_path}")
        print(f"   请确保 {parent_dir} 下存在完整的 diffusers 模型文件夹。")
        
        return None

    def _load_base_pipeline(self, base_model_path, controlnet_key: str = "canny"):
        """懒加载底模和 ControlNet 模型（CPU版优化）"""
        from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel
        
        if self.pipe is not None:
            return self.pipe
            
        # 解析 ControlNet 模型路径
        cn_path = resolve_controlnet_path(controlnet_key)
        if not cn_path:
            raise ValueError(f"找不到对应的 ControlNet 模型: {controlnet_key}")

        self.logger.info(f"加载 ControlNet: {cn_path}")
        
        # ✅ 重要：CPU 必须使用 float32，不能使用 float16！
        controlnet = ControlNetModel.from_pretrained(
            cn_path, torch_dtype=torch.float32
        )

        self.logger.info(f"准备加载底模: {base_model_path}")
        if base_model_path.endswith('.safetensors') or base_model_path.endswith('.ckpt'):
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,  # ✅ 改成 float32
                safety_checker=None,
            ).to("cpu")  # ✅ 强制使用 CPU
        else:
            self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                base_model_path,
                controlnet=controlnet,
                torch_dtype=torch.float32,  # ✅ 改成 float32
                safety_checker=None,
            ).to("cpu")  # ✅ 强制使用 CPU
        
        return self.pipe
        
    def _preprocess(self, image: Image.Image, preprocessor_type: str = "HED") -> Image.Image:
        """调用 controlnet_aux 获取线稿/边缘图"""
        try:
            # ✅ 修正：不管本地文件放在哪，直接传标准的 HF ID，会自动去缓存目录找！
            repo_id = "lllyasviel/Annotators"

            if preprocessor_type == "HED":
                from controlnet_aux import HEDdetector
                processor = HEDdetector.from_pretrained(repo_id)
                return processor(image)
            elif preprocessor_type == "MLSD":
                from controlnet_aux import MlsdDetector
                processor = MlsdDetector.from_pretrained(repo_id)
                return processor(image)
            elif preprocessor_type == "OPENPOSE":
                from controlnet_aux import OpenposeDetector
                processor = OpenposeDetector.from_pretrained(repo_id)
                return processor(image)
            elif preprocessor_type == "DEPTH":
                from controlnet_aux import MidasDetector
                processor = MidasDetector.from_pretrained(repo_id)
                return processor(image)
            elif preprocessor_type == "CANNY":
                # Canny 不需要权重，直接在本地算
                from controlnet_aux import CannyDetector
                return CannyDetector()(image)
            else:
                # 如果都不匹配，默认用 Canny 
                from controlnet_aux import CannyDetector
                return CannyDetector()(image)
        except ImportError as e:
            raise ImportError(f"请先安装 controlnet_aux: pip install controlnet-aux. 错误: {e}")
            
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能：
        Args:
            input_image_path: str, 原图路径
            prompt: str, 正向提示词
            negative_prompt: str, 负向提示词
            preprocessor_type: str, 预处理类型 (HED/Canny/MLSD/Openpose)
            controlnet_model: str, 底层 ControlNet 模型类型 (canny/lineart/openpose)
            strength: float, 重绘幅度 (默认 0.7)
            output_path: str, 输出图像路径
        """
        input_path = kwargs.get("input_image_path")
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        preprocessor_type = kwargs.get("preprocessor_type", "HED")
        controlnet_model = kwargs.get("controlnet_model", "canny")
        strength = kwargs.get("strength", 0.7)
        output_path = kwargs.get("output_path", "./output/controlnet_result.png")
        
        if not input_path:
            return {"status": "error", "error": "缺少 input_image_path 参数"}

        try:
            # 1. 获取基础 SD 模型配置
            sd_config = get_model_config()
            base_model_path = sd_config.get("model_path")
            if not base_model_path:
                return {"status": "error", "error": "未找到基础底模路径，请检查 model_config.py"}

            # 2. 读取并预处理原图 (获取线稿)
            original_image = Image.open(input_path).convert("RGB")
            self.logger.info(f"正在使用 {preprocessor_type} 提取线稿...")
            control_image = self._preprocess(original_image, preprocessor_type)

            # 3. 加载 Pipeline
            pipe = self._load_base_pipeline(base_model_path, controlnet_model)

            # 4. 图生图重绘
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

            # 5. 保存结果
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result_image.save(output_path)

            self.logger.info(f"生成完成: {output_path}")
            return {
                "status": "success",
                "image_path": str(output_path),
                "control_image_path": None  # 可选：这里可以顺便保存线稿图方便查看
            }

        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # 本地测试
    skill = ControlNetImg2Img()
    result = skill.execute(
        input_image_path="test.png",
        prompt="a beautiful realistic portrait, full color",
        preprocessor_type="HED",
        controlnet_model="hed"
    )
    print(result)