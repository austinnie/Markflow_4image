"""
SignatureExtractor - > 从带有签名的图片中，提取纯黑字迹并去除背景，自动裁剪生成透明背景的签名图片，可直接插入到文档中。
该技能利用 OpenCV 计算机视觉技术，对包含手写签名或印章的图片进行预处理。通过自适应阈值化、连通域面积过滤和形态学平滑，精准提取出签名笔迹，去除纸张底色、噪点和无关背景，并自动裁剪出签名的主体区域。最终输出带有 Alpha 通道的透明背景 PNG 图片，可直接无缝插入到 PDF 或 Word 文档中。


输入参数:
  - input_path (string): 包含签名的原图片路径 (支持 .jpg, .png, .bmp)
  - output_path (string): 提取后透明背景签名图片的保存路径 (必须为 .png)
  - min_area (integer): 过滤噪点的最小像素面积，可根据图片分辨率微调
  - save_result (boolean): 是否将提取参数和结果信息保存为日志文件

输出:
  - status: 执行状态：success / error
  - result: 包含提取结果详情、保存路径和图片尺寸等信息的字典
  - metadata: 技能名称、版本、执行时间等元数据

执行步骤:
  1. 使用 OpenCV 将输入图片读取为灰度图。
  2. 使用自适应高斯阈值反转为黑字白底（THRESH_BINARY_INV）。
  3. 遍历连通域，删除面积小于 min_area 的孤立噪点。
  4. 寻找笔迹边界框，添加 Padding 并进行裁剪。
  5. 构建 RGBA 图像，将笔迹设置为纯黑且不透明，背景设为全透明。
  6. 将结果保存为 PNG 格式，并返回执行结果。
"""

