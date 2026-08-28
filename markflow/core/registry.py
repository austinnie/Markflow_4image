"""
技能注册中心 - 管理和注册技能
"""

from typing import Dict, Type, Any, Optional, List
from pathlib import Path
import importlib
import importlib.util
import json
import logging

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self, storage_dir: Path = None):
        self._skills: Dict[str, Type] = {}
        self._metadata: Dict[str, Dict] = {}
        self._instances: Dict[str, Any] = {}
        self.storage_dir = storage_dir or Path("./skills")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def register(self, skill_class: Type, metadata: Dict = None) -> None:
        """注册技能"""
        name = skill_class.__name__
        self._skills[name] = skill_class
        
        if metadata:
            self._metadata[name] = metadata
        elif hasattr(skill_class, '__metadata__'):
            self._metadata[name] = skill_class.__metadata__
        else:
            self._metadata[name] = {
                "name": name,
                "description": skill_class.__doc__ or f"{name} skill",
                "inputs": []
            }
        
        logger.info(f"注册技能: {name}")
    
    def unregister(self, name: str) -> bool:
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            if name in self._metadata:
                del self._metadata[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"注销技能: {name}")
            return True
        return False
    
    def get(self, name: str) -> Type:
        """获取技能类"""
        if name not in self._skills:
            raise KeyError(f"技能未注册: {name}")
        return self._skills[name]
    
    def create_instance(self, name: str, config: Dict = None) -> Any:
        """创建技能实例"""
        skill_class = self.get(name)
        instance = skill_class(config or {})
        self._instances[name] = instance
        return instance
    
    def get_instance(self, name: str, config: Dict = None) -> Any:
        """获取或创建技能实例"""
        if name in self._instances:
            return self._instances[name]
        return self.create_instance(name, config)
    
    def list(self) -> Dict[str, Dict]:
        """列出所有已注册的技能（返回完整元数据）"""
        return {
            name: self._metadata.get(name, {})
            for name in self._skills.keys()
        }
    
    def has(self, name: str) -> bool:
        """检查技能是否已注册"""
        return name in self._skills
    
    def load_from_file(self, file_path: Path) -> Optional[Type]:
        """从文件加载技能"""
        module_name = file_path.stem
        if module_name in self._skills:
            self.unregister(module_name)
        
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr.__module__ == module.__name__ and
                    attr_name != 'SkillSpec'):
                    if hasattr(attr, 'execute') and callable(getattr(attr, 'execute')):
                        # 从 meta.json 加载元数据
                        meta_file = file_path.parent / "meta.json"
                        metadata = {}
                        if meta_file.exists():
                            try:
                                with open(meta_file, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                if 'inputs' not in metadata:
                                    metadata['inputs'] = []
                                print(f"   📄 加载 meta: {file_path.parent.name} - inputs: {len(metadata.get('inputs', []))} 个")
                            except Exception as e:
                                print(f"   ⚠️ 读取 meta.json 失败: {e}")
                        
                        self.register(attr, metadata)
                        return attr
            
            logger.warning(f"未找到技能类: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"加载技能失败 {file_path}: {e}")
            return None
    
    def load_from_directory(self, directory: Path) -> List[Type]:
        """从目录加载所有技能（支持子目录）"""
        loaded = []
        
        # 扫描子目录中的 skill.py
        for subdir in directory.iterdir():
            if subdir.is_dir():
                skill_file = subdir / "skill.py"
                meta_file = subdir / "meta.json"
                if skill_file.exists() and meta_file.exists():
                    skill_class = self.load_from_file(skill_file)
                    if skill_class:
                        loaded.append(skill_class)
                elif skill_file.exists() and not meta_file.exists():
                    print(f"⚠️ 跳过 {subdir.name}：缺少 meta.json")
        
        # 兼容旧的扁平结构
        for py_file in directory.glob("*.py"):
            if not py_file.name.startswith("_"):
                skill_class = self.load_from_file(py_file)
                if skill_class:
                    loaded.append(skill_class)
        
        return loaded
    
    def save_to_file(self, name: str, code: str, metadata: Dict = None) -> Path:
        """保存技能到文件（新格式：技能目录）"""
        # 转换为小写作为目录名
        skill_name = name.lower()
        skill_dir = self.storage_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 skill.py
        skill_file = skill_dir / "skill.py"
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 保存 meta.json
        if metadata:
            meta_file = skill_dir / "meta.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return skill_file
    
    def clear(self):
        """清空注册表"""
        self._skills.clear()
        self._metadata.clear()
        self._instances.clear()
        logger.info("清空技能注册表")