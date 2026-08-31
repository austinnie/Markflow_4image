"""
SignatureExtractor - 从带有签名的图片中提取纯黑字迹，去除背景并自动裁剪

输入参数:
  - input_path (string): 包含签名的原图片路径（支持 jpg/png/bmp）
  - output_path (string): 提取后透明背景签名图片的保存路径（必须为 .png）
  - min_area (integer): 过滤噪点的最小像素面积，默认 30
  - save_result (boolean): 是否将提取参数和结果信息保存为日志文件

输出:
  - status: 执行状态：success / error
  - result: 包含提取结果详情、保存路径和图片尺寸等信息的字典
  - metadata: 技能名称、版本、执行时间等元数据
"""

import os
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Signatureextractor:
    """
    基于 OpenCV 的签名提取与背景去除技能
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "SignatureExtractor"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()

        # 输出目录配置（完全参考 ImageRecognizer 写法）
        self.output_dir = Path(self.config.get("output_dir", "./skills/signatureextractor/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SignatureExtractor 初始化完成，版本: {self.version}")

    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        """设置配置"""
        defaults = {
            "output_dir": "./skills/signatureextractor/output",
            "default_min_area": 30,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required_params = ["input_path", "output_path"]
        for param in required_params:
            if param not in kwargs or kwargs[param] is None or kwargs[param] == "":
                raise ValueError(f"缺少必需参数: {param}")

        # 验证输入图片路径
        input_path = Path(kwargs["input_path"])
        if not input_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {input_path}")

        # 验证图片格式
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        if input_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"不支持的图片格式: {input_path.suffix}，支持: {', '.join(valid_extensions)}")

        # 验证输出路径必须是 png (因为需要透明通道)
        output_path = Path(kwargs["output_path"])
        if output_path.suffix.lower() != '.png':
            raise ValueError("输出格式必须是 .png，以确保保留透明背景通道！")

        # 设置默认值
        if "min_area" not in kwargs or kwargs["min_area"] is None:
            kwargs["min_area"] = self.config.get("default_min_area", 30)
        else:
            kwargs["min_area"] = int(kwargs["min_area"])

        if "save_result" not in kwargs or kwargs["save_result"] is None:
            kwargs["save_result"] = True

        return True

    def _run_core_algorithm(self, input_path: str, output_path: str, min_area: int = 30) -> Dict:
        """核心 OpenCV 提取逻辑"""
        # 1. 读取图片（灰度模式）
        img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"❌ 严重错误：无法读取图片，请检查路径是否正确！路径为: {input_path}")

        # 2. 自适应二值化提取笔迹
        thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 31, 10)

        # 3. 连通域过滤降噪
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)
        new_thresh = np.zeros_like(thresh)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                new_thresh[labels == i] = 255
        thresh = new_thresh

        # 4. 自动裁剪
        coords = cv2.findNonZero(thresh)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            pad = 10
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(thresh.shape[1] - x, w + pad * 2)
            h = min(thresh.shape[0] - y, h + pad * 2)
            thresh = thresh[y:y + h, x:x + w]
        else:
            raise ValueError("未检测到任何有效笔迹，无法提取签名。")

        # 5. 形态学平滑（去除毛刺）
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # 6. 构建透明背景的纯黑字迹 PNG
        height, width = thresh.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        rgba[:, :, 0] = 0
        rgba[:, :, 1] = 0
        rgba[:, :, 2] = 0
        rgba[:, :, 3] = thresh  # Alpha通道，笔迹处为255，背景为0

        # 7. 确保输出目录存在并保存
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cv2.imwrite(output_path, rgba)

        return {"width": width, "height": height, "shape": f"{width}x{height}", "output_path": output_path}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能

        Args:
            input_path: 包含签名的图片路径 (必填)
            output_path: 输出透明背景 PNG 的路径 (必填)
            min_area: 最小噪点面积阈值 (默认 30)
            save_result: 是否保存日志 (默认 True)

        Returns:
            执行结果字典
        """
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            self._validate_inputs(**kwargs)

            input_path = kwargs["input_path"]
            output_path = kwargs["output_path"]
            min_area = kwargs.get("min_area", 30)
            save_result = kwargs.get("save_result", True)

            # 执行核心提取
            result_info = self._run_core_algorithm(input_path, output_path, min_area)

            # 构建结果数据
            result_data = {
                "input_path": input_path,
                "output_path": output_path,
                "image_shape": result_info.get("shape"),
                "status": "success",
            }

            # 保存 JSON 日志（如果开启）
            saved_files = []
            if save_result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = self.output_dir / f"signature_{timestamp}.json"
                with open(log_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump({"status": "success", "result": result_data}, f, ensure_ascii=False, indent=2)
                saved_files.append(str(log_file))
                result_data["saved_to"] = saved_files

            result = {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }

            logger.info(f"✅ 提取完成")
            return result

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<Signatureextractor(name={self.name}, version={self.version})>"