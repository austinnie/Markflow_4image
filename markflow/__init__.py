"""
MarkFlow - 从Markdown到可执行技能的工作流引擎
"""
import warnings
warnings.filterwarnings("ignore", message=".*torchvision.*")
warnings.filterwarnings("ignore", message=".*CLIPImageProcessor.*")
warnings.filterwarnings("ignore", message=".*SiglipImageProcessor.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")

__version__ = "0.1.0"
__author__ = "MarkFlow Team"

from .core.parser import MarkdownParser, SkillSpec
from .core.generator import CodeGenerator
from .core.registry import SkillRegistry
from .core.executor import SkillExecutor
from .templates.base import TemplateManager

__all__ = [
    "MarkdownParser",
    "SkillSpec",
    "CodeGenerator",
    "SkillRegistry",
    "SkillExecutor",
    "TemplateManager"
]