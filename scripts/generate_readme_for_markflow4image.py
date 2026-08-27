#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动生成项目 README.md
扫描 skills/ 和 markflow/ 目录，生成完整的项目文档
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ReadmeGenerator:
    """自动生成 README.md"""
    
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir).resolve()
        self.skills_dir = self.root / "skills"
        self.markflow_dir = self.root / "markflow"
        self.template_dir = self.root / "markflow" / "templates" / "skills"
    
    def get_all_skills(self) -> List[Dict]:
        """获取所有技能信息"""
        skills = []
        if not self.skills_dir.exists():
            return skills
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            meta_file = skill_dir / "meta.json"
            if not meta_file.exists():
                continue
            
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                skill_info = {
                    'name': skill_dir.name,
                    'display_name': meta.get('name', skill_dir.name),
                    'description': meta.get('description', ''),
                    'version': meta.get('version', '1.0.0'),
                    'dependencies': meta.get('dependencies', []),
                    'inputs': meta.get('inputs', []),
                    'outputs': meta.get('outputs', []),
                    'has_readme': (skill_dir / "README.md").exists(),
                    'dir': skill_dir
                }
                skills.append(skill_info)
            except Exception as e:
                print(f"⚠️ 读取 {skill_dir.name} 失败: {e}")
        
        # 按名称排序
        return sorted(skills, key=lambda x: x['name'])
    
    def get_framework_modules(self) -> List[Dict]:
        """获取框架模块信息"""
        modules = []
        core_dir = self.markflow_dir / "core"
        
        if core_dir.exists():
            for py_file in core_dir.glob("*.py"):
                if py_file.name.startswith('_'):
                    continue
                # 提取模块描述
                description = self._extract_module_desc(py_file)
                modules.append({
                    'name': py_file.stem,
                    'file': py_file.name,
                    'description': description
                })
        
        return sorted(modules, key=lambda x: x['name'])
    
    def _extract_module_desc(self, file_path: Path) -> str:
        """从文件提取模块描述"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 提取第一行注释或 docstring
            lines = content.split('\n')
            for line in lines[:5]:
                line = line.strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # 提取 docstring 第一行
                    doc_lines = []
                    for l in lines[1:]:
                        if l.strip().endswith('"""') or l.strip().endswith("'''"):
                            break
                        doc_lines.append(l.strip())
                    if doc_lines:
                        return ' '.join(doc_lines[:2])
                elif line.startswith('#') and not line.startswith('#!'):
                    return line[1:].strip()
            return ''
        except:
            return ''
    
    def get_template_skills(self) -> List[str]:
        """获取模板技能列表"""
        if not self.template_dir.exists():
            return []
        return [f.stem for f in self.template_dir.glob("*.md")]
    
    def generate_badge(self, text: str, color: str = "blue") -> str:
        """生成徽章"""
        return f"[![{text}](https://img.shields.io/badge/{text.replace(' ', '%20')}-{color}.svg)]"
    
    def generate(self) -> str:
        """生成完整的 README 内容"""
        skills = self.get_all_skills()
        modules = self.get_framework_modules()
        templates = self.get_template_skills()
        
        lines = []
        
        # ==================== 标题 ====================
        lines.append("# MarkFlow")
        lines.append("")
        lines.append("> 🚀 从 Markdown 到可执行技能的工作流引擎")
        lines.append("")
        lines.append(f"[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)")
        lines.append("[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)")
        lines.append("[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)")
        lines.append("")
        lines.append("MarkFlow 是一个轻量级的技能生成框架，让你用 **Markdown** 编写技能描述，自动生成可执行的 **Python** 代码。")
        lines.append("")
        
        # ==================== 核心特性 ====================
        lines.append("## ✨ 核心特性")
        lines.append("")
        lines.append("- 📝 **Markdown 驱动**：用自然语言编写技能描述，无需编写重复的代码框架")
        lines.append("- 🚀 **自动生成代码**：从 Markdown 自动生成完整的 Python 可执行代码")
        lines.append("- 🔌 **热加载支持**：动态加载和更新技能，开发无需重启")
        lines.append("- 🎨 **内置模板**：基础、数据处理、API 客户端等多种模板开箱即用")
        lines.append("- 💻 **CLI 工具**：便捷的命令行操作，一行命令完成构建和执行")
        lines.append("- 🖥️ **GUI 界面**：图形化操作界面，参数分组显示，一键执行")
        lines.append("- 📦 **模块化设计**：每个技能独立目录，输出隔离，易于管理")
        lines.append("")
        
        # ==================== 已安装技能 ====================
        if skills:
            lines.append("## 📦 已安装技能")
            lines.append("")
            lines.append(f"共 **{len(skills)}** 个技能：")
            lines.append("")
            lines.append("| 技能 | 描述 | 版本 |")
            lines.append("|------|------|------|")
            for skill in skills:
                desc = skill['description'][:40] + "..." if len(skill['description']) > 40 else skill['description']
                lines.append(f"| `{skill['name']}` | {desc} | {skill['version']} |")
            lines.append("")
        
        # ==================== 代表性技能 ====================
        lines.append("## 🎯 代表性技能")
        lines.append("")
        
        # SD 图片生成器
        sd_skill = next((s for s in skills if s['name'] == 'sd_image_generator'), None)
        if sd_skill:
            lines.append("### 🎨 SD 图片生成器")
            lines.append("")
            lines.append(f"{sd_skill['description']}")
            lines.append("")
            lines.append("```bash")
            lines.append("python -m markflow.cli.commands execute sd_image_generator prompt=\"a beautiful sunset\" model_name=\"sd-v1-5-tiny.safetensors\"")
            lines.append("```")
            lines.append("")
            lines.append(f"📖 [详细文档](skills/sd_image_generator/README.md)")
            lines.append("")
        
        # 小说生成器
        novel_skill = next((s for s in skills if s['name'] == 'novel_writer'), None)
        if novel_skill:
            lines.append("### 📖 AI 小说生成器")
            lines.append("")
            lines.append(f"{novel_skill['description']}")
            lines.append("")
            lines.append("```bash")
            lines.append("python -m markflow.cli.commands execute novel_writer genre=\"科幻\" title=\"星际行者\" outline=\"探索宇宙\" chapter_count=3")
            lines.append("```")
            lines.append("")
            lines.append(f"📖 [详细文档](skills/novel_writer/README.md)")
            lines.append("")
        
        # 语音助手
        voice_skill = next((s for s in skills if s['name'] == 'voice_assistant'), None)
        if voice_skill:
            lines.append("### 🎙️ 语音助手")
            lines.append("")
            lines.append(f"{voice_skill['description']}")
            lines.append("")
            lines.append("```bash")
            lines.append("python -m markflow.cli.commands execute voice_assistant action=\"tts\" text=\"你好，欢迎使用 MarkFlow\"")
            lines.append("```")
            lines.append("")
            lines.append(f"📖 [详细文档](skills/voice_assistant/README.md)")
            lines.append("")
        
        # 图片工具箱
        image_toolbox = next((s for s in skills if s['name'] == 'image_toolbox'), None)
        if image_toolbox:
            lines.append("### 🖼️ 图片工具箱")
            lines.append("")
            lines.append(f"{image_toolbox['description']}")
            lines.append("")
            lines.append("```bash")
            lines.append("python -m markflow.cli.commands execute image_toolbox source_dir=\"./images\" operations=\"compress\" quality=85")
            lines.append("```")
            lines.append("")
            lines.append(f"📖 [详细文档](skills/image_toolbox/README.md)")
            lines.append("")
        
        # 图片查看器
        viewer_skill = next((s for s in skills if s['name'] == 'image_viewer'), None)
        if viewer_skill:
            lines.append("### 👁️ 图片查看器")
            lines.append("")
            lines.append(f"{viewer_skill['description']}")
            lines.append("")
            lines.append("```bash")
            lines.append("python -m markflow.cli.commands execute image_viewer action=\"browse\" source_dir=\"./images\"")
            lines.append("```")
            lines.append("")
            lines.append(f"📖 [详细文档](skills/image_viewer/README.md)")
            lines.append("")
        
        # ==================== 框架架构 ====================
        lines.append("## 🏗️ 框架架构")
        lines.append("")
        lines.append("```")
        lines.append("┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐")
        lines.append("│  Markdown   │───▶│   Parser    │───▶│  Generator  │───▶│   Skill     │")
        lines.append("│  描述文件    │    │  解析器     │    │  代码生成器  │    │  可执行代码  │")
        lines.append("└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘")
        lines.append("                                                                  │")
        lines.append("                                                                  ▼")
        lines.append("┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐")
        lines.append("│   User      │◀───│  Executor   │◀───│  Registry   │◀───│   Skill     │")
        lines.append("│   用户执行   │    │  执行器     │    │  注册中心   │    │  实例化     │")
        lines.append("└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘")
        lines.append("```")
        lines.append("")
        
        # ==================== 核心模块 ====================
        lines.append("### 核心模块")
        lines.append("")
        lines.append("| 模块 | 职责 |")
        lines.append("|------|------|")
        module_descs = {
            'parser': '解析 Markdown，提取技能规格（名称、参数、步骤等）',
            'generator': '从规格生成完整的 Python 可执行代码',
            'registry': '管理已注册的技能，支持动态加载',
            'executor': '创建技能实例并执行',
        }
        for mod in modules:
            desc = module_descs.get(mod['name'], mod['description'] or '')
            lines.append(f"| **{mod['name'].capitalize()}** | {desc} |")
        lines.append("| **CLI** | 命令行交互接口 |")
        lines.append("| **GUI** | 图形化操作界面 |")
        lines.append("")
        
        # ==================== 项目结构 ====================
        lines.append("## 📂 项目结构")
        lines.append("")
        lines.append("```")
        lines.append("MarkFlow/")
        lines.append("├── markflow/                         # 框架核心")
        lines.append("│   ├── core/                         # 核心模块")
        lines.append("│   │   ├── parser.py                 # Markdown 解析器")
        lines.append("│   │   ├── generator.py              # 代码生成器")
        lines.append("│   │   ├── registry.py               # 技能注册中心")
        lines.append("│   │   └── executor.py               # 技能执行器")
        lines.append("│   ├── cli/                          # CLI 工具")
        lines.append("│   │   └── commands.py")
        lines.append("│   ├── gui/                          # GUI 图形界面")
        lines.append("│   │   ├── __init__.py")
        lines.append("│   │   ├── __main__.py")
        lines.append("│   │   └── launcher.py")
        lines.append("│   ├── templates/                    # 模板管理")
        lines.append("│   │   ├── base.py                   # 模板管理器")
        lines.append("│   │   └── skills/                   # 技能定义模板")
        lines.append("│   └── utils/                        # 工具函数")
        lines.append("│       └── code_collect.py           # 代码收集/打包")
        lines.append("├── scripts/                          # 工具脚本")
        lines.append("│   ├── generate_all_girls.py         # 图片批量生成")
        lines.append("│   ├── novel_generator.py            # 小说生成")
        lines.append("│   ├── novel_scheduler.py            # 小说定时任务")
        lines.append("│   ├── generate_skill_readme.py      # 技能 README 生成")
        lines.append("│   └── markflow_gui.py               # GUI 启动")
        lines.append("├── skills/                           # 已安装的技能")
        for skill in skills:
            lines.append(f"│   ├── {skill['name']}/                 # {skill['display_name']}")
            lines.append("│   │   ├── skill.py              # 可执行代码")
            lines.append("│   │   ├── meta.json             # 元数据")
            lines.append("│   │   ├── skill.md              # 技能文档")
            lines.append("│   │   └── output/               # 输出目录")
        lines.append("├── collected_code/                   # 代码快照输出")
        lines.append("└── README.md                         # 项目文档")
        lines.append("```")
        lines.append("")
        
        # ==================== 快速开始 ====================
        lines.append("## 🚀 快速开始")
        lines.append("")
        lines.append("### 安装")
        lines.append("")
        lines.append("```bash")
        lines.append("git clone https://github.com/austinnie/MarkFlow.git")
        lines.append("cd MarkFlow")
        lines.append("```")
        lines.append("")
        lines.append("### 创建你的第一个技能")
        lines.append("")
        lines.append("**1. 编写技能描述** `hello.md`")
        lines.append("")
        lines.append("```markdown")
        lines.append("# HelloWorld")
        lines.append("")
        lines.append("## 描述")
        lines.append("一个简单的问候技能")
        lines.append("")
        lines.append("## 输入")
        lines.append("- name: string: 要问候的名字")
        lines.append("")
        lines.append("## 输出")
        lines.append("- greeting: 问候语")
        lines.append("")
        lines.append("## 步骤")
        lines.append("1. 获取名字")
        lines.append("2. 生成问候语")
        lines.append("3. 返回结果")
        lines.append("```")
        lines.append("")
        lines.append("**2. 构建技能**")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m markflow.cli.commands build hello.md")
        lines.append("```")
        lines.append("")
        lines.append("**3. 执行技能**")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m markflow.cli.commands execute HelloWorld name=MarkFlow")
        lines.append("```")
        lines.append("")
        lines.append("输出：")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "status": "success",')
        lines.append('  "result": {')
        lines.append('    "greeting": "Hello, MarkFlow!"')
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")
        
        # ==================== CLI 命令 ====================
        lines.append("## 📖 CLI 命令")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m markflow.cli.commands --help")
        lines.append("```")
        lines.append("")
        lines.append("| 命令 | 说明 | 示例 |")
        lines.append("|------|------|------|")
        lines.append("| `build <file>` | 从 Markdown 文件构建技能 | `build weather.md` |")
        lines.append("| `execute <skill>` | 执行技能 | `execute sd_image_generator prompt=\"test\"` |")
        lines.append("| `list` | 列出所有已注册的技能 | `list` |")
        lines.append("| `info <skill>` | 查看技能详情 | `info sd_image_generator` |")
        lines.append("| `generate -t <type> -n <name>` | 从模板生成技能 | `generate -t data -n data_cleaner` |")
        lines.append("| `remove <skill>` | 删除技能 | `remove sd_image_generator` |")
        lines.append("")
        
        # ==================== GUI ====================
        lines.append("## 🖥️ GUI 图形界面")
        lines.append("")
        lines.append("```bash")
        lines.append("python scripts/markflow_gui.py")
        lines.append("```")
        lines.append("")
        lines.append("或")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m markflow.gui")
        lines.append("```")
        lines.append("")
        lines.append("### GUI 功能")
        lines.append("")
        lines.append("| 功能 | 说明 |")
        lines.append("|------|------|")
        lines.append("| 技能列表 | 左侧显示所有已安装技能 |")
        lines.append("| 参数配置 | 选择技能后自动生成参数输入框 |")
        lines.append("| 分组折叠 | 参数按功能分组，可折叠/展开 |")
        lines.append("| 一键执行 | 填写参数后点击执行按钮 |")
        lines.append("| 日志输出 | 彩色日志显示执行过程和结果 |")
        lines.append("")
        
        # ==================== 贡献 ====================
        lines.append("## 🤝 贡献")
        lines.append("")
        lines.append("欢迎贡献！")
        lines.append("")
        lines.append("### 贡献方式")
        lines.append("")
        lines.append("1. **报告 Bug**：在 Issues 中详细描述问题")
        lines.append("2. **提交代码**：通过 Pull Request 提交改进")
        lines.append("3. **完善文档**：改进 README 或添加示例")
        lines.append("4. **提出建议**：在 Issues 中讨论新功能")
        lines.append("")
        lines.append("### 开发流程")
        lines.append("")
        lines.append("1. Fork 本仓库")
        lines.append("2. 创建你的特性分支")
        lines.append("3. 提交你的修改")
        lines.append("4. 推送到分支")
        lines.append("5. 开启一个 Pull Request")
        lines.append("")
        
        # ==================== 许可证 ====================
        lines.append("## 📄 许可证")
        lines.append("")
        lines.append("本项目采用 MIT 许可证")
        lines.append("")
        lines.append("## 🌟 支持")
        lines.append("")
        lines.append("如果这个项目对你有帮助，请给一个 Star ⭐️")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*文档自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("Made with ❤️ by MarkFlow Team")
        
        return '\n'.join(lines)


def main():
    """生成 README.md"""
    generator = ReadmeGenerator(".")
    content = generator.generate()
    
    output_file = Path("README.md")
    output_file.write_text(content, encoding='utf-8')
    
    skills = generator.get_all_skills()
    print(f"✅ README.md 已生成!")
    print(f"   📦 技能数: {len(skills)}")
    print(f"   📂 输出: {output_file.absolute()}")


if __name__ == "__main__":
    main()