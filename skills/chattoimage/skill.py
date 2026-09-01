"""
ChatToImage - 对话式图像生成技能
通过自然语言对话生成和编辑图片

支持两种调用方式:
  1. CLI: python -m markflow.cli.commands execute ChatToImage message="帮我换衣服"
  2. 直接运行: python skills/chattoimage/skill.py --message "帮我换衣服" --image_path input.jpg
"""

import os
import re
import json
import sys
import logging
import requests
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import deque

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 尝试导入 markflow 核心
try:
    from markflow.core.executor import SkillExecutor
    from markflow.core.quality import CodeQualityChecker
except ImportError:
    # 兼容独立运行
    SkillExecutor = None
    CodeQualityChecker = None

logger = logging.getLogger(__name__)


class Chattoimage:
    """对话式图像生成技能"""

    # ==================== 意图映射（完整版） ====================
    INTENT_MAP = {
        # ---- 文生图 ----
        "text_to_image": {
            "skill": "sd_image_generator",
            "params": {
                "prompt": "{prompt}",
                "negative_prompt": "",
                "model_name": "{model_name}",
                "width": "{width}",
                "height": "{height}",
                "steps": "{steps}",
                "cfg_scale": "{cfg_scale}",
                "seed": "{seed}",
                "batch_size": 1
            },
            "required": ["prompt"],
            "description": "文生图"
        },

        # ---- 人物编辑 ----
        "change_clothes": {
            "skill": "change_clothes",
            "params": {
                "image_path": "{image_path}",
                "prompt": "{prompt}",
                "strength": "{strength}",
                "controlnet_type": "openpose",
                "use_controlnet": True,
                "save_mask": False
            },
            "required": ["image_path", "prompt"],
            "description": "换衣服"
        },
        "change_clothing_style": {
            "skill": "change_clothing_style",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path", "style"],
            "description": "换服装风格"
        },
        "change_expression": {
            "skill": "change_expression",
            "params": {
                "image_path": "{image_path}",
                "expression": "{expression}",
                "strength": "{strength}"
            },
            "required": ["image_path", "expression"],
            "description": "换表情"
        },
        "change_hair": {
            "skill": "change_hair",
            "params": {
                "image_path": "{image_path}",
                "hair_color": "{hair_color}",
                "hairstyle": "{hairstyle}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "换发型/发色"
        },
        "change_eye_color": {
            "skill": "change_eye_color",
            "params": {
                "image_path": "{image_path}",
                "color": "{color}",
                "strength": "{strength}"
            },
            "required": ["image_path", "color"],
            "description": "换眼睛颜色"
        },
        "change_face": {
            "skill": "change_face",
            "params": {
                "image_path": "{image_path}",
                "face_prompt": "{face_prompt}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path", "face_prompt"],
            "description": "换脸"
        },
        "change_skin_tone": {
            "skill": "change_skin_tone",
            "params": {
                "image_path": "{image_path}",
                "tone": "{tone}",
                "strength": "{strength}"
            },
            "required": ["image_path", "tone"],
            "description": "换肤色"
        },
        "change_body_type": {
            "skill": "change_body_type",
            "params": {
                "image_path": "{image_path}",
                "body_type": "{body_type}",
                "strength": "{strength}"
            },
            "required": ["image_path", "body_type"],
            "description": "换体型"
        },
        "change_age": {
            "skill": "change_age",
            "params": {
                "image_path": "{image_path}",
                "age": "{age}",
                "strength": "{strength}"
            },
            "required": ["image_path", "age"],
            "description": "改变年龄"
        },
        "change_gender": {
            "skill": "change_gender",
            "params": {
                "image_path": "{image_path}",
                "direction": "{direction}",
                "strength": "{strength}"
            },
            "required": ["image_path", "direction"],
            "description": "改变性别"
        },
        "change_nationality": {
            "skill": "change_nationality",
            "params": {
                "image_path": "{image_path}",
                "ethnicity": "{ethnicity}",
                "strength": "{strength}"
            },
            "required": ["image_path", "ethnicity"],
            "description": "改变国籍"
        },
        "change_makeup": {
            "skill": "change_makeup",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path", "style"],
            "description": "改变妆容"
        },

        # ---- 场景/背景编辑 ----
        "change_background": {
            "skill": "change_background",
            "params": {
                "image_path": "{image_path}",
                "preset": "{preset}",
                "strength": "{strength}"
            },
            "required": ["image_path", "preset"],
            "description": "换背景"
        },
        "change_lighting": {
            "skill": "change_lighting",
            "params": {
                "image_path": "{image_path}",
                "lighting": "{lighting}",
                "strength": "{strength}"
            },
            "required": ["image_path", "lighting"],
            "description": "换光照"
        },
        "change_perspective": {
            "skill": "change_perspective",
            "params": {
                "image_path": "{image_path}",
                "perspective": "{perspective}",
                "strength": "{strength}"
            },
            "required": ["image_path", "perspective"],
            "description": "换视角"
        },
        "change_furniture": {
            "skill": "change_furniture",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path", "style"],
            "description": "换家具风格"
        },

        # ---- 添加元素 ----
        "add_glasses": {
            "skill": "add_glasses",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "加眼镜"
        },
        "add_animal_ears": {
            "skill": "add_animal_ears",
            "params": {
                "image_path": "{image_path}",
                "animal": "{animal}",
                "strength": "{strength}"
            },
            "required": ["image_path", "animal"],
            "description": "加兽耳"
        },
        "add_tattoo": {
            "skill": "add_tattoo",
            "params": {
                "image_path": "{image_path}",
                "tattoo": "{tattoo}",
                "strength": "{strength}"
            },
            "required": ["image_path", "tattoo"],
            "description": "加纹身"
        },
        "add_background_objects": {
            "skill": "add_background_objects",
            "params": {
                "image_path": "{image_path}",
                "object": "{object}",
                "strength": "{strength}"
            },
            "required": ["image_path", "object"],
            "description": "加背景物体"
        },

        # ---- 风格转换 ----
        "style_transfer": {
            "skill": "style_transfer",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path", "style"],
            "description": "风格转换"
        },
        "anime_to_real": {
            "skill": "anime_to_real",
            "params": {
                "image_path": "{image_path}",
                "style": "photorealistic",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "动漫转写实"
        },
        "real_to_anime": {
            "skill": "real_to_anime",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "写实转动漫"
        },
        "sketch_to_real": {
            "skill": "sketch_to_real",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "素描转写实"
        },
        "colorize_sketch": {
            "skill": "colorize_sketch",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "线稿上色"
        },

        # ---- 天气/季节/昼夜转换 ----
        "weather_transfer": {
            "skill": "weather_transfer",
            "params": {
                "image_path": "{image_path}",
                "weather": "{weather}",
                "strength": "{strength}"
            },
            "required": ["image_path", "weather"],
            "description": "天气转换"
        },
        "season_transfer": {
            "skill": "season_transfer",
            "params": {
                "image_path": "{image_path}",
                "season": "{season}",
                "strength": "{strength}"
            },
            "required": ["image_path", "season"],
            "description": "季节转换"
        },
        "day_night_transfer": {
            "skill": "day_night_transfer",
            "params": {
                "image_path": "{image_path}",
                "mode": "{mode}",
                "strength": "{strength}"
            },
            "required": ["image_path", "mode"],
            "description": "昼夜转换"
        },

        # ---- 移除/替换 ----
        "remove_clothes": {
            "skill": "remove_clothes",
            "params": {
                "image_path": "{image_path}",
                "prompt": "{prompt}",
                "negative_prompt": "{negative_prompt}",
                "strength": "{strength}",
                "steps": "{steps}",
                "device": "cpu"
            },
            "required": ["image_path"],
            "description": "去衣"
        },
        "remove_object": {
            "skill": "remove_object",
            "params": {
                "image_path": "{image_path}",
                "skip_manual": "{skip_manual}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "移除物体"
        },
        "replace_object": {
            "skill": "replace_object",
            "params": {
                "image_path": "{image_path}",
                "object_prompt": "{object_prompt}",
                "skip_manual": "{skip_manual}",
                "strength": "{strength}"
            },
            "required": ["image_path", "object_prompt"],
            "description": "替换物体"
        },

        # ---- 生成类 ----
        "fantasy_character": {
            "skill": "fantasy_character",
            "params": {
                "image_path": "{image_path}",
                "fantasy_type": "{fantasy_type}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path", "fantasy_type"],
            "description": "幻想角色生成"
        },
        "mecha_generator": {
            "skill": "mecha_generator",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "机甲生成"
        },
        "human_to_robot": {
            "skill": "human_to_robot",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "人转机器人"
        },

        # ---- 扩展 ----
        "expand_to_full_body": {
            "skill": "expand_to_full_body",
            "params": {
                "image_path": "{image_path}",
                "prompt": "{prompt}",
                "controlnet_type": "openpose"
            },
            "required": ["image_path"],
            "description": "扩展为全身图"
        },

        # ---- 修复 ----
        "old_photo_restore": {
            "skill": "old_photo_restore",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"],
            "description": "老照片修复"
        },
    }

    # ==================== 默认配置 ====================
    DEFAULT_CONFIG = {
        "model": "qwen2.5:7b",
        "api_type": "ollama",
        "api_base": "http://localhost:11434",
        "api_key": "",
        "temperature": 0.3,
        "max_history": 10,
        "default_steps": 30,
        "default_cfg": 7.5,
        "default_width": 512,
        "default_height": 768,
        "default_strength": 0.55,
        "enable_context": True,
        "auto_save_context": True
    }

    # ==================== 系统提示词（精简版） ====================
    SYSTEM_PROMPT = """你是一个智能图像生成助手，负责分析用户的自然语言描述，提取图像生成参数。

## 支持的意图类型（共 34 种）
text_to_image, change_clothes, change_clothing_style, change_expression, change_hair,
change_eye_color, change_face, change_skin_tone, change_body_type, change_age,
change_gender, change_nationality, change_makeup, change_background, change_lighting,
change_perspective, change_furniture, add_glasses, add_animal_ears, add_tattoo,
add_background_objects, style_transfer, anime_to_real, real_to_anime, sketch_to_real,
colorize_sketch, weather_transfer, season_transfer, day_night_transfer, remove_clothes,
remove_object, replace_object, fantasy_character, mecha_generator, human_to_robot,
expand_to_full_body, old_photo_restore, chat

## 输出格式
{
    "intent": "意图类型",
    "prompt": "提取/优化的提示词",
    "params": {
        "preset": "背景预设",
        "expression": "表情",
        "hair_color": "发色",
        "style": "风格",
        "animal": "动物",
        "color": "颜色",
        "tone": "肤色",
        "body_type": "体型",
        "age": "年龄",
        "direction": "性别转换方向",
        "ethnicity": "种族",
        "lighting": "光照",
        "perspective": "视角",
        "weather": "天气",
        "season": "季节",
        "mode": "昼夜模式",
        "fantasy_type": "幻想角色类型",
        "tattoo": "纹身图案",
        "object": "背景物体",
        "object_prompt": "替换物体描述",
        "face_prompt": "面部描述",
        "strength": 0.55,
        "width": 512,
        "height": 768,
        "steps": 30,
        "cfg_scale": 7.5
    },
    "confidence": 0.9,
    "reply": "给用户的友好回复"
}

## 关键词映射
- 换衣服/换装/穿裙子/穿裤子 → change_clothes
- 换服装风格/换风格 → change_clothing_style
- 换背景/换个场景 → change_background
- 换表情/笑/开心/难过/惊讶/生气 → change_expression
- 换发型/染发/头发颜色 → change_hair
- 换眼睛颜色/眼睛颜色 → change_eye_color
- 换脸/面部重绘 → change_face
- 换肤色/皮肤颜色 → change_skin_tone
- 换体型/变瘦/变胖/变壮 → change_body_type
- 变年轻/变老/改年龄 → change_age
- 变性/男变女/女变男 → change_gender
- 换国籍/换人种 → change_nationality
- 换妆容/化妆 → change_makeup
- 换光照/换光线 → change_lighting
- 换视角/换角度 → change_perspective
- 换家具风格 → change_furniture
- 加眼镜/戴眼镜 → add_glasses
- 加猫耳/兔耳/兽耳 → add_animal_ears
- 加纹身 → add_tattoo
- 加背景物体/加花/加树 → add_background_objects
- 风格转换/油画/水彩/漫画 → style_transfer
- 动漫转写实/二次元转真人 → anime_to_real
- 写实转动漫 → real_to_anime
- 素描转写实 → sketch_to_real
- 线稿上色 → colorize_sketch
- 换天气/晴天/雨天/雪天 → weather_transfer
- 换季节/春天/夏天/秋天/冬天 → season_transfer
- 昼夜转换/白天转黑夜 → day_night_transfer
- 去衣/脱衣服 → remove_clothes
- 移除物体/去掉 → remove_object
- 替换物体/换成 → replace_object
- 幻想角色/精灵/矮人/兽人 → fantasy_character
- 机甲/机器人 → mecha_generator
- 人转机器人/变机器人 → human_to_robot
- 全身/扩展为全身 → expand_to_full_body
- 修复照片/老照片 → old_photo_restore
- 生成/画/创建 → text_to_image"""

    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "ChatToImage"
        self.version = "1.0.0"

        # 合并默认配置
        self._apply_config()

        # 会话存储
        self._conversations: Dict[str, Dict] = {}
        self._current_conversation_id: Optional[str] = None

        # 技能执行器
        self.executor = None
        if SkillExecutor:
            self.executor = SkillExecutor()

        # 质量检查器（用于 LLM 调用）
        self.quality_checker = CodeQualityChecker() if CodeQualityChecker else None

        # 日志
        self._setup_logging()

        logger.info(f"ChatToImage 初始化完成 (模型: {self.config.get('model')})")

    def _apply_config(self):
        """应用配置默认值"""
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = value

    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # ==================== 配置管理 ====================

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置（供 Executor 使用）"""
        return self.DEFAULT_CONFIG.copy()

    # ==================== LLM 调用 ====================

    def _call_llm(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        调用 LLM
        支持 Ollama 和 OpenAI 兼容 API
        """
        api_type = self.config.get("api_type", "ollama")
        api_base = self.config.get("api_base", "http://localhost:11434")
        model = self.config.get("model", "qwen2.5:7b")
        api_key = self.config.get("api_key", "")
        temperature = self.config.get("temperature", 0.3)

        # 构建请求
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if api_type == "ollama":
                return self._call_ollama(messages, model, api_base, temperature)
            elif api_type == "openai":
                return self._call_openai(messages, model, api_base, api_key, temperature)
            elif api_type == "openai_compatible":
                return self._call_openai_compatible(messages, model, api_base, api_key, temperature)
            else:
                logger.warning(f"未知的 API 类型: {api_type}，回退到 Ollama")
                return self._call_ollama(messages, model, api_base, temperature)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return None

    def _call_ollama(self, messages: List[Dict], model: str, api_base: str, temperature: float) -> Optional[str]:
        """调用 Ollama API"""
        url = f"{api_base}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 256
            }
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    def _call_openai(self, messages: List[Dict], model: str, api_base: str, api_key: str, temperature: float) -> Optional[str]:
        """调用 OpenAI API"""
        url = f"{api_base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _call_openai_compatible(self, messages: List[Dict], model: str, api_base: str, api_key: str, temperature: float) -> Optional[str]:
        """调用 OpenAI 兼容 API（如 vLLM、LocalAI 等）"""
        url = f"{api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # ==================== 意图分析 ====================

    def _analyze_intent(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """
        使用 LLM 分析用户意图
        """
        # 构建上下文信息
        context_str = ""
        if context:
            context_parts = []
            if context.get("last_intent"):
                context_parts.append(f"上次操作: {context['last_intent']}")
            if context.get("last_prompt"):
                context_parts.append(f"上次主题: {context['last_prompt']}")
            if context.get("preferences"):
                prefs = context['preferences']
                if prefs.get("style"):
                    context_parts.append(f"偏好风格: {prefs['style']}")
                if prefs.get("scene"):
                    context_parts.append(f"偏好场景: {prefs['scene']}")
            if context_parts:
                context_str = "上下文: " + ", ".join(context_parts)

        # 构建提示词
        prompt = f"""用户输入: {message}

{context_str}

请分析用户意图，提取参数，输出 JSON。"""

        # 调用 LLM
        response = self._call_llm(prompt, self.SYSTEM_PROMPT)

        if not response:
            # 回退：使用简单规则
            return self._fallback_analyze(message)

        # 解析 JSON
        try:
            # 提取 JSON
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            else:
                # 尝试直接解析
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0)

            result = json.loads(response)

            # 确保必要字段
            if "intent" not in result:
                result["intent"] = "text_to_image"
            if "params" not in result:
                result["params"] = {}
            if "confidence" not in result:
                result["confidence"] = 0.7
            # 如果 prompt 为空，使用原始消息
            if not result.get("prompt"):
                result["prompt"] = message

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 响应: {response[:200]}")
            return self._fallback_analyze(message)

    def _fallback_analyze(self, message: str) -> Dict[str, Any]:
        """
        回退意图分析（基于关键词匹配）- 增强版
        """
        msg_lower = message.lower()

        # 意图判断（按优先级排序）
        intent_map = {
            # 移除/替换
            "remove_object": ["移除物体", "去掉", "删除", "remove"],
            "replace_object": ["替换成", "换成", "replace"],
            "remove_clothes": ["去衣", "脱衣服", "裸体", "nude", "naked", "without clothes"],

            # 生成类
            "fantasy_character": ["精灵", "矮人", "兽人", "妖精", "天使", "恶魔", "fantasy"],
            "mecha_generator": ["机甲", "机器人", "mecha"],
            "human_to_robot": ["变机器人", "人转机器人", "human to robot"],

            # 人物编辑
            "change_clothes": ["换衣服", "换装", "穿裙子", "穿裤子", "换裙子", "换裤子", "换上衣", "换外套"],
            "change_clothing_style": ["换服装风格", "换风格", "穿衣风格"],
            "change_expression": ["换表情", "表情换成", "笑", "开心", "难过", "惊讶", "生气", "害羞"],
            "change_hair": ["换发型", "染发", "头发", "发色", "粉色头发", "金色头发", "蓝色头发"],
            "change_eye_color": ["眼睛颜色", "瞳色", "换眼睛", "眼睛换成"],
            "change_face": ["换脸", "面部", "脸换成", "变脸"],
            "change_skin_tone": ["肤色", "皮肤颜色", "换肤色", "变白", "变黑", "变黄"],
            "change_body_type": ["体型", "变瘦", "变胖", "变壮", "身材", "body type"],
            "change_age": ["变年轻", "变老", "年龄", "年轻", "年老"],
            "change_gender": ["变性", "男变女", "女变男", "变性别", "性转"],
            "change_nationality": ["换国籍", "换人种", "变白人", "变亚洲人", "变黑人"],
            "change_makeup": ["化妆", "妆容", "换妆容"],

            # 场景/背景
            "change_background": ["换背景", "换场景", "背景换成", "场景换成"],
            "change_lighting": ["换光照", "换光线", "光照", "灯光", "打光"],
            "change_perspective": ["换视角", "换角度", "视角", "角度"],
            "change_furniture": ["家具", "家具风格", "换家具"],

            # 添加元素
            "add_glasses": ["加眼镜", "戴眼镜", "眼镜"],
            "add_animal_ears": ["加猫耳", "猫耳", "兔耳", "兽耳", "狐狸耳"],
            "add_tattoo": ["纹身", "加纹身", "刺青"],
            "add_background_objects": ["加花", "加树", "加云", "加鸟", "加蝴蝶", "加背景"],

            # 风格转换
            "style_transfer": ["风格转换", "转成", "油画", "水彩", "漫画", "素描", "水墨"],
            "anime_to_real": ["二次元转写实", "动漫转真人", "卡通转真实", "anime to real"],
            "real_to_anime": ["写实转动漫", "真人转动漫", "real to anime"],
            "sketch_to_real": ["素描转写实", "线稿转真人"],
            "colorize_sketch": ["线稿上色", "给线稿上色", "上色"],

            # 天气/季节/昼夜
            "weather_transfer": ["天气", "晴天", "雨天", "雪天", "多云", "暴风雨", "换天气"],
            "season_transfer": ["季节", "春天", "夏天", "秋天", "冬天", "换季节"],
            "day_night_transfer": ["白天转黑夜", "黑夜转白天", "昼夜", "夜晚", "day night"],

            # 修复
            "old_photo_restore": ["老照片", "修复照片", "修复老照片", "old photo"],

            # 扩展
            "expand_to_full_body": ["全身", "扩展为全身", "full body"],
        }

        intent = "text_to_image"  # 默认

        for int_key, keywords in intent_map.items():
            if any(k in msg_lower for k in keywords):
                intent = int_key
                break

        # 提取参数
        params = {}
        preset = self._extract_preset(message)
        if preset:
            params["preset"] = preset

        expression = self._extract_expression(message)
        if expression:
            params["expression"] = expression

        hair_color = self._extract_hair_color(message)
        if hair_color:
            params["hair_color"] = hair_color

        color = self._extract_color(message)
        if color:
            params["color"] = color

        tone = self._extract_skin_tone(message)
        if tone:
            params["tone"] = tone

        body_type = self._extract_body_type(message)
        if body_type:
            params["body_type"] = body_type

        age = self._extract_age(message)
        if age:
            params["age"] = age

        direction = self._extract_gender_direction(message)
        if direction:
            params["direction"] = direction

        ethnicity = self._extract_ethnicity(message)
        if ethnicity:
            params["ethnicity"] = ethnicity

        lighting = self._extract_lighting(message)
        if lighting:
            params["lighting"] = lighting

        perspective = self._extract_perspective(message)
        if perspective:
            params["perspective"] = perspective

        weather = self._extract_weather(message)
        if weather:
            params["weather"] = weather

        season = self._extract_season(message)
        if season:
            params["season"] = season

        mode = self._extract_daynight_mode(message)
        if mode:
            params["mode"] = mode

        fantasy_type = self._extract_fantasy_type(message)
        if fantasy_type:
            params["fantasy_type"] = fantasy_type

        tattoo = self._extract_tattoo(message)
        if tattoo:
            params["tattoo"] = tattoo

        obj = self._extract_background_object(message)
        if obj:
            params["object"] = obj

        style = self._extract_style_name(message)
        if style:
            params["style"] = style

        # 构建结果
        result = {
            "intent": intent,
            "prompt": message,
            "params": params,
            "confidence": 0.6,
            "reply": f"我理解你想要{self._get_intent_desc(intent)}"
        }

        return result

    def _get_intent_desc(self, intent: str) -> str:
        """获取意图描述"""
        descs = {
            "text_to_image": "生成图片",
            "change_clothes": "换衣服",
            "change_clothing_style": "换服装风格",
            "change_background": "换背景",
            "change_expression": "换表情",
            "change_hair": "换发型/发色",
            "change_eye_color": "换眼睛颜色",
            "change_face": "换脸",
            "change_skin_tone": "换肤色",
            "change_body_type": "换体型",
            "change_age": "改变年龄",
            "change_gender": "改变性别",
            "change_nationality": "改变国籍",
            "change_makeup": "改变妆容",
            "change_lighting": "改变光照",
            "change_perspective": "改变视角",
            "change_furniture": "改变家具风格",
            "add_glasses": "加眼镜",
            "add_animal_ears": "加兽耳",
            "add_tattoo": "加纹身",
            "add_background_objects": "加背景物体",
            "style_transfer": "风格转换",
            "anime_to_real": "二次元转写实",
            "real_to_anime": "写实转动漫",
            "sketch_to_real": "素描转写实",
            "colorize_sketch": "线稿上色",
            "weather_transfer": "天气转换",
            "season_transfer": "季节转换",
            "day_night_transfer": "昼夜转换",
            "remove_clothes": "去衣",
            "remove_object": "移除物体",
            "replace_object": "替换物体",
            "fantasy_character": "幻想角色生成",
            "mecha_generator": "机甲生成",
            "human_to_robot": "人转机器人",
            "expand_to_full_body": "扩展为全身图",
            "old_photo_restore": "老照片修复",
            "chat": "对话"
        }
        return descs.get(intent, "处理")

    # ==================== 参数提取（回退用）- 增强版 ====================

    def _extract_clothes_prompt(self, message: str) -> str:
        """提取换装描述"""
        for word in ["换衣服", "换装", "穿裙子", "穿裤子", "穿上", "换件", "换条", "换身"]:
            message = message.replace(word, "")
        return message.strip() or "换一套新衣服"

    def _extract_preset(self, message: str) -> str:
        """提取背景预设"""
        presets = {
            "海滩": "beach",
            "森林": "forest",
            "城市": "city",
            "樱花": "sakura",
            "日落": "sunset",
            "沙漠": "desert",
            "雪": "snow",
            "星空": "starry_night",
            "花园": "garden",
            "草原": "grassland",
            "雨": "rain",
            "夜景": "night",
            "工作室": "studio",
            "赛博朋克": "cyberpunk"
        }
        for cn, en in presets.items():
            if cn in message:
                return en
        return "beach"

    def _extract_expression(self, message: str) -> str:
        """提取表情"""
        expressions = {
            "笑": "smile",
            "开心": "happy",
            "大笑": "laughing",
            "惊讶": "surprised",
            "难过": "sad",
            "哭泣": "crying",
            "生气": "angry",
            "害羞": "blush",
            "微笑": "smile",
        }
        for cn, en in expressions.items():
            if cn in message:
                return en
        return "smile"

    def _extract_hair_color(self, message: str) -> str:
        """提取发色"""
        colors = {
            "粉色": "pink",
            "金色": "blonde",
            "棕色": "brown",
            "黑色": "black",
            "蓝色": "blue",
            "紫色": "purple",
            "红色": "red",
            "白色": "white",
            "银": "silver",
            "灰": "grey",
            "橙色": "orange",
            "绿色": "green",
            "亚麻": "linen",
        }
        for cn, en in colors.items():
            if cn in message:
                return en
        return ""

    def _extract_color(self, message: str) -> str:
        """提取颜色（用于眼睛颜色等）"""
        colors = {
            "蓝色": "blue",
            "绿色": "green",
            "棕色": "brown",
            "黑色": "black",
            "灰色": "grey",
            "紫色": "purple",
            "红色": "red",
            "金色": "gold",
            "琥珀色": "amber",
            "异色瞳": "heterochromia",
        }
        for cn, en in colors.items():
            if cn in message:
                return en
        return ""

    def _extract_skin_tone(self, message: str) -> str:
        """提取肤色"""
        tones = {
            "白": "light",
            "浅": "light",
            "自然": "natural",
            "小麦": "tan",
            "深": "dark",
            "黑": "dark",
            "古铜": "bronze",
            "橄榄": "olive",
        }
        for cn, en in tones.items():
            if cn in message:
                return en
        return ""

    def _extract_body_type(self, message: str) -> str:
        """提取体型"""
        types = {
            "瘦": "slim",
            "苗条": "slim",
            "纤细": "slim",
            "丰满": "curvy",
            "微胖": "curvy",
            "肌肉": "muscular",
            "壮": "muscular",
            "运动": "athletic",
            "健美": "athletic",
            "胖": "plus_size",
            "大码": "plus_size",
        }
        for cn, en in types.items():
            if cn in message:
                return en
        return ""

    def _extract_age(self, message: str) -> str:
        """提取年龄"""
        ages = {
            "年轻": "young",
            "青年": "young",
            "少年": "young",
            "儿童": "child",
            "小孩": "child",
            "中年": "middle-aged",
            "老年": "old",
            "年老": "old",
            "老者": "old",
        }
        for cn, en in ages.items():
            if cn in message:
                return en
        return ""

    def _extract_gender_direction(self, message: str) -> str:
        """提取性别转换方向"""
        if "男变女" in message or "男生变女生" in message or "男性变女性" in message:
            return "male_to_female"
        if "女变男" in message or "女生变男生" in message or "女性变男性" in message:
            return "female_to_male"
        return ""

    def _extract_ethnicity(self, message: str) -> str:
        """提取种族"""
        ethnicities = {
            "白": "caucasian",
            "欧洲": "caucasian",
            "亚洲": "asian",
            "东亚": "asian",
            "中国": "asian",
            "日本": "asian",
            "韩国": "asian",
            "非洲": "african",
            "黑": "african",
            "拉丁": "hispanic",
            "中东": "middle_eastern",
            "印度": "indian",
        }
        for cn, en in ethnicities.items():
            if cn in message:
                return en
        return ""

    def _extract_lighting(self, message: str) -> str:
        """提取光照"""
        lightings = {
            "黄金时刻": "golden_hour",
            "日落": "golden_hour",
            "黄昏": "golden_hour",
            "夜晚": "night",
            "夜景": "night",
            "工作室": "studio",
            "影棚": "studio",
            "柔和": "soft",
            "软光": "soft",
            "戏剧": "dramatic",
            "强烈": "dramatic",
            "暖": "warm",
            "冷": "cool",
            "自然光": "natural",
        }
        for cn, en in lightings.items():
            if cn in message:
                return en
        return ""

    def _extract_perspective(self, message: str) -> str:
        """提取视角"""
        perspectives = {
            "俯视": "aerial",
            "俯瞰": "aerial",
            "鸟瞰": "bird_eye",
            "低角度": "low_angle",
            "仰视": "low_angle",
            "高角度": "high_angle",
            "俯视": "high_angle",
            "特写": "close_up",
            "近景": "close_up",
            "广角": "wide",
            "虫眼": "worm_eye",
        }
        for cn, en in perspectives.items():
            if cn in message:
                return en
        return ""

    def _extract_weather(self, message: str) -> str:
        """提取天气"""
        weathers = {
            "晴": "sunny",
            "太阳": "sunny",
            "雨": "rainy",
            "下雨": "rainy",
            "雪": "snowy",
            "下雪": "snowy",
            "多云": "cloudy",
            "阴天": "cloudy",
            "雾": "foggy",
            "大雾": "foggy",
            "暴风雨": "stormy",
            "风": "windy",
        }
        for cn, en in weathers.items():
            if cn in message:
                return en
        return ""

    def _extract_season(self, message: str) -> str:
        """提取季节"""
        seasons = {
            "春": "spring",
            "夏天": "summer",
            "夏": "summer",
            "秋": "autumn",
            "冬天": "winter",
            "冬": "winter",
        }
        for cn, en in seasons.items():
            if cn in message:
                return en
        return ""

    def _extract_daynight_mode(self, message: str) -> str:
        """提取昼夜模式"""
        if "白天转黑夜" in message or "白天转夜晚" in message or "日转夜" in message:
            return "day_to_night"
        if "黑夜转白天" in message or "夜晚转白天" in message or "夜转日" in message:
            return "night_to_day"
        return ""

    def _extract_fantasy_type(self, message: str) -> str:
        """提取幻想角色类型"""
        types = {
            "精灵": "elf",
            "暗夜精灵": "dark_elf",
            "高等精灵": "high_elf",
            "矮人": "dwarf",
            "兽人": "orc",
            "妖精": "fairy",
            "天使": "angel",
            "恶魔": "demon",
            "龙裔": "dragonborn",
            "龙人": "dragonborn",
            "半兽人": "half_orc",
            "半精灵": "half_elf",
        }
        for cn, en in types.items():
            if cn in message:
                return en
        return ""

    def _extract_tattoo(self, message: str) -> str:
        """提取纹身图案"""
        tattoos = {
            "龙": "dragon",
            "花": "flower",
            "玫瑰": "rose",
            "星星": "star",
            "部落": "tribal",
            "骷髅": "skull",
            "羽毛": "feather",
            "几何": "geometric",
            "蝴蝶": "butterfly",
            "狼": "wolf",
            "虎": "tiger",
        }
        for cn, en in tattoos.items():
            if cn in message:
                return en
        return ""

    def _extract_background_object(self, message: str) -> str:
        """提取背景物体"""
        objects = {
            "花": "flowers",
            "花朵": "flowers",
            "树": "trees",
            "云": "clouds",
            "鸟": "birds",
            "蝴蝶": "butterflies",
            "星星": "stars",
            "气球": "balloons",
            "灯笼": "lanterns",
            "雨滴": "raindrops",
        }
        for cn, en in objects.items():
            if cn in message:
                return en
        return ""

    def _extract_glasses_style(self, message: str) -> str:
        """提取眼镜风格"""
        styles = {
            "圆": "round",
            "方": "square",
            "猫": "cat_eye",
            "墨镜": "sunglasses",
            "金丝": "gold_rim",
            "飞行员": "aviator",
            "椭圆": "oval",
            "无框": "rimless",
        }
        for cn, en in styles.items():
            if cn in message:
                return en
        return "round"

    def _extract_animal(self, message: str) -> str:
        """提取动物"""
        animals = {
            "猫": "cat",
            "兔": "rabbit",
            "狐狸": "fox",
            "狗": "dog",
            "狼": "wolf",
            "熊": "bear",
            "龙": "dragon",
            "鹿": "deer",
        }
        for cn, en in animals.items():
            if cn in message:
                return en
        return "cat"

    def _extract_style_name(self, message: str) -> str:
        """提取风格名称"""
        styles = {
            "油画": "oil_painting",
            "水彩": "watercolor",
            "漫画": "comic",
            "素描": "sketch",
            "水墨": "ink_wash",
            "赛博朋克": "cyberpunk",
            "暗黑": "dark",
            "写实": "photorealistic",
            "电影": "cinematic",
            "复古": "vintage",
            "蒸汽波": "vaporwave",
        }
        for cn, en in styles.items():
            if cn in message:
                return en
        return ""

    # ==================== 上下文管理 ====================

    def _get_context(self, conversation_id: str = None) -> Dict:
        """获取会话上下文"""
        if conversation_id is None:
            conversation_id = self._current_conversation_id or "default"

        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = {
                "history": [],
                "preferences": {},
                "last_intent": None,
                "last_prompt": None,
                "last_image": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

        return self._conversations[conversation_id]

    def _update_context(self, context: Dict, intent_result: Dict, result: Dict = None):
        """更新上下文"""
        context["last_intent"] = intent_result.get("intent")
        context["last_prompt"] = intent_result.get("prompt")
        context["updated_at"] = datetime.now().isoformat()

        # 更新偏好
        prefs = context["preferences"]
        params = intent_result.get("params", {})
        if params.get("style"):
            prefs["style"] = params["style"]
        if params.get("preset"):
            prefs["scene"] = params["preset"]

        # 记录历史
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": intent_result.get("original_message", ""),
            "intent": intent_result.get("intent"),
            "result": result
        }
        context["history"].append(history_entry)

        # 限制历史长度
        max_history = self.config.get("max_history", 10)
        if len(context["history"]) > max_history:
            context["history"] = context["history"][-max_history:]

        # 保存图片路径
        if result and result.get("image_paths"):
            context["last_image"] = result["image_paths"][0]

    def _get_context_summary(self, context: Dict) -> str:
        """获取上下文摘要"""
        if not context:
            return ""

        parts = []
        if context.get("last_intent"):
            parts.append(f"上次操作: {context['last_intent']}")
        if context.get("last_prompt"):
            parts.append(f"上次主题: {context['last_prompt'][:50]}")

        prefs = context.get("preferences", {})
        if prefs.get("style"):
            parts.append(f"偏好风格: {prefs['style']}")
        if prefs.get("scene"):
            parts.append(f"偏好场景: {prefs['scene']}")

        history_count = len(context.get("history", []))
        if history_count > 0:
            parts.append(f"已对话 {history_count} 轮")

        return ", ".join(parts) if parts else ""

    # ==================== 技能调用 ====================

    def _call_skill(self, skill_name: str, params: Dict) -> Dict:
        """
        调用子技能
        """
        import importlib
        import sys
        from pathlib import Path

        # 确保项目根目录在 sys.path 中
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        try:
            # 动态导入技能模块
            module = importlib.import_module(f"skills.{skill_name}.skill")

            # 查找技能类（排除 SkillSpec）
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr.__module__ == module.__name__ and
                    attr_name not in ['SkillSpec']):
                    skill_class = attr
                    break

            if not skill_class:
                raise ValueError(f"未找到技能类: {skill_name}")

            # 实例化并执行
            skill = skill_class()
            result = skill.execute(**params)

            # 统一返回格式
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    return {"status": "success", "result": result}
                else:
                    return {"status": "error", "error": result.get('error', '未知错误')}
            else:
                return {"status": "success", "result": result}

        except ImportError as e:
            logger.error(f"导入技能 {skill_name} 失败: {e}")
            return {"status": "error", "error": f"导入失败: {e}"}
        except Exception as e:
            logger.error(f"执行技能 {skill_name} 失败: {e}")
            return {"status": "error", "error": str(e)}

    def _prepare_params(self, intent_result: Dict, context: Dict) -> Dict:
        """
        准备调用参数
        """
        intent = intent_result.get("intent")
        params = intent_result.get("params", {})

        # 获取意图映射
        intent_config = self.INTENT_MAP.get(intent)
        if not intent_config:
            return {}

        # 构建参数
        skill_params = {}
        for key, template in intent_config.get("params", {}).items():
            if isinstance(template, str):
                for var_name in re.findall(r'\{(\w+)\}', template):
                    # 优先从 params 获取
                    if var_name in params and params[var_name]:
                        var_value = params[var_name]
                    elif var_name in intent_result and intent_result[var_name]:
                        var_value = intent_result[var_name]
                    elif var_name == "image_path" and context.get("last_image"):
                        var_value = context["last_image"]
                    elif var_name in context.get("preferences", {}):
                        var_value = context["preferences"][var_name]
                    else:
                        var_value = ""

                    if var_value is None:
                        var_value = ""

                    # 处理默认值
                    if var_value == "":
                        if var_name == "strength":
                            var_value = self.config.get("default_strength", 0.55)
                        elif var_name == "width":
                            var_value = self.config.get("default_width", 512)
                        elif var_name == "height":
                            var_value = self.config.get("default_height", 768)
                        elif var_name == "steps":
                            var_value = self.config.get("default_steps", 30)
                        elif var_name == "cfg_scale":
                            var_value = self.config.get("default_cfg", 7.5)
                        elif var_name == "model_name":
                            var_value = ""
                        elif var_name == "seed":
                            var_value = -1
                        elif var_name == "skip_manual":
                            var_value = False
                        elif var_name == "prompt" and intent_result.get("prompt"):
                            var_value = intent_result["prompt"]

                    template = template.replace(f"{{{var_name}}}", str(var_value))

                # 保留 image_path 和 prompt 即使为空
                if template.strip() == "" or template == "{}":
                    if key not in ["image_path", "prompt"]:
                        continue

                skill_params[key] = template
            else:
                skill_params[key] = template

        # 如果有 image_path 参数但为空，尝试从上下文获取
        if "image_path" in skill_params and not skill_params["image_path"]:
            if context.get("last_image"):
                skill_params["image_path"] = context["last_image"]

        # 类型转换
        for key in ["steps", "width", "height", "seed"]:
            if key in skill_params and skill_params[key]:
                try:
                    skill_params[key] = int(skill_params[key])
                except (ValueError, TypeError):
                    pass

        for key in ["cfg_scale", "strength"]:
            if key in skill_params and skill_params[key]:
                try:
                    skill_params[key] = float(skill_params[key])
                except (ValueError, TypeError):
                    pass

        # 布尔值转换
        for key in ["skip_manual", "use_controlnet", "save_mask"]:
            if key in skill_params:
                val = skill_params[key]
                if isinstance(val, str):
                    skill_params[key] = val.lower() in ["true", "1", "yes", "on"]
                elif isinstance(val, (int, float)):
                    skill_params[key] = bool(val)

        return skill_params

    # ==================== 主执行方法 ====================

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行对话式图像生成

        Args:
            message: 用户输入（必填）
            image_path: 输入图片路径（可选）
            model: LLM 模型名称（可选）
            api_type: API 类型（可选）
            api_base: API 地址（可选）
            api_key: API Key（可选）
            conversation_id: 会话 ID（可选）
            stream: 是否流式输出（可选）

        Returns:
            执行结果
        """
        # ========== 1. 获取参数 ==========
        message = kwargs.get("message", "")
        if not message:
            return {
                "status": "error",
                "error": "缺少必要参数: message",
                "skill": self.name
            }

        image_path = kwargs.get("image_path")
        conversation_id = kwargs.get("conversation_id") or "default"
        stream = kwargs.get("stream", False)

        # 覆盖配置
        if kwargs.get("model"):
            self.config["model"] = kwargs["model"]
        if kwargs.get("api_type"):
            self.config["api_type"] = kwargs["api_type"]
        if kwargs.get("api_base"):
            self.config["api_base"] = kwargs["api_base"]
        if kwargs.get("api_key"):
            self.config["api_key"] = kwargs["api_key"]

        # ========== 2. 获取上下文 ==========
        context = self._get_context(conversation_id)
        context_summary = self._get_context_summary(context)

        logger.info(f"执行 ChatToImage: {message[:50]}...")
        logger.debug(f"上下文: {context_summary}")

        # ========== 3. 分析意图 ==========
        intent_result = self._analyze_intent(message, context)
        intent_result["original_message"] = message

        logger.info(f"意图: {intent_result.get('intent')}, 置信度: {intent_result.get('confidence', 0)}")

        # ========== 4. 处理对话 ==========
        intent = intent_result.get("intent")

        if intent == "chat":
            # 纯对话
            reply = intent_result.get("reply", f"收到你的消息: {message}")
            self._update_context(context, intent_result)
            return {
                "status": "success",
                "response": reply,
                "intent": "chat",
                "conversation_id": conversation_id,
                "context_summary": self._get_context_summary(context)
            }

        # ========== 5. 获取意图映射 ==========
        intent_config = self.INTENT_MAP.get(intent)
        if not intent_config:
            return {
                "status": "error",
                "error": f"不支持的意图类型: {intent}",
                "skill": self.name
            }

        # ========== 6. 准备参数 ==========
        # 如果有图片参数，优先使用传入的
        if image_path:
            context["last_image"] = image_path

        skill_params = self._prepare_params(intent_result, context)

        # 检查必要参数
        required = intent_config.get("required", [])
        missing = []
        for req in required:
            if req not in skill_params or not skill_params[req]:
                missing.append(req)

        if missing:
            return {
                "status": "error",
                "error": f"缺少必要参数: {', '.join(missing)}",
                "skill": self.name,
                "params": skill_params
            }

        # ========== 7. 调用子技能 ==========
        skill_name = intent_config.get("skill")
        logger.info(f"调用技能: {skill_name}, 参数: {skill_params}")

        # 如果有 image_path 但技能参数中没有，尝试添加
        if "image_path" in skill_params and not skill_params["image_path"]:
            if context.get("last_image"):
                skill_params["image_path"] = context["last_image"]

        try:
            result = self._call_skill(skill_name, skill_params)

            # 处理结果
            image_paths = []
            if result.get("status") == "success":
                # 提取图片路径
                if result.get("result"):
                    if isinstance(result["result"], dict):
                        if "image_paths" in result["result"]:
                            image_paths = result["result"]["image_paths"]
                        elif "image_path" in result["result"]:
                            image_paths = [result["result"]["image_path"]]
                        elif "output_path" in result["result"]:
                            image_paths = [result["result"]["output_path"]]
                    elif isinstance(result["result"], list):
                        image_paths = result["result"]
                    elif isinstance(result["result"], str):
                        image_paths = [result["result"]]
            elif result.get("status") == "error":
                return {
                    "status": "error",
                    "error": result.get("error", "子技能执行失败"),
                    "skill": self.name,
                    "skill_used": skill_name
                }

            # ========== 8. 更新上下文 ==========
            execution_result = {
                "image_paths": image_paths,
                "skill_used": skill_name,
                "params": skill_params
            }
            self._update_context(context, intent_result, execution_result)

            # ========== 9. 返回结果 ==========
            reply = intent_result.get("reply", f"✅ 已{self._get_intent_desc(intent)}完成！")
            if image_paths:
                reply += f"\n📁 生成图片: {', '.join(image_paths)}"

            return {
                "status": "success",
                "response": reply,
                "image_paths": image_paths,
                "intent": intent,
                "skill_used": skill_name,
                "params": skill_params,
                "conversation_id": conversation_id,
                "context_summary": self._get_context_summary(context)
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "skill_used": skill_name
            }

    # ==================== 辅助方法 ====================

    def list_conversations(self) -> List[str]:
        """列出所有会话"""
        return list(self._conversations.keys())

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """获取会话详情"""
        return self._conversations.get(conversation_id)

    def clear_conversation(self, conversation_id: str = None):
        """清除会话"""
        if conversation_id is None:
            conversation_id = self._current_conversation_id or "default"
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"已清除会话: {conversation_id}")

    def clear_all_conversations(self):
        """清除所有会话"""
        self._conversations.clear()
        logger.info("已清除所有会话")

    def __repr__(self):
        return f"<Chattoimage(version={self.version}, model={self.config.get('model')})>"


# ==================== 直接运行入口 ====================

def main():
    """
    直接运行技能的命令行入口
    用法: python skills/chattoimage/skill.py --message "帮我换衣服" --image_path input.jpg
    """
    parser = argparse.ArgumentParser(
        description="ChatToImage - 对话式图像生成技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用 - 文生图
  python skills/chattoimage/skill.py --message "生成一个美丽的女孩"

  # 换衣服（需要图片）
  python skills/chattoimage/skill.py --message "把她的衣服换成红色裙子" --image_path input/girl.jpg

  # 换背景
  python skills/chattoimage/skill.py --message "把背景换成海滩" --image_path input/girl.jpg

  # 加猫耳
  python skills/chattoimage/skill.py --message "加猫耳" --image_path input/girl.jpg

  # 风格转换
  python skills/chattoimage/skill.py --message "转成油画风格" --image_path input/girl.jpg

  # 指定 LLM 模型
  python skills/chattoimage/skill.py --message "生成一个美丽的女孩" --model qwen2.5:14b

  # 交互式对话模式
  python skills/chattoimage/skill.py --interactive

  # 列出所有支持的意图
  python skills/chattoimage/skill.py --list-intents
        """
    )

    parser.add_argument(
        "--message", "-m",
        type=str,
        help="用户输入的自然语言描述"
    )
    parser.add_argument(
        "--image_path", "-i",
        type=str,
        help="输入图片路径（用于图生图操作）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM 模型名称 (默认: qwen2.5:7b)"
    )
    parser.add_argument(
        "--api_type",
        type=str,
        choices=["ollama", "openai", "openai_compatible"],
        default="ollama",
        help="API 类型 (默认: ollama)"
    )
    parser.add_argument(
        "--api_base",
        type=str,
        default="http://localhost:11434",
        help="API 地址 (默认: http://localhost:11434)"
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default="",
        help="API Key（OpenAI 等需要）"
    )
    parser.add_argument(
        "--conversation_id", "-c",
        type=str,
        default="default",
        help="会话 ID（用于多轮对话）"
    )
    parser.add_argument(
        "--interactive", "-I",
        action="store_true",
        help="交互式对话模式"
    )
    parser.add_argument(
        "--list-intents", "-l",
        action="store_true",
        help="列出所有支持的意图"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出结果到文件 (JSON格式)"
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # 列出所有意图
    if args.list_intents:
        print("\n" + "=" * 60)
        print("📋 ChatToImage 支持的意图列表")
        print("=" * 60)
        print(f"{'意图类型':<25} {'描述':<20} {'必需参数':<20}")
        print("-" * 60)
        for intent, config in Chattoimage.INTENT_MAP.items():
            required = ", ".join(config.get("required", []))
            desc = config.get("description", "")
            print(f"{intent:<25} {desc:<20} {required:<20}")
        print("=" * 60)
        print(f"共 {len(Chattoimage.INTENT_MAP)} 种意图")
        return

    # 交互式模式
    if args.interactive:
        print("\n" + "=" * 60)
        print("💬 ChatToImage 交互式对话模式")
        print("=" * 60)
        print("输入 'exit' 或 'quit' 退出")
        print("输入 'clear' 清除当前会话")
        print("输入 'list' 查看所有意图")
        print("-" * 60)

        skill = Chattoimage(config={
            "model": args.model or "qwen2.5:7b",
            "api_type": args.api_type,
            "api_base": args.api_base,
            "api_key": args.api_key
        })

        conversation_id = args.conversation_id
        current_image = args.image_path

        while True:
            try:
                user_input = input("\n📝 你: ").strip()
                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    print("👋 再见！")
                    break

                if user_input.lower() == "clear":
                    skill.clear_conversation(conversation_id)
                    print("🗑️ 会话已清除")
                    continue

                if user_input.lower() == "list":
                    print("\n支持的意图:")
                    for intent, config in Chattoimage.INTENT_MAP.items():
                        print(f"  - {intent}: {config.get('description', '')}")
                    continue

                # 执行
                result = skill.execute(
                    message=user_input,
                    image_path=current_image,
                    conversation_id=conversation_id
                )

                if result.get("status") == "success":
                    print(f"\n🤖 AI: {result.get('response', '')}")
                    if result.get("image_paths"):
                        print(f"📁 图片: {', '.join(result['image_paths'])}")
                    print(f"📊 意图: {result.get('intent')} | 技能: {result.get('skill_used')}")
                else:
                    print(f"\n❌ 错误: {result.get('error', '未知错误')}")

            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 异常: {e}")

        return

    # 单次执行模式
    if not args.message:
        print("❌ 请指定 --message 参数，或使用 --interactive 进入交互模式")
        print("   使用 --help 查看帮助")
        sys.exit(1)

    skill = Chattoimage(config={
        "model": args.model or "qwen2.5:7b",
        "api_type": args.api_type,
        "api_base": args.api_base,
        "api_key": args.api_key
    })

    result = skill.execute(
        message=args.message,
        image_path=args.image_path,
        conversation_id=args.conversation_id
    )

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到: {args.output}")

    if result.get("status") == "success":
        print(f"\n✅ {result.get('response', '')}")
        if result.get("image_paths"):
            print(f"📁 图片: {', '.join(result['image_paths'])}")
        if args.verbose:
            print(f"\n📊 详情:")
            print(f"   意图: {result.get('intent')}")
            print(f"   技能: {result.get('skill_used')}")
            print(f"   参数: {json.dumps(result.get('params', {}), ensure_ascii=False, indent=2)}")
    else:
        print(f"\n❌ 错误: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()