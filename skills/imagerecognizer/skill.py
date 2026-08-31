"""
ImageRecognizer - 使用 Ollama 多模态模型识别图片内容，支持多语言翻译

输入参数:
  - image_path (string): 图片文件路径（支持 jpg/png/webp/gif/bmp）
  - language (string): 输出语言代码（zh/en/ja/ko/fr/de/es/it/pt/ru/ar/th/vi/id/hi）
  - detail_level (string): 详细程度（brief/standard/detailed/tags/json）
  - translate_to (string): 翻译目标语言代码
  - save_result (boolean): 是否保存结果到文件

输出:
  - recognition: 图片识别结果文本
  - translated_result: 翻译后的结果（如果指定了 translate_to）
  - saved_to: 结果文件保存路径
  - image_name: 图片文件名
  - executed_at: 执行时间
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Imagerecognizer:
    """
    基于 Ollama 多模态模型的图片识别与翻译技能
    """

    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "fr": "Français",
        "de": "Deutsch",
        "es": "Español",
        "it": "Italiano",
        "pt": "Português",
        "ru": "Русский",
        "ar": "العربية",
        "th": "ภาษาไทย",
        "vi": "Tiếng Việt",
        "id": "Bahasa Indonesia",
        "hi": "हिन्दी",
    }

    # 支持的语言列表（用于翻译）
    TRANSLATION_LANGUAGES = {
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "fr": "Français",
        "de": "Deutsch",
        "es": "Español",
        "it": "Italiano",
        "pt": "Português",
        "ru": "Русский",
        "ar": "العربية",
        "th": "ภาษาไทย",
        "vi": "Tiếng Việt",
        "id": "Bahasa Indonesia",
        "hi": "हिन्दी",
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "ImageRecognizer"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()

        # Ollama 配置
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.model = self.config.get("model", "qwen3-vl:2b")
        self.translate_model = self.config.get("translate_model", "qwen2.5:1.5b")
        self.default_lang = self.config.get("default_language", "zh")
        self.output_dir = Path(self.config.get("output_dir", "./skills/imagerecognizer/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ImageRecognizer 初始化完成，模型: {self.model}")
        logger.info(f"🔄 翻译模型: {self.translate_model}")

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
            "ollama_url": "http://localhost:11434",
            "model": "qwen3-vl:2b",
            "translate_model": "qwen2.5:1.5b",
            "default_language": "zh",
            "output_dir": "./skills/imagerecognizer/output",
            "max_tokens": 2048,
            "temperature": 0.3,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required_params = ["image_path"]
        for param in required_params:
            if param not in kwargs or kwargs[param] is None or kwargs[param] == "":
                raise ValueError(f"缺少必需参数: {param}")

        # 验证图片路径
        image_path = Path(kwargs["image_path"])
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        # 验证图片格式
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
        if image_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"不支持的图片格式: {image_path.suffix}，支持: {', '.join(valid_extensions)}")

        # 验证语言代码
        language = kwargs.get("language", self.default_lang)
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的语言代码: {language}，支持: {', '.join(self.SUPPORTED_LANGUAGES.keys())}")

        # 验证详细程度
        detail_level = kwargs.get("detail_level", "standard")
        valid_levels = ["brief", "standard", "detailed", "tags", "json"]
        if detail_level not in valid_levels:
            raise ValueError(f"不支持的详细程度: {detail_level}，支持: {', '.join(valid_levels)}")

        # 验证翻译目标语言（如果指定）
        translate_to = kwargs.get("translate_to")
        if translate_to and translate_to not in self.TRANSLATION_LANGUAGES:
            raise ValueError(f"不支持的翻译目标语言: {translate_to}，支持: {', '.join(self.TRANSLATION_LANGUAGES.keys())}")

        return True

    def _encode_image(self, image_path: Path) -> str:
        """将图片编码为 Base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_ollama(self, prompt: str, image_base64: str) -> str:
        """调用 Ollama 多模态模型"""
        import requests

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": self.config.get("temperature", 0.3),
                "num_predict": self.config.get("max_tokens", 2048),
            }
        }

        try:
            logger.info(f"📤 调用模型: {self.model}")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "").strip()
            logger.info(f"📥 识别结果长度: {len(result)} 字符")
            return result
        except requests.exceptions.Timeout:
            logger.error("Ollama 请求超时")
            return "错误: 请求超时，请检查 Ollama 服务是否正常运行"
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到 Ollama")
            return "错误: 无法连接到 Ollama，请确保 Ollama 服务已启动 (ollama serve)"
        except Exception as e:
            logger.error(f"Ollama 请求失败: {e}")
            return f"错误: {e}"

    def _build_prompt(self, lang: str, detail: str = "standard") -> str:
        """构建识别提示词"""
        lang_name = self.SUPPORTED_LANGUAGES.get(lang, "中文")

        detail_instructions = {
            "brief": "请用简洁的语言描述这张图片的主要内容（50字以内）。",
            "standard": "请详细描述这张图片的内容，包括主要物体、场景、颜色、人物表情/动作、文字信息等。",
            "detailed": "请非常详细地分析这张图片，包括构图、光影、色彩搭配、物体位置关系、人物服装/表情/动作细节、背景环境、可能的艺术风格等。",
            "tags": "请为这张图片生成 5-10 个标签（关键词），用逗号分隔。",
            "json": '请以 JSON 格式输出识别结果，包含以下字段：objects(物体列表)、scene(场景描述)、colors(主要颜色)、text(图片中的文字)、mood(氛围/情绪)。',
        }

        instruction = detail_instructions.get(detail, detail_instructions["standard"])

        prompt = f"""你是一个专业的图片识别助手。请分析这张图片，{instruction}

输出语言请使用：{lang_name}

请确保描述准确、客观、详细。"""

        return prompt

    def _translate_text(self, text: str, target_lang: str) -> str:
        """使用 Ollama 翻译文本"""
        if target_lang not in self.TRANSLATION_LANGUAGES:
            return text

        import requests

        lang_name = self.TRANSLATION_LANGUAGES[target_lang]
        prompt = f"""请将以下内容翻译成 {lang_name}，只输出翻译结果，不要添加任何额外说明：

{text}"""

        try:
            logger.info(f"📤 翻译模型: {self.translate_model}")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.translate_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 4096,
                    }
                },
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return text

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能

        Args:
            image_path: 图片路径 (必填)
            language: 输出语言 (默认: zh)
            detail_level: 详细程度 (默认: standard)
            translate_to: 翻译目标语言 (可选)
            save_result: 是否保存结果 (默认: True)
            model: Ollama 模型 (可选)

        Returns:
            执行结果
        """
        start_time = datetime.now()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            self._validate_inputs(**kwargs)

            image_path = Path(kwargs["image_path"])
            language = kwargs.get("language", self.default_lang)
            detail_level = kwargs.get("detail_level", "standard")
            translate_to = kwargs.get("translate_to")
            save_result = kwargs.get("save_result", True)

            # 处理布尔值
            if isinstance(save_result, str):
                save_result = save_result.lower() in ["true", "1", "yes", "on"]

            # 从 kwargs 读取 model 参数
            if "model" in kwargs and kwargs["model"]:
                self.model = kwargs["model"]
                logger.info(f"🔄 使用指定的模型: {self.model}")

            logger.info(f"📷 识别图片: {image_path}")
            logger.info(f"🌐 输出语言: {language}")
            logger.info(f"📊 详细程度: {detail_level}")
            if translate_to:
                logger.info(f"🔄 翻译到: {translate_to}")

            # 编码图片
            image_base64 = self._encode_image(image_path)

            # 构建提示词
            prompt = self._build_prompt(language, detail_level)

            # 调用 Ollama 识别
            logger.info("⏳ 正在识别图片...")
            recognition_result = self._call_ollama(prompt, image_base64)

            # 翻译（如果需要）
            translated_result = None
            if translate_to and translate_to != language:
                logger.info(f"⏳ 正在翻译到 {translate_to}...")
                translated_result = self._translate_text(recognition_result, translate_to)

            # 构建结果
            result_data = {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "language": language,
                "detail_level": detail_level,
                "recognition": recognition_result,
                "translated_to": translate_to,
                "translated_result": translated_result,
                "executed_at": datetime.now().isoformat(),
            }

            # 保存结果
            saved_files = []
            if save_result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"recognition_{image_path.stem}_{timestamp}"

                # 保存 JSON
                json_file = self.output_dir / f"{base_name}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "status": "success",
                        "result": result_data,
                        "metadata": {
                            "skill": self.name,
                            "version": self.version,
                            "model": self.model,
                            "translate_model": self.translate_model,
                            "executed_at": datetime.now().isoformat()
                        }
                    }, f, ensure_ascii=False, indent=2)
                saved_files.append(str(json_file))

                # 保存 TXT
                txt_file = self.output_dir / f"{base_name}.txt"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 70 + "\n")
                    f.write("  📷 图片识别结果\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(f"📁 图片: {image_path.name}\n")
                    f.write(f"🤖 识别模型: {self.model}\n")
                    f.write(f"🔄 翻译模型: {self.translate_model}\n")
                    f.write(f"🌐 语言: {self.SUPPORTED_LANGUAGES.get(language, language)}\n")
                    f.write(f"📊 详细程度: {detail_level}\n")
                    f.write(f"🕐 识别时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("-" * 70 + "\n")
                    f.write("📝 识别结果:\n")
                    f.write("-" * 70 + "\n\n")
                    f.write(recognition_result + "\n\n")
                    if translated_result:
                        f.write("-" * 70 + "\n")
                        f.write(f"🌍 翻译 ({self.TRANSLATION_LANGUAGES.get(translate_to, translate_to)}):\n")
                        f.write("-" * 70 + "\n\n")
                        f.write(translated_result + "\n")
                    f.write("\n" + "=" * 70 + "\n")
                saved_files.append(str(txt_file))

                result_data["saved_to"] = saved_files
                logger.info(f"💾 结果已保存到: {', '.join(saved_files)}")

            result = {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "model": self.model,
                    "translate_model": self.translate_model,
                    "executed_at": datetime.now().isoformat()
                }
            }

            logger.info(f"✅ 识别完成")
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
        return f"<Imagerecognizer(name={self.name}, version={self.version}, model={self.model}, translate_model={self.translate_model})>"