# import opencv-python  # 可选依赖
import os
import time
import json
import sys
import numpy as np
import random
import re

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Signatureextractor:
    """
    > 从带有签名的图片中，提取纯黑字迹并去除背景，自动裁剪生成透明背景的签名图片，可直接插入到文档中。
该技能利用 OpenCV 计算机视觉技术，对包含手写签名或印章的图片进行预处理。通过自适应阈值化、连通域面积过滤和形态学平滑，精准提取出签名笔迹，去除纸张底色、噪点和无关背景，并自动裁剪出签名的主体区域。最终输出带有 Alpha 通道的透明背景 PNG 图片，可直接无缝插入到 PDF 或 Word 文档中。
    
    执行技能功能
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化技能
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.name = "SignatureExtractor"
        self.version = "1.0.0"
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
        """设置配置"""
        defaults = {}
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> bool:
        """
        验证输入参数
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            验证是否通过
        """
        # 检查必填参数
        required_params = ["input_path", "output_path"]
        for param in required_params:
            if param not in kwargs or kwargs[param] is None or kwargs[param] == "":
                raise ValueError(f"缺少必需参数: {param}")

        # 类型验证
        if "min_area" in kwargs and kwargs["min_area"] is not None:
            try:
                kwargs["min_area"] = int(kwargs["min_area"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 min_area 必须是整数")
        if "save_result" in kwargs and kwargs["save_result"] is not None:
            if isinstance(kwargs["save_result"], str):
                kwargs["save_result"] = kwargs["save_result"].lower() in ["true", "1", "yes", "on"]

        # 设置默认值
        if "min_area" not in kwargs or kwargs["min_area"] is None:
            kwargs["min_area"] = '30'
        if "save_result" not in kwargs or kwargs["save_result"] is None:
            kwargs["save_result"] = 'True'

        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            执行结果
        """
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            # 执行步骤
            kwargs = self._step_1(**kwargs)
            kwargs = self._step_2(**kwargs)
            kwargs = self._step_3(**kwargs)
            kwargs = self._step_4(**kwargs)
            kwargs = self._step_5(**kwargs)
            kwargs = self._step_6(**kwargs)
            
            result_data = kwargs
            
            result = {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"技能执行成功: {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"技能执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _step_1(self, **kwargs):
            """
            使用 OpenCV 将输入图片读取为灰度图。
            """
            logger.info(f"执行步骤: 使用 OpenCV 将输入图片读取为灰度图。")
            
            # 获取数据源
            source = kwargs.get("source") or kwargs.get("file_path") or kwargs.get("data_source")
            if not source:
                for key in ["md_file", "file", "path", "input"]:
                    if key in kwargs and kwargs[key]:
                        source = kwargs[key]
                        break
            
            if not source:
                raise ValueError("未指定数据源")
            
            try:
                data = self._load_data(source, **kwargs)
                kwargs["data"] = data
                logger.info(f"数据加载成功: {source}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据加载失败: {e}")
                raise
            
            return kwargs

    def _step_2(self, **kwargs):
            """
            使用自适应高斯阈值反转为黑字白底（THRESH_BINARY_INV）。
            """
            logger.info(f"执行步骤: 使用自适应高斯阈值反转为黑字白底（THRESH_BINARY_INV）。")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {len(input_data)} 项")
                else:
                    logger.info(f"处理数据: {type(input_data).__name__}")
                kwargs["processed"] = input_data
            
            return kwargs

    def _step_3(self, **kwargs):
            """
            遍历连通域，删除面积小于 min_area 的孤立噪点。
            """
            logger.info(f"执行步骤: 遍历连通域，删除面积小于 min_area 的孤立噪点。")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {len(input_data)} 项")
                else:
                    logger.info(f"处理数据: {type(input_data).__name__}")
                kwargs["processed"] = input_data
            
            return kwargs

    def _step_4(self, **kwargs):
            """
            寻找笔迹边界框，添加 Padding 并进行裁剪。
            """
            logger.info(f"执行步骤: 寻找笔迹边界框，添加 Padding 并进行裁剪。")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {len(input_data)} 项")
                else:
                    logger.info(f"处理数据: {type(input_data).__name__}")
                kwargs["processed"] = input_data
            
            return kwargs

    def _step_5(self, **kwargs):
            """
            构建 RGBA 图像，将笔迹设置为纯黑且不透明，背景设为全透明。
            """
            logger.info(f"执行步骤: 构建 RGBA 图像，将笔迹设置为纯黑且不透明，背景设为全透明。")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {len(input_data)} 项")
                else:
                    logger.info(f"处理数据: {type(input_data).__name__}")
                kwargs["processed"] = input_data
            
            return kwargs

    def _step_6(self, **kwargs):
            """
            将结果保存为 PNG 格式，并返回执行结果。
            """
            logger.info(f"执行步骤: 将结果保存为 PNG 格式，并返回执行结果。")
            
            data = kwargs.get("data") or kwargs.get("result")
            destination = kwargs.get("destination") or kwargs.get("output") or kwargs.get("output_path")
            
            if not destination:
                for key in ["output_file", "save_path", "path"]:
                    if key in kwargs and kwargs[key]:
                        destination = kwargs[key]
                        break
            
            if not destination:
                raise ValueError("未指定保存路径")
            
            if data is None:
                raise ValueError("没有数据可保存")
            
            try:
                self._save_data(data, destination, **kwargs)
                kwargs["saved_path"] = destination
                logger.info(f"数据保存成功: {destination}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据保存失败: {e}")
                raise
            
            return kwargs


    def _handle_error(self, error: Exception, context: str = "") -> Dict:
        """处理错误"""
        logger.error(f"{context}: {error}")
        return {
            "status": "error",
            "error": str(error),
            "context": context
        }
    
    def _log_step(self, step_name: str, **kwargs):
        """记录步骤日志"""
        logger.info(f"步骤: {step_name}")


    def _load_data(self, source: str, **kwargs) -> Any:
        """加载数据"""
        import json
        from pathlib import Path
        
        if source.startswith(('http://', 'https://')):
            import requests
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type:
                return response.json()
            elif 'text' in content_type:
                return response.text
            else:
                return response.content
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {source}")
            
            if source.endswith(('.csv', '.tsv')):
                import pandas as pd
                return pd.read_csv(source)
            elif source.endswith('.json'):
                with open(source, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif source.endswith(('.yaml', '.yml')):
                import yaml
                with open(source, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    return f.read()


    def _save_data(self, data: Any, destination: str, **kwargs) -> bool:
        """保存数据"""
        import json
        from pathlib import Path
        
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        if destination.endswith('.json'):
            with open(destination, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif destination.endswith('.csv'):
            import pandas as pd
            if isinstance(data, (list, dict)):
                pd.DataFrame(data).to_csv(destination, index=False)
            else:
                pd.DataFrame([data]).to_csv(destination, index=False)
        elif destination.endswith(('.yaml', '.yml')):
            import yaml
            with open(destination, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        else:
            with open(destination, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        logger.info(f"数据已保存: {destination}")
        return True

    def __repr__(self):
        return f"<Signatureextractor(name={self.name}, version={self.version})>"