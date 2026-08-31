# skills/human_to_robot/skill.py
"""
HumanToRobot - 将人物照片转换为机器人/机械风格

输入参数:
  - image_path (string): 输入图片路径 (必填)
  - output_path (string): 输出图片路径 (必须为 .png)
  - ai_convert (boolean): 是否开启 AI 图生图转换 (默认: False，使用 OpenCV 机械滤镜)
  - style (string): 机器人风格 (cyberpunk_robot / mechanical / android)
  - save_result (boolean): 是否保存处理日志

输出:
  - status: 执行状态：success / error
  - result: 包含输出路径和转换详情的字典
  - metadata: 技能执行元数据
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 依赖检查
try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# 尝试引入 ControlNet 引擎
try:
    from skills.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError:
    CONTROLNET_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class HumanToRobot:
    """人物转机器人技能"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "HumanToRobot"
        self.version = "1.0.0"

        # 设定输出目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 ControlNet
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
            except Exception as e:
                logger.warning(f"ControlNet 初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_style': 'cyberpunk_robot',
            'default_ai_convert': False,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _apply_cyberpunk_filters(self, image: Image.Image, style: str = "cyberpunk_robot") -> Image.Image:
        """使用 OpenCV 赛博朋克滤镜"""
        if not CV2_AVAILABLE:
            return image

        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        # 1. 提取边缘
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

        # 2. 赛博朋克颜色偏移 (青色/洋红)
        b, g, r = cv2.split(img_cv)
        b = cv2.add(b, 60)
        r = cv2.add(r, 30)
        cyber_img = cv2.merge((b, g, r))

        # 3. 添加机械网格纹理
        noise = np.random.randint(0, 30, (h, w), dtype=np.uint8)
        grid = np.zeros((h, w), dtype=np.uint8)
        grid[::4, :] = 255
        grid[:, ::4] = 255
        grid = cv2.bitwise_and(grid, noise)

        # 4. 合并图层
        cyber_img[edges > 0] = [255, 255, 255]
        cyber_img[grid > 0] = [0, 255, 255]

        return Image.fromarray(cv2.cvtColor(cyber_img, cv2.COLOR_BGR2RGB))

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行技能（支持单张和批量目录）"""
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            # 1. 验证输入
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "缺少必填参数: image_path"}
            
            abs_image_path = Path(image_path).absolute()
            if not abs_image_path.exists():
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}"}

            # 读取参数
            ai_convert = kwargs.get('ai_convert', self.config.get('default_ai_convert', False))
            style = kwargs.get('style', self.config.get('default_style', 'cyberpunk_robot'))

            # ================= 支持批量模式 =================
            # 如果传入的是目录，则批量处理
            if abs_image_path.is_dir():
                valid_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                images = [p for p in abs_image_path.iterdir() if p.suffix.lower() in valid_exts]
                
                if not images:
                    return {"status": "error", "error": f"目录中没有找到图片: {abs_image_path}"}
                
                logger.info(f"📂 发现 {len(images)} 张图片，开始批量处理...")
                results = []
                
                for idx, img_path in enumerate(images):
                    # 自动生成输出路径
                    output_filename = f"{img_path.stem}_robot_{idx}.png"
                    output_path = str(self.output_dir / output_filename)
                    
                    # 调用内部处理方法
                    result = self._process_single_image(str(img_path), output_path, ai_convert, style)
                    results.append(result)
                
                return {
                    "status": "success",
                    "result": {
                        "batch": True,
                        "total": len(results),
                        "items": results
                    },
                    "metadata": {
                        "skill": self.name,
                        "version": self.version,
                        "executed_at": str(__import__('datetime').datetime.now().isoformat())
                    }
                }
            
            # ================= 单张模式 =================
            output_path = kwargs.get('output_path')
            if not output_path:
                timestamp = Path(abs_image_path).stem
                output_path = str(self.output_dir / f"{timestamp}_robot.png")

            result = self._process_single_image(str(abs_image_path), output_path, ai_convert, style)
            
            return {
                "status": result.get("status"),
                "result": result,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": str(__import__('datetime').datetime.now().isoformat())
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": str(__import__('datetime').datetime.now().isoformat())
            }

    def _process_single_image(self, input_path: str, output_path: str, ai_convert: bool, style: str) -> Dict:
        """处理单张图片的私有方法"""
        try:
            if ai_convert and self.controlnet_engine:
                style_prompts = {
                    "cyberpunk_robot": "cyberpunk robot, humanoid robot, metallic skin, cybernetic implants, neon lights, 4k, masterpiece",
                    "mechanical": "mechanical android, metallic joints, industrial robot, exposed wires, highly detailed",
                    "android": "advanced android, artificial intelligence, human-like face, sleek metal, 8k"
                }
                prompt = style_prompts.get(style, style_prompts["cyberpunk_robot"])

                result = self.controlnet_engine.execute(
                    input_image_path=input_path,
                    prompt=prompt,
                    negative_prompt="human, skin, hair, organic, cartoon, blurry, low quality, deformed",
                    preprocessor_type="HED",
                    controlnet_model="canny",
                    strength=0.65,
                    output_path=output_path
                )
                if result['status'] != 'success':
                    return result
            else:
                image = Image.open(input_path).convert("RGB")
                image = self._apply_cyberpunk_filters(image, style=style)
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                image.save(output_path, format='PNG')

            return {
                "status": "success",
                "output_path": output_path,
                "style": style,
                "ai_converted": ai_convert
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "input_path": input_path
            }
            
    def __repr__(self):
        return f"<HumanToRobot(name={self.name}, version={self.version})>"