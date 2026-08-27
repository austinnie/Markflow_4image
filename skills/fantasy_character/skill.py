# skills/fantasy_character/skill.py
"""
奇幻角色 Skill - 将人物变成奇幻角色（精灵/天使/恶魔/魔法师等）
使用 OpenPose ControlNet 保持姿态，Inpaint 重绘整体
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 尝试导入依赖
try:
    import torch
    from PIL import Image
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 未安装: {e}")

try:
    from skills.controlnet.skill import Controlnet
    CONTROLNET_AVAILABLE = True
except ImportError as e:
    CONTROLNET_AVAILABLE = False
    logger.warning(f"ControlNet 技能不可用: {e}")

# 奇幻角色提示词配置
FANTASY_PROMPTS = {
    "elf": {
        "prompt": "beautiful elf, long pointed ears, fantasy elf, elegant, magical, nature, fantasy character, masterpiece, high quality, detailed",
        "negative": "ugly, deformed, human, modern, realistic, bad anatomy"
    },
    "angel": {
        "prompt": "beautiful angel, white feathered wings, golden halo, divine, ethereal, heavenly, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, demon, devil, dark, evil"
    },
    "demon": {
        "prompt": "beautiful demon, curved horns, dark bat wings, seductive, dark fantasy, hellfire, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, angel, holy, light, pure"
    },
    "mage": {
        "prompt": "powerful mage, wizard, magical robes, staff, spellcasting, arcane energy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, realistic, casual"
    },
    "knight": {
        "prompt": "majestic knight, full plate armor, fantasy knight, sword, shield, heroic, noble, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, casual, civilian"
    },
    "fairy": {
        "prompt": "beautiful fairy, translucent wings, glowing, magical, ethereal, nature spirit, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "vampire": {
        "prompt": "elegant vampire, pale skin, sharp fangs, gothic, aristocratic, dark fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cheerful"
    },
    "merfolk": {
        "prompt": "beautiful mermaid, fish tail, underwater, coral, seashells, aquatic fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, legs"
    },
    "dragonborn": {
        "prompt": "dragonborn character, dragon scales, reptilian features, fantasy, powerful, elemental, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "phoenix": {
        "prompt": "phoenix themed character, fiery, reborn, majestic, golden flames, fantasy, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cold"
    }
}


class FantasyCharacter:
    """奇幻角色技能 - 将人物照片转换为奇幻角色"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化奇幻角色技能
        
        Args:
            config: 配置字典，支持以下键：
                - models_dir: 模型目录
                - device: 设备 (cuda/cpu)
                - default_model: 默认模型名称
                - default_steps: 默认推理步数
                - default_strength: 默认变换强度
                - default_type: 默认奇幻类型
                - default_negative: 默认负面提示词
                - output_dir: 输出目录
                - log_level: 日志级别
        """
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "1.0.0"

        # 设置目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = Path(self.config.get('output_dir', self.skill_dir / 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置模型路径和设备
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # 初始化状态
        self.pipeline = None
        self.current_model = None
        self.controlnet_skill = None

        # 初始化 ControlNet
        if CONTROLNET_AVAILABLE:
            try:
                self.controlnet_skill = Controlnet(config={
                    'device': self.device,
                    'max_size': 512,
                    'models_dir': str(self.models_dir)
                })
                logger.info("ControlNet 技能初始化成功")
            except Exception as e:
                logger.warning(f"ControlNet 技能初始化失败: {e}")

        # 设置配置和日志
        self._setup_logging()
        self._setup_config()

        logger.info(f"FantasyCharacter 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  输出目录: {self.output_dir}")
        logger.info(f"  奇幻类型: {list(FANTASY_PROMPTS.keys())}")

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
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 35,
            'default_strength': 0.8,
            'default_type': 'elf',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality, modern, realistic, human',
            'max_size': 768,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _find_model(self, model_name: str) -> Optional[Path]:
        """查找模型文件"""
        if not model_name:
            return None
        
        # 尝试多个可能的路径
        possible_paths = [
            self.models_dir / "sd-v1-5" / model_name,
            self.models_dir / "inpainting" / model_name,
            self.models_dir / model_name,
            Path(model_name),  # 直接路径
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        """加载 Inpaint Pipeline"""
        try:
            if not DIFFUSERS_AVAILABLE:
                logger.error("diffusers 不可用，请安装: pip install diffusers")
                return False
            
            logger.info(f"加载模型: {model_path}")
            
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline.to(self.device)
            
            # 内存优化
            self.pipeline.enable_attention_slicing()
            if self.device == 'cuda':
                self.pipeline.enable_model_cpu_offload()
            
            self.current_model = model_path.name
            logger.info(f"模型加载成功: {self.current_model}")
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        """加载模型"""
        if self.current_model == model_name and self.pipeline is not None:
            return True
        
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型不存在: {model_name}")
            return False
        
        return self._load_pipeline(model_path)

    def _generate_pose_image(self, image: Image.Image) -> Optional[Image.Image]:
        """使用 ControlNet 生成姿态图"""
        if self.controlnet_skill is None:
            logger.debug("ControlNet 不可用，跳过姿态检测")
            return None
        
        try:
            # 临时保存图片
            temp_path = self.output_dir / "temp_pose_input.png"
            image.save(temp_path)
            
            result = self.controlnet_skill.execute(
                action='detect_pose',
                image=str(temp_path),
                controlnet_type='openpose',
                output_path=None
            )
            
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            
            if result.get('status') == 'success':
                output_path = result.get('output_path')
                if output_path and Path(output_path).exists():
                    pose_img = Image.open(output_path)
                    logger.info("姿态图生成成功")
                    return pose_img
            
            return None
            
        except Exception as e:
            logger.warning(f"姿态图生成失败: {e}")
            return None

    def _resize_image(self, image: Image.Image) -> tuple:
        """调整图片大小到合适尺寸"""
        w, h = image.size
        max_size = self.config.get('max_size', 768)
        
        # 确保尺寸是 64 的倍数（Stable Diffusion 要求）
        def make_multiple_of_64(x):
            return (x // 64) * 64
        
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
        else:
            new_w, new_h = w, h
        
        # 确保是 64 的倍数
        new_w = make_multiple_of_64(new_w)
        new_h = make_multiple_of_64(new_h)
        
        if new_w < 64:
            new_w = 64
        if new_h < 64:
            new_h = 64
        
        if (new_w, new_h) != (w, h):
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            logger.info(f"图片调整大小: {w}x{h} -> {new_w}x{new_h}")
        
        return image, (new_w, new_h)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行奇幻角色转换
        
        Args:
            image_path: 输入图片路径 (必需)
            fantasy_type: 奇幻类型 (elf/angel/demon/mage/knight/fairy/vampire/merfolk/dragonborn/phoenix)
            model_name: 模型名称
            prompt: 自定义提示词
            negative_prompt: 自定义负面提示词
            steps: 推理步数
            strength: 变换强度 (0.0-1.0)
            seed: 随机种子 (-1 表示随机)
            output_dir: 输出目录
            use_controlnet: 是否使用 ControlNet (默认 True)
            
        Returns:
            包含状态、输出路径和元数据的字典
        """
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            # 1. 验证输入
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "缺少 image_path 参数"}
            
            if not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}

            # 2. 获取参数
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_PROMPTS:
                return {
                    "status": "error",
                    "error": f"未知奇幻类型: {fantasy_type}，可用: {list(FANTASY_PROMPTS.keys())}"
                }

            f_config = FANTASY_PROMPTS[fantasy_type]
            prompt = kwargs.get('prompt') or f_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or f_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))
            use_controlnet = kwargs.get('use_controlnet', True)

            # 3. 加载模型
            if not self._load_model(model_name):
                return {"status": "error", "error": f"无法加载模型: {model_name}"}

            # 4. 准备图片
            image = Image.open(image_path).convert("RGB")
            image, (width, height) = self._resize_image(image)
            original_size = Image.open(image_path).size
            logger.info(f"图片尺寸: {width}x{height}")

            # 5. 生成姿态图 (可选)
            control_image = None
            if use_controlnet and self.controlnet_skill is not None:
                control_image = self._generate_pose_image(image)

            # 6. 设置种子
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            # 7. 创建全图遮罩 (Inpaint 全图)
            mask = Image.new("L", (width, height), 0)

            # 8. 执行生成
            logger.info(f"奇幻类型: {fantasy_type}")
            logger.info(f"提示词: {prompt[:80]}...")
            logger.info(f"步数: {steps}, 强度: {strength}, 种子: {seed}")

            pipeline_kwargs = {
                'prompt': prompt,
                'negative_prompt': negative_prompt if negative_prompt else None,
                'image': control_image if control_image else image,
                'mask_image': mask,
                'num_inference_steps': steps,
                'strength': strength,
                'generator': generator,
                'width': width,
                'height': height,
                'guidance_scale': 7.5,
            }

            result = self.pipeline(**pipeline_kwargs)

            if not result or not hasattr(result, 'images') or len(result.images) == 0:
                return {"status": "error", "error": "生成失败，未返回图像"}

            generated_image = result.images[0]

            # 9. 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(kwargs.get('output_dir', self.config.get('output_dir', str(self.output_dir))))
            output_dir.mkdir(parents=True, exist_ok=True)

            output_filename = f"{fantasy_type}_{timestamp}.png"
            output_path = output_dir / output_filename
            generated_image.save(output_path)

            # 10. 保存元数据
            metadata = {
                'skill': self.name,
                'version': self.version,
                'fantasy_type': fantasy_type,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'model': model_name,
                'steps': steps,
                'strength': strength,
                'seed': seed,
                'width': width,
                'height': height,
                'original_image': os.path.basename(image_path),
                'original_size': original_size,
                'output_path': str(output_path),
                'timestamp': timestamp,
                'use_controlnet': use_controlnet,
            }

            metadata_path = output_dir / f"{fantasy_type}_{timestamp}.meta.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            elapsed_time = time.time() - start_time
            logger.info(f"生成完成，耗时: {elapsed_time:.2f}s")
            logger.info(f"输出: {output_path}")

            return {
                "status": "success",
                "output_path": str(output_path),
                "metadata_path": str(metadata_path),
                "fantasy_type": fantasy_type,
                "seed": seed,
                "elapsed_time": elapsed_time,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"执行失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }
        finally:
            # 清理 GPU 内存
            if hasattr(self, 'pipeline') and self.pipeline is not None:
                try:
                    if torch.cuda.is_available():
                        self.pipeline.to('cpu')
                        torch.cuda.empty_cache()
                except:
                    pass

    def get_available_types(self) -> Dict[str, str]:
        """获取可用的奇幻类型及描述"""
        return {
            k: v['prompt'][:50] + '...' 
            for k, v in FANTASY_PROMPTS.items()
        }

    def get_type_info(self, fantasy_type: str) -> Optional[Dict[str, str]]:
        """获取特定类型的提示词信息"""
        return FANTASY_PROMPTS.get(fantasy_type)

    def batch_process(self, image_paths: List[str], fantasy_type: str = 'elf', **kwargs) -> List[Dict[str, Any]]:
        """
        批量处理多张图片
        
        Args:
            image_paths: 图片路径列表
            fantasy_type: 奇幻类型
            **kwargs: 其他参数
            
        Returns:
            结果列表
        """
        results = []
        total = len(image_paths)
        
        for idx, img_path in enumerate(image_paths):
            logger.info(f"处理 {idx+1}/{total}: {img_path}")
            result = self.execute(
                image_path=img_path,
                fantasy_type=fantasy_type,
                **kwargs
            )
            results.append({
                'image': img_path,
                'result': result
            })
            # 简单延迟避免资源竞争
            if idx < total - 1:
                time.sleep(0.5)
        
        return results

    def __repr__(self) -> str:
        return f"<FantasyCharacter skill v{self.version} on {self.device}>"


# ============ 便捷函数 ============

def create_fantasy_character(
    image_path: str,
    fantasy_type: str = 'elf',
    model_name: str = None,
    output_dir: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    快捷函数：将人物照片转换为奇幻角色
    
    Args:
        image_path: 输入图片路径
        fantasy_type: 奇幻类型 (elf/angel/demon/mage/knight/fairy/vampire/merfolk/dragonborn/phoenix)
        model_name: 模型名称
        output_dir: 输出目录
        **kwargs: 其他参数 (steps, strength, seed, prompt, negative_prompt, use_controlnet)
    
    Returns:
        包含输出路径和元数据的字典
    """
    skill = FantasyCharacter(config={
        'default_model': model_name,
        'output_dir': output_dir,
    })
    
    return skill.execute(
        image_path=image_path,
        fantasy_type=fantasy_type,
        **kwargs
    )


# ============ 命令行入口 ============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='奇幻角色生成器 - 将人物照片转换为奇幻角色',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
可用的奇幻类型:
  {', '.join(FANTASY_PROMPTS.keys())}

示例:
  python skill.py photo.jpg -t elf -s 30 -r 0.75
  python skill.py photo.jpg -t angel --seed 42
  python skill.py photo.jpg -t demon --prompt "beautiful dark demon queen"
        '''
    )
    
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-t', '--type', default='elf', 
                       choices=list(FANTASY_PROMPTS.keys()),
                       help='奇幻类型 (默认: elf)')
    parser.add_argument('-m', '--model', help='模型名称')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-s', '--steps', type=int, default=35, help='推理步数 (默认: 35)')
    parser.add_argument('-r', '--strength', type=float, default=0.8, help='变换强度 0.0-1.0 (默认: 0.8)')
    parser.add_argument('--seed', type=int, default=-1, help='随机种子 (默认: -1 随机)')
    parser.add_argument('--prompt', help='自定义提示词')
    parser.add_argument('--negative', help='自定义负面提示词')
    parser.add_argument('--no-controlnet', action='store_true', help='禁用 ControlNet')
    parser.add_argument('--list-types', action='store_true', help='列出所有奇幻类型')
    
    args = parser.parse_args()
    
    if args.list_types:
        print("可用的奇幻类型:")
        for t in FANTASY_PROMPTS.keys():
            print(f"  - {t}")
        sys.exit(0)
    
    # 创建技能实例并执行
    skill = FantasyCharacter()
    result = skill.execute(
        image_path=args.image,
        fantasy_type=args.type,
        model_name=args.model,
        output_dir=args.output,
        steps=args.steps,
        strength=args.strength,
        seed=args.seed,
        prompt=args.prompt,
        negative_prompt=args.negative,
        use_controlnet=not args.no_controlnet,
    )
    
    if result['status'] == 'success':
        print(f"\n✅ 生成成功!")
        print(f"  输出: {result['output_path']}")
        print(f"  类型: {result['fantasy_type']}")
        print(f"  种子: {result['seed']}")
        print(f"  耗时: {result['elapsed_time']:.2f}s")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")
        sys.exit(1)