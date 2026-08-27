"""
ControlNet - 提供姿态检测和 ControlNet 控制能力
支持 10 种 ControlNet 类型，Pipeline 生图，批量处理
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

# ==================== 依赖检查 ====================
try:
    import torch
    import numpy as np
    from PIL import Image
    import cv2
    TORCH_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    logger.warning(f"基础依赖未安装: {e}")

try:
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")

try:
    from controlnet_aux import (
        OpenposeDetector,
        CannyDetector,
        HEDdetector,
        MidasDetector,
        LineartDetector,
        NormalBaeDetector,
        MLSDdetector,
        DWposeDetector,
    )
    # 尝试导入新增的检测器
    try:
        from controlnet_aux import (SegDetector, UniformerDetector)
        SEG_AVAILABLE = True
    except ImportError:
        SEG_AVAILABLE = False
        logger.warning("SegDetector/UniformerDetector 不可用，请更新 controlnet-aux")
    
    CONTROLNET_AUX_AVAILABLE = True
except ImportError as e:
    CONTROLNET_AUX_AVAILABLE = False
    SEG_AVAILABLE = False
    logger.warning(f"controlnet_aux 未安装: {e}")


# ==================== ControlNet 类型配置 ====================
CONTROLNET_TYPES = {
    # ===== 原有类型 =====
    "canny": {
        "name": "Canny (边缘)",
        "model_id": "lllyasviel/sd-controlnet-canny",
        "preprocessor": "canny",
        "description": "边缘轮廓控制，适合保持构图"
    },
    "hed": {
        "name": "HED (软边缘)",
        "model_id": "lllyasviel/sd-controlnet-hed",
        "preprocessor": "hed",
        "description": "软边缘检测，更灵活"
    },
    "lineart": {
        "name": "Lineart (线稿)",
        "model_id": "lllyasviel/control_v11p_sd15_lineart",
        "preprocessor": "lineart",
        "description": "线稿提取，适合二次元"
    },
    "depth": {
        "name": "Depth (深度)",
        "model_id": "lllyasviel/sd-controlnet-depth",
        "preprocessor": "depth",
        "description": "深度图控制，适合保持空间结构"
    },
    "normal": {
        "name": "Normal (法线)",
        "model_id": "lllyasviel/sd-controlnet-normal",
        "preprocessor": "normal",
        "description": "法线图控制，适合保持光影"
    },
    "mlsd": {
        "name": "MLSD (直线)",
        "model_id": "lllyasviel/sd-controlnet-mlsd",
        "preprocessor": "mlsd",
        "description": "直线检测，适合建筑"
    },
    "openpose": {
        "name": "OpenPose (姿态)",
        "model_id": "lllyasviel/sd-controlnet-openpose",
        "preprocessor": "openpose",
        "description": "检测人体姿态骨架，适合换装"
    },
    "openpose_full": {
        "name": "OpenPose Full (完整姿态)",
        "model_id": "lllyasviel/control_v11p_sd15_openpose",
        "preprocessor": "openpose_full",
        "description": "全身姿态 + 手指 + 面部表情"
    },
    
    # ===== 新增类型 =====
    "seg": {
        "name": "Segmentation (语义分割)",
        "model_id": "lllyasviel/sd-controlnet-seg",
        "preprocessor": "seg",
        "description": "语义分割控制，适合换背景、场景转换"
    },
    "scribble": {
        "name": "Scribble (涂鸦)",
        "model_id": "lllyasviel/sd-controlnet-scribble",
        "preprocessor": "scribble",
        "description": "涂鸦控制，适合手绘控制"
    },
}


class Controlnet:
    """
    ControlNet 技能

    提供:
        1. 姿态检测 (detect_pose)
        2. ControlNet Pipeline 加载 (load_pipeline)
        3. 图片生成 (generate)
        4. 批量处理 (batch_process)
        5. 状态查看 (status)
        6. 类型列表 (list_types)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 ControlNet 技能

        Args:
            config: 配置字典
                - device: 设备 (cpu/cuda)
                - max_size: 最大尺寸
                - cache_dir: 缓存目录
                - default_model_path: 默认 SD 模型路径
        """
        self.config = config or {}
        self.name = "ControlNet"
        self.version = "2.0.0"

        # 获取技能目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 配置
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.max_size = self.config.get('max_size', 512)
        self.cache_dir = self.config.get('cache_dir', str(self.skill_dir / 'cache'))
        self.default_model_path = self.config.get('default_model_path', None)

        # 缓存
        self._pipelines = {}
        self._detectors = {}

        self._setup_logging()
        self._setup_config()

        logger.info(f"ControlNet v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  最大尺寸: {self.max_size}")
        logger.info(f"  diffusers: {'✅' if DIFFUSERS_AVAILABLE else '❌'}")
        logger.info(f"  controlnet_aux: {'✅' if CONTROLNET_AUX_AVAILABLE else '❌'}")

    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        """设置配置默认值"""
        defaults = {
            'max_size': 512,
            'controlnet_strength': 0.8,
            'device': self.device,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _get_detector(self, controlnet_type: str):
        """获取或创建检测器"""
        if not CONTROLNET_AUX_AVAILABLE:
            return None

        if controlnet_type in self._detectors:
            return self._detectors[controlnet_type]

        try:
            detectors = {
                "openpose": lambda: OpenposeDetector.from_pretrained("lllyasviel/Annotators"),
                "openpose_full": lambda: OpenposeDetector.from_pretrained("lllyasviel/Annotators"),
                "canny": lambda: CannyDetector(),
                "hed": lambda: HEDdetector.from_pretrained("lllyasviel/Annotators"),
                "lineart": lambda: LineartDetector.from_pretrained("lllyasviel/Annotators"),
                "depth": lambda: MidasDetector.from_pretrained("lllyasviel/Annotators"),
                "normal": lambda: NormalBaeDetector.from_pretrained("lllyasviel/Annotators"),
                "mlsd": lambda: MLSDdetector.from_pretrained("lllyasviel/Annotators"),
            }
            
            # 新增检测器（如果可用）
            if SEG_AVAILABLE:
                detectors["seg"] = lambda: SegDetector.from_pretrained("lllyasviel/Annotators")
                detectors["scribble"] = lambda: ScribbleDetector.from_pretrained("lllyasviel/Annotators")

            if controlnet_type in detectors:
                logger.info(f"加载检测器: {controlnet_type}")
                self._detectors[controlnet_type] = detectors[controlnet_type]()
                return self._detectors[controlnet_type]
            else:
                logger.warning(f"不支持的检测器类型: {controlnet_type}")
                return None

        except Exception as e:
            logger.error(f"加载检测器失败 ({controlnet_type}): {e}")
            return None

    # ==================== 核心功能 ====================

    def detect_pose(
        self,
        image: Union[str, Image.Image],
        controlnet_type: str = "openpose",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检测图片，生成 ControlNet 控制图

        Args:
            image: 图片路径或 PIL Image
            controlnet_type: ControlNet 类型
            output_path: 输出路径 (可选)

        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"检测姿态: controlnet_type={controlnet_type}")

        # 1. 检查依赖
        if not CONTROLNET_AUX_AVAILABLE:
            return {
                "status": "error",
                "error": "controlnet_aux 未安装，请运行: pip install controlnet-aux"
            }

        # 2. 加载图片
        try:
            if isinstance(image, str):
                if not os.path.exists(image):
                    return {"status": "error", "error": f"图片不存在: {image}"}
                pil_image = Image.open(image).convert("RGB")
                image_path = image
            else:
                pil_image = image.convert("RGB")
                image_path = None
        except Exception as e:
            return {"status": "error", "error": f"加载图片失败: {e}"}

        # 3. 获取检测器
        detector = self._get_detector(controlnet_type)
        if detector is None:
            return {
                "status": "error",
                "error": f"无法加载检测器: {controlnet_type}"
            }

        # 4. 生成控制图
        try:
            # 调整尺寸
            w, h = pil_image.size
            if max(w, h) > self.max_size:
                scale = self.max_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # 执行检测
            if controlnet_type == "openpose":
                result = detector(pil_image, output_type="pil", include_hands=False, include_face=False)
            elif controlnet_type == "openpose_full":
                result = detector(pil_image, output_type="pil", include_hands=True, include_face=True)
            else:
                result = detector(pil_image, output_type="pil")

            if result is None:
                return {"status": "error", "error": "检测返回空结果"}

            # 5. 保存结果
            if output_path is None:
                if image_path:
                    base, ext = os.path.splitext(image_path)
                    filename = f"{os.path.basename(base)}_{controlnet_type}_control.png"
                    output_path = str(self.output_dir / filename)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = str(self.output_dir / f"pose_{controlnet_type}_{timestamp}.png")

            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "controlnet_type": controlnet_type,
                "processing_time": f"{time.time() - start_time:.2f}s",
                "size": result.size,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"检测失败: {e}")
            return {"status": "error", "error": str(e)}

    def get_pipeline(
        self,
        model_path: str,
        controlnet_type: str = "openpose"
    ) -> Dict[str, Any]:
        """
        加载 ControlNet Pipeline

        Args:
            model_path: SD 模型路径
            controlnet_type: ControlNet 类型

        Returns:
            执行结果
        """
        logger.info(f"加载 ControlNet Pipeline: model={model_path}, type={controlnet_type}")

        # 1. 检查依赖
        if not DIFFUSERS_AVAILABLE:
            return {
                "status": "error",
                "error": "diffusers 未安装，请运行: pip install diffusers"
            }

        # 2. 检查模型
        if not os.path.exists(model_path):
            return {
                "status": "error",
                "error": f"模型不存在: {model_path}"
            }

        # 3. 检查缓存
        cache_key = f"{model_path}_{controlnet_type}"
        if cache_key in self._pipelines:
            logger.info("使用缓存的 Pipeline")
            return {
                "status": "success",
                "pipeline": self._pipelines[cache_key],
                "controlnet_type": controlnet_type,
                "cached": True
            }

        # 4. 加载 ControlNet
        try:
            info = CONTROLNET_TYPES.get(controlnet_type)
            if info is None:
                return {
                    "status": "error",
                    "error": f"不支持的 ControlNet 类型: {controlnet_type}"
                }

            model_id = info["model_id"]
            logger.info(f"加载 ControlNet 模型: {model_id}")

            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                cache_dir=self.cache_dir,
            )

            # 5. 加载 Pipeline
            logger.info(f"加载 SD 模型: {model_path}")
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                model_path,
                controlnet=controlnet,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            pipe.to(self.device)
            pipe.enable_attention_slicing()

            # 6. 缓存
            self._pipelines[cache_key] = pipe

            return {
                "status": "success",
                "pipeline": pipe,
                "controlnet_type": controlnet_type,
                "cached": False,
                "device": self.device,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"加载 ControlNet Pipeline 失败: {e}")
            return {"status": "error", "error": str(e)}

    # ==================== 新增功能 1: Pipeline 生图 ====================

    def generate(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        controlnet_type: str = "openpose",
        model_path: Optional[str] = None,
        negative_prompt: str = "",
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        seed: int = -1,
        controlnet_conditioning_scale: float = 1.0,
        output_path: Optional[str] = None,
        save_control: bool = True,
    ) -> Dict[str, Any]:
        """
        使用 ControlNet 生成图片（一步到位）

        Args:
            image: 输入图片（控制源）
            prompt: 生成提示词
            controlnet_type: ControlNet 类型
            model_path: SD 模型路径（默认使用配置中的路径）
            negative_prompt: 负面提示词
            num_inference_steps: 推理步数
            guidance_scale: CFG 尺度
            seed: 随机种子 (-1 表示随机)
            controlnet_conditioning_scale: ControlNet 控制强度 (0.0-1.0)
            output_path: 输出路径
            save_control: 是否保存控制图

        Returns:
            生成结果
        """
        start_time = time.time()
        logger.info(f"ControlNet 生成图片: prompt={prompt[:50]}...")

        # 1. 检测控制图
        control_result = self.detect_pose(image, controlnet_type=controlnet_type)
        if control_result['status'] != 'success':
            return control_result

        control_image = Image.open(control_result['output_path'])

        # 2. 加载 Pipeline
        if model_path is None:
            model_path = self.default_model_path
            if model_path is None:
                return {
                    "status": "error",
                    "error": "请指定 model_path 或在配置中设置 default_model_path"
                }

        pipe_result = self.get_pipeline(model_path, controlnet_type=controlnet_type)
        if pipe_result['status'] != 'success':
            return pipe_result

        pipe = pipe_result['pipeline']

        # 3. 设置种子
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device=self.device).manual_seed(seed)

        # 4. 生成
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                image=control_image,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                controlnet_conditioning_scale=controlnet_conditioning_scale,
            )

            if not result or not result.images:
                return {"status": "error", "error": "生成失败，未返回图片"}

            generated_image = result.images[0]

            # 5. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"generated_{controlnet_type}_{timestamp}.png")

            generated_image.save(output_path)

            # 6. 保存控制图（可选）
            control_path = None
            if save_control:
                control_path = control_result['output_path']

            return {
                "status": "success",
                "output_path": output_path,
                "control_path": control_path,
                "controlnet_type": controlnet_type,
                "prompt": prompt,
                "seed": seed,
                "processing_time": f"{time.time() - start_time:.2f}s",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成失败: {e}")
            return {"status": "error", "error": str(e)}

    # ==================== 新增功能 2: 批量处理 ====================

    def batch_detect_pose(
        self,
        images: List[str],
        controlnet_type: str = "openpose",
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量检测姿态

        Args:
            images: 图片路径列表
            controlnet_type: ControlNet 类型
            output_dir: 输出目录

        Returns:
            批量结果
        """
        logger.info(f"批量检测: {len(images)} 张图片, type={controlnet_type}")

        results = []
        total = len(images)

        if output_dir is None:
            output_dir = str(self.output_dir / "batch")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        for idx, img_path in enumerate(images, 1):
            logger.info(f"处理 {idx}/{total}: {img_path}")

            if not os.path.exists(img_path):
                results.append({
                    "image": img_path,
                    "result": {"status": "error", "error": "图片不存在"}
                })
                continue

            output_path = str(Path(output_dir) / f"{Path(img_path).stem}_{controlnet_type}.png")
            result = self.detect_pose(img_path, controlnet_type, output_path)

            # 重试一次（如果失败）
            if result['status'] != 'success' and idx < total:
                logger.info(f"  重试...")
                result = self.detect_pose(img_path, controlnet_type, output_path)

            results.append({
                "image": img_path,
                "output": result['output_path'] if result['status'] == 'success' else None,
                "result": result
            })

            # 避免 GPU 过载
            if idx % 5 == 0 and self.device == 'cuda':
                torch.cuda.empty_cache()

        success_count = sum(1 for r in results if r['result']['status'] == 'success')

        return {
            "status": "success",
            "total": total,
            "success": success_count,
            "failed": total - success_count,
            "results": results,
            "output_dir": output_dir,
            "processing_time": f"{time.time() - start_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }

    def batch_generate(
        self,
        images: List[str],
        prompts: List[str],
        controlnet_type: str = "openpose",
        model_path: Optional[str] = None,
        negative_prompt: str = "",
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量生成图片

        Args:
            images: 图片路径列表
            prompts: 提示词列表（长度需与 images 一致，或单个提示词复用）
            controlnet_type: ControlNet 类型
            model_path: SD 模型路径
            negative_prompt: 负面提示词
            num_inference_steps: 推理步数
            guidance_scale: CFG 尺度
            output_dir: 输出目录

        Returns:
            批量结果
        """
        # 处理提示词
        if isinstance(prompts, str):
            prompts = [prompts] * len(images)
        elif len(prompts) != len(images):
            return {
                "status": "error",
                "error": f"提示词数量 ({len(prompts)}) 与图片数量 ({len(images)}) 不匹配"
            }

        logger.info(f"批量生成: {len(images)} 张图片")

        results = []
        total = len(images)

        if output_dir is None:
            output_dir = str(self.output_dir / "batch_generated")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        for idx, (img_path, prompt) in enumerate(zip(images, prompts), 1):
            logger.info(f"生成 {idx}/{total}: {img_path}")

            if not os.path.exists(img_path):
                results.append({
                    "image": img_path,
                    "result": {"status": "error", "error": "图片不存在"}
                })
                continue

            output_path = str(Path(output_dir) / f"{Path(img_path).stem}_{controlnet_type}_gen.png")
            result = self.generate(
                image=img_path,
                prompt=prompt,
                controlnet_type=controlnet_type,
                model_path=model_path,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                output_path=output_path,
            )

            results.append({
                "image": img_path,
                "prompt": prompt,
                "output": result['output_path'] if result['status'] == 'success' else None,
                "result": result
            })

            # 避免 GPU 过载
            if idx % 5 == 0 and self.device == 'cuda':
                torch.cuda.empty_cache()

        success_count = sum(1 for r in results if r['result']['status'] == 'success')

        return {
            "status": "success",
            "total": total,
            "success": success_count,
            "failed": total - success_count,
            "results": results,
            "output_dir": output_dir,
            "processing_time": f"{time.time() - start_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }

    # ==================== 新增功能 3: Gradio UI ====================

    def launch_gradio(self, share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860):
        """
        启动 Gradio UI

        Args:
            share: 是否生成公开链接
            server_name: 服务器地址
            server_port: 端口号
        """
        try:
            import gradio as gr
        except ImportError:
            print("❌ gradio 未安装，请运行: pip install gradio")
            return

        # 获取可用模型列表
        available_models = ["openpose", "canny", "hed", "depth", "normal", "mlsd", "lineart", "seg"]

        def gradio_detect(image, controlnet_type, max_size):
            if image is None:
                return None, "请上传图片"
            skill = Controlnet(config={'device': self.device, 'max_size': max_size})
            result = skill.detect_pose(image, controlnet_type=controlnet_type)
            if result['status'] == 'success':
                return result['output_path'], f"✅ 成功！耗时: {result['processing_time']}"
            return None, f"❌ 失败: {result.get('error', '未知错误')}"

        def gradio_generate(image, prompt, controlnet_type, model_path, steps, scale, seed, max_size):
            if image is None:
                return None, None, "请上传图片"
            if not prompt:
                return None, None, "请输入提示词"
            
            skill = Controlnet(config={'device': self.device, 'max_size': max_size})
            result = skill.generate(
                image=image,
                prompt=prompt,
                controlnet_type=controlnet_type,
                model_path=model_path,
                num_inference_steps=steps,
                guidance_scale=scale,
                seed=seed,
            )
            
            if result['status'] == 'success':
                control_path = result.get('control_path')
                return control_path, result['output_path'], f"✅ 成功！种子: {result['seed']}, 耗时: {result['processing_time']}"
            return None, None, f"❌ 失败: {result.get('error', '未知错误')}"

        with gr.Blocks(title="ControlNet 技能", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🎨 ControlNet 图片控制与生成")
            gr.Markdown("基于 ControlNet 的图片控制图提取和 AI 图片生成")

            with gr.Tab("🔍 检测控制图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        input_image_detect = gr.Image(label="上传图片", type="pil")
                        controlnet_type_detect = gr.Dropdown(
                            choices=available_models,
                            label="ControlNet 类型",
                            value="openpose"
                        )
                        max_size_detect = gr.Slider(256, 1024, value=512, step=64, label="最大尺寸")
                        detect_btn = gr.Button("🚀 提取控制图", variant="primary")
                    with gr.Column(scale=1):
                        output_image_detect = gr.Image(label="控制图")
                        status_detect = gr.Textbox(label="状态")

                detect_btn.click(
                    fn=gradio_detect,
                    inputs=[input_image_detect, controlnet_type_detect, max_size_detect],
                    outputs=[output_image_detect, status_detect]
                )

            with gr.Tab("✨ 生成图片"):
                with gr.Row():
                    with gr.Column(scale=1):
                        input_image_gen = gr.Image(label="上传控制源图片", type="pil")
                        prompt_gen = gr.Textbox(label="提示词", lines=3, placeholder="描述你想要生成的图片...")
                        controlnet_type_gen = gr.Dropdown(
                            choices=available_models,
                            label="ControlNet 类型",
                            value="openpose"
                        )
                        model_path_gen = gr.Textbox(
                            label="SD 模型路径",
                            value=self.default_model_path or "",
                            placeholder="E:/SD_OpenVINO/models/sd-v1-5/xxx.safetensors"
                        )
                        with gr.Row():
                            steps_gen = gr.Slider(10, 50, value=20, step=1, label="推理步数")
                            scale_gen = gr.Slider(1, 20, value=7.5, step=0.5, label="CFG Scale")
                        with gr.Row():
                            seed_gen = gr.Number(value=-1, label="随机种子 (-1 随机)")
                            max_size_gen = gr.Slider(256, 1024, value=512, step=64, label="最大尺寸")
                        generate_btn = gr.Button("🚀 生成图片", variant="primary")
                    with gr.Column(scale=1):
                        control_output_gen = gr.Image(label="控制图")
                        output_image_gen = gr.Image(label="生成结果")
                        status_gen = gr.Textbox(label="状态")

                generate_btn.click(
                    fn=gradio_generate,
                    inputs=[
                        input_image_gen, prompt_gen, controlnet_type_gen,
                        model_path_gen, steps_gen, scale_gen, seed_gen, max_size_gen
                    ],
                    outputs=[control_output_gen, output_image_gen, status_gen]
                )

            with gr.Tab("📋 帮助"):
                gr.Markdown("""
                ## 使用说明

                ### ControlNet 类型说明

                | 类型 | 说明 | 适用场景 |
                |------|------|----------|
                | openpose | 人体姿态骨架 | 换衣服、换装、保持动作 |
                | canny | 边缘轮廓 | 保持构图、换风格 |
                | depth | 空间深度结构 | 换背景、保持场景布局 |
                | hed | 软边缘 | 更灵活的风格转换 |
                | lineart | 线稿 | 线稿上色、二次元风格 |
                | normal | 法线图 | 保持光影结构 |
                | mlsd | 直线 | 建筑/室内设计 |
                | seg | 语义分割 | 换背景、场景转换 |

                ### 使用步骤

                1. 上传一张图片
                2. 选择 ControlNet 类型
                3. 点击 "提取控制图" 查看控制效果
                4. 输入提示词，点击 "生成图片" 生成结果

                ### 提示词示例

                - `"a beautiful girl, detailed face, masterpiece"`
                - `"cyberpunk city, neon lights, futuristic"`
                - `"oil painting style, van gogh, starry night"`
                """)

        print(f"🚀 启动 Gradio UI...")
        print(f"   http://{server_name}:{server_port}")
        demo.launch(share=share, server_name=server_name, server_port=server_port)

    # ==================== 基础功能 ====================

    def list_types(self) -> Dict[str, Any]:
        """列出所有支持的 ControlNet 类型"""
        types = {}
        for key, info in CONTROLNET_TYPES.items():
            types[key] = {
                "name": info["name"],
                "description": info["description"],
                "available": CONTROLNET_AUX_AVAILABLE,
            }

        return {
            "status": "success",
            "types": types,
            "count": len(types),
            "controlnet_aux_available": CONTROLNET_AUX_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

    def status(self) -> Dict[str, Any]:
        """查看 ControlNet 技能状态"""
        return {
            "status": "success",
            "skill": {
                "name": self.name,
                "version": self.version,
                "device": self.device,
                "max_size": self.max_size,
                "cache_dir": self.cache_dir,
                "default_model_path": self.default_model_path,
            },
            "dependencies": {
                "diffusers": DIFFUSERS_AVAILABLE,
                "controlnet_aux": CONTROLNET_AUX_AVAILABLE,
                "seg_available": SEG_AVAILABLE,
                "torch": TORCH_AVAILABLE,
            },
            "supported_types": list(CONTROLNET_TYPES.keys()),
            "cached_pipelines": list(self._pipelines.keys()),
            "timestamp": datetime.now().isoformat()
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 ControlNet 技能

        支持的操作:
            - status: 查看状态 (默认)
            - list_types: 列出支持的 ControlNet 类型
            - detect_pose: 检测姿态，生成控制图
            - load_pipeline: 加载 ControlNet Pipeline
            - generate: 一步生成图片（新增）
            - batch_detect: 批量检测（新增）
            - batch_generate: 批量生成（新增）
            - gui: 启动 Gradio UI（新增）
        """
        action = kwargs.get('action', 'status')
        logger.info(f"执行 ControlNet 技能: action={action}")

        if action == 'status':
            return self.status()

        elif action == 'list_types':
            return self.list_types()

        elif action == 'detect_pose':
            image = kwargs.get('image') or kwargs.get('image_path')
            if image is None:
                return {"status": "error", "error": "image 或 image_path 是必填参数"}
            controlnet_type = kwargs.get('controlnet_type', 'openpose')
            output_path = kwargs.get('output_path')
            return self.detect_pose(image, controlnet_type, output_path)

        elif action == 'load_pipeline':
            model_path = kwargs.get('model_path')
            if model_path is None:
                return {"status": "error", "error": "model_path 是必填参数"}
            controlnet_type = kwargs.get('controlnet_type', 'openpose')
            return self.get_pipeline(model_path, controlnet_type)

        elif action == 'generate':
            image = kwargs.get('image') or kwargs.get('image_path')
            if image is None:
                return {"status": "error", "error": "image 或 image_path 是必填参数"}
            prompt = kwargs.get('prompt')
            if prompt is None:
                return {"status": "error", "error": "prompt 是必填参数"}
            return self.generate(
                image=image,
                prompt=prompt,
                controlnet_type=kwargs.get('controlnet_type', 'openpose'),
                model_path=kwargs.get('model_path'),
                negative_prompt=kwargs.get('negative_prompt', ''),
                num_inference_steps=kwargs.get('steps', 20),
                guidance_scale=kwargs.get('cfg_scale', 7.5),
                seed=kwargs.get('seed', -1),
                controlnet_conditioning_scale=kwargs.get('controlnet_strength', 1.0),
                output_path=kwargs.get('output_path'),
                save_control=kwargs.get('save_control', True),
            )

        elif action == 'batch_detect':
            images = kwargs.get('images')
            if images is None:
                return {"status": "error", "error": "images 是必填参数"}
            if isinstance(images, str):
                images = [img.strip() for img in images.split(',')]
            return self.batch_detect_pose(
                images=images,
                controlnet_type=kwargs.get('controlnet_type', 'openpose'),
                output_dir=kwargs.get('output_dir'),
            )

        elif action == 'batch_generate':
            images = kwargs.get('images')
            prompts = kwargs.get('prompts')
            if images is None:
                return {"status": "error", "error": "images 是必填参数"}
            if prompts is None:
                return {"status": "error", "error": "prompts 是必填参数"}
            if isinstance(images, str):
                images = [img.strip() for img in images.split(',')]
            if isinstance(prompts, str):
                prompts = [p.strip() for p in prompts.split('||')]
            return self.batch_generate(
                images=images,
                prompts=prompts,
                controlnet_type=kwargs.get('controlnet_type', 'openpose'),
                model_path=kwargs.get('model_path'),
                negative_prompt=kwargs.get('negative_prompt', ''),
                num_inference_steps=kwargs.get('steps', 20),
                guidance_scale=kwargs.get('cfg_scale', 7.5),
                output_dir=kwargs.get('output_dir'),
            )

        elif action == 'gui':
            self.launch_gradio(
                share=kwargs.get('share', False),
                server_name=kwargs.get('server_name', '127.0.0.1'),
                server_port=kwargs.get('server_port', 7860),
            )
            return {"status": "success", "message": "Gradio UI 已启动"}

        else:
            return {
                "status": "error",
                "error": f"未知操作: {action}，支持: status, list_types, detect_pose, load_pipeline, generate, batch_detect, batch_generate, gui",
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<Controlnet(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ControlNet 技能 v2.0")
    parser.add_argument("--action", default="status",
                        choices=["status", "list_types", "detect_pose", "load_pipeline", 
                                "generate", "batch_detect", "batch_generate", "gui"],
                        help="操作类型")
    parser.add_argument("--image", help="图片路径 (detect_pose/generate)")
    parser.add_argument("--image-path", help="图片路径 (detect_pose/generate, 同 image)")
    parser.add_argument("--images", help="批量图片路径，用逗号分隔 (batch_detect/batch_generate)")
    parser.add_argument("--prompt", help="生成提示词 (generate/batch_generate)")
    parser.add_argument("--prompts", help="批量提示词，用 || 分隔 (batch_generate)")
    parser.add_argument("--output-path", help="输出路径 (detect_pose/generate)")
    parser.add_argument("--output-dir", help="输出目录 (batch_detect/batch_generate)")
    parser.add_argument("--model-path", help="SD 模型路径 (load_pipeline/generate)")
    parser.add_argument("--controlnet-type", default="openpose",
                        choices=list(CONTROLNET_TYPES.keys()),
                        help="ControlNet 类型")
    parser.add_argument("--negative-prompt", default="", help="负面提示词")
    parser.add_argument("--steps", type=int, default=20, help="推理步数")
    parser.add_argument("--cfg-scale", type=float, default=7.5, help="CFG 尺度")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子 (-1 随机)")
    parser.add_argument("--controlnet-strength", type=float, default=1.0, help="ControlNet 控制强度 (0.0-1.0)")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--share", action="store_true", help="Gradio 公开链接 (gui)")
    parser.add_argument("--port", type=int, default=7860, help="Gradio 端口 (gui)")

    args = parser.parse_args()

    skill = Controlnet(config={'device': args.device})

    if args.action == "gui":
        skill.launch_gradio(share=args.share, server_port=args.port)
    else:
        result = skill.execute(
            action=args.action,
            image=args.image or args.image_path,
            images=args.images,
            prompt=args.prompt,
            prompts=args.prompts,
            output_path=args.output_path,
            output_dir=args.output_dir,
            model_path=args.model_path,
            controlnet_type=args.controlnet_type,
            negative_prompt=args.negative_prompt,
            steps=args.steps,
            cfg_scale=args.cfg_scale,
            seed=args.seed,
            controlnet_strength=args.controlnet_strength,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))