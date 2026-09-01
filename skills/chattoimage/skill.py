"""
ChatToImage - 对话式图像生成技能
通过自然语言对话生成和编辑图片
"""

import os
import re
import json
import logging
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import deque

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

    # ==================== 意图映射 ====================
    INTENT_MAP = {
        # 文生图
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
            "required": ["prompt"]
        },
        # 换装
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
            "required": ["image_path", "prompt"]
        },
        # 换背景
        "change_background": {
            "skill": "change_background",
            "params": {
                "image_path": "{image_path}",
                "preset": "{preset}",
                "strength": "{strength}"
            },
            "required": ["image_path", "preset"]
        },
        # 换表情
        "change_expression": {
            "skill": "change_expression",
            "params": {
                "image_path": "{image_path}",
                "expression": "{expression}",
                "strength": "{strength}"
            },
            "required": ["image_path", "expression"]
        },
        # 换发型/发色
        "change_hair": {
            "skill": "change_hair",
            "params": {
                "image_path": "{image_path}",
                "hair_color": "{hair_color}",
                "prompt": "{prompt}",
                "strength": "{strength}"
            },
            "required": ["image_path"]
        },
        # 加眼镜
        "add_glasses": {
            "skill": "add_glasses",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path"]
        },
        # 加兽耳
        "add_animal_ears": {
            "skill": "add_animal_ears",
            "params": {
                "image_path": "{image_path}",
                "animal": "{animal}",
                "strength": "{strength}"
            },
            "required": ["image_path", "animal"]
        },
        # 风格转换
        "style_transfer": {
            "skill": "style_transfer",
            "params": {
                "image_path": "{image_path}",
                "style": "{style}",
                "strength": "{strength}"
            },
            "required": ["image_path", "style"]
        },
        # 二次元转写实
        "anime_to_real": {
            "skill": "anime_to_real",
            "params": {
                "image_path": "{image_path}",
                "style": "photorealistic",
                "strength": "{strength}"
            },
            "required": ["image_path"]
        },
        # 全身扩展
        "expand_to_full_body": {
            "skill": "expand_to_full_body",
            "params": {
                "image_path": "{image_path}",
                "prompt": "{prompt}",
                "controlnet_type": "openpose"
            },
            "required": ["image_path"]
        }
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

    # ==================== 系统提示词 ====================
    SYSTEM_PROMPT = """你是一个智能图像生成助手，负责分析用户的自然语言描述，提取图像生成参数。

你需要判断用户的意图并提取关键信息：

## 支持的意图类型
1. text_to_image - 文生图：用户想要生成一张全新的图片
2. change_clothes - 换装：用户想给图片中的人物换衣服
3. change_background - 换背景：用户想换图片背景
4. change_expression - 换表情：用户想改人物表情
5. change_hair - 换发型/发色：用户想改发型或发色
6. add_glasses - 加眼镜：用户想给人物加眼镜
7. add_animal_ears - 加兽耳：用户想加动物耳朵
8. style_transfer - 风格转换：用户想改变图片风格
9. anime_to_real - 二次元转写实
10. expand_to_full_body - 扩展为全身图
11. chat - 普通对话

## 输出格式
请输出 JSON 格式：
{
    "intent": "意图类型",
    "prompt": "提取/优化的提示词",
    "params": {
        "preset": "背景预设名（change_background需要）",
        "expression": "表情（change_expression需要）",
        "hair_color": "发色（change_hair需要）",
        "style": "风格（style_transfer/add_glasses需要）",
        "animal": "动物（add_animal_ears需要）",
        "strength": 0.55,
        "width": 512,
        "height": 768,
        "steps": 30,
        "cfg_scale": 7.5
    },
    "confidence": 0.9,
    "reply": "给用户的友好回复"
}

## 注意事项
- 如果用户没有明确指定意图，根据上下文推断
- 提取主体、场景、风格、颜色等关键信息
- prompt 应该是完整的英文描述
- 对中文输入，输出时转换为英文提示词
- 如果是对话，设置 intent 为 "chat"
- 如果用户说"换衣服"、"换装"、"穿裙子"等，判断为 change_clothes
- 如果用户说"换背景"、"换个场景"等，判断为 change_background
- 如果用户说"换表情"、"开心点"、"笑"等，判断为 change_expression
- 如果用户说"换发型"、"染发"、"粉色头发"等，判断为 change_hair
- 如果用户说"加眼镜"、"戴眼镜"等，判断为 add_glasses
- 如果用户说"加猫耳"、"加兔耳"等，判断为 add_animal_ears
- 如果用户说"转油画"、"水彩风格"等，判断为 style_transfer
- 如果用户说"二次元转写实"等，判断为 anime_to_real"""

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
        回退意图分析（基于关键词匹配）
        """
        msg_lower = message.lower()

        # 意图判断
        if any(k in msg_lower for k in ["换衣服", "换装", "穿裙子", "换裙子", "换裤子", "换上衣", "换外套"]):
            intent = "change_clothes"
            prompt = self._extract_clothes_prompt(message)
        elif any(k in msg_lower for k in ["换背景", "换场景", "背景换成", "场景换成"]):
            intent = "change_background"
            preset = self._extract_preset(message)
        elif any(k in msg_lower for k in ["换表情", "表情换成", "笑", "开心", "难过", "惊讶", "生气"]):
            intent = "change_expression"
            expression = self._extract_expression(message)
        elif any(k in msg_lower for k in ["换发型", "染发", "头发", "发色", "粉色头发", "金色头发"]):
            intent = "change_hair"
            hair_color = self._extract_hair_color(message)
        elif any(k in msg_lower for k in ["加眼镜", "戴眼镜", "眼镜"]):
            intent = "add_glasses"
            style = self._extract_glasses_style(message)
        elif any(k in msg_lower for k in ["加猫耳", "猫耳", "兔耳", "兽耳"]):
            intent = "add_animal_ears"
            animal = self._extract_animal(message)
        elif any(k in msg_lower for k in ["风格转换", "转成", "油画", "水彩", "漫画"]):
            intent = "style_transfer"
            style = self._extract_style_name(message)
        elif any(k in msg_lower for k in ["二次元转写实", "动漫转真人", "卡通转真实"]):
            intent = "anime_to_real"
        elif any(k in msg_lower for k in ["全身", "扩展为全身"]):
            intent = "expand_to_full_body"
        elif any(k in msg_lower for k in ["生成", "画", "创建", "create"]):
            intent = "text_to_image"
        else:
            intent = "chat"

        # 构建结果
        result = {
            "intent": intent,
            "prompt": message,
            "params": {},
            "confidence": 0.6,
            "reply": f"我理解你想要{self._get_intent_desc(intent)}"
        }

        # 填充参数
        if intent == "change_background" and preset:
            result["params"]["preset"] = preset
        elif intent == "change_expression" and expression:
            result["params"]["expression"] = expression
        elif intent == "change_hair" and hair_color:
            result["params"]["hair_color"] = hair_color
        elif intent == "add_glasses" and style:
            result["params"]["style"] = style
        elif intent == "add_animal_ears" and animal:
            result["params"]["animal"] = animal
        elif intent == "style_transfer" and style:
            result["params"]["style"] = style

        return result

    def _get_intent_desc(self, intent: str) -> str:
        """获取意图描述"""
        descs = {
            "text_to_image": "生成图片",
            "change_clothes": "换衣服",
            "change_background": "换背景",
            "change_expression": "换表情",
            "change_hair": "换发型/发色",
            "add_glasses": "加眼镜",
            "add_animal_ears": "加兽耳",
            "style_transfer": "风格转换",
            "anime_to_real": "二次元转写实",
            "expand_to_full_body": "扩展为全身图",
            "chat": "对话"
        }
        return descs.get(intent, "处理")

    # ==================== 参数提取（回退用） ====================

    def _extract_clothes_prompt(self, message: str) -> str:
        """提取换装描述"""
        for word in ["换衣服", "换装", "穿裙子", "穿裤子", "穿上", "换件"]:
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
            "草原": "grassland"
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
            "害羞": "blush"
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
            "灰": "grey"
        }
        for cn, en in colors.items():
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
            "金丝": "gold_rim"
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
            "熊": "bear"
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
            "暗黑": "dark"
        }
        for cn, en in styles.items():
            if cn in message:
                return en
        return "oil_painting"

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
        调用子技能 - 模仿 execute_skill 的方式
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
        
    def _call_skill_direct(self, skill_name: str, params: Dict) -> Dict:
        """
        直接调用技能（不通过 Executor）
        """
        try:
            # 动态导入技能模块
            module_path = f"skills.{skill_name}.skill"
            module = __import__(module_path, fromlist=[""])

            # 查找模块中所有类，找到匹配的类
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr.__module__ == module.__name__ and
                    attr_name != 'SkillSpec'):
                    skill_class = attr
                    break

            if not skill_class:
                raise ValueError(f"未找到技能类: {skill_name}")

            skill = skill_class()
            result = skill.execute(**params)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"直接调用 {skill_name} 失败: {e}")
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

        # ✅ 在返回前转换类型
        for key in ["steps", "width", "height", "seed"]:
            if key in skill_params and skill_params[key]:
                try:
                    skill_params[key] = int(skill_params[key])
                except:
                    pass
        
        if "cfg_scale" in skill_params and skill_params["cfg_scale"]:
            try:
                skill_params["cfg_scale"] = float(skill_params["cfg_scale"])
            except:
                pass
        
        if "strength" in skill_params and skill_params["strength"]:
            try:
                skill_params["strength"] = float(skill_params["strength"])
            except:
                pass

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